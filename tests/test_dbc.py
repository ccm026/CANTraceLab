"""Decoding regression tests using synthetic, non-proprietary DBC definitions."""

from pathlib import Path

import pytest

from cantracelab.dbc import DbcDecoder
from cantracelab.trace import Frame

SAMPLE_DBC = Path(__file__).resolve().parents[1] / "samples" / "demo.dbc"


def frame(
    can_id=0x123,
    data=b"\x11\x22\x33\x44",
    *,
    extended=False,
    error=False,
    remote=False,
):
    return Frame(1700000000.0, "vcan0", can_id, data, extended, error, remote)


@pytest.fixture(scope="module")
def decoder():
    return DbcDecoder.from_file(SAMPLE_DBC)


def test_dbc_loads_messages(decoder):
    assert decoder.message_count == 2


def test_scaled_signals_and_units(decoder):
    result = decoder.decode(frame())
    assert result.status == "decoded"
    assert result.message_name == "SensorFrame"
    values = {item.name: item for item in result.signals}
    assert values["VehicleSpeed"].value == pytest.approx(87.21)
    assert values["VehicleSpeed"].unit == "km/h"
    assert values["CoolantTemperature"].value == 51
    assert values["CoolantTemperature"].unit == "degC"
    assert values["SensorStatus"].value == 68


def test_second_message_decodes_scaled_engine_speed_and_choices(decoder):
    result = decoder.decode(frame(can_id=0x456, data=bytes.fromhex("AA BB CC DD")))
    assert result.status == "decoded"
    assert result.message_name == "PowertrainStatus"
    signals = {item.name: item.value for item in result.signals}
    assert signals["EngineSpeed"] == pytest.approx(1201.05)
    assert signals["Gear"] == 204
    assert signals["Mode"] == "Sport"


def test_unknown_can_id_is_nonfatal(decoder):
    result = decoder.decode(frame(can_id=0x777))
    assert result.status == "unknown"
    assert not result.signals
    assert "0x777" in result.detail


def test_standard_and_extended_ids_do_not_confuse_each_other(decoder):
    result = decoder.decode(frame(extended=True))
    assert result.status == "unknown"
    assert "frame format" in result.detail


@pytest.mark.parametrize("bad_data", [b"", b"\x11\x22", b"\x11\x22\x33\x44\x55"])
def test_wrong_payload_size_is_reported_not_silently_truncated(decoder, bad_data):
    result = decoder.decode(frame(data=bad_data))
    assert result.status == "invalid"
    assert "expected 4" in result.detail
    assert not result.signals


def test_error_frames_are_not_decoded(decoder):
    result = decoder.decode(frame(error=True))
    assert result.status == "skipped"
    assert not result.signals


def test_remote_frames_are_not_decoded(decoder):
    result = decoder.decode(frame(remote=True))
    assert result.status == "skipped"
    assert not result.signals


def test_missing_file_fails_explicitly(tmp_path):
    with pytest.raises(FileNotFoundError, match="DBC file not found"):
        DbcDecoder.from_file(tmp_path / "missing.dbc")


def test_bad_extension_is_rejected(tmp_path):
    path = tmp_path / "database.txt"
    path.write_text("not a DBC", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported database format"):
        DbcDecoder.from_file(path)


def test_invalid_dbc_is_rejected(tmp_path):
    path = tmp_path / "invalid.dbc"
    path.write_text("BO_ this cannot be a real DBC", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid DBC"):
        DbcDecoder.from_file(path)
