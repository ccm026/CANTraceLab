"""Filtering regressions independent of Qt widgets or CAN hardware."""

from cantracelab.filtering import frame_matches
from cantracelab.trace import Frame


def sample():
    return Frame(1.5, "vcan0", 0x123, bytes.fromhex("AA BB 00 CC"), False, False, False)


def test_empty_filters_accept_frame():
    assert frame_matches(sample())


def test_hex_id_filter_accepts_optional_prefix():
    assert frame_matches(sample(), can_id="0x123")
    assert frame_matches(sample(), can_id="12")
    assert not frame_matches(sample(), can_id="456")


def test_channel_is_case_insensitive():
    assert frame_matches(sample(), channel="VCAN")
    assert not frame_matches(sample(), channel="can1")


def test_payload_matches_hex_ignoring_spaces():
    assert frame_matches(sample(), payload="bb00")
    assert frame_matches(sample(), payload="AA BB")
    assert not frame_matches(sample(), payload="DE AD")


def test_filters_are_combined_with_and():
    assert frame_matches(sample(), can_id="0x123", channel="CAN0", payload="BB")
    assert not frame_matches(sample(), can_id="123", channel="can1", payload="BB")
