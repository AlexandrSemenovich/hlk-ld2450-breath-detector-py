from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QTabWidget, QPushButton, QLabel, QFrame)

from core.config import UI
from viewmodels.connection_vm import ConnectionViewModel
from viewmodels.settings_vm import SettingsViewModel
from viewmodels.heatmap_vm import HeatmapViewModel
from views.connection_panel import ConnectionPanel
from views.settings_panel import SettingsPanel
from views.info_panel import InfoPanel
from views.heatmap_view import HeatmapView


class MainWindow(QMainWindow):
    def __init__(self, connection_vm: ConnectionViewModel,
                 settings_vm: SettingsViewModel,
                 heatmap_vm: HeatmapViewModel,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(UI.window_title)
        self.resize(UI.window_width, UI.window_height)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(UI.panel_spacing)
        main_layout.setContentsMargins(UI.content_margin, UI.content_margin,
                                        UI.content_margin, UI.content_margin)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(UI.panel_spacing)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.connection_panel = ConnectionPanel(connection_vm)
        self.settings_panel = SettingsPanel(settings_vm)
        self.info_panel = InfoPanel()

        left_layout.addWidget(self.connection_panel)
        left_layout.addWidget(self.settings_panel)
        left_layout.addWidget(self.info_panel)
        left_layout.addStretch()

        self.clear_btn = QPushButton("Очистить карту")
        left_layout.addWidget(self.clear_btn)

        main_layout.addWidget(left, stretch=UI.left_panel_stretch)

        self.tabs = QTabWidget()
        self.heatmap_view = HeatmapView(heatmap_vm)
        self.tabs.addTab(self.heatmap_view, "Heatmap")
        main_layout.addWidget(self.tabs, stretch=UI.right_panel_stretch)

        self._init_status_bar(connection_vm)

    def add_tab(self, widget: QWidget, title: str):
        self.tabs.addTab(widget, title)

    def _init_status_bar(self, connection_vm: ConnectionViewModel):
        bar = self.statusBar()
        bar.setSizeGripEnabled(True)
        bar.setMinimumHeight(UI.status_bar_min_height)

        self.connection_status_label = QLabel("Статус: отключено")
        self.connection_info_label = QLabel(
            "Порт: —    Скорость: —    Формат: —    Timeout: —"
        )
        self.words_label = QLabel("Слов: 0")

        bar.addWidget(self.connection_status_label)
        bar.addWidget(self._status_separator())
        bar.addWidget(self.connection_info_label, 1)
        bar.addPermanentWidget(self._status_separator())
        bar.addPermanentWidget(self.words_label)

        connection_vm.statusChanged.connect(self._on_connection_status)
        connection_vm.infoChanged.connect(self._on_connection_info)
        connection_vm.wordsChanged.connect(self._on_words_changed)

    def _status_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _on_connection_status(self, _ok: bool, message: str):
        self.connection_status_label.setText(f"Статус: {message}")

    def _on_connection_info(self, text: str):
        self.connection_info_label.setText(text)

    def _on_words_changed(self, count: int):
        self.words_label.setText(f"Слов: {count}")
