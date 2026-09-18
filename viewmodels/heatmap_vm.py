import time

from PySide6.QtCore import QObject, QTimer, Signal

from core.config import SERIAL, VISUALIZATION
from core.zones import apply_zones
from models.heatmap_model import HeatmapModel
from viewmodels.settings_vm import SettingsViewModel


class HeatmapViewModel(QObject):
    updated = Signal(object)

    def __init__(self, settings: SettingsViewModel, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.model = HeatmapModel()
        self._dirty = False
        self._ingest_ms = 0.0
        self._payload_ms = 0.0
        self._sync()
        settings.changed.connect(self._sync)

        self._payload_timer = QTimer(self)
        self._payload_timer.setInterval(VISUALIZATION.render_interval_ms)
        self._payload_timer.timeout.connect(self._flush_payload)
        self._payload_timer.start()

    def _sync(self):
        self.model.fade_time_ms = self.settings.fade_time_ms
        self.model.point_intensity = self.settings.point_intensity
        self.model.trail_time_ms = self.settings.trail_time_ms
        self.model.trail_points_max = self.settings.trail_points_max
        mirrored = self.model.set_mirror_x(self.settings.mirror_x)
        self.model._trim_trails(self.model.last_ts_ms or 0)
        if mirrored:
            self._emit_payload(force=True)

    def ingest(self, frames):
        if not isinstance(frames, (list, tuple)):
            frames = (frames,)
        if not frames:
            return
        limit = max(1, int(SERIAL.max_ingest_frames))
        if len(frames) > limit:
            frames = frames[-limit:]
        started = time.perf_counter()
        for frame in frames:
            self.model.ingest(frame)
        per_frame = (time.perf_counter() - started) * 1000.0 / max(len(frames), 1)
        self._ingest_ms = self._ema(self._ingest_ms, per_frame)
        self._dirty = True

    def clear(self):
        self.model.clear()
        self._ingest_ms = 0.0
        self._payload_ms = 0.0
        self._emit_payload(force=True)

    def _flush_payload(self):
        self._emit_payload(force=False)

    def _emit_payload(self, force: bool):
        if not force and not self._dirty:
            return
        started = time.perf_counter()
        payload = self.model.payload_from_state()
        self._payload_ms = self._ema(
            self._payload_ms, (time.perf_counter() - started) * 1000.0
        )
        stats = payload["stats"]
        stats["ingest_ms"] = self._ingest_ms
        stats["payload_ms"] = self._payload_ms
        self._dirty = False
        self.updated.emit(apply_zones(payload))

    @staticmethod
    def _ema(previous: float, sample: float, alpha: float = 0.25) -> float:
        if previous <= 0.0:
            return sample
        return previous * (1.0 - alpha) + sample * alpha
