from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QSpinBox

from core.config import RANGES
from viewmodels.settings_vm import SettingsViewModel


class SettingsPanel(QWidget):
    def __init__(self, vm: SettingsViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("Настройки визуализации")
        form = QFormLayout()

        fade_range = RANGES["fade_time_ms"]
        self.fade = QSpinBox()
        self.fade.setRange(fade_range.minimum, fade_range.maximum)
        self.fade.setSingleStep(fade_range.step)
        self.fade.setValue(vm.fade_time_ms)
        self.fade.valueChanged.connect(vm.set_fade_time_ms)
        form.addRow("Следы исчезают через (ms):", self.fade)

        intensity_range = RANGES["point_intensity"]
        self.intensity = QSpinBox()
        self.intensity.setRange(intensity_range.minimum, intensity_range.maximum)
        self.intensity.setSingleStep(intensity_range.step)
        self.intensity.setValue(vm.point_intensity)
        self.intensity.valueChanged.connect(vm.set_point_intensity)
        form.addRow("Интенсивность (контраст):", self.intensity)

        trail_time_range = RANGES["trail_time_ms"]
        self.trail_time = QSpinBox()
        self.trail_time.setRange(trail_time_range.minimum, trail_time_range.maximum)
        self.trail_time.setSingleStep(trail_time_range.step)
        self.trail_time.setValue(vm.trail_time_ms)
        self.trail_time.valueChanged.connect(vm.set_trail_time_ms)
        form.addRow("Длина трейла (ms):", self.trail_time)

        trail_max_range = RANGES["trail_points_max"]
        self.trail_max = QSpinBox()
        self.trail_max.setRange(trail_max_range.minimum, trail_max_range.maximum)
        self.trail_max.setSingleStep(trail_max_range.step)
        self.trail_max.setValue(vm.trail_points_max)
        self.trail_max.valueChanged.connect(vm.set_trail_points_max)
        form.addRow("Макс. точек в трейле:", self.trail_max)

        group.setLayout(form)
        layout.addWidget(group)
