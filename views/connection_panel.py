from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                               QComboBox, QSpinBox, QPushButton, QLabel)

from core.config import SERIAL, RANGES, STYLES
from viewmodels.connection_vm import ConnectionViewModel


class ConnectionPanel(QWidget):
    def __init__(self, vm: ConnectionViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Подключение")
        form = QFormLayout()

        self.port_combo = QComboBox()
        self.port_combo.addItems(list(SERIAL.available_ports))
        if self.vm.port in [self.port_combo.itemText(i) for i in range(self.port_combo.count())]:
            self.port_combo.setCurrentText(self.vm.port)
        form.addRow("Порт:", self.port_combo)

        baud_range = RANGES["baud"]
        self.baud = QSpinBox()
        self.baud.setRange(baud_range.minimum, baud_range.maximum)
        self.baud.setSingleStep(baud_range.step)
        self.baud.setValue(self.vm.baud)
        form.addRow("Скорость:", self.baud)

        self.btn = QPushButton("Подключиться")
        self.btn.clicked.connect(self._on_clicked)
        form.addRow(self.btn)

        group.setLayout(form)
        layout.addWidget(group)

        self.status_label = QLabel("Статус: отключено")
        self.status_label.setStyleSheet(STYLES.status_box)
        layout.addWidget(self.status_label)

        vm.statusChanged.connect(self._on_status)

    def _on_clicked(self):
        self.vm.port = self.port_combo.currentText()
        self.vm.baud = self.baud.value()
        if self.vm.connected:
            self.vm.disconnect()
        else:
            self.vm.connect()

    def _on_status(self, ok: bool, message: str):
        self.btn.setText("Отключиться" if ok else "Подключиться")
        self.status_label.setText(f"Статус: {message}")
