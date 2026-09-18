from PySide6.QtCore import QObject, Signal

from core.config import SERIAL


class ConnectionViewModel(QObject):
    statusChanged = Signal(bool, str)
    wordsChanged = Signal(int)
    infoChanged = Signal(str)
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

        worker.connectionChanged.connect(self._on_connection)
        worker.connectionInfoChanged.connect(self._on_connection_info)
        worker.rawReady.connect(self._on_raw)
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
            self.wordsChanged.emit(self.words_received)
        self.statusChanged.emit(ok, message)

    def _on_connection_info(self, info):
        self.infoChanged.emit(self._format_info(info))

    def _on_raw(self, line: str):
        self.words_received += self._count_words(line)
        self.wordsChanged.emit(self.words_received)

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
