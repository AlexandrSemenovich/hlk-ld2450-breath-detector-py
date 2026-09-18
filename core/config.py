from dataclasses import dataclass


@dataclass(frozen=True)
class SerialConfig:
    default_port: str = "COM3"
    default_baud: int = 921600
    available_ports: tuple = ("COM3", "COM4", "COM5", "COM6", "/dev/ttyUSB0")
    read_timeout_s: float = 0.01
    poll_interval_ms: int = 5


@dataclass(frozen=True)
class HeatmapConfig:
    max_range_mm: int = 6000
    bins: int = 90
    kernel_radius: int = 4
    kernel_sigma: float = 1.6
    history_max: int = 5000
    intensity_baseline: float = 80.0
    contrast_divisor: float = 100.0


@dataclass(frozen=True)
class VisualizationConfig:
    render_interval_ms: int = 33
    background_color: str = "#ffffff"
    grid_alpha: float = 0.25
    axis_x_label: str = "X (mm)"
    axis_y_label: str = "Y (mm)"
    title: str = "Сцена — присутствие людей"
    colormap: tuple = (
        "#ffffff", "#dbeafe", "#93c5fd", "#60a5fa",
        "#34d399", "#fde047", "#fb923c", "#ef4444",
    )
    trail_color: str = "#1976d2"
    trail_linewidth: float = 2.0
    trail_alpha: float = 0.85
    point_color: str = "#d32f2f"
    point_size: int = 130
    point_edge_color: str = "black"
    point_edge_width: float = 1.2
    target_colors: tuple = ("#d32f2f", "#1565c0", "#2e7d32")
    target_labels: tuple = ("Target 0", "Target 1", "Target 2")
    heat_alpha: float = 0.38
    fov_deg: float = 60.0
    ring_step_mm: int = 1000
    x_axis_clip_mm: int = 500
    scene_trail_ms: int = 2000
    moving_speed_cm_s: int = 20
    vector_scale: float = 12.0
    vector_linewidth: float = 0.9
    vector_linestyle: tuple = (0, (4, 3))
    vector_head_size: int = 14
    label_offset_mm: int = 180
    presence_window_ms: int = 45000
    presence_bins: int = 180


@dataclass(frozen=True)
class SettingsDefaults:
    fade_time_ms: int = 3000
    point_intensity: int = 80
    trail_time_ms: int = 2500
    trail_points_max: int = 1200
    mirror_x: bool = False


@dataclass(frozen=True)
class SpinRange:
    minimum: int
    maximum: int
    step: int


RANGES = {
    "baud": SpinRange(9600, 2000000, 115200),
    "fade_time_ms": SpinRange(200, 20000, 100),
    "point_intensity": SpinRange(10, 200, 5),
    "trail_time_ms": SpinRange(200, 20000, 100),
    "trail_points_max": SpinRange(50, 5000, 50),
}


@dataclass(frozen=True)
class Theme:
    bg_app: str = "#eef1f5"
    bg_panel: str = "#ffffff"
    border: str = "#d4dce4"
    text_primary: str = "#1f2933"
    text_secondary: str = "#5b6770"
    accent: str = "#1976d2"
    accent_hover: str = "#1565c0"
    accent_pressed: str = "#0d47a1"
    disabled: str = "#b6c2cc"
    raw_bg: str = "#0e1116"
    raw_text: str = "#36e07a"
    status_on: str = "#2e7d32"
    status_off: str = "#c62828"
    occupancy_on_bg: str = "#e8f5e9"
    occupancy_off_bg: str = "#ffebee"
    occupancy_on: str = "#2e7d32"
    occupancy_off: str = "#c62828"


@dataclass(frozen=True)
class Typography:
    font_family: str = "Segoe UI"
    font_size: int = 10
    mono_family: str = "Consolas"


@dataclass(frozen=True)
class UIConfig:
    window_title: str = "LD2450 — Monitor (MVVM)"
    window_width: int = 1350
    window_height: int = 850
    left_panel_stretch: int = 1
    right_panel_stretch: int = 4
    panel_spacing: int = 12
    content_margin: int = 12
    settings_column_max_width: int = 520
    viz_grid_row_stretch: tuple = (4, 1)
    viz_grid_col_stretch: tuple = (4, 1)
    status_bar_min_height: int = 38
    status_bar_font_size: int = 11
    status_led_size: int = 14
    raw_history_lines: int = 300
    raw_terminal_min_height: int = 240
    target_font_size: int = 11
    stats_font_size: int = 14


