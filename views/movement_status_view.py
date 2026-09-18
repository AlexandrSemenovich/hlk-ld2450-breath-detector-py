import math

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from core.config import THEME, TYPO, VISUALIZATION
from viewmodels.heatmap_vm import HeatmapViewModel


class MovementStatusView(QFrame):
    def __init__(self, vm: HeatmapViewModel, parent=None):
        super().__init__(parent)
        self.setObjectName("MovementStatus")
        ignored = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setSizePolicy(ignored)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Движение относительно радара")
        title.setFont(QFont(TYPO.font_family, 9, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {THEME.text_secondary};")
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        layout.addWidget(title)

        self.rows = []
        for color, name in zip(VISUALIZATION.target_colors, VISUALIZATION.target_labels):
            row = QFrame()
            row.setObjectName("MovementRow")
            row.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(2)

            header = QHBoxLayout()
            badge = QLabel(name.replace("Target ", "T"))
            badge.setFixedWidth(28)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(QFont(TYPO.font_family, 10, QFont.Weight.Bold))
            badge.setStyleSheet(
                f"color: #ffffff; background-color: {color}; "
                "border-radius: 6px; padding: 2px 0;"
            )
            action = QLabel("нет цели")
            action.setWordWrap(False)
            action.setTextFormat(Qt.TextFormat.PlainText)
            action.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            action.setFont(QFont(TYPO.font_family, 10, QFont.Weight.DemiBold))
            header.addWidget(badge)
            header.addWidget(action, stretch=1)

            detail = QLabel("—")
            detail.setWordWrap(False)
            detail.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            detail.setFont(QFont(TYPO.mono_family, 9))
            detail.setStyleSheet(f"color: {THEME.text_secondary};")

            row_layout.addLayout(header)
            row_layout.addWidget(detail)
            layout.addWidget(row)
            self.rows.append({
                "action": action,
                "detail": detail,
                "action_full": "нет цели",
                "detail_full": "—",
            })

        layout.addStretch()
        vm.updated.connect(self._on_update)

    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_elide()

    def _on_update(self, payload: dict):
        currents = payload.get("currents") or []
        for index, row in enumerate(self.rows):
            current = currents[index] if index < len(currents) else None
            action, detail = self._describe(current)
            row["action_full"] = action
            row["detail_full"] = detail
        self._apply_elide()

    def _apply_elide(self):
        for row in self.rows:
            row["action"].setText(self._elide(row["action"], row["action_full"]))
            row["detail"].setText(self._elide(row["detail"], row["detail_full"]))

    def _elide(self, label: QLabel, text: str) -> str:
        width = max(label.width() - 4, 40)
        return label.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, width)

    def _describe(self, current):
        if not current or not current.get("present"):
            return "нет цели", "—"

        x = float(current["x"])
        y = float(current["y"])
        speed = float(current["speed"])
        distance_m = math.hypot(x, y) / 1000.0
        direction = self._direction(x, y)
        if abs(speed) < VISUALIZATION.moving_speed_cm_s:
            action = f"на месте, {direction}"
        elif speed < 0:
            action = f"приближается к радару {direction}"
        else:
            action = f"удаляется от радара {direction}"
        detail = f"{distance_m:.1f} м  ·  {speed:+.0f} см/с"
        return action, detail

    def _direction(self, x: float, y: float) -> str:
        angle = math.degrees(math.atan2(x, max(y, 1.0)))
        if abs(angle) < 12:
            return "по центру"
        if angle < 0:
            return "слева"
        return "справа"

    def clear(self):
        empty = [{"present": False} for _ in self.rows]
        self._on_update({"currents": empty})
