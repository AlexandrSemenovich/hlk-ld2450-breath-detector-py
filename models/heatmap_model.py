from collections import deque

import numpy as np

from core.config import HEATMAP, SETTINGS_DEFAULTS, HeatmapConfig


class HeatmapModel:
    def __init__(self, config: HeatmapConfig = HEATMAP):
        self.max_range = config.max_range_mm
        self.bins_x = config.bins
        self.bins_y = config.bins

        self.heat = np.zeros((self.bins_y, self.bins_x), dtype=np.float32)
        self.last_ts_ms = None

        self.trail = deque()
        self.history_max = config.history_max

        self.kernel_r = config.kernel_radius
        self.kernel = self._make_gaussian_kernel(2 * config.kernel_radius + 1, config.kernel_sigma)

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
        kh, kw = k.shape

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

    def ingest(self, frame):
        x = frame.target.x
        y = frame.target.y
        ts = frame.timestamp_ms

        tau = max(1, int(self.fade_time_ms))
        if self.last_ts_ms is not None and ts > 0 and self.last_ts_ms > 0:
            dt = max(0, ts - self.last_ts_ms)
            decay = float(np.exp(-dt / tau))
        else:
            decay = float(np.exp(-10.0 / tau))

        self.heat *= decay

        iy, ix = self._mm_to_bin(x, y)
        add_value = float(self.point_intensity) / self.intensity_baseline
        self._add_kernel_to_heat(iy, ix, add_value)

        self.last_ts_ms = ts if (ts is not None and ts > 0) else self.last_ts_ms

        self.trail.append((x, y, ts))
        while len(self.trail) > self.history_max:
            self.trail.popleft()

        points = list(self.trail)
        if ts is not None and ts > 0:
            cutoff = ts - int(self.trail_time_ms)
            pruned = [(px, py, pts) for (px, py, pts) in points if (pts is not None and pts > 0 and pts >= cutoff)]
            if not pruned:
                pruned = points[-int(self.trail_points_max):]
            points = pruned
        else:
            points = points[-int(self.trail_points_max):]

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        vmax_now = float(np.max(self.heat))
        if vmax_now < 1e-6:
            vmax_now = 1.0

        contrast = float(self.point_intensity) / self.contrast_divisor
        vmax = max(1e-3, vmax_now * max(0.5, contrast))

        return {
            "heat": self.heat,
            "vmax": vmax,
            "trail_xs": xs,
            "trail_ys": ys,
            "current": (x, y),
            "stats": self._compute_stats(points),
        }

    def _compute_stats(self, points):
        n = len(points)
        if n < 2:
            return {
                "points": n,
                "max_y": 0.0,
                "distance_m": 0.0,
                "heat_sum": float(np.sum(self.heat)),
            }

        xs = np.array([p[0] for p in points], dtype=np.float64)
        ys = np.array([p[1] for p in points], dtype=np.float64)
        dist_mm = float(np.sqrt(np.diff(xs) ** 2 + np.diff(ys) ** 2).sum())

        return {
            "points": n,
            "max_y": float(np.max(ys)),
            "distance_m": dist_mm / 1000.0,
            "heat_sum": float(np.sum(self.heat)),
        }

    def snapshot(self):
        return {
            "heat": self.heat,
            "vmax": 1.0,
            "trail_xs": [],
            "trail_ys": [],
            "current": (float("nan"), float("nan")),
            "stats": self._compute_stats([]),
        }

    def clear(self):
        self.heat[:] = 0.0
        self.last_ts_ms = None
        self.trail.clear()
