"""Offline CAN trace loading and simple summary statistics.

This intentionally delegates format parsing to python-can rather than
introducing a second handwritten parser for CAN utility logs.
"""

from dataclasses import dataclass
from pathlib import Path

import can

SUPPORTED_SUFFIXES = {".log", ".asc", ".blf"}


@dataclass(frozen=True)
class Frame:
    timestamp: float
    channel: str
    arbitration_id: int
    data: bytes
    is_extended_id: bool
    is_error_frame: bool
    is_remote_frame: bool


def load_frames(filename: str | Path) -> list[Frame]:
    """Load supported CAN log formats into normalized, read-only frames.

    Large-file streaming and background indexing are planned for later milestones.
    """
    path = Path(filename)
    if not path.is_file():
        raise FileNotFoundError(f"CAN log not found: {path}")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported CAN log format: {path.suffix}")

    reader = can.LogReader(path)
    try:
        return [
            Frame(
                timestamp=float(message.timestamp),
                channel=str(message.channel) if message.channel is not None else "",
                arbitration_id=message.arbitration_id,
                data=bytes(message.data),
                is_extended_id=message.is_extended_id,
                is_error_frame=message.is_error_frame,
                is_remote_frame=message.is_remote_frame,
            )
            for message in reader
        ]
    finally:
        # python-can readers may hold an open file handle.
        stop = getattr(reader, "stop", None)
        if callable(stop):
            stop()


def summarize(frames: list[Frame]) -> dict[str, int | float]:
    """Return deterministic, basic trace statistics."""
    if not frames:
        return {"frames": 0, "unique_ids": 0, "duration_s": 0.0}
    timestamps = [frame.timestamp for frame in frames]
    return {
        "frames": len(frames),
        "unique_ids": len({frame.arbitration_id for frame in frames}),
        "duration_s": round(max(timestamps) - min(timestamps), 6),
    }