def build_stylesheet(theme: Theme = None, typo: Typography = None) -> str:
    theme = theme or THEME
    typo = typo or TYPO
    return f"""
    QWidget {{
        font-family: "{typo.font_family}";
        font-size: {typo.font_size}pt;
        color: {theme.text_primary};
        background-color: {theme.bg_app};
    }}
    QGroupBox {{
        font-weight: 600;
        border: 1px solid {theme.border};
        border-radius: 10px;
        margin-top: 16px;
        background: {theme.bg_panel};
        padding: 12px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px 0 6px;
        color: {theme.text_secondary};
    }}
    QPushButton {{
        background-color: {theme.accent};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {theme.accent_hover}; }}
    QPushButton:pressed {{ background-color: {theme.accent_pressed}; }}
    QPushButton:disabled {{ background-color: {theme.disabled}; }}
    QComboBox, QSpinBox {{
        padding: 6px 8px;
        border: 1px solid {theme.border};
        border-radius: 8px;
        background: {theme.bg_panel};
        selection-background-color: {theme.accent};
    }}
    QComboBox:focus, QSpinBox:focus {{ border: 1px solid {theme.accent}; }}
    QTabWidget::pane {{
        border: 1px solid {theme.border};
        border-radius: 10px;
        top: 6px;
    }}
    QTabBar::tab {{
        background: {theme.bg_panel};
        border: 1px solid {theme.border};
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 8px 16px;
        margin-right: 4px;
        color: {theme.text_secondary};
    }}
    QTabBar::tab:selected {{
        background: {theme.accent};
        color: #ffffff;
        border: 1px solid {theme.accent};
    }}
    QLabel {{ background: transparent; color: {theme.text_primary}; }}
    QStatusBar {{
        background-color: {theme.bg_panel};
        border-top: 1px solid {theme.border};
        color: {theme.text_secondary};
        min-height: {UI.status_bar_min_height}px;
        font-size: {UI.status_bar_font_size}pt;
        padding: 4px 8px;
    }}
    QStatusBar QLabel {{
        background: transparent;
        color: {theme.text_secondary};
        padding: 8px 16px;
        font-size: {UI.status_bar_font_size}pt;
    }}
    QStatusBar::item {{
        border: none;
    }}
    QFrame#StatusLed {{
        border: 1px solid rgba(0, 0, 0, 40);
        min-width: {UI.status_led_size}px;
        max-width: {UI.status_led_size}px;
        min-height: {UI.status_led_size}px;
        max-height: {UI.status_led_size}px;
        border-radius: {UI.status_led_size // 2}px;
        background-color: {theme.status_off};
    }}
    QFrame#MovementStatus {{
        background-color: {theme.bg_panel};
        border: 1px solid {theme.border};
        border-radius: 10px;
    }}
    QFrame#MovementStatus QLabel {{
        background: transparent;
    }}
    QFrame#MovementRow {{
        background-color: {theme.bg_app};
        border-radius: 8px;
    }}
    QPlainTextEdit#RawTerminal {{
        background-color: {theme.raw_bg};
        color: {theme.raw_text};
        border: 1px solid #2a2f36;
        border-radius: 8px;
        padding: 8px;
        font-family: "{typo.mono_family}";
        font-size: {typo.font_size}pt;
    }}
    """


SERIAL = SerialConfig()
HEATMAP = HeatmapConfig()
VISUALIZATION = VisualizationConfig()
SETTINGS_DEFAULTS = SettingsDefaults()
UI = UIConfig()
THEME = Theme()
TYPO = Typography()

STYLESHEET = build_stylesheet(THEME, TYPO)


@dataclass(frozen=True)
class Styles:
    label_box: str = (
        f"QLabel {{ background-color:{THEME.bg_panel}; border:1px solid {THEME.border}; "
        f"border-radius:8px; padding:10px; color:{THEME.text_primary}; }}"
    )
    label_raw: str = (
        f"QLabel {{ background-color:{THEME.raw_bg}; color:{THEME.raw_text}; "
        f"border:1px solid #2a2f36; border-radius:8px; padding:10px; }}"
    )
    target_box: str = (
        f"QLabel {{ background-color:{THEME.bg_panel}; border:1px solid {THEME.border}; "
        f"border-radius:8px; padding:12px; color:{THEME.text_primary}; }}"
    )
    stats_box: str = (
        f"QLabel {{ background-color:{THEME.bg_panel}; border:1px solid {THEME.border}; "
        f"border-radius:8px; padding:14px; color:{THEME.text_primary}; }}"
    )
    status_box: str = (
        f"QLabel {{ background-color:{THEME.bg_panel}; border:1px solid {THEME.border}; "
        f"border-radius:8px; padding:8px; color:{THEME.text_primary}; }}"
    )


STYLES = Styles()
