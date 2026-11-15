"""Offline CAN frame timing statistics and configurable gap diagnostics.

Timing analysis is independent of Qt, DBC and hardware. Gap anomalies require
an explicitly configured expected cycle time; statistical dispersion alone is
not proof of a missing CAN frame. Frames are grouped by bus, ID and format.
"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .trace import Frame


@dataclass(frozen=True, order=True)
class TimingKey:
    channel: str
    arbitration_id: int
    is_extended_id: bool

    @property
    def label(self) -> str:
        frame_type = "extended" if self.is_extended_id else "standard"
        return f"{self.channel or 'no channel'} · 0x{self.arbitration_id:X} ({frame_type})"


@dataclass(frozen=True)
class TimingInterval:
    start_timestamp_s: float
    end_timestamp_s: float
    duration_ms: float
    deviation_ms: float | None
    status: str
    estimated_missing: int


@dataclass(frozen=True)
class TimingReport:
    key: TimingKey
    frame_count: int
    intervals: tuple[TimingInterval, ...]
    mean_ms: float | None
    median_ms: float | None
    min_ms: float | None
    max_ms: float | None
    peak_jitter_ms: float | None
    alert_count: int
    estimated_missing: int
    expected_period_ms: float | None
    tolerance_percent: float


def _valid_data_frame(frame: "Frame") -> bool:
    return (
        not frame.is_error_frame
        and not frame.is_remote_frame
        and math.isfinite(frame.timestamp)
    )


def available_timing_keys(frames: Sequence["Frame"]) -> tuple[TimingKey, ...]:
    """Return unique channel/ID/frame-format groups for finite data frames."""
    return tuple(
        sorted(
            {
                TimingKey(frame.channel, frame.arbitration_id, frame.is_extended_id)
                for frame in frames
                if _valid_data_frame(frame)
            }
        )
    )


def analyze_timing(
    frames: Sequence["Frame"],
    key: TimingKey,
    *,
    expected_period_ms: float | None = None,
    tolerance_percent: float = 20.0,
) -> TimingReport:
    """Compute chronological gaps and optional expected-cycle anomalies.

    A gap is 'early' or 'late' if it deviates more than the selected tolerance.
    A sufficiently long late gap is a 'possible missing' event, with an
    approximate missing-frame count based on the nearest expected multiple.
    This cannot prove loss: pauses, bus scheduling or capture gaps also qualify.
    No extrapolation is made before the first or after the last captured frame.
    """
    if expected_period_ms is not None and (
        not math.isfinite(expected_period_ms) or expected_period_ms <= 0
    ):
        raise ValueError("Expected cycle must be finite and greater than zero milliseconds")
    if not math.isfinite(tolerance_percent) or not 0 <= tolerance_percent <= 100:
        raise ValueError("Tolerance must be a finite percentage between 0 and 100")

    timestamps = sorted(
        frame.timestamp
        for frame in frames
        if _valid_data_frame(frame)
        and frame.channel == key.channel
        and frame.arbitration_id == key.arbitration_id
        and frame.is_extended_id == key.is_extended_id
    )
    gaps = [
        (later - earlier) * 1000.0
        for earlier, later in pairwise(timestamps)
    ]
    median = statistics.median(gaps) if gaps else None
    intervals: list[TimingInterval] = []
    alert_count = 0
    missing_total = 0

    for start, end, duration_ms in zip(timestamps, timestamps[1:], gaps):
        deviation = None
        estimated_missing = 0
        status = "not configured"
        if expected_period_ms is not None:
            deviation = duration_ms - expected_period_ms
            allowance = expected_period_ms * tolerance_percent / 100.0
            if abs(deviation) <= allowance + 1e-9:
                status = "on time"
            elif deviation < 0:
                status = "early"
            else:
                # Missing events are only estimates and only for late gaps.
                estimated_missing = max(0, math.floor(duration_ms / expected_period_ms + 0.5) - 1)
                status = "possible missing" if estimated_missing else "late"
            if status != "on time":
                alert_count += 1
            missing_total += estimated_missing
        intervals.append(
            TimingInterval(
                start_timestamp_s=start,
                end_timestamp_s=end,
                duration_ms=duration_ms,
                deviation_ms=deviation,
                status=status,
                estimated_missing=estimated_missing,
            )
        )

    baseline = expected_period_ms if expected_period_ms is not None else median
    return TimingReport(
        key=key,
        frame_count=len(timestamps),
        intervals=tuple(intervals),
        mean_ms=statistics.fmean(gaps) if gaps else None,
        median_ms=median,
        min_ms=min(gaps) if gaps else None,
        max_ms=max(gaps) if gaps else None,
        peak_jitter_ms=max((abs(value - baseline) for value in gaps), default=None)
        if baseline is not None
        else None,
        alert_count=alert_count,
        estimated_missing=missing_total,
        expected_period_ms=expected_period_ms,
        tolerance_percent=tolerance_percent,
    )
