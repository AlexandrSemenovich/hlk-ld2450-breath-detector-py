from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer, QSize

from core.config import VISUALIZATION


class TimedMplWidget(QWidget):
    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.figure = Figure(facecolor=VISUALIZATION.background_color, layout=None)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.canvas.setMinimumSize(0, 0)
        self.canvas.sizeHint = lambda: QSize(0, 0)
        self.canvas.minimumSizeHint = lambda: QSize(0, 0)
        layout.addWidget(self.canvas)

        self._latest = None
        self._dirty = False
        self._blit_bg = None
        self._axes_margins = (0.12, 0.98, 0.96, 0.18)
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(VISUALIZATION.render_interval_ms)
        self._render_timer.timeout.connect(self._on_tick)
        vm.updated.connect(self._on_update)

    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def start(self):
        self._dirty = True
        self._blit_bg = None
        if not self._render_timer.isActive():
            self._render_timer.start()
        self._sync_figure_size()

    def stop(self):
        self._render_timer.stop()

    def _on_update(self, payload: dict):
        self._latest = payload
        self._dirty = True

    def resizeEvent(self, event):
        self._sync_figure_size()
        super().resizeEvent(event)

    def _invalidate_blit(self):
        self._blit_bg = None

    def _sync_figure_size(self):
        self._invalidate_blit()
        width = self.canvas.width()
        height = self.canvas.height()
        if width > 0 and height > 0:
            self.figure.set_size_inches(width / self.figure.dpi, height / self.figure.dpi)
            left, right, top, bottom = self._axes_margins
            self.figure.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
            self._dirty = True
            if self.isVisible():
                self.canvas.draw_idle()

    def _on_tick(self):
        if not self._dirty or not self.isVisible() or self.width() <= 0:
            return
        self._dirty = False
        self._render()

    def _blit_artists(self):
        return ()

    def _draw_dynamic(self):
        artists = self._blit_artists()
        bbox = self.ax.bbox
        if bbox.width <= 1 or bbox.height <= 1:
            self.canvas.draw()
            return
        if self._blit_bg is None:
            vis = [artist.get_visible() for artist in artists]
            for artist in artists:
                artist.set_visible(False)
            self.canvas.draw()
            self._blit_bg = self.canvas.copy_from_bbox(bbox)
            for artist, visible in zip(artists, vis):
                artist.set_visible(visible)

        self.canvas.restore_region(self._blit_bg)
        for artist in artists:
            if artist.get_visible():
                self.ax.draw_artist(artist)
        self._draw_axes_overlay()
        self.canvas.blit(bbox)

    def _draw_axes_overlay(self):
        ax = self.ax
        for spine in ax.spines.values():
            ax.draw_artist(spine)
        ax.draw_artist(ax.xaxis)
        ax.draw_artist(ax.yaxis)

    def _fill_axes(self, inset: float = 0.02):
        width = self.canvas.width()
        height = self.canvas.height()
        if width <= 0 or height <= 0:
            return False
        self.figure.set_size_inches(width / self.figure.dpi, height / self.figure.dpi)
        self.figure.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        self.ax.set_position([inset, inset, 1.0 - 2 * inset, 1.0 - 2 * inset])
        return True

    def _apply_inner_ticks(self):
        self.ax.tick_params(
            which="both",
            direction="in",
            top=True,
            right=True,
            labelsize=8,
            length=5,
            width=0.8,
            pad=-14,
        )
        bbox = {
            "facecolor": VISUALIZATION.background_color,
            "edgecolor": "none",
            "alpha": 0.82,
            "pad": 1.5,
        }
        for label in self.ax.get_xticklabels():
            label.set_verticalalignment("bottom")
            label.set_bbox(bbox)
        for label in self.ax.get_yticklabels():
            label.set_horizontalalignment("left")
            label.set_bbox(bbox)

    def _render(self):
        raise NotImplementedError
