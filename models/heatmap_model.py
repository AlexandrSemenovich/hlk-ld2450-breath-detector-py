from collections import deque

import numpy as np

from core.config import HEATMAP, SETTINGS_DEFAULTS, VISUALIZATION, HeatmapConfig


class HeatmapModel:
    def __init__(self, config: HeatmapConfig = HEATMAP):
        self.max_range = config.max_range_mm
        self.bins_x = config.bins
        self.bins_y = config.bins

        self.heat = np.zeros((self.bins_y, self.bins_x), dtype=np.float32)
        self.range_profile = np.zeros(self.bins_y, dtype=np.float32)
        self.last_ts_ms = None
        self._occupied_since_ms = None

        self.trails = [deque(), deque(), deque()]
        self.presence_log = deque()
        self.history_max = config.history_max

        self.kernel_r = config.kernel_radius
        self.kernel = self._make_gaussian_kernel(2 * config.kernel_radius + 1, config.kernel_sigma)
        self.kernel_1d = self.kernel[self.kernel_r]

        self.intensity_baseline = config.intensity_baseline
        self.contrast_divisor = config.contrast_divisor

        self.fade_time_ms = SETTINGS_DEFAULTS.fade_time_ms
        self.point_intensity = SETTINGS_DEFAULTS.point_intensity
        self.trail_time_ms = SETTINGS_DEFAULTS.trail_time_ms
        self.trail_points_max = SETTINGS_DEFAULTS.trail_points_max

    def _make_gaussian_kernel(self, size=9, sigma=1.5):
        r = size // 2
        ax = np.arange(-r, r + 1, dtype=np.float32)
        xx, yy = np.meshgrid(ax, ax)
        k = np.exp(-(xx * xx + yy * yy) / (2.0 * sigma * sigma))
        k /= np.max(k) if np.max(k) > 0 else 1.0
        return k.astype(np.float32)

    def _mm_to_bin(self, x_mm, y_mm):
        x_mm = float(x_mm)
        y_mm = float(y_mm)

        x_mm = max(-self.max_range, min(self.max_range, x_mm))
        y_mm = max(0.0, min(self.max_range, y_mm))

        t_x = (x_mm + self.max_range) / (2.0 * self.max_range)
        t_y = y_mm / self.max_range

        ix = int(t_x * (self.bins_x - 1) + 0.5)
        iy = int(t_y * (self.bins_y - 1) + 0.5)

        ix = max(0, min(self.bins_x - 1, ix))
        iy = max(0, min(self.bins_y - 1, iy))
        return iy, ix

    def _add_kernel_to_heat(self, iy, ix, add_value):
        r = self.kernel_r
        k = self.kernel

        y0 = iy - r
        y1 = iy + r + 1
        x0 = ix - r
        x1 = ix + r + 1

        yy0 = max(0, y0)
        yy1 = min(self.bins_y, y1)
        xx0 = max(0, x0)
        xx1 = min(self.bins_x, x1)

        ky0 = yy0 - y0
        ky1 = ky0 + (yy1 - yy0)
        kx0 = xx0 - x0
        kx1 = kx0 + (xx1 - xx0)

        if yy0 < yy1 and xx0 < xx1:
            self.heat[yy0:yy1, xx0:xx1] += k[ky0:ky1, kx0:kx1] * add_value

    def _add_kernel_to_range(self, iy, add_value):
        r = self.kernel_r
        k = self.kernel_1d
        y0 = iy - r
        y1 = iy + r + 1
        yy0 = max(0, y0)
        yy1 = min(self.bins_y, y1)
        ky0 = yy0 - y0
        ky1 = ky0 + (yy1 - yy0)
        if yy0 < yy1:
            self.range_profile[yy0:yy1] += k[ky0:ky1] * add_value

    def ingest(self, frame):
        ts = frame.timestamp_ms

        tau = max(1, int(self.fade_time_ms))
        if self.last_ts_ms is not None and ts > 0 and self.last_ts_ms > 0:
            dt = max(0, ts - self.last_ts_ms)
            decay = float(np.exp(-dt / tau))
        else:
            decay = float(np.exp(-10.0 / tau))

        self.heat *= decay
        self.range_profile *= decay
        add_value = float(self.point_intensity) / self.intensity_baseline
        if ts is not None and ts > 0:
            self.last_ts_ms = ts

        currents = []
        presents = []
        speeds = []
        for index, target in enumerate(frame.targets):
            if not target.present:
                currents.append(self._empty_current())
                presents.append(False)
                speeds.append(0.0)
                continue

            x, y = float(target.x), float(target.y)
            speed = float(target.speed)
            iy, ix = self._mm_to_bin(x, y)
            self._add_kernel_to_heat(iy, ix, add_value)
            self._add_kernel_to_range(iy, add_value)
            self.trails[index].append((x, y, ts, speed))
            while len(self.trails[index]) > self.history_max:
                self.trails[index].popleft()
            currents.append({
                "x": x,
                "y": y,
                "speed": speed,
                "present": True,
            })
            presents.append(True)
            speeds.append(speed)

        now_ts = self.last_ts_ms if self.last_ts_ms is not None else 0
        self._update_presence_log(now_ts, presents, speeds)
        occupancy = self._compute_occupancy(now_ts, presents)

        trails = []
        scene_trails = []
        trails_points = []
        for trail in self.trails:
            points = self._prune_trail(list(trail), ts, self.trail_time_ms)
            scene_points = self._prune_trail(list(trail), ts, VISUALIZATION.scene_trail_ms)
            trails.append(self._trail_payload(points))
            scene_trails.append(self._trail_payload(scene_points))
            trails_points.append(points)

        vmax_now = float(np.max(self.heat))
        if vmax_now < 1e-6:
            vmax_now = 1.0
        contrast = float(self.point_intensity) / self.contrast_divisor
        vmax = max(1e-3, vmax_now * max(0.5, contrast))

        range_vmax = float(np.max(self.range_profile))
        if range_vmax < 1e-6:
            range_vmax = 1.0

        presence, speed_series = self._presence_arrays(now_ts)
        stats = self._compute_stats(trails_points, occupancy)

        return {
            "heat": self.heat,
            "vmax": vmax,
            "trails": trails,
            "scene_trails": scene_trails,
            "currents": currents,
            "range_profile": self.range_profile,
            "range_vmax": range_vmax,
            "presence": presence,
            "speed_series": speed_series,
            "presence_window_s": VISUALIZATION.presence_window_ms / 1000.0,
            "occupancy": occupancy,
            "stats": stats,
        }

    def _empty_current(self):
        return {
            "x": float("nan"),
            "y": float("nan"),
            "speed": 0.0,
            "present": False,
        }

    def _trail_payload(self, points):
        return {
            "xs": [p[0] for p in points],
            "ys": [p[1] for p in points],
        }

    def _update_presence_log(self, ts, presents, speeds):
        self.presence_log.append((ts, tuple(presents), tuple(speeds)))
        cutoff = ts - int(VISUALIZATION.presence_window_ms)
        while self.presence_log and self.presence_log[0][0] < cutoff:
            self.presence_log.popleft()

    def _compute_occupancy(self, ts, presents):
        count = int(sum(1 for present in presents if present))
        occupied = count > 0
        if not occupied:
            self._occupied_since_ms = None
            dwell_s = 0.0
        else:
            if self._occupied_since_ms is None or (
                ts > 0 and self._occupied_since_ms > 0 and ts < self._occupied_since_ms
            ):
                self._occupied_since_ms = ts if ts > 0 else self._occupied_since_ms
            if self._occupied_since_ms and ts > 0:
                dwell_s = max(0.0, (ts - self._occupied_since_ms) / 1000.0)
            else:
                dwell_s = 0.0
        return {
            "count": count,
            "occupied": occupied,
            "dwell_s": dwell_s,
        }

    def _presence_arrays(self, now_ts):
        bins = VISUALIZATION.presence_bins
        window_ms = int(VISUALIZATION.presence_window_ms)
        presence = np.zeros((3, bins), dtype=np.float32)
        speeds = np.full((3, bins), np.nan, dtype=np.float32)
        if now_ts <= 0 or not self.presence_log:
            return presence, speeds

        t0 = now_ts - window_ms
        for ts, presents, target_speeds in self.presence_log:
            if ts < t0:
                continue
            col = int((ts - t0) / window_ms * (bins - 1) + 0.5)
            col = max(0, min(bins - 1, col))
            for index, present in enumerate(presents):
                if present:
                    presence[index, col] = 1.0
                    speeds[index, col] = abs(float(target_speeds[index]))
        return presence, speeds

    def _prune_trail(self, points, ts, window_ms):
        limit = int(self.trail_points_max)
        if ts is not None and ts > 0:
            cutoff = ts - int(window_ms)
            pruned = [
                item for item in points
                if item[2] is not None and item[2] > 0 and item[2] >= cutoff
            ]
            if not pruned:
                pruned = points[-limit:]
            return pruned
        return points[-limit:]

    def _compute_stats(self, trails_points, occupancy):
        heat_sum = float(np.sum(self.heat))
        n = sum(len(points) for points in trails_points)
        max_y = 0.0
        dist_mm = 0.0
        for points in trails_points:
            if not points:
                continue
            ys = np.array([p[1] for p in points], dtype=np.float64)
            max_y = max(max_y, float(np.max(ys)))
            if len(points) >= 2:
                xs = np.array([p[0] for p in points], dtype=np.float64)
                dist_mm += float(np.sqrt(np.diff(xs) ** 2 + np.diff(ys) ** 2).sum())

        return {
            "points": n,
            "max_y": max_y,
            "distance_m": dist_mm / 1000.0,
            "heat_sum": heat_sum,
            "people_count": occupancy["count"],
            "dwell_s": occupancy["dwell_s"],
        }

    def snapshot(self):
        empty_current = [self._empty_current() for _ in range(3)]
        empty_trail = {"xs": [], "ys": []}
        occupancy = {"count": 0, "occupied": False, "dwell_s": 0.0}
        return {
            "heat": self.heat,
            "vmax": 1.0,
            "trails": [empty_trail] * 3,
            "scene_trails": [empty_trail] * 3,
            "currents": empty_current,
            "range_profile": self.range_profile,
            "range_vmax": 1.0,
            "presence": np.zeros((3, VISUALIZATION.presence_bins), dtype=np.float32),
            "speed_series": np.full((3, VISUALIZATION.presence_bins), np.nan, dtype=np.float32),
            "presence_window_s": VISUALIZATION.presence_window_ms / 1000.0,
            "occupancy": occupancy,
            "stats": self._compute_stats([], occupancy),
        }

    def clear(self):
        self.heat[:] = 0.0
        self.range_profile[:] = 0.0
        self.last_ts_ms = None
        self._occupied_since_ms = None
        self.presence_log.clear()
        for trail in self.trails:
            trail.clear()
