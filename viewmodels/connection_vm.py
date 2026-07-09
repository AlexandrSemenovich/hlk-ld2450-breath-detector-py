from PySide6.QtCore import QObject, Signal

from core.config import SERIAL


class ConnectionViewModel(QObject):
    statusChanged = Signal(bool, str)
    _connectRequested = Signal(str, int)
    _disconnectRequested = Signal()
    _finishRequested = Signal()

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.connected = False
        self.port = SERIAL.default_port
        self.baud = SERIAL.default_baud

        worker.connectionChanged.connect(self._on_connection)
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
        self.statusChanged.emit(ok, message)
