"""Pure signal-series tests: no GUI, display server or CAN adapter needed."""

from dataclasses import replace
from pathlib import Path

import pytest

from cantracelab.dbc import DbcDecoder, DecodedFrame, DecodedSignal
from cantracelab.plot_series import extract_signal_series
from cantracelab.trace import Frame, load_frames

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DBC = ROOT / "samples" / "demo.dbc"
SAMPLE_LOG = ROOT / "samples" / "demo.log"


def prepared():
    return load_frames(SAMPLE_LOG), DbcDecoder.from_file(SAMPLE_DBC)


def one_signal(series, name, channel="vcan0"):
    return next(item for item in series if item.key.signal_name == name and item.key.channel == channel)


def test_builds_numeric_series_and_omits_categorical_choices():
    frames, decoder = prepared()
    result = extract_signal_series(frames, decoder)
    assert {series.key.signal_name for series in result} == {
        "VehicleSpeed", "CoolantTemperature", "SensorStatus", "EngineSpeed", "Gear"
    }
    assert "Mode" not in {series.key.signal_name for series in result}


def test_scaled_values_and_units_match_decoded_samples():
    frames, decoder = prepared()
    result = extract_signal_series(frames, decoder)
    speed = one_signal(result, "VehicleSpeed")
    assert speed.key.unit == "km/h"
    assert speed.values == pytest.approx((87.21, 82.08))
    assert speed.sample_count == 2
    assert one_signal(result, "EngineSpeed").values == pytest.approx((1201.05,))
    assert one_signal(result, "CoolantTemperature").values == pytest.approx((51, 48))


def test_all_series_share_same_trace_time_origin():
    frames, decoder = prepared()
    series = extract_signal_series(frames, decoder)
    assert one_signal(series, "VehicleSpeed").times_s == pytest.approx((0.0, 0.02), abs=1e-5)
    assert one_signal(series, "EngineSpeed").times_s == pytest.approx((0.01,), abs=1e-5)


def test_out_of_order_frames_are_sorted_by_timestamp():
    frames, decoder = prepared()
    series = extract_signal_series(frames[::-1], decoder)
    speed = one_signal(series, "VehicleSpeed")
    assert speed.times_s == pytest.approx((0.0, 0.02), abs=1e-5)
    assert speed.values == pytest.approx((87.21, 82.08))


def test_unknown_invalid_and_remote_frames_cannot_pollute_plots():
    frames, decoder = prepared()
    bad = [
        replace(frames[0], arbitration_id=0x777),
        replace(frames[0], data=b"\x01"),
        replace(frames[0], is_extended_id=True),
        replace(frames[0], is_remote_frame=True),
        replace(frames[0], is_error_frame=True),
    ]
    result = extract_signal_series([*bad, *frames], decoder)
    assert one_signal(result, "VehicleSpeed").sample_count == 2
    assert len(result) == 5


def test_identical_identifiers_from_different_channels_are_kept_separate():
    frames, decoder = prepared()
    same_data_other_bus = replace(frames[0], channel="can1", timestamp=frames[0].timestamp)
    series = extract_signal_series([*frames, same_data_other_bus], decoder)
    assert one_signal(series, "VehicleSpeed", "can1").sample_count == 1
    assert one_signal(series, "VehicleSpeed", "vcan0").sample_count == 2


def test_unknown_frame_can_precede_first_plottable_measurement():
    frames, decoder = prepared()
    first = replace(frames[0], arbitration_id=0x777, timestamp=frames[0].timestamp - 2)
    series = extract_signal_series([first, *frames], decoder)
    assert one_signal(series, "VehicleSpeed").times_s == pytest.approx((2.0, 2.02), abs=1e-5)


def test_no_frames_and_non_finite_timestamps_produce_no_series():
    frames, decoder = prepared()
    assert extract_signal_series([], decoder) == ()
    assert extract_signal_series([replace(frames[0], timestamp=float("nan"))], decoder) == ()


def test_invalid_numeric_and_categorical_results_are_skipped():
    frames, _ = prepared()

    class FakeDecoder:
        def decode(self, _frame: Frame):
            return DecodedFrame(
                status="decoded",
                message_name="Synthetic",
                signals=(
                    DecodedSignal("Valid", 1.25, "V"),
                    DecodedSignal("Nan", float("nan"), "V"),
                    DecodedSignal("Infinite", float("inf"), "V"),
                    DecodedSignal("Categorical", "Sport", ""),
                    DecodedSignal("Boolean", True, ""),
                ),
            )

    result = extract_signal_series(frames[:1], FakeDecoder())
    assert len(result) == 1
    assert result[0].key.signal_name == "Valid"
    assert result[0].values == (1.25,)
