"""Build unit-safe, time-aligned plot series from DBC-decoded CAN frames.

Independent of Qt: invalid frames and non-numeric choice labels are ignored,
while each CAN channel and standard/extended identifier stays separate.
"""

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from .dbc import DbcDecoder
from .trace import Frame


@dataclass(frozen=True)
class SignalKey:
    channel: str
    arbitration_id: int
    is_extended_id: bool
    message_name: str
    signal_name: str
    unit: str

    @property
    def label(self) -> str:
        frame_type = "extended" if self.is_extended_id else "standard"
        suffix = f" ({self.unit})" if self.unit else ""
        return (
            f"{self.message_name} / {self.signal_name}{suffix} "
            f"· {self.channel or 'no channel'} · 0x{self.arbitration_id:X} ({frame_type})"
        )


@dataclass(frozen=True)
class SignalSeries:
    key: SignalKey
    times_s: tuple[float, ...]
    values: tuple[float, ...]

    @property
    def sample_count(self) -> int:
        return len(self.times_s)


def extract_signal_series(
    frames: Sequence[Frame], decoder: DbcDecoder
) -> tuple[SignalSeries, ...]:
    """Return sorted, timestamp-relative numeric series for each signal and channel.

    Values are scaled/decoded by the shared DbcDecoder. A timestamp of zero is
    the earliest finite timestamp in the trace, even for unknown CAN IDs.
    Frames from different channels are not mixed. Categorical DBC choices are
    intentionally omitted because they cannot be plotted on a numeric axis.
    """
    finite_times = [float(frame.timestamp) for frame in frames if math.isfinite(frame.timestamp)]
    if not finite_times:
        return ()
    origin = min(finite_times)
    samples: dict[SignalKey, list[tuple[float, float]]] = defaultdict(list)

    for frame in frames:
        if not math.isfinite(frame.timestamp):
            continue
        decoded = decoder.decode(frame)
        if decoded.status != "decoded":
            continue
        for signal in decoded.signals:
            value = signal.value
            if isinstance(value, bool) or not isinstance(value, (float, int)):
                continue
            if not math.isfinite(value):
                continue
            key = SignalKey(
                channel=frame.channel,
                arbitration_id=frame.arbitration_id,
                is_extended_id=frame.is_extended_id,
                message_name=decoded.message_name,
                signal_name=signal.name,
                unit=signal.unit,
            )
            samples[key].append((float(frame.timestamp) - origin, float(value)))

    result = []
    for key in sorted(
        samples,
        key=lambda k: (k.channel, k.arbitration_id, k.is_extended_id, k.signal_name),
    ):
        # Python's stable sort preserves frame order at identical timestamps.
        ordered = sorted(samples[key], key=lambda sample: sample[0])
        result.append(
            SignalSeries(
                key=key,
                times_s=tuple(sample[0] for sample in ordered),
                values=tuple(sample[1] for sample in ordered),
            )
        )
    return tuple(result)
