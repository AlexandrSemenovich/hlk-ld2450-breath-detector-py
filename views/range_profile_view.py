import numpy as np
from matplotlib.collections import PolyCollection

from core.config import HEATMAP, VISUALIZATION
from views.mpl_widget import TimedMplWidget


class RangeProfileView(TimedMplWidget):
    def __init__(self, vm, parent=None):
        super().__init__(vm, parent)
        self.max_range = HEATMAP.max_range_mm
        self.bins = vm.model.bins_y
        self.bin_height = self.max_range / self.bins
        self.bar_h = self.bin_height * 0.95

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(VISUALIZATION.background_color)
        self.ax.set_title("")
        self.ax.set_xlabel("")
        self.ax.set_ylabel("")
        self.ax.set_xlim(0, 1.0)
        self.ax.set_ylim(0, self.max_range)
        self.ax.grid(True, axis="x", alpha=VISUALIZATION.grid_alpha)
        self._apply_inner_ticks()

        self.bars = PolyCollection(
            self._bar_verts(np.zeros(self.bins)),
            facecolors="#90caf9",
            edgecolors="none",
            zorder=2,
        )
        self.ax.add_collection(self.bars)
        self.markers = []
        for color in VISUALIZATION.target_colors:
            marker, = self.ax.plot(
                [], [], "o", color=color, markersize=8, zorder=4,
            )
            self.markers.append(marker)

    def _sync_figure_size(self):
        self._invalidate_blit()
        if not self._fill_axes(inset=0.02):
            return
        self._apply_inner_ticks()
        self._dirty = True
        if self.isVisible():
            self.canvas.draw_idle()

    def _bar_verts(self, widths):
        widths = np.asarray(widths, dtype=np.float64).reshape(self.bins)
        y0 = (np.arange(self.bins) + 0.5) * self.bin_height - self.bar_h / 2.0
        verts = np.empty((self.bins, 4, 2), dtype=np.float64)
        verts[:, 0, 0] = 0.0
        verts[:, 0, 1] = y0
        verts[:, 1, 0] = widths
        verts[:, 1, 1] = y0
        verts[:, 2, 0] = widths
        verts[:, 2, 1] = y0 + self.bar_h
        verts[:, 3, 0] = 0.0
        verts[:, 3, 1] = y0 + self.bar_h
        return verts

    def _blit_artists(self):
        return (self.bars, *self.markers)

    def _render(self):
        if self._latest is None:
            return
        profile = np.asarray(self._latest["range_profile"], dtype=np.float64)
        vmax = max(float(self._latest["range_vmax"]), 1e-6)
        widths = np.clip(profile / vmax, 0.0, 1.0)
        self.bars.set_verts(self._bar_verts(widths))

        for marker, current in zip(self.markers, self._latest["currents"]):
            if current.get("present"):
                marker.set_data([0.12], [current["y"]])
                marker.set_visible(True)
            else:
                marker.set_data([], [])
                marker.set_visible(False)
        self._draw_dynamic()

    def clear(self):
        self._latest = None
        self.bars.set_verts(self._bar_verts(np.zeros(self.bins)))
        for marker in self.markers:
            marker.set_data([], [])
            marker.set_visible(False)
        self._invalidate_blit()
        self._dirty = True
        if self.isVisible():
            self.canvas.draw_idle()
