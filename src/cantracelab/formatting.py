"""Presentation-only formatting for decoded engineering signals.

The original numeric data is kept intact for plots, exports, and calculations.
"""

import math
from numbers import Real


def format_signal_value(value: object, *, significant_digits: int = 6) -> str:
    """Keep enum choices, integers and bools legible; round only display text.

    Non-finite numeric inputs are indicated as unavailable rather than shown
    as fabricated measurements. This does not mutate the underlying decoded
    value or its precision.
    """
    if significant_digits < 1:
        raise ValueError("significant_digits must be at least 1")
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, Real):
        if not math.isfinite(value):
            return "—"
        if isinstance(value, int):
            return str(value)
        text = format(value, f".{significant_digits}g")
        return "0" if text == "-0" else text
    return str(value)
