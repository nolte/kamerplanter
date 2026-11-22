"""Parser for the range strings the species catalogue stores for distances.

``Species.spacing_cm``, ``row_spacing_cm``, ``mature_height_cm`` and
``mature_width_cm`` are free-form strings (``species.py:384-386``), not numbers.
REQ-053 GP-FR-061 prefills the planting dialog from them and defines the
numeric reading as the **lower value** of the range.

Shapes measured in ``app/migrations/seed_data/*.yaml`` (724 values, 2026-10-16):
``"30-40"`` (405), ``"30--40"`` (190), ``"30"`` (98), ``null`` (27) and a bare
integer (4). The seed schema (``_defs.schema.yaml`` ``distance_cm_string``,
``^\\d+(\\.\\d+)?(\\s*[-–—]+\\s*\\d+(\\.\\d+)?)?$``) additionally admits en/em
dashes, whitespace around the dash and a decimal point. The parser accepts all
of that and is deliberately a little more lenient than the schema — surrounding
whitespace and a trailing ``cm`` — because the same fields also arrive through
the species API and the CSV import, which validate nothing. It does NOT accept a
decimal comma: ``"1,500"`` is the German thousands notation of a 15 m tree
spacing as often as it is 1.5 cm, and a guess here would be a silent default.

Unparsable input yields ``None`` rather than an exception: GP-FR-061 says a
missing value falls back to "last used" or an empty field with a hint — never a
silent default — and that decision belongs to the caller. So does the 5–1 500 cm
plausibility bound of GP-FR-060; the parser only reads the number.
"""

from __future__ import annotations

import math
import re

_NUMBER = r"\d+(?:\.\d+)?"
# One number, optionally followed by one or more dash characters (ASCII hyphen,
# en dash, em dash) and a second number; a trailing unit ``cm`` is tolerated.
# ``re.ASCII`` keeps ``\d`` to 0-9, matching the ECMA ``\d`` of the JSON schema.
_RANGE_PATTERN = re.compile(
    rf"^\s*(?P<low>{_NUMBER})\s*(?:[-–—]+\s*(?P<high>{_NUMBER}))?\s*(?:cm)?\s*$",
    re.IGNORECASE | re.ASCII,
)


def parse_range_bounds(value: str | int | float | None) -> tuple[float, float] | None:
    """Return ``(lower, upper)`` of a distance range string, or ``None``.

    A single value yields ``(v, v)``. A reversed range (``"40-30"``) is
    normalised so the lower bound comes first. Numbers are accepted directly
    because a few seed rows store a bare integer instead of a string; a
    negative or non-finite number is as unusable as an unparsable string.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number) or number < 0:
            return None
        return (number, number)
    if not isinstance(value, str):
        return None
    match = _RANGE_PATTERN.match(value)
    if match is None:
        return None
    low = float(match.group("low"))
    high_token = match.group("high")
    high = float(high_token) if high_token is not None else low
    if high < low:
        low, high = high, low
    return (low, high)


def parse_range_lower(value: str | int | float | None) -> float | None:
    """Return the lower value of a distance range string (GP-FR-061), or ``None``.

    ``"40"`` → ``40.0``, ``"25-30"`` → ``25.0``, ``"20--30"`` → ``20.0``,
    ``"5–10 cm"`` → ``5.0``; ``None``, ``""``, ``"unknown"`` and ``"1,500"`` → ``None``.
    The result is a ``float`` (``PlantingRunEntry.spacing_cm`` is a float and the
    schema admits ``"2.5"``); every integer the seeds store round-trips exactly.
    """
    bounds = parse_range_bounds(value)
    return bounds[0] if bounds is not None else None
