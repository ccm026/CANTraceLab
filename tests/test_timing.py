"""Regression tests for pure CAN timing analysis (no Qt or CAN adapter)."""

from dataclasses import replace

import pytest

from cantracelab.timing import TimingKey, analyze_timing, available_timing_keys
from cantracelab.trace import Frame


def frame(
    timestamp: float, *, can_id=0x123, channel="vcan0",
    extended=False, remote=False, error=False,
):
    return Frame(
        timestamp=timestamp,
        channel=channel,
        arbitration_id=can_id,
        data=b"\x11\x22\x33\x44",
        is_extended_id=extended,
        is_error_frame=error,
        is_remote_frame=remote,
    )


KEY = TimingKey("vcan0", 0x123, False)


def test_groups_by_channel_id_and_frame_format():
    frames = [
        frame(1.0), frame(1.1, channel="can1"), frame(1.2, extended=True),
        frame(1.3, can_id=0x456),
    ]
    assert available_timing_keys(frames) == (
        TimingKey("can1", 0x123, False),
        KEY,
        TimingKey("vcan0", 0x123, True),
        TimingKey("vcan0", 0x456, False),
    )


def test_ignores_remote_error_and_invalid_timestamps():
    frames = [
        frame(1.0, remote=True), frame(1.1, error=True),
        frame(float("nan")), frame(float("inf")), frame(float("-inf")),
    ]
    assert available_timing_keys(frames) == ()
    assert analyze_timing(frames, KEY).frame_count == 0


def test_out_of_order_input_is_sorted_and_statistics_match():
    frames = [frame(3.030), frame(3.000), frame(3.010)]
    report = analyze_timing(frames, KEY)
    assert report.frame_count == 3
    assert [v.duration_ms for v in report.intervals] == pytest.approx((10.0, 20.0))
    assert report.min_ms == pytest.approx(10.0)
    assert report.max_ms == pytest.approx(20.0)
    assert report.mean_ms == pytest.approx(15.0)
    assert report.median_ms == pytest.approx(15.0)
    assert report.peak_jitter_ms == pytest.approx(5.0)


def test_missing_expectation_never_reports_missing_or_anomaly():
    report = analyze_timing([frame(0.0), frame(0.020)], KEY)
    assert report.alert_count == 0
    assert report.estimated_missing == 0
    assert report.intervals[0].status == "not configured"
    assert report.intervals[0].deviation_ms is None


def test_expected_period_on_time_and_bounded_jitter():
    report = analyze_timing(
        [frame(0.0), frame(0.009), frame(0.020)],
        KEY,
        expected_period_ms=10.0,
        tolerance_percent=20,
    )
    assert [r.status for r in report.intervals] == ["on time", "on time"]
    assert report.alert_count == 0
    assert report.peak_jitter_ms == pytest.approx(1.0)


def test_long_gap_estimates_one_missing_frame():
    report = analyze_timing(
        [frame(0.0), frame(0.010), frame(0.030)], KEY, expected_period_ms=10.0
    )
    assert [v.status for v in report.intervals] == ["on time", "possible missing"]
    assert report.alert_count == 1
    assert report.estimated_missing == 1
    assert report.intervals[1].deviation_ms == pytest.approx(10.0)


def test_late_gap_shorter_than_two_cycles_is_not_necessarily_missing():
    report = analyze_timing(
        [frame(0.0), frame(0.013)], KEY, expected_period_ms=10.0, tolerance_percent=20
    )
    assert report.intervals[0].status == "late"
    assert report.alert_count == 1
    assert report.estimated_missing == 0


def test_early_gap_is_flagged_without_claiming_missing_frame():
    report = analyze_timing(
        [frame(0.0), frame(0.005)], KEY, expected_period_ms=10.0, tolerance_percent=20
    )
    assert report.intervals[0].status == "early"
    assert report.estimated_missing == 0


def test_large_gap_estimates_multiple_missing_frames():
    report = analyze_timing(
        [frame(0.0), frame(0.050)], KEY, expected_period_ms=10.0, tolerance_percent=10
    )
    assert report.intervals[0].estimated_missing == 4
    assert report.estimated_missing == 4


def test_duplicate_timestamps_are_measured_as_zero_length_interval():
    report = analyze_timing([frame(1.0), frame(1.0)], KEY, expected_period_ms=10.0)
    assert report.intervals[0].duration_ms == 0
    assert report.intervals[0].status == "early"


def test_other_can_group_cannot_contaminate_timing():
    frames = [frame(0.0), frame(0.020), frame(0.010, channel="can1"), frame(0.015, can_id=0x456)]
    report = analyze_timing(frames, KEY)
    assert report.frame_count == 2
    assert len(report.intervals) == 1
    assert report.intervals[0].duration_ms == pytest.approx(20.0)


def test_mismatched_format_does_not_contaminate_timing():
    frames = [frame(0.0), frame(0.020), frame(0.010, extended=True)]
    report = analyze_timing(frames, KEY)
    assert report.frame_count == 2
    assert report.intervals[0].duration_ms == pytest.approx(20.0)


def test_no_matching_frames_and_single_frame_are_safe():
    assert analyze_timing([], KEY).intervals == ()
    report = analyze_timing([frame(1.0)], KEY)
    assert report.frame_count == 1
    assert report.mean_ms is None
    assert report.peak_jitter_ms is None
    assert report.alert_count == 0


@pytest.mark.parametrize("period", [0, -1, float("nan"), float("inf")])
def test_invalid_expected_period_rejected(period):
    with pytest.raises(ValueError, match="Expected cycle"):
        analyze_timing([frame(0.0)], KEY, expected_period_ms=period)


@pytest.mark.parametrize("tolerance", [-1, 101, float("nan"), float("inf")])
def test_invalid_tolerance_rejected(tolerance):
    with pytest.raises(ValueError, match="Tolerance"):
        analyze_timing([frame(0.0)], KEY, tolerance_percent=tolerance)


def test_error_and_remote_frames_skipped_even_when_they_match_selected_id():
    base = frame(0.0)
    frames = [base, replace(base, timestamp=0.010, is_error_frame=True),
              replace(base, timestamp=0.020, is_remote_frame=True), frame(0.030)]
    assert analyze_timing(frames, KEY).intervals[0].duration_ms == pytest.approx(30.0)


def test_maximum_allowed_tolerance_prevents_late_alert_for_double_period():
    report = analyze_timing([frame(0.0), frame(0.020)], KEY,
                            expected_period_ms=10, tolerance_percent=100)
    assert report.alert_count == 0
    assert report.estimated_missing == 0
