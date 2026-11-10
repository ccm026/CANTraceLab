"""Regression tests for log reading and basic trace statistics."""

import pytest

from cantracelab.trace import Frame, load_frames, summarize


def test_canutils_log_parses_messages(tmp_path):
    path = tmp_path / "capture.log"
    path.write_text(
        "(1700000000.000000) vcan0 123#11223344\n"
        "(1700000000.020000) vcan0 456#AABBCCDD\n",
        encoding="utf-8",
    )
    frames = load_frames(path)
    assert [f.arbitration_id for f in frames] == [0x123, 0x456]
    assert frames[0].data == bytes.fromhex("11 22 33 44")
    assert frames[1].data == bytes.fromhex("AA BB CC DD")
    assert summarize(frames)["unique_ids"] == 2
    assert summarize(frames)["duration_s"] == pytest.approx(0.02)


def test_missing_file_is_explicit(tmp_path):
    with pytest.raises(FileNotFoundError, match="CAN log not found"):
        load_frames(tmp_path / "missing.log")


def test_unknown_extension_is_rejected(tmp_path):
    path = tmp_path / "capture.txt"
    path.write_text("not a trace", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported CAN log format"):
        load_frames(path)


def test_empty_trace_summary():
    assert summarize([]) == {"frames": 0, "unique_ids": 0, "duration_s": 0.0}


def test_summary_does_not_depend_on_frame_order():
    def frame(t, arb_id):
        return Frame(t, "vcan0", arb_id, b"\x01", False, False, False)

    stats = summarize([frame(4.0, 0x123), frame(2.0, 0x123), frame(3.0, 0x456)])
    assert stats == {"frames": 3, "unique_ids": 2, "duration_s": 2.0}
