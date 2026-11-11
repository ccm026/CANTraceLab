"""Pure, testable filtering rules for offline CAN frames.

An identifier filter matches hexadecimal characters, not decimal integers.
A payload filter matches contiguous hexadecimal byte characters.
"""

from .trace import Frame


def frame_matches(
    frame: Frame,
    *,
    can_id: str = "",
    channel: str = "",
    payload: str = "",
) -> bool:
    """Return whether a frame satisfies all non-empty, case-insensitive filters."""
    id_query = can_id.strip().lower()
    id_query = id_query.removeprefix("0x")
    if id_query and id_query not in f"{frame.arbitration_id:X}".lower():
        return False

    if channel.strip().casefold() not in frame.channel.casefold():
        return False

    payload_query = "".join(payload.split()).lower()
    payload_query = payload_query.removeprefix("0x")
    return payload_query in frame.data.hex()
