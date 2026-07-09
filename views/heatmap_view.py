import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LinearSegmentedColormap

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer, QSize

from core.config import HEATMAP, VISUALIZATION
from viewmodels.heatmap_vm import HeatmapViewModel


class HeatmapView(QWidget):
    def __init__(self, vm: HeatmapViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.max_range = HEATMAP.max_range_mm

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.figure = plt.figure(facecolor=VISUALIZATION.background_color)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.ax = self.figure.add_subplot(111)

        self.ax.set_facecolor(VISUALIZATION.background_color)
        self.ax.grid(True, alpha=VISUALIZATION.grid_alpha)
        self.ax.set_xlim(-self.max_range, self.max_range)
        self.ax.set_ylim(0, self.max_range)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_autoscale_on(False)

        self.cmap = LinearSegmentedColormap.from_list("light_heat", list(VISUALIZATION.colormap))

        self.ax.set_xlabel(VISUALIZATION.axis_x_label)
        self.ax.set_ylabel(VISUALIZATION.axis_y_label)
        self.ax.set_title(VISUALIZATION.title, pad=15)

        self.heat = np.zeros((vm.model.bins_y, vm.model.bins_x), dtype=np.float32)
        self.heat_img = self.ax.imshow(
            self.heat,
            origin="lower",
            cmap=self.cmap,
            extent=[-self.max_range, self.max_range, 0, self.max_range],
            interpolation="bilinear",
            vmin=0,
            vmax=1,
        )

        self.trail_line, = self.ax.plot(
            [], [], color=VISUALIZATION.trail_color,
            lw=VISUALIZATION.trail_linewidth, alpha=VISUALIZATION.trail_alpha, zorder=4,
        )
        self.current_point = self.ax.scatter(
            [], [], c=VISUALIZATION.point_color, s=VISUALIZATION.point_size,
            edgecolors=VISUALIZATION.point_edge_color, linewidths=VISUALIZATION.point_edge_width, zorder=6,
        )

        layout.addWidget(self.canvas)

        self._latest = None
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(VISUALIZATION.render_interval_ms)
        self._render_timer.timeout.connect(self._render)
        vm.updated.connect(self._on_update)

        self._sync_figure_size()

    def _sync_figure_size(self):
        w = self.canvas.width()
        h = self.canvas.height()
        if w > 0 and h > 0:
            self.figure.set_size_inches(w / self.figure.dpi, h / self.figure.dpi)
            self.canvas.draw_idle()

    def resizeEvent(self, event):
        self._sync_figure_size()
        super().resizeEvent(event)

    def _on_update(self, payload: dict):
        self._latest = payload

    def _render(self):
        if self._latest is None:
            return
        p = self._latest
        self.heat_img.set_data(p["heat"])
        self.heat_img.set_clim(0.0, p["vmax"])
        self.trail_line.set_data(p["trail_xs"], p["trail_ys"])
        self.current_point.set_offsets(np.array([p["current"]], dtype=np.float64))
        self.canvas.draw_idle()

    def start(self):
        self._render_timer.start()

    def clear(self):
        self._latest = None
        self.heat_img.set_data(np.zeros_like(self.heat))
        self.heat_img.set_clim(0.0, 1.0)
        self.trail_line.set_data([], [])
        self.current_point.set_offsets(np.array([[np.nan, np.nan]], dtype=np.float64))
        self.canvas.draw_idle()
