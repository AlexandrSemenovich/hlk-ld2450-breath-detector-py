from PySide6.QtCore import QObject, Signal

from models.heatmap_model import HeatmapModel
from viewmodels.settings_vm import SettingsViewModel


class HeatmapViewModel(QObject):
    updated = Signal(object)

    def __init__(self, settings: SettingsViewModel, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.model = HeatmapModel()
        self._sync()
        settings.changed.connect(self._sync)

    def _sync(self):
        self.model.fade_time_ms = self.settings.fade_time_ms
        self.model.point_intensity = self.settings.point_intensity
        self.model.trail_time_ms = self.settings.trail_time_ms
        self.model.trail_points_max = self.settings.trail_points_max

    def ingest(self, frame):
        payload = self.model.ingest(frame)
        self.updated.emit(payload)

    def clear(self):
        self.model.clear()
        self.updated.emit(self.model.snapshot())
