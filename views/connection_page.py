from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton

from core.config import UI
from viewmodels.connection_vm import ConnectionViewModel
from viewmodels.settings_vm import SettingsViewModel
from views.connection_panel import ConnectionPanel
from views.settings_panel import SettingsPanel
from views.info_panel import InfoPanel


class ConnectionPage(QWidget):
    def __init__(self, connection_vm: ConnectionViewModel,
                 settings_vm: SettingsViewModel, parent=None):
        super().__init__(parent)

        page_layout = QHBoxLayout(self)
        page_layout.setContentsMargins(UI.content_margin, UI.content_margin,
                                        UI.content_margin, UI.content_margin)
        page_layout.setSpacing(UI.panel_spacing)

        column = QWidget()
        column.setMaximumWidth(UI.settings_column_max_width)
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(UI.panel_spacing)

        self.connection_panel = ConnectionPanel(connection_vm)
        self.settings_panel = SettingsPanel(settings_vm)
        self.info_panel = InfoPanel(settings_vm)
        self.clear_btn = QPushButton("Очистить карту")

        layout.addWidget(self.connection_panel)
        layout.addWidget(self.settings_panel)
        layout.addStretch()
        layout.addWidget(self.clear_btn)

        page_layout.addWidget(column)
        page_layout.addWidget(self.info_panel, stretch=1)
