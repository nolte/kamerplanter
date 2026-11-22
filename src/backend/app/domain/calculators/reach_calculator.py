"""Reach: can a bed be tended without stepping into it? (REQ-053 GP-FR-166, WP 8.23).

A pure function, no I/O. Python is the reference; ``features/gardenPlanner/model/reach.ts`` is the port,
and both run against the ``reach`` cases of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (§19.6).

The hint ``bed.reach_too_wide`` speaks when the **width** of the bed exceeds the reach threshold of its
access. It is a hint only, never an error: nothing is refused and nothing is blocked because of it.

* **Thresholds** (confirmed, O-17, ``spec/analysis/agrobiology-thresholds-req-053.md`` §B): 1.2 m when the bed is
  tended from two opposite sides, 0.6 m when it is tended from one side (OSU/ISU Extension: 4 ft / 2 ft; MKUEM
  RLP 2019: 120 cm). The reason is arm length, so it holds for raised and flat beds alike. Both are
  parameters with these defaults so the site configuration (WP 8.24) can feed other values.
* **Manual access** comes from ``SiteConditions.access_sides``. ``both`` means the list holds an opposite pair,
  ``N`` + ``S`` or ``E`` + ``W`` (three or four sides contain one); one side or two adjacent sides (``N`` + ``E``)
  are ``one``; an empty or missing list is ``unknown`` and takes the strict one-side threshold. The compass sides
  are not matched against the geometry: an opposite pair is read as the two long sides of the bed.
* **Access from paths** (#2703, operator decision 2026-11-09) is the second source, :func:`path_access`. A garden
  object of class ``path`` makes a **bed edge** reachable when it comes within ``max_distance_m`` (default
  :data:`PATH_ACCESS_MAX_DISTANCE_M`, 0.3 m, configurable per site) of that edge, edge to edge
  (:func:`geometry_distance.raw_distance_to_ring_m`, the primitive of GP-FR-167). Concretely the path must meet the
  **strip** beside the edge: the rectangle outward of the edge, ``max_distance_m`` deep, shortened at both ends by
  :data:`PATH_CORNER_INSET_M`. The inset is what tells sides apart: a path that runs past a short end of the bed
  comes within 0 m of the corner of each long side and would otherwise count for both of them; it meets neither
  long-side strip and counts only for the short end. The distance to the strip is rounded to 0.001 m like every
  length (GP-FR-004), so a path exactly ``max_distance_m`` away still reaches.
  Paths give ``both`` when two reached edges are **opposite across the width**: antiparallel, and the bed measured
  from each of them is exactly its width (the long sides of a rect; parallel sides of a convex polygon that span
  its minimum caliper width). Paths at both short ends of a long bed are two sides, but not across the width,
  so they are ``one``. Any reached edge is ``one``; no reached edge is ``none``. Edges exist for a rect and a
  convex polygon; a circle has none, so a path near it is ``one`` (never ``both``); a concave polygon, a polyline
  or a point has no width here and needs no access. A path drawn **across** a bed reaches both strips and counts
  as ``both`` - the plan cannot tell a crossing path from two paths.
* **Combining** both sources: the stronger class wins (``both`` > ``one`` > ``unknown``/``none``). A manual side
  and a path on the opposite side are not joined to ``both``: the compass sides are not matched against the
  geometry, so the grower enters the opposite pair by hand if that is the access.
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
from app.domain.calculators.geometry_calculator import VertexShape, is_convex, to_shape
from app.domain.calculators.geometry_distance import raw_distance_to_ring_m, raw_edge_distance_m
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

#: A path gives access to a bed edge within this edge-to-edge distance, metres (operator decision 2026-11-09,
#: #2703); the default of the per-site value ``ReachThresholds.path_access_max_distance_m``.
PATH_ACCESS_MAX_DISTANCE_M: Final = 0.3
#: The strip beside a bed edge is shortened by this much at both ends, metres: a path must run alongside the edge,
#: meeting the bed at a corner is no side. Well above the rounding of 0.0005 m, well below any bed edge.
PATH_CORNER_INSET_M: Final = 0.01

# Access classes.
ACCESS_BOTH: Final = "both"
ACCESS_ONE: Final = "one"
ACCESS_UNKNOWN: Final = "unknown"
#: :func:`path_access` found no path beside the bed.
ACCESS_NONE: Final = "none"

#: The order the two access sources are combined in: the stronger class wins.
_ACCESS_RANK: Final[dict[str, int]] = {ACCESS_UNKNOWN: 0, ACCESS_NONE: 0, ACCESS_ONE: 1, ACCESS_BOTH: 2}
#: Two unit edge directions are antiparallel when their cross product is below this (numerical noise only).
_PARALLEL_EPS: Final = 1e-9

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


@dataclass(frozen=True)
class PathAccess:
    """Which edges of a bed paths reach, and the access class that gives (:func:`path_access`)."""

    #: ``both`` | ``one`` | ``none``.
    access: str
    #: Indices of the reached bed edges, ascending: edge ``i`` runs from vertex ``i`` to ``i + 1`` of the resolved
    #: shape (a rect's vertices before rotation: ``(0, 0)``, ``(w, 0)``, ``(w, l)``, ``(0, l)``). Empty for a shape
    #: without edges here.
    edges: tuple[int, ...]


def _bed_ring(geometry: Geometry) -> tuple[Point2D, ...] | None:
    """The resolved vertex ring of a rect or a convex polygon (the shapes with edges here), else ``None``."""
    if isinstance(geometry, RectGeometry) or (isinstance(geometry, PolygonGeometry) and is_convex(geometry.points)):
        shape = to_shape(geometry)
        if isinstance(shape, VertexShape) and len(shape.vertices) >= 3:
            return shape.vertices
    return None


def _is_counter_clockwise(ring: tuple[Point2D, ...]) -> bool:
    total = 0.0
    for i, (x1, y1) in enumerate(ring):
        x2, y2 = ring[(i + 1) % len(ring)]
        total += x1 * y2 - x2 * y1
    return total > 0.0


def _edge_strip(a: Point2D, b: Point2D, outward: Point2D, depth_m: float) -> tuple[Point2D, ...] | None:
    """The strip outward of the edge ``a-b``, ``depth_m`` deep and inset at both ends; ``None`` for a short edge."""
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    if length <= 2.0 * PATH_CORNER_INSET_M:
        return None
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    start = (a[0] + ux * PATH_CORNER_INSET_M, a[1] + uy * PATH_CORNER_INSET_M)
    end = (b[0] - ux * PATH_CORNER_INSET_M, b[1] - uy * PATH_CORNER_INSET_M)
    if depth_m <= 0.0:
        return (start, end)
    nx, ny = outward[0] * depth_m, outward[1] * depth_m
    return (start, end, (end[0] + nx, end[1] + ny), (start[0] + nx, start[1] + ny))


def _span_from_edge(ring: tuple[Point2D, ...], index: int) -> float:
    """The largest distance of a vertex from the line of edge ``index`` (the bed measured from that edge)."""
    (ax, ay), (bx, by) = ring[index], ring[(index + 1) % len(ring)]
    length = math.hypot(bx - ax, by - ay)
    return max(abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / length for px, py in ring)


def _across_the_width(ring: tuple[Point2D, ...], i: int, j: int, width: float) -> bool:
    """Whether edges ``i`` and ``j`` are antiparallel and the bed measured from each is exactly its width."""
    (ax, ay), (bx, by) = ring[i], ring[(i + 1) % len(ring)]
    (cx, cy), (dx, dy) = ring[j], ring[(j + 1) % len(ring)]
    len_i, len_j = math.hypot(bx - ax, by - ay), math.hypot(dx - cx, dy - cy)
    ux, uy, vx, vy = (bx - ax) / len_i, (by - ay) / len_i, (dx - cx) / len_j, (dy - cy) / len_j
    if abs(ux * vy - uy * vx) > _PARALLEL_EPS or ux * vx + uy * vy >= 0.0:
        return False
    return round_length(_span_from_edge(ring, i)) == width and round_length(_span_from_edge(ring, j)) == width


def _within(distance_m: float, limit_m: float) -> bool:
    """A distance rounded to the storage precision (GP-FR-004) is at most ``limit_m``."""
    return round_length(distance_m) <= limit_m


def path_access(
    bed: Geometry | None,
    paths: Iterable[Geometry],
    *,
    max_distance_m: float = PATH_ACCESS_MAX_DISTANCE_M,
) -> PathAccess:
    """Which bed edges the ``paths`` reach and the access class that gives; see the module docstring. Pure.

    ``paths`` are the geometries of the site's ``path`` objects in the frame of ``bed`` (the plan frame); which
    objects count is the caller's decision. Never raises on data.
    """
    if bed is None:
        return PathAccess(ACCESS_NONE, ())
    path_list = list(paths)
    if not path_list:
        return PathAccess(ACCESS_NONE, ())
    ring = _bed_ring(bed)
    if ring is None:
        near = any(_within(raw_edge_distance_m(bed, path), max_distance_m) for path in path_list)
        return PathAccess(ACCESS_ONE if near else ACCESS_NONE, ())
    ccw = _is_counter_clockwise(ring)
    reached: list[int] = []
    for i, a in enumerate(ring):
        b = ring[(i + 1) % len(ring)]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        if length == 0.0:
            continue
        # The outward normal: right of the edge for a counter-clockwise ring, left for a clockwise one.
        dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        outward = (dy, -dx) if ccw else (-dy, dx)
        strip = _edge_strip(a, b, outward, max_distance_m)
        if strip is not None and any(_within(raw_distance_to_ring_m(path, strip), 0.0) for path in path_list):
            reached.append(i)
    if not reached:
        return PathAccess(ACCESS_NONE, ())
    raw_width = bed_width_m(bed)
    width = round_length(raw_width) if raw_width is not None and math.isfinite(raw_width) else None
    both = width is not None and any(
        _across_the_width(ring, i, j, width) for k, i in enumerate(reached) for j in reached[k + 1 :]
    )
    return PathAccess(ACCESS_BOTH if both else ACCESS_ONE, tuple(reached))


def combined_access(manual: str, from_paths: str | None) -> str:
    """The stronger of the manual access class and the one derived from paths (``both`` > ``one`` > unknown)."""
    if from_paths is not None and _ACCESS_RANK.get(from_paths, 0) > _ACCESS_RANK[manual]:
        return from_paths
    return manual


def assess(
    geometry: Geometry | None,
    access_sides: Iterable[str | AccessSide] | None,
    *,
    both_sides_m: float = REACH_BOTH_SIDES_M,
    one_side_m: float = REACH_ONE_SIDE_M,
    path_access_class: str | None = None,
) -> ReachResult:
    """Whether ``bed.reach_too_wide`` applies; see the module docstring for the rules. Never raises on data.

    ``path_access_class`` is the class :func:`path_access` derived for the bed (``both`` | ``one`` | ``none``), ``None``
    when it is not known; it joins ``access_sides`` by :func:`combined_access`.
    """
    access = combined_access(access_class(access_sides), path_access_class)
    threshold = both_sides_m if access == ACCESS_BOTH else one_side_m
    raw = bed_width_m(geometry)
    if raw is None or not math.isfinite(raw):
        return ReachResult(False, REASON_WIDTH_UNKNOWN, access, threshold, None)
    width = round_length(raw)
    if width > threshold:
        return ReachResult(True, REASON_TOO_WIDE, access, threshold, width)
    return ReachResult(False, REASON_WITHIN_REACH, access, threshold, width)
