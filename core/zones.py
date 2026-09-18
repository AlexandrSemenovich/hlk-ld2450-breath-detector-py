import math
from dataclasses import dataclass

from core.config import VISUALIZATION, ZONES


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    shape: str
    color: str
    x_min: float = 0.0
    x_max: float = 0.0
    y_min: float = 0.0
    y_max: float = 0.0
    cx: float = 0.0
    cy: float = 0.0
    radius: float = 0.0
    fov_deg: float = 0.0

    def contains(self, x: float, y: float) -> bool:
        if self.shape == "rect":
            return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max
        if self.shape == "sector":
            dx = x - self.cx
            dy = y - self.cy
            distance = math.hypot(dx, dy)
            if distance > self.radius:
                return False
            if distance <= 1e-6:
                return True
            angle = math.degrees(math.atan2(dy, dx))
            theta1 = 90.0 - self.fov_deg
            theta2 = 90.0 + self.fov_deg
            return theta1 <= angle <= theta2
        dx = x - self.cx
        dy = y - self.cy
        return dx * dx + dy * dy <= self.radius * self.radius

    @property
    def label_xy(self) -> tuple[float, float]:
        if self.shape == "rect":
            return (self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0
        if self.shape == "sector":
            return self.cx, self.cy + self.radius * 0.55
        return self.cx, self.cy


def _build_zones() -> tuple[Zone, ...]:
    square_side = float(ZONES.square_y_max_mm - ZONES.square_y_min_mm)
    square_half = square_side / 2.0
    circle_radius = float(ZONES.circle_y_max_mm - ZONES.circle_y_min_mm) / 2.0
    circle_cy = (ZONES.circle_y_min_mm + ZONES.circle_y_max_mm) / 2.0
    return (
        Zone(
            id="near",
            name=ZONES.near_name,
            shape="sector",
            color=ZONES.near_color,
            cx=0.0,
            cy=0.0,
            radius=float(ZONES.near_range_mm),
            fov_deg=float(VISUALIZATION.fov_deg),
        ),
        Zone(
            id="left_square",
            name=ZONES.square_name,
            shape="rect",
            color=ZONES.square_color,
            x_min=float(ZONES.square_x_center_mm) - square_half,
            x_max=float(ZONES.square_x_center_mm) + square_half,
            y_min=float(ZONES.square_y_min_mm),
            y_max=float(ZONES.square_y_max_mm),
        ),
        Zone(
            id="right_circle",
            name=ZONES.circle_name,
            shape="circle",
            color=ZONES.circle_color,
            cx=float(ZONES.circle_x_center_mm),
            cy=circle_cy,
            radius=circle_radius,
        ),
    )


SCENE_ZONES = _build_zones()


def classify_point(x: float, y: float) -> Zone | None:
    for zone in SCENE_ZONES:
        if zone.contains(x, y):
            return zone
    return None


def apply_zones(payload: dict) -> dict:
    for current in payload.get("currents") or []:
        zone = classify_point(float(current["x"]), float(current["y"])) if current.get("present") else None
        current["zone_id"] = zone.id if zone else None
        current["zone_name"] = zone.name if zone else None
        current["zone_color"] = zone.color if zone else None
    return payload
