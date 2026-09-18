from core.frame import RadarFrame, Target


def parse_raw_line(line: str) -> RadarFrame | None:
    line = line.strip()
    if not line.startswith("R"):
        return None

    parts = line[1:].split(",")
    if len(parts) < 14:
        return None

    try:
        targets = (
            _parse_target(parts, 0),
            _parse_target(parts, 4),
            _parse_target(parts, 8),
        )
        timestamp_ms = int(parts[12])
        frame_id = parts[13]
    except (ValueError, IndexError):
        return None

    return RadarFrame(
        targets=targets,
        timestamp_ms=timestamp_ms,
        frame_id=frame_id,
        raw_line=line,
    )


def _parse_target(parts: list[str], offset: int) -> Target:
    return Target(
        x=int(parts[offset]),
        y=int(parts[offset + 1]),
        speed=int(parts[offset + 2]),
        resolution=int(parts[offset + 3]),
    )
