import time

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel
from PySide6.QtGui import QFont

from core.config import STYLES, TYPO
from core.frame import RadarFrame


class InfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        parsed = QGroupBox("Target 0 + Timestamp + Frame ID")
        pl = QVBoxLayout()
        self.data_label = QLabel("Ожидание данных...")
        self.data_label.setFont(QFont(TYPO.mono_family, 11))
        self.data_label.setWordWrap(True)
        self.data_label.setStyleSheet(STYLES.label_box)
        pl.addWidget(self.data_label)
        parsed.setLayout(pl)
        layout.addWidget(parsed)

        raw = QGroupBox("RAW строка из COM порта")
        rl = QVBoxLayout()
        self.raw_label = QLabel("Ожидание RAW строки...")
        self.raw_label.setFont(QFont(TYPO.mono_family, 10))
        self.raw_label.setWordWrap(True)
        self.raw_label.setStyleSheet(STYLES.label_raw)
        rl.addWidget(self.raw_label)
        raw.setLayout(rl)
        layout.addWidget(raw)

        self.stats_label = QLabel("Статистика:\n—")
        self.stats_label.setFont(QFont(TYPO.mono_family, 11))
        self.stats_label.setStyleSheet(STYLES.label_box)
        layout.addWidget(self.stats_label)

    def update_frame(self, frame: RadarFrame):
        t = frame.target
        ts_str = self._format_ts(frame.timestamp_ms)
        self.data_label.setText(
            "TARGET 0\n"
            "--------------------------------\n"
            f"X: {t.x:6d} мм\n"
            f"Y: {t.y:6d} мм\n"
            f"Скорость: {t.speed:6d} см/с\n"
            f"Разрешение: {t.resolution:6d} мм\n\n"
            f"Timestamp ts_ms: {ts_str}\n"
            f"Frame ID: {frame.frame_id}"
        )
        self.raw_label.setText(frame.raw_line)

    def update_stats(self, stats: dict):
        self.stats_label.setText(
            "Статистика:\n"
            f"Точек в трейле: {stats['points']}\n"
            f"Макс. Y: {stats['max_y']:.0f} мм\n"
            f"Пройдено ≈ {stats['distance_m']:.2f} м\n"
            f"Heat sum: {stats['heat_sum']:.1f}"
        )

    def _format_ts(self, ts_ms):
        try:
            ts_ms = int(ts_ms)
        except Exception:
            return "—"
        if ts_ms <= 0:
            return f"{ts_ms} ms"
        if ts_ms > 10 ** 12:
            dt = time.localtime(ts_ms / 1000.0)
            readable = time.strftime("%H:%M:%S", dt)
            ms_part = ts_ms % 1000
            return f"{ts_ms} ms (Local: {readable}.{ms_part:03d})"
        return f"{ts_ms} ms"
