from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy

from core.config import THEME, TYPO
from viewmodels.heatmap_vm import HeatmapViewModel


class OccupancyStatusView(QFrame):
    def __init__(self, vm: HeatmapViewModel, parent=None):
        super().__init__(parent)
        self.setObjectName("OccupancyStatus")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        self.count_label = QLabel("0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setFont(QFont(TYPO.font_family, 42, QFont.Weight.Bold))

        self.state_label = QLabel("пусто")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setFont(QFont(TYPO.font_family, 14, QFont.Weight.DemiBold))

        self.dwell_label = QLabel("занято 0 с")
        self.dwell_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dwell_label.setFont(QFont(TYPO.font_family, 11))

        layout.addStretch()
        layout.addWidget(self.count_label)
        layout.addWidget(self.state_label)
        layout.addWidget(self.dwell_label)
        layout.addStretch()

        vm.updated.connect(self._on_update)
        self._set_occupied(False)

    def _on_update(self, payload: dict):
        occupancy = payload.get("occupancy") or {}
        count = int(occupancy.get("count", 0))
        occupied = bool(occupancy.get("occupied", False))
        dwell_s = float(occupancy.get("dwell_s", 0.0))
        self.count_label.setText(str(count))
        self.state_label.setText("есть люди" if occupied else "пусто")
        self.dwell_label.setText(f"занято {dwell_s:.0f} с")
        self._set_occupied(occupied)

    def _set_occupied(self, occupied: bool):
        if occupied:
            bg, border, color = THEME.occupancy_on_bg, THEME.occupancy_on, THEME.occupancy_on
        else:
            bg, border, color = THEME.occupancy_off_bg, THEME.occupancy_off, THEME.occupancy_off
        self.setStyleSheet(
            f"QFrame#OccupancyStatus {{ background-color: {bg}; "
            f"border: 2px solid {border}; border-radius: 10px; }}"
        )
        self.count_label.setStyleSheet(f"color: {color};")
        self.state_label.setStyleSheet(f"color: {color};")
        self.dwell_label.setStyleSheet(f"color: {THEME.text_secondary};")

    def clear(self):
        self._on_update({"occupancy": {"count": 0, "occupied": False, "dwell_s": 0.0}})
