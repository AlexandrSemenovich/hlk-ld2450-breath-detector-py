from dataclasses import dataclass


@dataclass
class Target:
    x: int
    y: int
    speed: int
    resolution: int

    @property
    def present(self) -> bool:
        return not (self.x == 0 and self.y == 0 and self.speed == 0)


@dataclass
class RadarFrame:
    targets: tuple[Target, Target, Target]
    timestamp_ms: int
    frame_id: str
    raw_line: str

    @property
    def target(self) -> Target:
        return self.targets[0]
