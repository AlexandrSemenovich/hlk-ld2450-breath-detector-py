import time

from PySide6.QtCore import QObject, QTimer, Signal

from core.config import SERIAL, VISUALIZATION


class ConnectionViewModel(QObject):
    statusChanged = Signal(bool, str)
    wordsChanged = Signal(int)
    infoChanged = Signal(str)
    channelStatsChanged = Signal(object)
    _connectRequested = Signal(str, int)
    _disconnectRequested = Signal()
    _finishRequested = Signal()

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.connected = False
        self.port = SERIAL.default_port
        self.baud = SERIAL.default_baud
        self.words_received = 0
        self._reset_channel_stats()

        self._words_dirty = False
        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(SERIAL.stats_interval_ms)
        self._stats_timer.timeout.connect(self._emit_channel_stats)
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(VISUALIZATION.render_interval_ms)
        self._ui_timer.timeout.connect(self._flush_words)

        worker.connectionChanged.connect(self._on_connection)
        worker.connectionInfoChanged.connect(self._on_connection_info)
        worker.rawReady.connect(self._on_raw)
        worker.frameReady.connect(self._on_frame)
        worker.packetInvalid.connect(self._on_invalid)
        self._connectRequested.connect(worker.connect)
        self._disconnectRequested.connect(worker.disconnect)
        self._finishRequested.connect(worker.finish)

    def connect(self):
        self._connectRequested.emit(self.port, self.baud)

    def disconnect(self):
        self._disconnectRequested.emit()

    def request_finish(self):
        self._finishRequested.emit()

    def _on_connection(self, ok: bool, message: str):
        self.connected = ok
        if ok:
            self.words_received = 0
            self._words_dirty = True
            self._reset_channel_stats()
            self._stats_timer.start()
            self._ui_timer.start()
            self._flush_words()
            self._emit_channel_stats()
        else:
            self._stats_timer.stop()
            self._ui_timer.stop()
            self._flush_words()
            self._emit_channel_stats()
        self.statusChanged.emit(ok, message)

    def _on_connection_info(self, info):
        self.infoChanged.emit(self._format_info(info))

    def _on_raw(self, lines):
        if isinstance(lines, str):
            lines = (lines,)
        for line in lines:
            if not line:
                continue
            self.words_received += self._count_words(line)
            self.bytes_total += len(line) + 1
        self._words_dirty = True

    def _flush_words(self):
        if not self._words_dirty:
            return
        self._words_dirty = False
        self.wordsChanged.emit(self.words_received)

    def _on_frame(self, frames):
        if not isinstance(frames, (list, tuple)):
            frames = (frames,)
        self.packets_ok += len(frames)
        for frame in frames:
            self._count_missed(frame)

    def _on_invalid(self, count=1):
        self.packets_bad += max(1, int(count))

    def _count_missed(self, frame):
        try:
            frame_id = int(str(frame.frame_id).strip(), 0)
        except (TypeError, ValueError):
            return
        if self._last_frame_id is not None and frame_id > self._last_frame_id + 1:
            self.packets_missed += frame_id - self._last_frame_id - 1
        self._last_frame_id = frame_id

    def _reset_channel_stats(self):
        self.packets_ok = 0
        self.packets_bad = 0
        self.packets_missed = 0
        self.bytes_total = 0
        self.packet_rate = 0.0
        self.byte_rate = 0.0
        self._last_frame_id = None
        self._rate_t = time.monotonic()
        self._rate_ok = 0
        self._rate_bytes = 0

    def _emit_channel_stats(self):
        now = time.monotonic()
        dt = max(now - self._rate_t, 1e-3)
        self.packet_rate = (self.packets_ok - self._rate_ok) / dt
        self.byte_rate = (self.bytes_total - self._rate_bytes) / dt
        self._rate_t = now
        self._rate_ok = self.packets_ok
        self._rate_bytes = self.bytes_total
        self.channelStatsChanged.emit({
            "packets_ok": self.packets_ok,
            "packets_bad": self.packets_bad,
            "packets_missed": self.packets_missed,
            "bytes_total": self.bytes_total,
            "packet_rate": self.packet_rate,
            "byte_rate": self.byte_rate,
            "data_format": SERIAL.data_format,
        })

    @staticmethod
    def _count_words(line: str) -> int:
        return sum(1 for part in line.replace(",", " ").split() if part)

    @staticmethod
    def _format_info(info) -> str:
        if not info:
            return "Порт: —    Скорость: —    Формат: —    Timeout: —"

        stopbits = info.get("stopbits", 1)
        stop = int(stopbits) if float(stopbits).is_integer() else stopbits
        timeout = info.get("timeout_s")
        timeout_str = "—" if timeout is None else f"{timeout:g} с"
        return (
            f"Порт: {info.get('port', '—')}    "
            f"Скорость: {info.get('baud', '—')} бод    "
            f"Формат: {info.get('bytesize', 8)}{info.get('parity', 'N')}{stop}    "
            f"Timeout: {timeout_str}"
        )
