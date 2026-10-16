"""The pure derivations of migration M1 (``v0093_garden_plan_geometry``, REQ-053 §9.2a / §20.8).

Two legacy fields become geometry:

* ``Location.dimensions = (length, width, height)`` in metres — the frontend labels
  it *L × B × H* — becomes a ``rect`` in the plan frame with ``origin = (0, 0)``,
  ``width_m`` along ``+x`` and ``length_m`` along ``+y`` (§20.1), plus ``height_m``
  (O-02). A location whose ``dimensions`` are ``(0, 0, 0)`` keeps ``geometry = null``
  and stays in every list (GP-ACC-035).
* ``Slot.position = (row, col)``, a unit-less grid cell, becomes a ``point`` in the
  bed frame of its location: ``origin = (col × pitch, row × pitch)`` with ``pitch``
  = ``Location.pitch_m`` (default :data:`DEFAULT_PITCH_M`, an 11-litre pot), and
  ``geometry_source = migrated_grid`` marks the estimate (R-08). ``row_index`` keeps
  the row; ``sequence`` is the slot's 1-based rank within its location ordered by
  ``(row, col, slot_id, _key)`` — the spec's ``R2P05 → sequence 11`` (§20.5).

What real volumes hold (measured 2026-10-16): no write path ever set a slot's
``position`` — ``SlotCreate.position`` defaults to ``(0, 0)`` and the dialog never
sends it — so on an installation every slot of a location sits on the **same**
cell and the migration stacks them on the bed origin. The rank then comes from
``slot_id`` in natural order (``BED_2`` before ``BED_10``), which is the order the
grower gave the positions, and the migration's report counts the collapsed
locations so the operator sees it before the production run (plan §8, P-1).

The functions here are pure so the version module stays an orchestration and the
derivation can be read — and ported — on its own. Every geometry goes through
:func:`~app.domain.models.geometry.parse_geometry`, so a value V-01 refuses (a 0 m
width, a 2 km bed) is reported, never stored half-valid.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import ValidationError

from app.common.enums import GeometryKind, GeometrySource
from app.domain.models.geometry import (
    MAX_DIMENSION_M,
    MIN_DIMENSION_M,
    GeometryFrame,
    parse_geometry,
    round_length,
)

#: The pitch assumed for a slot whose location declares no ``pitch_m`` (REQ-053 §9.2a).
DEFAULT_PITCH_M = 0.30

#: The stored ``geometry_source`` of every slot point this migration derives.
MIGRATED_GRID = GeometrySource.MIGRATED_GRID.value

_DIGITS = re.compile(r"(\d+)")


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def dimensions_triple(value: object) -> tuple[float, float, float] | None:
    """``(length, width, height)`` as floats, or ``None`` when the stored value is not a numeric triple."""
    if not isinstance(value, list | tuple) or len(value) != 3 or not all(_is_number(part) for part in value):
        return None
    length, width, height = (float(part) for part in value)
    return length, width, height


def has_dimensions(value: object) -> bool:
    """Whether ``dimensions`` carries any extent at all — ``(0, 0, 0)`` is the legacy "unset"."""
    triple = dimensions_triple(value)
    return triple is not None and any(part != 0 for part in triple)


def rect_from_dimensions(value: object) -> dict[str, Any] | None:
    """The ``rect`` geometry of a legacy ``dimensions`` triple, or ``None`` when V-01 refuses it.

    ``origin`` is ``(0, 0)`` (§20.8): the bed sits at the plan origin until the user
    places it. ``width_m`` is the second component (B), ``length_m`` the first (L).
    """
    triple = dimensions_triple(value)
    if triple is None:
        return None
    length, width, _ = triple
    try:
        geometry = parse_geometry(
            {"kind": GeometryKind.RECT, "origin": (0.0, 0.0), "width_m": width, "length_m": length},
            frame=GeometryFrame.PLAN,
        )
    except ValidationError:
        return None
    return geometry.model_dump(mode="json")


def height_from_dimensions(value: object) -> float | None:
    """``height_m`` from the third component, rounded to the storage precision.

    ``None`` below 1 cm or above the plan frame's 1 000 m — the same bounds V-01
    puts on a width, applied here because ``height_m`` is not a geometry and has
    no validator of its own yet. A zero height is the legacy "unset" and ``None``
    too; :func:`height_is_unset` tells the two apart for the report.
    """
    triple = dimensions_triple(value)
    if triple is None:
        return None
    height = round_length(triple[2])
    return height if MIN_DIMENSION_M <= height <= MAX_DIMENSION_M else None


def height_is_unset(value: object) -> bool:
    """Whether the third component is exactly ``0`` — no height recorded, nothing to refuse."""
    triple = dimensions_triple(value)
    return triple is not None and triple[2] == 0


def grid_cell(value: object) -> tuple[int, int] | None:
    """``(row, col)`` as integers, or ``None`` when the stored ``position`` is not an integer pair."""
    if not isinstance(value, list | tuple) or len(value) != 2:
        return None
    cells: list[int] = []
    for part in value:
        if not _is_number(part) or float(part) != int(part):
            return None
        cells.append(int(part))
    return cells[0], cells[1]


def effective_pitch(value: object) -> tuple[float, bool]:
    """``(pitch_m, assumed)`` — the location's ``pitch_m`` when it is a usable length, else the default."""
    if _is_number(value) and float(value) >= MIN_DIMENSION_M:  # type: ignore[arg-type]
        return float(value), False  # type: ignore[arg-type]
    return DEFAULT_PITCH_M, True


