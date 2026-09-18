import serial

from PySide6.QtCore import QObject, Signal, QTimer, QCoreApplication

from core.config import SERIAL
from core.protocol import parse_raw_line

_RX_LIMIT = 65536
_RX_KEEP = 8192


class SerialWorker(QObject):
    frameReady = Signal(object)
    rawReady = Signal(object)
    packetInvalid = Signal(int)
    connectionChanged = Signal(bool, str)
    connectionInfoChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial = None
        self._running = False
        self._timer = None
        self._rx = bytearray()

    def connect(self, port: str, baud: int):
        try:
            self._serial = serial.Serial(
                port,
                baud,
                timeout=0,
                write_timeout=0,
            )
            self._running = True
            self._rx.clear()
            if self._timer is None:
                self._timer = QTimer(self)
                self._timer.timeout.connect(self._poll)
            self._timer.start(SERIAL.poll_interval_ms)
            self.connectionChanged.emit(True, "Подключено")
            self.connectionInfoChanged.emit(self._serial_info())
        except Exception as exc:
            self._running = False
            self.connectionChanged.emit(False, f"Ошибка подключения: {exc}")
            self.connectionInfoChanged.emit(None)

    def disconnect(self):
        self._running = False
        if self._timer is not None:
            self._timer.stop()
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        self._rx.clear()
        self.connectionChanged.emit(False, "Отключено")
        self.connectionInfoChanged.emit(None)

    def _serial_info(self):
        ser = self._serial
        return {
            "port": ser.port,
            "baud": ser.baudrate,
            "bytesize": int(ser.bytesize),
            "parity": str(ser.parity),
            "stopbits": float(ser.stopbits),
            "timeout_s": ser.timeout,
        }

    def finish(self):
        self._running = False
        if self._timer is not None:
            self._timer.stop()
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
        self._rx.clear()
        self.moveToThread(QCoreApplication.instance().thread())

    def _poll(self):
        if not (self._running and self._serial is not None and self._serial.is_open):
            if self._timer is not None:
                self._timer.stop()
            return

        try:
            waiting = self._serial.in_waiting
            if waiting:
                self._rx.extend(self._serial.read(waiting))
        except Exception:
            self.packetInvalid.emit(1)
            return

        if len(self._rx) > _RX_LIMIT:
            del self._rx[:-_RX_KEEP]
            nl = self._rx.find(b"\n")
            if nl >= 0:
                del self._rx[:nl + 1]

        raw_lines = []
        frames = []
        invalid = 0
        limit = max(1, int(SERIAL.max_lines_per_poll))
        while len(raw_lines) < limit:
            nl = self._rx.find(b"\n")
            if nl < 0:
                break
            chunk = bytes(self._rx[:nl])
            del self._rx[:nl + 1]
            if chunk.endswith(b"\r"):
                chunk = chunk[:-1]
            raw = chunk.decode("ascii", errors="ignore").strip()
            if not raw:
                continue
            raw_lines.append(raw)
            frame = parse_raw_line(raw)
            if frame is not None:
                frames.append(frame)
            else:
                invalid += 1

        if raw_lines:
            self.rawReady.emit(raw_lines)
        if frames:
            self.frameReady.emit(frames)
        if invalid:
            self.packetInvalid.emit(invalid)
