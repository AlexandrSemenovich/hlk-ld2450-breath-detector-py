from dataclasses import dataclass


@dataclass
class Target:
    x: int
    y: int
    speed: int
    resolution: int


@dataclass
class RadarFrame:
    target: Target
    timestamp_ms: int
    frame_id: str
    raw_line: str
