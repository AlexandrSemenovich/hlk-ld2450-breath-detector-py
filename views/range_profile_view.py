import numpy as np

from core.config import HEATMAP, VISUALIZATION
from views.mpl_widget import TimedMplWidget


class RangeProfileView(TimedMplWidget):
    def __init__(self, vm, parent=None):
        super().__init__(vm, parent)
        self.max_range = HEATMAP.max_range_mm
        self.bins = vm.model.bins_y
        self.bin_height = self.max_range / self.bins
        self.centers = (np.arange(self.bins) + 0.5) * self.bin_height

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(VISUALIZATION.background_color)
        self.ax.set_title("Дальность", pad=8)
        self.ax.set_xlabel("Занятость")
        self.ax.set_ylabel("Y (мм)")
        self.ax.set_xlim(0, 1.0)
        self.ax.set_ylim(0, self.max_range)
        self.ax.grid(True, axis="x", alpha=VISUALIZATION.grid_alpha)

        self.bars = self.ax.barh(
            self.centers, np.zeros(self.bins), height=self.bin_height * 0.95,
            color="#90caf9", edgecolor="none", zorder=2,
        )
        self.markers = []
        for color in VISUALIZATION.target_colors:
            marker, = self.ax.plot(
                [], [], "o", color=color, markersize=8, zorder=4,
            )
            self.markers.append(marker)

    def _render(self):
        if self._latest is None:
            return
        profile = np.asarray(self._latest["range_profile"], dtype=np.float64)
        vmax = max(float(self._latest["range_vmax"]), 1e-6)
        widths = np.clip(profile / vmax, 0.0, 1.0)
        for bar, width in zip(self.bars, widths):
            bar.set_width(float(width))

        for marker, current in zip(self.markers, self._latest["currents"]):
            if current.get("present"):
                marker.set_data([0.12], [current["y"]])
            else:
                marker.set_data([], [])
        self.canvas.draw_idle()

    def clear(self):
        self._latest = None
        for bar in self.bars:
            bar.set_width(0.0)
        for marker in self.markers:
            marker.set_data([], [])
        self.canvas.draw_idle()
