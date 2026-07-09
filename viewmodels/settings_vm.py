from PySide6.QtCore import QObject, Signal

from core.config import SETTINGS_DEFAULTS


class SettingsViewModel(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fade_time_ms = SETTINGS_DEFAULTS.fade_time_ms
        self.point_intensity = SETTINGS_DEFAULTS.point_intensity
        self.trail_time_ms = SETTINGS_DEFAULTS.trail_time_ms
        self.trail_points_max = SETTINGS_DEFAULTS.trail_points_max

    def set_fade_time_ms(self, value: int):
        if self.fade_time_ms != value:
            self.fade_time_ms = value
            self.changed.emit()

    def set_point_intensity(self, value: int):
        if self.point_intensity != value:
            self.point_intensity = value
            self.changed.emit()

    def set_trail_time_ms(self, value: int):
        if self.trail_time_ms != value:
            self.trail_time_ms = value
            self.changed.emit()

    def set_trail_points_max(self, value: int):
        if self.trail_points_max != value:
            self.trail_points_max = value
            self.changed.emit()
