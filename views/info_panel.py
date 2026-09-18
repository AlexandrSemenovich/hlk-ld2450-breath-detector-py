import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPlainTextEdit,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QAbstractScrollArea,
)
from PySide6.QtGui import QFont, QTextOption
from PySide6.QtCore import Qt

from core.config import STYLES, TYPO, UI, SERIAL
from core.frame import RadarFrame, Target
from viewmodels.settings_vm import SettingsViewModel

_CHANNEL_ROWS = (
    ("packets_ok", "Пакеты"),
    ("packet_rate", "Обработка"),
    ("packets_bad", "Битые"),
    ("packets_missed", "Пропущенные"),
    ("byte_rate", "Поток"),
    ("bytes_total", "Всего"),
)


class InfoPanel(QWidget):
    def __init__(self, settings_vm: SettingsViewModel | None = None, parent=None):
        super().__init__(parent)
        self.settings = settings_vm
        self._last_frame = None
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

        channel = QGroupBox("Канал связи")
        channel_layout = QVBoxLayout()
        channel_layout.setContentsMargins(0, 8, 0, 0)
        channel_layout.setSpacing(0)

        self.channel_table = QTableWidget(len(_CHANNEL_ROWS), 2)
        self.channel_table.setObjectName("ChannelTable")
        self.channel_table.setHorizontalHeaderLabels(["Параметр", "Значение"])
        self.channel_table.verticalHeader().setVisible(False)
        self.channel_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.channel_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.channel_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.channel_table.setAlternatingRowColors(True)
        self.channel_table.setShowGrid(True)
        self.channel_table.setWordWrap(False)
        self.channel_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.channel_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.channel_table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.channel_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        header = self.channel_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_header = QTableWidgetItem("Параметр")
        name_header.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        value_header = QTableWidgetItem("Значение")
        value_header.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.channel_table.setHorizontalHeaderItem(0, name_header)
        self.channel_table.setHorizontalHeaderItem(1, value_header)
        self.channel_table.verticalHeader().setDefaultSectionSize(30)
        self.channel_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        value_font = QFont(TYPO.mono_family, UI.target_font_size)
        self._channel_value_items: list[QTableWidgetItem] = []
        for row, (_key, title) in enumerate(_CHANNEL_ROWS):
            name_item = QTableWidgetItem(title)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.channel_table.setItem(row, 0, name_item)

            value_item = QTableWidgetItem("—")
            value_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            value_item.setFont(value_font)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.channel_table.setItem(row, 1, value_item)
            self._channel_value_items.append(value_item)

        self.channel_format = QLabel()
        self.channel_format.setObjectName("ChannelFormat")
        self.channel_format.setWordWrap(True)
        self.channel_format.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        channel_layout.addWidget(self.channel_table)
        channel_layout.addWidget(self.channel_format)
        channel.setLayout(channel_layout)
        self._apply_channel_stats({})

        targets_row = QHBoxLayout()
        targets_row.setSpacing(UI.panel_spacing)
        self.target_labels: list[QLabel] = []
        for _index in range(3):
            label = QLabel("Ожидание данных...")
            label.setFont(QFont(TYPO.mono_family, UI.target_font_size))
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            label.setStyleSheet(STYLES.target_box)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            targets_row.addWidget(label, stretch=1)
            self.target_labels.append(label)
        parsed_layout.addLayout(targets_row)
        parsed.setLayout(parsed_layout)
        layout.addWidget(channel)
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

        self.stats_group = QGroupBox("Статистика", self)
        stats_layout = QVBoxLayout()
        self.stats_label = QLabel("—")
        self.stats_label.setFont(QFont(TYPO.mono_family, UI.stats_font_size))
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet(STYLES.stats_box)
        stats_layout.addWidget(self.stats_label)
        self.stats_group.setLayout(stats_layout)

        if settings_vm is not None:
            settings_vm.changed.connect(self._refresh_frame)

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_channel_table()

    def update_frame(self, frame: RadarFrame):
        self._last_frame = frame
        self._refresh_frame()

    def _refresh_frame(self):
        frame = self._last_frame
        if frame is None:
            return
        ts_str = self._format_ts(frame.timestamp_ms)
        self.frame_meta_label.setText(
            f"Timestamp ts_ms: {ts_str}    Frame ID: {frame.frame_id}"
        )
        for index, target in enumerate(frame.targets):
            self.target_labels[index].setText(self._format_target(index, target))

    def update_channel_stats(self, stats: dict):
        self._apply_channel_stats(stats)

    def _apply_channel_stats(self, stats: dict):
        packets_ok = int(stats.get("packets_ok", 0))
        packets_bad = int(stats.get("packets_bad", 0))
        packets_missed = int(stats.get("packets_missed", 0))
        packet_rate = float(stats.get("packet_rate", 0.0))
        byte_rate = float(stats.get("byte_rate", 0.0))
        bytes_total = int(stats.get("bytes_total", 0))
        data_format = stats.get("data_format") or SERIAL.data_format
        values = {
            "packets_ok": f"{packets_ok:,}".replace(",", " "),
            "packet_rate": f"{packet_rate:.1f} кадр/с",
            "packets_bad": f"{packets_bad:,}".replace(",", " "),
            "packets_missed": f"{packets_missed:,}".replace(",", " "),
            "byte_rate": f"{self._format_bytes(byte_rate)}/с",
            "bytes_total": self._format_bytes(bytes_total),
        }
        for row, (key, _title) in enumerate(_CHANNEL_ROWS):
            self._channel_value_items[row].setText(values[key])
        self.channel_format.setText(f"Формат: {data_format}")
        self._fit_channel_table()

    def _fit_channel_table(self):
        self.channel_table.resizeRowsToContents()
        self.channel_table.resizeColumnToContents(0)
        header_h = self.channel_table.horizontalHeader().height()
        rows_h = sum(
            self.channel_table.rowHeight(row)
            for row in range(self.channel_table.rowCount())
        )
        frame = self.channel_table.frameWidth() * 2
        self.channel_table.setFixedHeight(header_h + rows_h + frame)

    @staticmethod
    def _format_bytes(value: float) -> str:
        value = float(value)
        if value >= 1024 * 1024:
            return f"{value / (1024 * 1024):.2f} МБ"
        if value >= 1024:
            return f"{value / 1024:.1f} КБ"
        return f"{value:.0f} Б"

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
        x = -target.x if self.settings is not None and self.settings.mirror_x else target.x
        return (
            f"TARGET {index}  [{status}]\n"
            "--------------------------------\n"
            f"X: {x:6d} мм\n"
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
