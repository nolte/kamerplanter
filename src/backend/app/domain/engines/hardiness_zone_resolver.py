"""REQ-039 — hardiness-zone resolver: pure, algorithmic zone derivation.

Derives a plant hardiness zone from *climate normals* (chiefly the coldest
monthly mean daily-minimum temperature) using the **license-free USDA zone
schema** — a fixed temperature-band formula — and never any proprietary
USDA/PHZM/PRISM gridded map data. The whole module is pure domain logic with no
I/O: the temperature bands are computed from the schema constants, so the derived
value depends only on the site's own climate normals.

Schema (license-free): the USDA scale defines 26 half-zones from ``1a`` to
``13b``. Each half-zone spans 5 °F; zone ``1a`` starts at -60 °F. From this the
whole ``°C`` band table follows by conversion — no external data set is
consulted, so nothing proprietary is embedded.

The resolver returns a zone *label* (e.g. ``"7b"``); the reference catalog
(collection ``hardiness_zones``, seeded separately) carries only the human-facing
descriptions and frost-date defaults and is looked up by that label in the
service layer.
"""

from __future__ import annotations

from app.domain.models.weather import ClimateNormal

#: Number of half-zones on the USDA scale (``1a`` … ``13b``).
_HALF_ZONE_COUNT = 26
#: Index of the coldest (``1a``) and warmest (``13b``) half-zone.
MIN_ZONE_INDEX = 0
MAX_ZONE_INDEX = _HALF_ZONE_COUNT - 1
#: Width of one half-zone in °F (the license-free USDA schema constant).
_HALF_ZONE_WIDTH_F = 5.0
#: Lower temperature bound of zone ``1a`` in °F (schema anchor).
_ZONE_1A_MIN_F = -60.0


def fahrenheit_to_celsius(temp_f: float) -> float:
    """Convert °F to °C (rounded to two decimals for a stable band table)."""
    return round((temp_f - 32.0) * 5.0 / 9.0, 2)


def zone_label_for_index(index: int) -> str:
    """Return the USDA half-zone label (``"1a"`` … ``"13b"``) for a 0-based index."""
    if not MIN_ZONE_INDEX <= index <= MAX_ZONE_INDEX:
        raise ValueError(f"Hardiness half-zone index {index} out of range [0, {MAX_ZONE_INDEX}]")
    zone_number = 1 + index // 2
    subzone = "a" if index % 2 == 0 else "b"
    return f"{zone_number}{subzone}"


def index_for_zone_label(zone: str) -> int:
    """Return the 0-based half-zone index for a label (``"7b" -> 13``).

    Raises :class:`ValueError` for a label outside ``1a``…``13b``.
    """
    normalized = zone.strip().lower()
    subzone = normalized[-1]
    if subzone not in ("a", "b"):
        raise ValueError(f"Invalid hardiness zone label {zone!r}: must end in 'a' or 'b'")
    zone_number = int(normalized[:-1])
    index = (zone_number - 1) * 2 + (0 if subzone == "a" else 1)
    if not MIN_ZONE_INDEX <= index <= MAX_ZONE_INDEX:
        raise ValueError(f"Hardiness zone label {zone!r} out of range 1a…13b")
    return index


def zone_bounds_f(index: int) -> tuple[float, float]:
    """Return ``(temp_min_f, temp_max_f)`` of the half-zone at ``index``."""
    temp_min_f = _ZONE_1A_MIN_F + index * _HALF_ZONE_WIDTH_F
    return temp_min_f, temp_min_f + _HALF_ZONE_WIDTH_F


def zone_bounds_c(index: int) -> tuple[float, float]:
    """Return ``(temp_min_c, temp_max_c)`` of the half-zone at ``index``."""
    temp_min_f, temp_max_f = zone_bounds_f(index)
    return fahrenheit_to_celsius(temp_min_f), fahrenheit_to_celsius(temp_max_f)


def classify_from_minimum(mean_annual_minimum_c: float) -> str:
    """Classify a mean annual minimum temperature (°C) into a USDA half-zone.

    Applies the license-free band formula and clamps out-of-range inputs onto the
    coldest (``1a``) / warmest (``13b``) zone rather than raising, so an extreme
    Arctic or tropical normal still yields a well-defined zone.
    """
    temp_f = mean_annual_minimum_c * 9.0 / 5.0 + 32.0
    raw_index = int((temp_f - _ZONE_1A_MIN_F) // _HALF_ZONE_WIDTH_F)
    clamped_index = max(MIN_ZONE_INDEX, min(MAX_ZONE_INDEX, raw_index))
    return zone_label_for_index(clamped_index)


def mean_annual_minimum_from_normals(normal: ClimateNormal) -> float | None:
    """Extract the mean annual minimum (°C) that drives the zone classification.

    Prefers the pre-computed ``coldest_month_min_c``; falls back to the minimum of
    the twelve ``monthly_temp_min_c`` values. Returns ``None`` when a record has
    neither (a coarse foundation record that no fully-populating adapter has
    filled yet), so the caller can skip it instead of deriving a bogus zone.
    """
    if normal.coldest_month_min_c is not None:
        return normal.coldest_month_min_c
    if normal.monthly_temp_min_c:
        return min(normal.monthly_temp_min_c)
    return None


def derive_from_climate_normals(normal: ClimateNormal) -> tuple[str, float] | None:
    """Derive ``(zone_label, mean_annual_minimum_c)`` from a climate-normal record.

    Returns ``None`` when the record carries no usable minimum temperature.
    """
    minimum = mean_annual_minimum_from_normals(normal)
    if minimum is None:
        return None
    return classify_from_minimum(minimum), minimum
