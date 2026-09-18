import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Wedge, FancyArrowPatch
from matplotlib.ticker import MultipleLocator

from core.config import HEATMAP, VISUALIZATION
from views.mpl_widget import TimedMplWidget


class HeatmapView(TimedMplWidget):
    def __init__(self, vm, parent=None):
        super().__init__(vm, parent)
        self.max_range = HEATMAP.max_range_mm
        self._x_half = self.max_range - VISUALIZATION.x_axis_clip_mm

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor(VISUALIZATION.background_color)
        self.figure.set_facecolor(VISUALIZATION.background_color)
        self.ax.grid(True, alpha=VISUALIZATION.grid_alpha)
        self.ax.set_xlim(-self._x_half, self._x_half)
        self.ax.set_ylim(0, self.max_range)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_autoscale_on(False)
        self.ax.set_title("")
        self.ax.set_xlabel("")
        self.ax.set_ylabel("")
        self._apply_inner_ticks()

        self._draw_static_scene()

        self.cmap = LinearSegmentedColormap.from_list("light_heat", list(VISUALIZATION.colormap))
        self.heat = np.zeros((vm.model.bins_y, vm.model.bins_x), dtype=np.float32)
        self.heat_img = self.ax.imshow(
            self.heat,
            origin="lower",
            cmap=self.cmap,
            extent=[-self.max_range, self.max_range, 0, self.max_range],
            interpolation="bilinear",
            vmin=0,
            vmax=1,
            alpha=VISUALIZATION.heat_alpha,
            zorder=0,
        )

        self.vector_arrows = []
        self.current_points = []
        self.target_labels = []
        for color, label in zip(VISUALIZATION.target_colors, VISUALIZATION.target_labels):
            arrow = FancyArrowPatch(
                (0, 0), (0, 0),
                arrowstyle="-|>",
                mutation_scale=VISUALIZATION.vector_head_size,
                linewidth=VISUALIZATION.vector_linewidth,
                linestyle=VISUALIZATION.vector_linestyle,
                color=color,
                shrinkA=0,
                shrinkB=0,
                zorder=5,
            )
            arrow.set_visible(False)
            self.ax.add_patch(arrow)
            current_point = self.ax.scatter(
                [], [], c=color, s=VISUALIZATION.point_size,
                edgecolors=VISUALIZATION.point_edge_color,
                linewidths=VISUALIZATION.point_edge_width, zorder=6,
            )
            text = self.ax.text(
                0, 0, label.replace("Target ", "T"),
                color=color, fontsize=9, fontweight="bold",
                ha="left", va="bottom", zorder=8, visible=False,
            )
            self.vector_arrows.append(arrow)
            self.current_points.append(current_point)
            self.target_labels.append(text)

        self.ax.scatter([0], [0], marker="^", c="#1f2933", s=70, zorder=7)

    def _sync_figure_size(self):
        width = self.canvas.width()
        height = self.canvas.height()
        if width <= 0 or height <= 0:
            return

        self.figure.set_size_inches(width / self.figure.dpi, height / self.figure.dpi)
        self.figure.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)

        inset = 0.02
        axes_w = 1.0 - 2 * inset
        axes_h = 1.0 - 2 * inset
        self.ax.set_position([inset, inset, axes_w, axes_h])

        pixel_w = width * axes_w
        pixel_h = height * axes_h
        if pixel_w <= 0 or pixel_h <= 0:
            return

        span_x = 2.0 * self._x_half
        span_y = max(self.max_range, span_x * (pixel_h / pixel_w))

        extra_y = max(0.0, span_y - self.max_range)
        y_min = -extra_y * 0.12
        self.ax.set_xlim(-span_x / 2.0, span_x / 2.0)
        self.ax.set_ylim(y_min, y_min + span_y)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.xaxis.set_major_locator(MultipleLocator(2000))
        self._apply_inner_ticks()
        self.canvas.draw_idle()

    def _apply_inner_ticks(self):
        self.ax.tick_params(
            which="both",
            direction="in",
            top=True,
            right=True,
            labelsize=8,
            length=5,
            width=0.8,
            pad=-14,
        )
        for label in self.ax.get_xticklabels():
            label.set_verticalalignment("bottom")
        for label in self.ax.get_yticklabels():
            label.set_horizontalalignment("left")

    def _draw_static_scene(self):
        fov = VISUALIZATION.fov_deg
        theta1 = 90.0 - fov
        theta2 = 90.0 + fov
        wedge = Wedge(
            (0, 0), self.max_range, theta1, theta2,
            facecolor="#1976d2", alpha=0.06, edgecolor="#1976d2",
            linewidth=1.2, zorder=1,
        )
        self.ax.add_patch(wedge)

        rings = range(VISUALIZATION.ring_step_mm, self.max_range + 1, VISUALIZATION.ring_step_mm)
        az = np.linspace(np.radians(theta1), np.radians(theta2), 64)
        for radius in rings:
            self.ax.plot(
                radius * np.cos(az), radius * np.sin(az),
                color="#9aa5b1", lw=0.8, alpha=0.7, zorder=2,
            )
            self.ax.text(
                220, radius, f"{radius / 1000:.0f} м",
                color="#5b6770", fontsize=8, va="bottom", zorder=2,
            )

    def _render(self):
        if self._latest is None:
            return
        payload = self._latest
        self.heat_img.set_data(payload["heat"])
        self.heat_img.set_clim(0.0, payload["vmax"])

        offset = VISUALIZATION.label_offset_mm
        empty = np.array([[np.nan, np.nan]], dtype=np.float64)
        for index, current in enumerate(payload["currents"]):
            point = self.current_points[index]
            label = self.target_labels[index]
            arrow = self.vector_arrows[index]
            if not current.get("present"):
                point.set_offsets(empty)
                label.set_visible(False)
                arrow.set_visible(False)
                continue

            x, y = current["x"], current["y"]
            speed = current["speed"]
            point.set_offsets(np.array([[x, y]], dtype=np.float64))
            moving = abs(speed) >= VISUALIZATION.moving_speed_cm_s
            point.set_linewidths(2.4 if moving else 1.0)
            label.set_position((x + offset, y + offset))
            label.set_visible(True)

            if moving:
                radius = max((x * x + y * y) ** 0.5, 1.0)
                scale = VISUALIZATION.vector_scale * speed
                arrow.set_positions(
                    (x, y),
                    (x + scale * x / radius, y + scale * y / radius),
                )
                arrow.set_visible(True)
            else:
                arrow.set_visible(False)

        self.canvas.draw_idle()

    def clear(self):
        self._latest = None
        self.heat_img.set_data(np.zeros_like(self.heat))
        self.heat_img.set_clim(0.0, 1.0)
        empty = np.array([[np.nan, np.nan]], dtype=np.float64)
        for arrow, point, label in zip(
            self.vector_arrows, self.current_points, self.target_labels
        ):
            arrow.set_visible(False)
            point.set_offsets(empty)
            label.set_visible(False)
        self.canvas.draw_idle()
