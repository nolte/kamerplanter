"""Edge-to-edge distance between two plan geometries (REQ-053 GP-FR-167, WP 9.12).

A pure function, no I/O, no external geometry library (D-04). Python is the reference;
``features/gardenPlanner/model/geometryDistance.ts`` is the port, and both run against the ``edge_distance`` and
``nearest_water_source`` cases of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (§19.6).

**The measure** is the shortest distance between the *outlines* of two shapes, not between their centres: two beds
side by side are as far apart as the gap between their facing edges. Shapes that touch, overlap or contain one
another are 0 apart. It is symmetric and general - GP-FR-167 (nearest water source) uses it here, GP-FR-130
(path access, #2703) consumes the same primitive.

Every geometry is resolved in the frame its coordinates are expressed in (rotation about the anchor applied, as
:func:`geometry_calculator.to_shape` does) and split into a **core** and an **inflation**:

* rect, polygon - the closed vertex ring, inflation 0;
* point - the point itself, inflation 0;
* circle - its centre, inflation = the radius (exact, never polygonised);
* polyline - the open centre line, inflation = half the stroke ``width_m`` (a band with round ends).

The distance is then ``max(0, core_distance - inflation_a - inflation_b)`` - the distance between two sets each
grown by a disc is the distance between the sets minus both radii. The core distance is 0 when a segment of one
meets a segment of the other or when a closed core contains a vertex of the other (containment without an edge
crossing); otherwise it is the smallest point-to-segment distance between the two vertex chains.

The result is exact - no tolerance - and rounded to the storage precision of 0.001 m (GP-FR-004) by the public
functions. Nothing agronomic is derived from it: it is a length the grower reads.

**What counts as a water source** (GP-FR-167) is decided here too, once: a garden object of class ``water_source``
that is not ``off_site`` scenery (the neighbour's tap behind the fence is not the garden's water). The service narrows
its query with :data:`WATER_SOURCE_OBJECT_TYPE` / :data:`WATER_SOURCES_ON_SITE_ONLY` and applies
:func:`is_water_source` to what comes back; the TS port mirrors the predicate (vector operation ``is_water_source``).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from app.common.enums import GardenObjectType
from app.domain.calculators.geometry_calculator import (
    CircleShape,
    point_in_polygon,
    segments_intersect,
    to_shape,
)
from app.domain.models.garden_object import GardenObject
from app.domain.models.geometry import Geometry, Point2D, PolylineGeometry, round_length

#: The class of garden object GP-FR-167 measures to.
WATER_SOURCE_OBJECT_TYPE: Final = GardenObjectType.WATER_SOURCE
#: ``off_site`` scenery is not the garden's water.
WATER_SOURCES_ON_SITE_ONLY: Final = True

#: Below this squared length a segment is a point (numerical noise floor, well under the storage precision).
_DEGENERATE_SQ = 1e-18


@dataclass(frozen=True)
class _Core:
    """A geometry as a vertex chain plus the distance it is grown by on every side."""

    vertices: tuple[Point2D, ...]
    #: ``True`` when the chain encloses an area (rect, polygon): the closing edge is implicit.
    closed: bool
    inflation_m: float


def _core(geometry: Geometry) -> _Core:
    shape = to_shape(geometry)
    if isinstance(shape, CircleShape):
        return _Core((shape.center,), closed=False, inflation_m=shape.radius_m)
    inflation = geometry.width_m / 2.0 if isinstance(geometry, PolylineGeometry) else 0.0
    return _Core(shape.vertices, closed=shape.closed, inflation_m=inflation)


def _segments(core: _Core) -> list[tuple[Point2D, Point2D]]:
    """The edges of the chain; a single vertex is one zero-length segment, so a point takes part like an edge."""
    vertices = core.vertices
    count = len(vertices)
    if count == 1:
        return [(vertices[0], vertices[0])]
    last = count if core.closed else count - 1
    return [(vertices[i], vertices[(i + 1) % count]) for i in range(last)]


def _point_segment_distance(point: Point2D, a: Point2D, b: Point2D) -> float:
    abx, aby = b[0] - a[0], b[1] - a[1]
    length_sq = abx * abx + aby * aby
    if length_sq <= _DEGENERATE_SQ:
        return math.hypot(point[0] - a[0], point[1] - a[1])
    t = ((point[0] - a[0]) * abx + (point[1] - a[1]) * aby) / length_sq
    t = max(0.0, min(1.0, t))
    return math.hypot(point[0] - (a[0] + t * abx), point[1] - (a[1] + t * aby))


def _segment_distance(a: Point2D, b: Point2D, c: Point2D, d: Point2D) -> float:
    """Distance between the segments ``a-b`` and ``c-d``: 0 when they meet, else the nearest end to the other."""
    if segments_intersect(a, b, c, d):
        return 0.0
    return min(
        _point_segment_distance(a, c, d),
        _point_segment_distance(b, c, d),
        _point_segment_distance(c, a, b),
        _point_segment_distance(d, a, b),
    )


def _contains_vertex(outer: _Core, inner: _Core) -> bool:
    """Whether the closed chain ``outer`` encloses the first vertex of ``inner`` (no edge crossing assumed)."""
    return outer.closed and len(outer.vertices) >= 3 and point_in_polygon(inner.vertices[0], outer.vertices)


def _core_distance(a: _Core, b: _Core) -> float:
    if _contains_vertex(a, b) or _contains_vertex(b, a):
        return 0.0
    best = math.inf
    for p, q in _segments(a):
        for r, s in _segments(b):
            distance = _segment_distance(p, q, r, s)
            if distance == 0.0:
                return 0.0
            best = min(best, distance)
    return best


def raw_edge_distance_m(a: Geometry, b: Geometry) -> float:
    """:func:`edge_distance_m` unrounded - for a caller that compares or sums before it stores."""
    core_a, core_b = _core(a), _core(b)
    return max(0.0, _core_distance(core_a, core_b) - core_a.inflation_m - core_b.inflation_m)


def edge_distance_m(a: Geometry, b: Geometry) -> float:
    """The shortest outline-to-outline distance of ``a`` and ``b`` in metres, 0 when they touch, overlap or nest.

    Both geometries are in the same frame (the plan frame for locations and garden objects). Rounded to 0.001 m.
    """
    return round_length(raw_edge_distance_m(a, b))


def is_water_source(object_type: GardenObjectType | str, off_site: bool) -> bool:
    """Whether a garden object is one GP-FR-167 measures to: class ``water_source`` and not ``off_site``."""
    return str(object_type) == WATER_SOURCE_OBJECT_TYPE.value and not (WATER_SOURCES_ON_SITE_ONLY and off_site)


def water_source_geometries(objects: Iterable[GardenObject]) -> list[Geometry]:
    """The geometries of those ``objects`` that are water sources (:func:`is_water_source`)."""
    return [item.geometry for item in objects if is_water_source(item.object_type, item.off_site)]


def nearest_water_source_m(bed: Geometry | None, sources: Iterable[Geometry]) -> float | None:
    """The distance from the bed's edge to the nearest of ``sources`` in metres (GP-FR-167), rounded to 0.001 m.

    ``None`` without a bed geometry or without a single source - "no water source" is not "0 m away". Which garden
    objects count as sources is the caller's decision (the service passes the site's ``water_source`` objects).
    """
    if bed is None:
        return None
    best: float | None = None
    for source in sources:
        distance = raw_edge_distance_m(bed, source)
        if best is None or distance < best:
            best = distance
    return None if best is None else round_length(best)
