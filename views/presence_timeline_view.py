import numpy as np

from core.config import VISUALIZATION
from views.mpl_widget import TimedMplWidget


class PresenceTimelineView(TimedMplWidget):
    def __init__(self, vm, parent=None):
        super().__init__(vm, parent)
        window_s = VISUALIZATION.presence_window_ms / 1000.0
        bins = VISUALIZATION.presence_bins

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(VISUALIZATION.background_color)
        self.ax.set_title("Присутствие", pad=8)
        self.ax.set_xlabel("Время, с")
        self.ax.set_xlim(-window_s, 0)
        self.ax.set_ylim(-0.5, 2.5)
        self.ax.set_yticks([0, 1, 2])
        self.ax.set_yticklabels(list(VISUALIZATION.target_labels))
        self.ax.grid(True, axis="x", alpha=VISUALIZATION.grid_alpha)

        empty = np.zeros((3, bins, 4), dtype=np.float32)
        self.image = self.ax.imshow(
            empty, aspect="auto", origin="lower",
            extent=[-window_s, 0, -0.5, 2.5],
            interpolation="nearest", zorder=2,
        )
        self.speed_lines = []
        for color in VISUALIZATION.target_colors:
            line, = self.ax.plot([], [], color=color, lw=1.3, zorder=4)
            self.speed_lines.append(line)

        self._rgba_colors = np.array(
            [self._hex_to_rgb(color) for color in VISUALIZATION.target_colors],
            dtype=np.float32,
        )

    def _hex_to_rgb(self, color: str):
        value = color.lstrip("#")
        return [int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def _render(self):
        if self._latest is None:
            return
        presence = np.asarray(self._latest["presence"], dtype=np.float32)
        speeds = np.asarray(self._latest["speed_series"], dtype=np.float32)
        window_s = float(self._latest["presence_window_s"])
        bins = presence.shape[1]

        rgba = np.zeros((3, bins, 4), dtype=np.float32)
        rgba[..., :3] = self._rgba_colors[:, None, :]
        rgba[..., 3] = presence * 0.78
        self.image.set_data(rgba)
        self.image.set_extent([-window_s, 0, -0.5, 2.5])

        times = np.linspace(-window_s, 0, bins)
        speed_norm = np.clip(np.nan_to_num(speeds, nan=0.0) / 80.0, 0.0, 1.0)
        for index, line in enumerate(self.speed_lines):
            y = index - 0.35 + 0.7 * speed_norm[index]
            y = np.where(presence[index] > 0.5, y, np.nan)
            line.set_data(times, y)
        self.canvas.draw_idle()

    def clear(self):
        self._latest = None
        bins = VISUALIZATION.presence_bins
        self.image.set_data(np.zeros((3, bins, 4), dtype=np.float32))
        for line in self.speed_lines:
            line.set_data([], [])
        self.canvas.draw_idle()
