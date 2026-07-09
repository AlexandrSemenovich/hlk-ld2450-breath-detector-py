from core.frame import RadarFrame, Target


def parse_raw_line(line: str) -> RadarFrame | None:
    line = line.strip()
    if not line.startswith("R"):
        return None

    parts = line[1:].split(",")
    if len(parts) < 14:
        return None

    try:
        x = int(parts[0])
        y = int(parts[1])
        speed = int(parts[2])
        resolution = int(parts[3])
        timestamp_ms = int(parts[12])
        frame_id = parts[13]
    except (ValueError, IndexError):
        return None

    target = Target(x=x, y=y, speed=speed, resolution=resolution)
    return RadarFrame(
        target=target,
        timestamp_ms=timestamp_ms,
        frame_id=frame_id,
        raw_line=line,
    )
