"""Presentation precision: do not round the actual decoded signal values."""

import math

import pytest

from cantracelab.formatting import format_signal_value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (87.21000000000001, "87.21"),
        (82.08, "82.08"),
        (0.0, "0"),
        (1.23456789, "1.23457"),
        (123, "123"),
        ("Sport", "Sport"),
        (True, "True"),
    ],
)
def test_formats_decoded_value_for_display(value, expected):
    assert format_signal_value(value) == expected


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nonfinite_values_are_not_presented_as_measurements(value):
    assert format_signal_value(value) == "—"


def test_invalid_precision_is_rejected():
    with pytest.raises(ValueError, match="significant_digits"):
        format_signal_value(1.0, significant_digits=0)
