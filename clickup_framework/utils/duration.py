"""Duration parsing helpers for CLI commands."""

from __future__ import annotations

import re


_DURATION_TOKEN_RE = re.compile(r"(\d+(?:\.\d+)?)([dhms])", re.IGNORECASE)
_UNIT_TO_MS = {
    "d": 24 * 60 * 60 * 1000,
    "h": 60 * 60 * 1000,
    "m": 60 * 1000,
    "s": 1000,
}


def parse_duration_to_ms(value: str) -> int:
    """Parse a human duration string into milliseconds.

    Supported examples:
    - ``2h30m``
    - ``90m``
    - ``1.5h``
    - ``45s``
    """
    if value is None:
        raise ValueError("Duration is required")

    normalized = value.strip().lower().replace(" ", "")
    if not normalized:
        raise ValueError("Duration is required")

    if normalized.isdigit():
        return int(normalized) * _UNIT_TO_MS["m"]

    total = 0.0
    position = 0
    for match in _DURATION_TOKEN_RE.finditer(normalized):
        if match.start() != position:
            raise ValueError(f"Invalid duration: {value}")
        amount = float(match.group(1))
        unit = match.group(2).lower()
        total += amount * _UNIT_TO_MS[unit]
        position = match.end()

    if position != len(normalized):
        raise ValueError(f"Invalid duration: {value}")

    milliseconds = int(total)
    if milliseconds <= 0:
        raise ValueError("Duration must be greater than zero")

    return milliseconds
