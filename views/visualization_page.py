from PySide6.QtWidgets import QWidget, QGridLayout

from core.config import UI
from viewmodels.heatmap_vm import HeatmapViewModel
from views.heatmap_view import HeatmapView
from views.plot_placeholder import PlotPlaceholder


class VisualizationPage(QWidget):
    def __init__(self, heatmap_vm: HeatmapViewModel, parent=None):
        super().__init__(parent)

        self.heatmap_view = HeatmapView(heatmap_vm)
        self.placeholder_right = PlotPlaceholder("Будущий график\n1×4")
        self.placeholder_bottom = PlotPlaceholder("Будущий график\n4×1")
        self.placeholder_corner = PlotPlaceholder("Будущий график\n1×1")

        grid = QGridLayout(self)
        grid.setContentsMargins(UI.content_margin, UI.content_margin,
                                 UI.content_margin, UI.content_margin)
        grid.setSpacing(UI.panel_spacing)
        grid.addWidget(self.heatmap_view, 0, 0)
        grid.addWidget(self.placeholder_right, 0, 1)
        grid.addWidget(self.placeholder_bottom, 1, 0)
        grid.addWidget(self.placeholder_corner, 1, 1)

        row_top, row_bottom = UI.viz_grid_row_stretch
        col_left, col_right = UI.viz_grid_col_stretch
        grid.setRowStretch(0, row_top)
        grid.setRowStretch(1, row_bottom)
        grid.setColumnStretch(0, col_left)
        grid.setColumnStretch(1, col_right)
