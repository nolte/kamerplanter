"""How many plants a sown row or zone holds after thinning (REQ-053 §11.3 "gesät", §12 ``thinning``, W-015).

Direct sowing in a ``row``/``zone`` slot records the sowing day (``Slot.sown_at``), not one plant per seed. Thinning
("Vereinzeln") turns the sown slot into plants: their number follows from the slot's measure and the spacing the
seedlings are thinned to — ``PlantingRunEntry.thinning_to_cm``, a value of the species' sowing data the grower
entered with the run.

* **Row** (``polyline``): the seedlings stand in one line, one every ``thinning_to_cm`` along it —
  ``floor(length / spacing)`` plants (the first and the last half a spacing from the ends).
* **Zone sown in rows or bands** (any area shape with a ``row_spacing_cm``): the seedlings stand ``thinning_to_cm``
  apart within rows ``row_spacing_cm`` apart — ``floor(area / (row_spacing x spacing))`` plants, the ``rows`` density
  of ``slot_capacity_calculator`` (#2862).
* **Zone without a row spacing** (broadcast seed, or no row spacing known): a square grid of ``thinning_to_cm`` —
  ``floor(area / spacing²)`` plants. This is an *estimate*: the stand of a band sowing also depends on the row
  spacing, which the square grid replaces by the in-row spacing (and so overstates).

A slot shorter or smaller than one spacing still holds the one seedling left standing (at least 1).

**No agronomic default** (E-10, guardrail G-W10 d): a missing spacing or row spacing is not replaced by a value of
this module — :func:`thinning_count` takes both as arguments; the caller takes them from the run, the species profile
or the grower, and asks the grower when there is none.

Pure: no I/O.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from app.common.enums import SlotRole
from app.domain.calculators.geometry_calculator import area_m2
from app.domain.models.geometry import Geometry, PolylineGeometry

type SownMeasureKind = Literal["length", "area"]
#: How a count was reached: one plant per spacing along a row, rows x in-row spacing, or the square-grid estimate.
type ThinningFormula = Literal["along_row", "rows", "square_grid"]

#: Decimals a measure is rounded to before the floor: 1.0 m / 10 cm is 10 plants, not 9 (float noise).
_FLOOR_DECIMALS = 6
#: Slot roles that can be sown (§11.3): a position slot holds one planted plant, never sown seed.
SOWABLE_ROLES: frozenset[SlotRole] = frozenset({SlotRole.ROW, SlotRole.ZONE})


@dataclass(frozen=True)
class SownMeasure:
    """What thinning divides: the row length in metres or the zone area in square metres."""

    kind: SownMeasureKind
    value: float


def polyline_length_m(geometry: PolylineGeometry) -> float:
    """The length of the line along its vertices, in metres."""
    return sum(math.dist(a, b) for a, b in zip(geometry.points, geometry.points[1:], strict=False))


def sown_measure(role: SlotRole, geometry: Geometry | None) -> SownMeasure | None:
    """The measure of a sown slot, or ``None`` when it has no usable geometry (unplaced, or a point).

    A ``row`` is measured along its line; a ``zone`` by its area. A row stored with an area shape is measured
    by its area — the shape, not the label, holds the seed.
    """
    if geometry is None or role not in SOWABLE_ROLES:
        return None
    if isinstance(geometry, PolylineGeometry):
        length = polyline_length_m(geometry)
        return SownMeasure("length", length) if length > 0 else None
    area = area_m2(geometry)
    return SownMeasure("area", area) if area > 0 else None


def thinning_formula(measure: SownMeasure, row_spacing_cm: float | None = None) -> ThinningFormula:
    """Which rule :func:`thinning_count` applies: a row ignores the row spacing, a zone uses it when there is one."""
    if measure.kind == "length":
        return "along_row"
    return "rows" if row_spacing_cm is not None else "square_grid"


def thinning_count(measure: SownMeasure, thinning_to_cm: float, row_spacing_cm: float | None = None) -> int:
    """The plants left standing after thinning ``measure`` to ``thinning_to_cm`` (see the module docstring).

    ``row_spacing_cm`` counts only for an area: with it the zone holds rows of seedlings, without it the square-grid
    estimate applies. A row (a length) holds one plant per ``thinning_to_cm`` whatever the row spacing.

    Raises:
        ValueError: ``thinning_to_cm`` or a given ``row_spacing_cm`` is not positive.
    """
    if not thinning_to_cm > 0:
        raise ValueError("thinning_to_cm must be positive.")
    if row_spacing_cm is not None and not row_spacing_cm > 0:
        raise ValueError("row_spacing_cm must be positive.")
    spacing_m = thinning_to_cm / 100.0
    formula = thinning_formula(measure, row_spacing_cm)
    if formula == "along_row":
        per_plant = spacing_m
    elif formula == "rows" and row_spacing_cm is not None:
        per_plant = spacing_m * (row_spacing_cm / 100.0)
    else:
        per_plant = spacing_m * spacing_m
    raw = measure.value / per_plant
    return max(1, math.floor(round(raw, _FLOOR_DECIMALS)))


__all__ = [
    "SOWABLE_ROLES",
    "SownMeasure",
    "ThinningFormula",
    "polyline_length_m",
    "sown_measure",
    "thinning_count",
    "thinning_formula",
]
