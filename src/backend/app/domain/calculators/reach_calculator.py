"""Reach: can a bed be tended without stepping into it? (REQ-053 GP-FR-166, WP 8.23).

A pure function, no I/O. Python is the reference; ``features/gardenPlanner/model/reach.ts`` is the port,
and both run against the ``reach`` cases of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (§19.6).

The hint ``bed.reach_too_wide`` speaks when the **width** of the bed exceeds the reach threshold of its
access. It is a hint only, never an error: nothing is refused and nothing is blocked because of it.

* **Thresholds** (confirmed, O-17, ``spec/analysis/agrobiology-thresholds-req-053.md`` §B): 1.2 m when the bed is
  tended from two opposite sides, 0.6 m when it is tended from one side (OSU/ISU Extension: 4 ft / 2 ft; MKUEM
  RLP 2019: 120 cm). The reason is arm length, so it holds for raised and flat beds alike. Both are
  parameters with these defaults so the site configuration (WP 8.24) can feed other values.
* **Access** comes from ``SiteConditions.access_sides`` only. ``both`` means the list holds an opposite pair,
  ``N`` + ``S`` or ``E`` + ``W`` (three or four sides contain one); one side or two adjacent sides (``N`` + ``E``)
  are ``one``; an empty or missing list is ``unknown`` and takes the strict one-side threshold. Access derived
  from adjacent ``path`` objects is not part of this function (it needs a bed-to-object edge rule that GP-FR-130
  does not define yet). The compass sides are not matched against the geometry: an opposite pair is read as the
  two long sides of the bed.
* **Width** is the narrowest extent of the bed in the plan: ``min(width_m, length_m)`` of a rect (rotation does not
  change it), the diameter of a circle, the minimum caliper width of a **convex** polygon (the smallest, over all
  edges, of the largest vertex distance from that edge's line). A concave polygon, a polyline, a point or a missing
  geometry has no width here (``width_unknown``, no hint): a concave bed's hull width would overstate the width
  of its arms and raise a hint that is not true.
* The width is rounded to 0.001 m (GP-FR-004) and must **exceed** the threshold: a bed exactly as wide as the
  threshold is within reach.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from app.common.enums import AccessSide
from app.domain.calculators.geometry_calculator import is_convex
from app.domain.models.geometry import (
    CircleGeometry,
    Geometry,
    Point2D,
    PolygonGeometry,
    RectGeometry,
    round_length,
)

#: Reach threshold with access from two opposite sides, metres (confirmed, O-17).
REACH_BOTH_SIDES_M: Final = 1.2
#: Reach threshold with access from one side, metres (confirmed, O-17); also taken when access is unknown.
REACH_ONE_SIDE_M: Final = 0.6

#: The hint code (GP-FR-166); the UI maps it to a sentence (``pages.gardenPlanner.bed.reach.*``).
HINT_REACH_TOO_WIDE: Final = "bed.reach_too_wide"

# Access classes.
ACCESS_BOTH: Final = "both"
ACCESS_ONE: Final = "one"
ACCESS_UNKNOWN: Final = "unknown"

# Reasons.
REASON_TOO_WIDE: Final = "too_wide"
REASON_WITHIN_REACH: Final = "within_reach"
REASON_WIDTH_UNKNOWN: Final = "width_unknown"

#: Pairs of opposite sides; holding one of them is access from both sides.
_OPPOSITE_PAIRS: Final[tuple[frozenset[str], ...]] = (
    frozenset({AccessSide.NORTH.value, AccessSide.SOUTH.value}),
    frozenset({AccessSide.EAST.value, AccessSide.WEST.value}),
)


@dataclass(frozen=True)
class ReachResult:
    """The verdict with what the UI shows next to it."""

    #: ``True`` when ``bed.reach_too_wide`` applies.
    hint: bool
    reason: str
    #: ``both`` | ``one`` | ``unknown``.
    access: str
    #: The threshold that was applied, metres.
    threshold_m: float
    #: The bed width compared, rounded to 0.001 m; ``None`` when the shape has none here.
    width_m: float | None


def access_class(access_sides: Iterable[str | AccessSide] | None) -> str:
    """``both`` for an opposite pair, ``one`` for any other non-empty list, ``unknown`` for none."""
    sides = {str(side) for side in access_sides or ()}
    if not sides:
        return ACCESS_UNKNOWN
    if any(pair <= sides for pair in _OPPOSITE_PAIRS):
        return ACCESS_BOTH
    return ACCESS_ONE


def _caliper_width(points: tuple[Point2D, ...]) -> float | None:
    """The minimum width of a convex polygon: over its edges, the largest vertex distance from the edge line."""
    count = len(points)
    best: float | None = None
    for i in range(count):
        ax, ay = points[i]
        bx, by = points[(i + 1) % count]
        length = math.hypot(bx - ax, by - ay)
        if length == 0.0:
            continue
        span = max(abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / length for px, py in points)
        if best is None or span < best:
            best = span
    return best


def bed_width_m(geometry: Geometry | None) -> float | None:
    """The narrowest extent of the bed, unrounded; ``None`` where the module docstring says so."""
    if isinstance(geometry, RectGeometry):
        return min(geometry.width_m, geometry.length_m)
    if isinstance(geometry, CircleGeometry):
        return 2.0 * geometry.radius_m
    if isinstance(geometry, PolygonGeometry) and is_convex(geometry.points):
        return _caliper_width(geometry.points)
    return None


def assess(
    geometry: Geometry | None,
    access_sides: Iterable[str | AccessSide] | None,
    *,
    both_sides_m: float = REACH_BOTH_SIDES_M,
    one_side_m: float = REACH_ONE_SIDE_M,
) -> ReachResult:
    """Whether ``bed.reach_too_wide`` applies; see the module docstring for the rules. Never raises on data."""
    access = access_class(access_sides)
    threshold = both_sides_m if access == ACCESS_BOTH else one_side_m
    raw = bed_width_m(geometry)
    if raw is None or not math.isfinite(raw):
        return ReachResult(False, REASON_WIDTH_UNKNOWN, access, threshold, None)
    width = round_length(raw)
    if width > threshold:
        return ReachResult(True, REASON_TOO_WIDE, access, threshold, width)
    return ReachResult(False, REASON_WITHIN_REACH, access, threshold, width)