def point_from_grid(cell: tuple[int, int], pitch_m: float) -> dict[str, Any] | None:
    """The bed-frame ``point`` of grid cell ``(row, col)`` at ``pitch_m``, or ``None`` when V-01 refuses it.

    ``x = col × pitch``, ``y = row × pitch`` (§9.2a), each rounded to 0.001 m with
    the same rule the TypeScript port uses, so a 3 × 3 tent at 0.30 m puts its middle
    slot at ``(0.30, 0.30)`` and GP-ACC-036's drag lands on ``(0.40, 0.30)``.
    """
    row, col = cell
    origin = (round_length(col * pitch_m), round_length(row * pitch_m))
    try:
        geometry = parse_geometry({"kind": GeometryKind.POINT, "origin": origin}, frame=GeometryFrame.BED)
    except ValidationError:
        return None
    return geometry.model_dump(mode="json")


def natural_key(text: object) -> tuple[tuple[int, int | str], ...]:
    """A sort key that orders digit runs numerically: ``BED_2`` before ``BED_10``."""
    parts = _DIGITS.split(str(text or ""))
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in parts if part != "")


def sequence_ranks(slots: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """The 1-based ``sequence`` of every slot within its location, ordered by ``(row, col, slot_id, _key)``.

    Ranked over *all* slots of a location — not only the ones still lacking a
    geometry — so a run interrupted halfway hands the remaining slots the same
    numbers a single run would have. Within one cell (the real-volume case: every
    slot at ``(0, 0)``) the ``slot_id`` decides in natural order, so ``TENT01_A2``
    precedes ``TENT01_A10``; the ``_key`` only breaks an exact tie. A slot whose
    ``position`` does not parse sorts after every valid cell.
    """
    by_location: dict[str, list[tuple[Any, ...]]] = {}
    for slot in slots:
        cell = grid_cell(slot.get("position"))
        order = (0, cell[0], cell[1]) if cell is not None else (1, 0, 0)
        sort_key = (*order, natural_key(slot.get("slot_id")), str(slot["_key"]))
        by_location.setdefault(str(slot.get("location_key") or ""), []).append(sort_key)
    ranks: dict[str, int] = {}
    for entries in by_location.values():
        for rank, entry in enumerate(sorted(entries), start=1):
            ranks[entry[-1]] = rank
    return ranks
