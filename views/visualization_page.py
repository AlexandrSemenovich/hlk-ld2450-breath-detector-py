from PySide6.QtWidgets import QWidget, QGridLayout, QSizePolicy

from core.config import UI
from viewmodels.heatmap_vm import HeatmapViewModel
from views.heatmap_view import HeatmapView
from views.range_profile_view import RangeProfileView
from views.presence_timeline_view import PresenceTimelineView
from views.movement_status_view import MovementStatusView


class VisualizationPage(QWidget):
    def __init__(self, heatmap_vm: HeatmapViewModel, parent=None):
        super().__init__(parent)

        self.heatmap_view = HeatmapView(heatmap_vm)
        self.range_profile_view = RangeProfileView(heatmap_vm)
        self.presence_view = PresenceTimelineView(heatmap_vm)
        self.movement_view = MovementStatusView(heatmap_vm)

        ignored = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.heatmap_view.setSizePolicy(ignored)
        self.range_profile_view.setSizePolicy(ignored)
        self.presence_view.setSizePolicy(ignored)
        self.movement_view.setSizePolicy(ignored)

        grid = QGridLayout(self)
        grid.setContentsMargins(UI.content_margin, UI.content_margin,
                                 UI.content_margin, UI.content_margin)
        grid.setSpacing(UI.panel_spacing)
        grid.addWidget(self.heatmap_view, 0, 0)
        grid.addWidget(self.range_profile_view, 0, 1)
        grid.addWidget(self.presence_view, 1, 0)
        grid.addWidget(self.movement_view, 1, 1)

        row_top, row_bottom = UI.viz_grid_row_stretch
        col_left, col_right = UI.viz_grid_col_stretch
        grid.setRowStretch(0, row_top)
        grid.setRowStretch(1, row_bottom)
        grid.setColumnStretch(0, col_left)
        grid.setColumnStretch(1, col_right)

    def start(self):
        self.heatmap_view.start()
        self.range_profile_view.start()
        self.presence_view.start()

    def clear(self):
        self.heatmap_view.clear()
        self.range_profile_view.clear()
        self.presence_view.clear()
        self.movement_view.clear()
