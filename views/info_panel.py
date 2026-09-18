import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPlainTextEdit, QSizePolicy,
)
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtCore import Qt

from core.config import STYLES, TYPO, UI
from core.frame import RadarFrame, Target


class InfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(UI.panel_spacing)

        parsed = QGroupBox("Targets + Timestamp + Frame ID")
        parsed_layout = QVBoxLayout()

        self.frame_meta_label = QLabel("Ожидание данных...")
        self.frame_meta_label.setFont(QFont(TYPO.mono_family, UI.target_font_size))
        self.frame_meta_label.setStyleSheet(STYLES.target_box)
        parsed_layout.addWidget(self.frame_meta_label)

        targets_row = QHBoxLayout()
        targets_row.setSpacing(UI.panel_spacing)
        self.target_labels: list[QLabel] = []
        for index in range(3):
            box = QGroupBox(f"Target {index}")
            box_layout = QVBoxLayout()
            label = QLabel("Ожидание данных...")
            label.setFont(QFont(TYPO.mono_family, UI.target_font_size))
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet(STYLES.target_box)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            box_layout.addWidget(label)
            box.setLayout(box_layout)
            targets_row.addWidget(box, stretch=1)
            self.target_labels.append(label)
        parsed_layout.addLayout(targets_row)
        parsed.setLayout(parsed_layout)
        layout.addWidget(parsed)

        raw = QGroupBox("RAW терминал (COM)")
        raw_layout = QVBoxLayout()
        self.raw_terminal = QPlainTextEdit()
        self.raw_terminal.setObjectName("RawTerminal")
        self.raw_terminal.setReadOnly(True)
        self.raw_terminal.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.raw_terminal.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.raw_terminal.setMaximumBlockCount(UI.raw_history_lines)
        self.raw_terminal.setMinimumHeight(UI.raw_terminal_min_height)
        self.raw_terminal.setFont(QFont(TYPO.mono_family, TYPO.font_size))
        self.raw_terminal.setPlaceholderText("Ожидание RAW строк...")
        self.raw_terminal.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        raw_layout.addWidget(self.raw_terminal)
        raw.setLayout(raw_layout)
        layout.addWidget(raw, stretch=1)

        stats = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel("—")
        self.stats_label.setFont(QFont(TYPO.mono_family, UI.stats_font_size))
        self.stats_label.setStyleSheet(STYLES.stats_box)
        stats_layout.addWidget(self.stats_label)
        stats.setLayout(stats_layout)
        layout.addWidget(stats)

    def update_frame(self, frame: RadarFrame):
        ts_str = self._format_ts(frame.timestamp_ms)
        self.frame_meta_label.setText(
            f"Timestamp ts_ms: {ts_str}    Frame ID: {frame.frame_id}"
        )
        for index, target in enumerate(frame.targets):
            self.target_labels[index].setText(self._format_target(index, target))

    def append_raw(self, line: str):
        if not line:
            return
        self.raw_terminal.appendPlainText(line)

    def update_stats(self, stats: dict):
        self.stats_label.setText(
            f"Людей: {stats.get('people_count', 0)}\n"
            f"Зона занята: {stats.get('dwell_s', 0):.0f} с\n"
            f"Точек в трейле: {stats['points']}\n"
            f"Макс. Y: {stats['max_y']:.0f} мм\n"
            f"Пройдено ≈ {stats['distance_m']:.2f} м\n"
            f"Heat sum: {stats['heat_sum']:.1f}"
        )

    def _format_target(self, index: int, target: Target) -> str:
        status = "есть цель" if target.present else "нет цели"
        return (
            f"TARGET {index}  [{status}]\n"
            "--------------------------------\n"
            f"X: {target.x:6d} мм\n"
            f"Y: {target.y:6d} мм\n"
            f"Скорость: {target.speed:6d} см/с\n"
            f"Разрешение: {target.resolution:6d} мм"
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
