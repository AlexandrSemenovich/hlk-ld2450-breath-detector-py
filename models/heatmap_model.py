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
        self.history_max = config.history_max
        bins = VISUALIZATION.presence_bins
        self.presence = np.zeros((3, bins), dtype=np.float32)
        self.speed_series = np.full((3, bins), np.nan, dtype=np.float32)
        self._presence_now_ts = None
        self._currents = [self._empty_current() for _ in range(3)]
        self._ingest_count = 0

        self.kernel_r = config.kernel_radius
        self.kernel = self._make_gaussian_kernel(2 * config.kernel_radius + 1, config.kernel_sigma)
        self.kernel_1d = self.kernel[self.kernel_r]

        self.intensity_baseline = config.intensity_baseline
        self.contrast_divisor = config.contrast_divisor

        self.fade_time_ms = SETTINGS_DEFAULTS.fade_time_ms
        self.point_intensity = SETTINGS_DEFAULTS.point_intensity
        self.trail_time_ms = SETTINGS_DEFAULTS.trail_time_ms
        self.trail_points_max = SETTINGS_DEFAULTS.trail_points_max
        self.mirror_x = SETTINGS_DEFAULTS.mirror_x
        self._last_occupancy = {"count": 0, "occupied": False, "dwell_s": 0.0}

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

            x, y = self._map_x(float(target.x)), float(target.y)
            speed = float(target.speed)
            iy, ix = self._mm_to_bin(x, y)
            self._add_kernel_to_heat(iy, ix, add_value)
            self._add_kernel_to_range(iy, add_value)
            self.trails[index].append((x, y, ts, speed))
            currents.append({
                "x": x,
                "y": y,
                "speed": speed,
                "present": True,
            })
            presents.append(True)
            speeds.append(speed)

        now_ts = self.last_ts_ms if self.last_ts_ms is not None else 0
        self._trim_trails(now_ts)
        self._update_presence_ring(now_ts, presents, speeds)
        occupancy = self._compute_occupancy(now_ts, presents)
        self._currents = currents
        self._last_occupancy = occupancy
        self._ingest_count += 1

    def _map_x(self, x: float) -> float:
        return -x if self.mirror_x else x

    def set_mirror_x(self, enabled: bool):
        enabled = bool(enabled)
        if self.mirror_x == enabled:
            return False
        self.mirror_x = enabled
        self.heat[:] = np.fliplr(self.heat)
        for index, trail in enumerate(self.trails):
            self.trails[index] = deque(
                (-x, y, ts, speed) for (x, y, ts, speed) in trail
            )
        for current in self._currents:
            if current.get("present"):
                current["x"] = -current["x"]
        return True

    def payload_from_state(self):
        ingest_batch = self._ingest_count
        self._ingest_count = 0
        occupancy = self._last_occupancy
        vmax_now = float(np.max(self.heat))
        if vmax_now < 1e-6:
            vmax_now = 1.0
        contrast = float(self.point_intensity) / self.contrast_divisor
        vmax = max(1e-3, vmax_now * max(0.5, contrast))

        range_vmax = float(np.max(self.range_profile))
        if range_vmax < 1e-6:
            range_vmax = 1.0

        stats = self._compute_stats(occupancy)
        stats["ingest_batch"] = ingest_batch
        stats["trail_len"] = sum(len(trail) for trail in self.trails)

        return {
            "heat": self.heat,
            "vmax": vmax,
            "currents": self._currents,
            "range_profile": self.range_profile,
            "range_vmax": range_vmax,
            "presence": self.presence,
            "speed_series": self.speed_series,
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

    def _trail_count_limit(self) -> int:
        return max(1, min(int(self.trail_points_max), int(self.history_max)))

    def _trail_window_ms(self) -> int:
        return max(int(self.trail_time_ms), int(VISUALIZATION.scene_trail_ms))

    def _trim_trails(self, ts):
        limit = self._trail_count_limit()
        cutoff = None
        if ts is not None and ts > 0:
            cutoff = ts - self._trail_window_ms()
        for trail in self.trails:
            if cutoff is not None:
                while trail:
                    item_ts = trail[0][2]
                    if item_ts is None or item_ts <= 0 or item_ts >= cutoff:
                        break
                    trail.popleft()
            while len(trail) > limit:
                trail.popleft()

    def _update_presence_ring(self, ts, presents, speeds):
        if ts is None or ts <= 0:
            return

        bins = VISUALIZATION.presence_bins
        window_ms = int(VISUALIZATION.presence_window_ms)
        now_ts = self._presence_now_ts
        if now_ts is None or now_ts <= 0:
            self._presence_now_ts = ts
        else:
            dt = ts - now_ts
            if dt < 0:
                self.presence.fill(0.0)
                self.speed_series.fill(np.nan)
                self._presence_now_ts = ts
            elif dt > 0:
                shift = int(dt / window_ms * (bins - 1) + 0.5)
                if shift >= bins:
                    self.presence.fill(0.0)
                    self.speed_series.fill(np.nan)
                    self._presence_now_ts = ts
                elif shift > 0:
                    self.presence[:, :-shift] = self.presence[:, shift:]
                    self.presence[:, -shift:] = 0.0
                    self.speed_series[:, :-shift] = self.speed_series[:, shift:]
                    self.speed_series[:, -shift:] = np.nan
                    self._presence_now_ts = ts

        for index, present in enumerate(presents):
            if present:
                self.presence[index, -1] = 1.0
                self.speed_series[index, -1] = abs(float(speeds[index]))

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

    def _compute_stats(self, occupancy):
        heat_sum = float(np.sum(self.heat))
        n = 0
        max_y = 0.0
        dist_mm = 0.0
        cutoff = None
        ts = self.last_ts_ms
        if ts is not None and ts > 0:
            cutoff = ts - int(self.trail_time_ms)
        for trail in self.trails:
            prev_x = None
            prev_y = None
            for x, y, item_ts, _speed in trail:
                if cutoff is not None and item_ts is not None and item_ts > 0 and item_ts < cutoff:
                    continue
                n += 1
                if y > max_y:
                    max_y = float(y)
                if prev_x is not None:
                    dx = x - prev_x
                    dy = y - prev_y
                    dist_mm += (dx * dx + dy * dy) ** 0.5
                prev_x, prev_y = x, y

        return {
            "points": n,
            "max_y": max_y,
            "distance_m": dist_mm / 1000.0,
            "heat_sum": heat_sum,
            "people_count": occupancy["count"],
            "dwell_s": occupancy["dwell_s"],
        }

    def snapshot(self):
        occupancy = {"count": 0, "occupied": False, "dwell_s": 0.0}
        stats = self._compute_stats(occupancy)
        stats["ingest_batch"] = 0
        stats["trail_len"] = 0
        return {
            "heat": self.heat,
            "vmax": 1.0,
            "currents": self._currents,
            "range_profile": self.range_profile,
            "range_vmax": 1.0,
            "presence": self.presence,
            "speed_series": self.speed_series,
            "presence_window_s": VISUALIZATION.presence_window_ms / 1000.0,
            "occupancy": occupancy,
            "stats": stats,
        }

    def clear(self):
        self.heat[:] = 0.0
        self.range_profile[:] = 0.0
        self.presence.fill(0.0)
        self.speed_series.fill(np.nan)
        self.last_ts_ms = None
        self._occupied_since_ms = None
        self._presence_now_ts = None
        self._ingest_count = 0
        self._currents = [self._empty_current() for _ in range(3)]
        self._last_occupancy = {"count": 0, "occupied": False, "dwell_s": 0.0}
        for trail in self.trails:
            trail.clear()
