"""Area doses of the bed care log (REQ-053 GP-FR-123, WP 8.9, review acceptance "area dosing").

The reference of the arithmetic the care dialog shows and the care log stores; the TypeScript port is
``features/gardenPlanner/model/areaDose.ts``. Both run against the operations ``area_dose``,
``nitrogen_approximation`` and ``unit_identity`` of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json``.

* :func:`quantity_total` — a rate per m² (``g_per_m2``, ``l_per_m2``) times the bed area becomes the total the
  care event stores (``quantity_total``, rounded to 3 places, unit ``g`` or ``l``). Any other unit, no quantity
  or a bed without area (``area_m2 <= 0``) has no total (``None``), never a silent 0.
* :func:`display_total` — the total as the dialog shows it: whole grams, litres to 0.1 (review U-001).
* :func:`nitrogen_approximation` — the product's N % on the label times a rate in g/m²: g N/m² (0.1) and
  kg N/ha (whole). An approximation of the product N, never a nutrient balance; it has no threshold and no
  seasonal warning (R-004 stays open, threshold default ``None``).
* :func:`g_per_m2_to_kg_per_ha`, :func:`l_per_m2_to_mm` — the unit identities 1 g/m² = 10 kg/ha and
  1 L/m² = 1 mm (pure mathematics, no agronomy).

Rounding is half-up on the exact binary value, the rule ``Number.prototype.toFixed`` follows in the port.
Pure: no I/O, no agronomic default. A rate is never derived here from a soil analysis or a feeder class.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

#: Units that are a dose per m² of the bed (GP-FR-100); the service derives ``quantity_total`` from them.
AREA_UNITS: frozenset[str] = frozenset({"g_per_m2", "l_per_m2"})
#: The unit of the total per area unit.
TOTAL_UNIT: dict[str, str] = {"g_per_m2": "g", "l_per_m2": "l"}

#: The stored total keeps three places (GP-FR-123).
TOTAL_DECIMALS = 3
#: The dialog shows whole grams and litres to 0.1 (review U-001).
DISPLAY_DECIMALS: dict[str, int] = {"g": 0, "l": 1}
#: A rate (pre-filled from the product data sheet) and g N/m² are shown to 0.1.
RATE_DECIMALS = 1

#: 1 g/m² = 10 000 g/ha = 10 kg/ha.
KG_PER_HA_PER_G_PER_M2 = 10.0
#: 1 L/m² = 1 dm³ over 100 dm² = 0.01 dm = 1 mm.
MM_PER_L_PER_M2 = 1.0


def round_half_up(value: float, decimals: int) -> float:
    """``value`` rounded to ``decimals`` places, ties away from zero on the exact binary value; ``-0.0`` is ``0.0``."""
    quantum = Decimal(1).scaleb(-decimals)
    return float(Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP)) + 0.0


def quantity_total(quantity: float | None, unit: str | None, area_m2: float | None) -> tuple[float | None, str | None]:
    """``quantity × area_m2`` for an area unit, rounded to 3 places, with its unit; ``(None, None)`` otherwise."""
    if quantity is None or not math.isfinite(quantity) or unit not in AREA_UNITS:
        return None, None
    if area_m2 is None or not math.isfinite(area_m2) or area_m2 <= 0:
        return None, None
    return round_half_up(quantity * area_m2, TOTAL_DECIMALS), TOTAL_UNIT[unit]


def display_total(total: float, total_unit: str) -> float:
    """The total as the dialog shows it: whole grams, litres to 0.1."""
    return round_half_up(total, DISPLAY_DECIMALS[total_unit])


def g_per_m2_to_kg_per_ha(rate_g_per_m2: float) -> float:
    """1 g/m² = 10 kg/ha (unrounded)."""
    return rate_g_per_m2 * KG_PER_HA_PER_G_PER_M2


def l_per_m2_to_mm(rate_l_per_m2: float) -> float:
    """1 L/m² = 1 mm layer (unrounded)."""
    return rate_l_per_m2 * MM_PER_L_PER_M2


def nitrogen_approximation(rate_g_per_m2: float | None, n_percent: float | None) -> tuple[float, float] | None:
    """``(g N/m², kg N/ha)`` from a rate in g/m² and the product's N % on the label; ``None`` without both.

    A product without an N value (``None`` or 0, the catalogue's "not stated") has no approximation, so a
    missing label never reads as "no nitrogen".
    """
    if rate_g_per_m2 is None or not math.isfinite(rate_g_per_m2) or rate_g_per_m2 <= 0:
        return None
    if n_percent is None or not math.isfinite(n_percent) or not 0 < n_percent <= 100:
        return None
    n_g_per_m2 = rate_g_per_m2 * n_percent / 100
    return round_half_up(n_g_per_m2, RATE_DECIMALS), round_half_up(g_per_m2_to_kg_per_ha(n_g_per_m2), 0)
