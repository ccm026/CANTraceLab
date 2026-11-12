"""DBC-backed decoding of offline CAN frames.

Keep decoder errors explicit and separate from the raw frame display. The
raw trace always remains inspectable even when the selected DBC is incomplete.
"""

from dataclasses import dataclass
from pathlib import Path

import cantools
from cantools.database.errors import DecodeError
from cantools.database.errors import Error as CantoolsError

from .trace import Frame


@dataclass(frozen=True)
class DecodedSignal:
    name: str
    value: int | float | str
    unit: str


@dataclass(frozen=True)
class DecodedFrame:
    """A single frame's decoding status and optional engineering signals.

    status is one of: decoded, unknown, invalid, skipped.
    """

    status: str
    message_name: str = ""
    signals: tuple[DecodedSignal, ...] = ()
    detail: str = ""


class DbcDecoder:
    """Read a DBC once, then decode frames without changing source records."""

    def __init__(self, database: cantools.database.can.Database):
        self._database = database

    @classmethod
    def from_file(cls, filename: str | Path) -> "DbcDecoder":
        path = Path(filename)
        if not path.is_file():
            raise FileNotFoundError(f"DBC file not found: {path}")
        if path.suffix.lower() != ".dbc":
            raise ValueError(f"Unsupported database format: {path.suffix or '<none>'}")
        try:
            database = cantools.database.load_file(path, database_format="dbc", strict=True)
        except (CantoolsError, UnicodeError, ValueError) as exc:
            raise ValueError(f"Invalid DBC file '{path.name}': {exc}") from exc
        return cls(database)

    @property
    def message_count(self) -> int:
        return len(self._database.messages)

    def decode(self, frame: Frame) -> DecodedFrame:
        if frame.is_error_frame:
            return DecodedFrame(status="skipped", detail="CAN error frame has no signals")
        if frame.is_remote_frame:
            return DecodedFrame(status="skipped", detail="Remote request has no payload")

        try:
            message = self._database.get_message_by_frame_id(frame.arbitration_id)
        except KeyError:
            return DecodedFrame(
                status="unknown",
                detail=f"No DBC definition for CAN ID 0x{frame.arbitration_id:X}",
            )

        # A standard and an extended frame carrying the same numeric identifier
        # must not be treated as interchangeable.
        if message.is_extended_frame != frame.is_extended_id:
            return DecodedFrame(
                status="unknown",
                detail=f"CAN ID 0x{frame.arbitration_id:X} frame format does not match DBC",
            )

        if len(frame.data) != message.length:
            return DecodedFrame(
                status="invalid",
                message_name=message.name,
                detail=(
                    f"Invalid payload length: expected {message.length}, "
                    f"received {len(frame.data)}"
                ),
            )

        try:
            values = message.decode(
                frame.data,
                decode_choices=True,
                scaling=True,
                allow_truncated=False,
                allow_excess=False,
            )
        except (DecodeError, ValueError, TypeError) as exc:
            return DecodedFrame(
                status="invalid", message_name=message.name, detail=f"Decode failed: {exc}"
            )

        # Container messages require a different representation. Leave them as
        # explicit unsupported frames in this milestone rather than guessing.
        if not isinstance(values, dict):
            return DecodedFrame(
                status="invalid",
                message_name=message.name,
                detail="Container decoding is not supported in this milestone",
            )

        units = {signal.name: signal.unit or "" for signal in message.signals}
        decoded_signals = tuple(
            DecodedSignal(
                name=name,
                value=value if isinstance(value, (int, float)) else str(value),
                unit=units.get(name, ""),
            )
            for name, value in values.items()
        )
        return DecodedFrame(status="decoded", message_name=message.name, signals=decoded_signals)
