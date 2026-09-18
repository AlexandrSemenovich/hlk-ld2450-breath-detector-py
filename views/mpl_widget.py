import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer

from core.config import VISUALIZATION


class TimedMplWidget(QWidget):
    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.figure = plt.figure(facecolor=VISUALIZATION.background_color)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumSize(0, 0)
        layout.addWidget(self.canvas)

        self._latest = None
        self._render_timer = QTimer(self)
        self._render_timer.setInterval(VISUALIZATION.render_interval_ms)
        self._render_timer.timeout.connect(self._render)
        vm.updated.connect(self._on_update)

    def start(self):
        self._render_timer.start()
        self._sync_figure_size()

    def _on_update(self, payload: dict):
        self._latest = payload

    def resizeEvent(self, event):
        self._sync_figure_size()
        super().resizeEvent(event)

    def _sync_figure_size(self):
        width = self.canvas.width()
        height = self.canvas.height()
        if width > 0 and height > 0:
            self.figure.set_size_inches(width / self.figure.dpi, height / self.figure.dpi)
            self.figure.tight_layout(pad=0.4)
            self.canvas.draw_idle()

    def _render(self):
        raise NotImplementedError
