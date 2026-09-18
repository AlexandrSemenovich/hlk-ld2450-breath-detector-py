from PySide6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QLabel, QFrame, QHBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from core.config import UI, THEME, TYPO
from viewmodels.connection_vm import ConnectionViewModel
from viewmodels.settings_vm import SettingsViewModel
from viewmodels.heatmap_vm import HeatmapViewModel
from views.connection_page import ConnectionPage
from views.visualization_page import VisualizationPage


class MainWindow(QMainWindow):
    def __init__(self, connection_vm: ConnectionViewModel,
                 settings_vm: SettingsViewModel,
                 heatmap_vm: HeatmapViewModel,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(UI.window_title)
        self.resize(UI.window_width, UI.window_height)

        self.connection_page = ConnectionPage(connection_vm, settings_vm)
        self.visualization_page = VisualizationPage(heatmap_vm)

        self.connection_panel = self.connection_page.connection_panel
        self.settings_panel = self.connection_page.settings_panel
        self.info_panel = self.connection_page.info_panel
        self.clear_btn = self.connection_page.clear_btn
        self.heatmap_view = self.visualization_page.heatmap_view

        self.tabs = QTabWidget()
        self.tabs.addTab(self.connection_page, "Настройки подключений")
        self.tabs.addTab(self.visualization_page, "Визуализация")
        self.setCentralWidget(self.tabs)

        self._init_status_bar(connection_vm)

    def add_tab(self, widget: QWidget, title: str):
        self.tabs.addTab(widget, title)

    def _init_status_bar(self, connection_vm: ConnectionViewModel):
        bar = self.statusBar()
        bar.setSizeGripEnabled(True)
        bar.setMinimumHeight(UI.status_bar_min_height)

        self.connection_status_led = QFrame()
        self.connection_status_led.setObjectName("StatusLed")
        self.connection_status_led.setFixedSize(UI.status_led_size, UI.status_led_size)
        self.connection_status_label = QLabel("Статус: отключено")
        self._set_status_led(False)

        status_wrap = QWidget()
        status_row = QHBoxLayout(status_wrap)
        status_row.setContentsMargins(10, 0, 10, 0)
        status_row.setSpacing(8)
        status_row.addWidget(self.connection_status_led)
        status_row.addWidget(self.connection_status_label)

        self.connection_info_label = QLabel(
            "Порт: —    Скорость: —    Формат: —    Timeout: —"
        )
        self.words_label = QLabel("Слов:        0")
        self.words_label.setFont(QFont(TYPO.mono_family, UI.status_bar_font_size))
        self.words_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.words_label.setMinimumWidth(UI.status_words_width)
        self.words_label.setMaximumWidth(UI.status_words_width)
        self.words_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        bar.addWidget(status_wrap)
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

    def _on_connection_status(self, ok: bool, message: str):
        self._set_status_led(ok)
        self.connection_status_label.setText(f"Статус: {message}")

    def _set_status_led(self, ok: bool):
        color = THEME.status_on if ok else THEME.status_off
        radius = UI.status_led_size // 2
        self.connection_status_led.setStyleSheet(
            f"background-color: {color}; border-radius: {radius}px;"
            "border: 1px solid rgba(0, 0, 0, 40);"
        )

    def _on_connection_info(self, text: str):
        self.connection_info_label.setText(text)

    def _on_words_changed(self, count: int):
        self.words_label.setText(f"Слов: {count:8d}")
