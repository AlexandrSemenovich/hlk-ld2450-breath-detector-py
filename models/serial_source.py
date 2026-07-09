import serial

from PySide6.QtCore import QObject, Signal, QTimer, QCoreApplication

from core.config import SERIAL
from core.protocol import parse_raw_line


class SerialWorker(QObject):
    frameReady = Signal(object)
    rawReady = Signal(str)
    connectionChanged = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None
        self._running = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)

    def connect(self, port: str, baud: int):
        try:
            self._serial = serial.Serial(port, baud, timeout=SERIAL.read_timeout_s)
            self._running = True
            self._timer.start(SERIAL.poll_interval_ms)
            self.connectionChanged.emit(True, "Подключено")
        except Exception as exc:
            self.connectionChanged.emit(False, f"Ошибка подключения: {exc}")

    def disconnect(self):
        self._running = False
        self._timer.stop()
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self.connectionChanged.emit(False, "Отключено")

    def finish(self):
        self._running = False
        self._timer.stop()
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self.moveToThread(QCoreApplication.instance().thread())

    def _poll(self):
        if not (self._running and self._serial is not None and self._serial.is_open):
            self._timer.stop()
            return

        try:
            raw = self._serial.readline().decode("ascii", errors="ignore").strip()
        except Exception:
            return

        if not raw:
            return

        self.rawReady.emit(raw)
        frame = parse_raw_line(raw)
        if frame is not None:
            self.frameReady.emit(frame)
