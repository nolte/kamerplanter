"""Where an object's name sits on the plan, and how wide it may run (REQ-053 GP-UX-047, GP-FR-003; WP 7.24, #2490).

GP-UX-047 puts a name in the middle of its object - for a polygon at the **pole of inaccessibility**, the inner
point farthest from every edge - instead of at the area centroid, which for an L-shaped bed can lie in the notch,
outside the bed. The label is horizontal on the page and on the screen and centred on that point, so the room it
has is twice the shorter reach along the **horizontal chord** through it - the stretch of the line ``y = anchor_y``
that lies inside the shape around the anchor. That width, not the bounding-box width, is what a name is shortened
to.

* ``rect`` and ``circle``: the centre (the pole of a rectangle is a segment along its long axis; the centre is
  the point on it the editor and the PDF both use). The room of a circle through its centre is its diameter.
* ``polygon``: the pole, found by the quadtree search of Agafonkin's *polylabel* to within
  :data:`POLE_PRECISION_M`, seeded with the area centroid. The search runs in the polygon's local frame (first vertex
  at the origin, no rotation, the frame the vertices are stored in up to a subtraction) and is transformed
  afterwards, so the Python reference and the TypeScript port start from the same floats. Cells are taken in a
  total order (most promising first, then by x, then by y), so the result is the same whatever the queue.
* ``polyline``: the point at half its length - on the stroke, where the vertex mean of a bent path is not. Its
  room is the bounding-box width, stroke included.
* ``point``: the point itself, room 0.

Point and room are rounded to the storage precision (0.001 m, GP-FR-004). Pure functions, no I/O. Python is the
reference; ``features/gardenPlanner/model/labelAnchor.ts`` is the port, and both run against the ``label_anchor``
cases of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` so that the PDF and the editor agree (GP-FR-003).
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from app.domain.calculators.geometry_calculator import (
    CircleShape,
    bounding_box,
    to_local_shape,
    to_shape,
    transform_bed_to_plan,
)
from app.domain.models.geometry import (
    CircleGeometry,
    Geometry,
    Point2D,
    PointGeometry,
    PolygonGeometry,
    PolylineGeometry,
    RectGeometry,
    round_length,
)

#: The pole search stops once no cell can beat the best point by more than this (1 cm, well below a glyph).
POLE_PRECISION_M = 0.01
#: Below this a polygon has no area to search: its first vertex stands in for the pole.
_DEGENERATE_M = 1e-9


@dataclass(frozen=True)
class LabelAnchor:
    """The centre of an object's label and the horizontal room around it, in metres of the plan frame."""

    point: Point2D
    width_m: float


# ── Pole of inaccessibility ──────────────────────────────────────────────────


def _segment_distance_sq(px: float, py: float, a: Point2D, b: Point2D) -> float:
    """Squared distance from ``(px, py)`` to the segment ``a-b``."""
    x, y = a
    dx, dy = b[0] - x, b[1] - y
    if dx != 0 or dy != 0:
        t = ((px - x) * dx + (py - y) * dy) / (dx * dx + dy * dy)
        if t > 1:
            x, y = b
        elif t > 0:
            x += dx * t
            y += dy * t
    dx, dy = px - x, py - y
    return dx * dx + dy * dy


def _signed_distance(px: float, py: float, vertices: tuple[Point2D, ...]) -> float:
    """Distance from ``(px, py)`` to the polygon's boundary: positive inside, negative outside (even-odd rule)."""
    inside = False
    best_sq = math.inf
    count = len(vertices)
    j = count - 1
    for i in range(count):
        a, b = vertices[i], vertices[j]
        if (a[1] > py) != (b[1] > py) and px < (b[0] - a[0]) * (py - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
        best_sq = min(best_sq, _segment_distance_sq(px, py, a, b))
        j = i
    distance = math.sqrt(best_sq)
    return distance if inside else -distance


@dataclass(frozen=True)
class _Cell:
    x: float
    y: float
    half: float
    distance: float
    potential: float


def _cell(x: float, y: float, half: float, vertices: tuple[Point2D, ...]) -> _Cell:
    distance = _signed_distance(x, y, vertices)
    return _Cell(x, y, half, distance, distance + half * math.sqrt(2.0))


def _area_centroid(vertices: tuple[Point2D, ...]) -> Point2D:
    """The area centroid; the first vertex when the area vanishes."""
    doubled = cx = cy = 0.0
    count = len(vertices)
    j = count - 1
    for i in range(count):
        ax, ay = vertices[i]
        bx, by = vertices[j]
        cross = ax * by - bx * ay
        cx += (ax + bx) * cross
        cy += (ay + by) * cross
        doubled += cross
        j = i
    if doubled == 0:
        return vertices[0]
    return (cx / (3.0 * doubled), cy / (3.0 * doubled))


def pole_of_inaccessibility(vertices: tuple[Point2D, ...], precision_m: float = POLE_PRECISION_M) -> Point2D:
    """The inner point of the simple polygon *vertices* farthest from its boundary, to within *precision_m*.

    Unrounded, in the frame of *vertices*. Cells leave the queue in a total order - highest potential first, then
    lowest x, then lowest y, then the order of insertion - so equal candidates resolve the same way in every port.
    """
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    min_x, min_y, max_x, max_y = min(xs), min(ys), max(xs), max(ys)
    width, height = max_x - min_x, max_y - min_y
    cell_size = min(width, height)
    if cell_size <= _DEGENERATE_M:
        return vertices[0]
    half = cell_size / 2.0
    queue: list[tuple[float, float, float, int, _Cell]] = []
    pushed = 0

    def push(cell: _Cell) -> None:
        nonlocal pushed
        heapq.heappush(queue, (-cell.potential, cell.x, cell.y, pushed, cell))
        pushed += 1

    x = min_x
    while x < max_x:
        y = min_y
        while y < max_y:
            push(_cell(x + half, y + half, half, vertices))
            y += cell_size
        x += cell_size

    centre = _area_centroid(vertices)
    best = _cell(centre[0], centre[1], 0.0, vertices)
    box_centre = _cell(min_x + width / 2.0, min_y + height / 2.0, 0.0, vertices)
    if box_centre.distance > best.distance:
        best = box_centre

    while queue:
        cell = heapq.heappop(queue)[4]
        if cell.distance > best.distance:
            best = cell
        if cell.potential - best.distance <= precision_m:
            continue
        half = cell.half / 2.0
        push(_cell(cell.x - half, cell.y - half, half, vertices))
        push(_cell(cell.x + half, cell.y - half, half, vertices))
        push(_cell(cell.x - half, cell.y + half, half, vertices))
        push(_cell(cell.x + half, cell.y + half, half, vertices))
    return (best.x, best.y)


# ── Horizontal room ──────────────────────────────────────────────────────────


def centred_room(vertices: tuple[Point2D, ...], point: Point2D) -> float | None:
    """Width of the widest horizontal text centred on *point* that stays inside the polygon *vertices*.

    The stretch of ``y = point_y`` inside the polygon that contains *point*, taken symmetrically: twice the shorter
    distance from *point* to its ends. Edges are half-open in y (an edge counts when exactly one end lies above the
    line), so a vertex on the line is met once. ``None`` when *point* lies in no inside stretch (it is outside, or the
    line only grazes the shape).
    """
    px, py = point
    crossings: list[float] = []
    count = len(vertices)
    j = count - 1
    for i in range(count):
        a, b = vertices[i], vertices[j]
        if (a[1] > py) != (b[1] > py):
            crossings.append(a[0] + (py - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
        j = i
    crossings.sort()
    for k in range(0, len(crossings) - 1, 2):
        left, right = crossings[k], crossings[k + 1]
        if left <= px <= right:
            return 2.0 * min(px - left, right - px)
    return None


# ── Label anchor ─────────────────────────────────────────────────────────────


def _length(a: Point2D, b: Point2D) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)


def _polyline_midpoint(vertices: tuple[Point2D, ...]) -> Point2D:
    """The point at half the length of the open path *vertices*; its first vertex when it has no length."""
    lengths = [_length(a, b) for a, b in zip(vertices, vertices[1:], strict=False)]
    remaining = sum(lengths) / 2.0
    for (a, b), length in zip(zip(vertices, vertices[1:], strict=False), lengths, strict=True):
        if length > 0 and remaining <= length:
            t = remaining / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        remaining -= length
    return vertices[0]


def label_anchor(geometry: Geometry) -> LabelAnchor:
    """The label centre of *geometry* (plan frame) and the horizontal room for its text (GP-UX-047)."""
    if isinstance(geometry, PointGeometry):
        x, y = geometry.origin
        return LabelAnchor((round_length(x), round_length(y)), 0.0)
    if isinstance(geometry, CircleGeometry):
        x, y = geometry.origin
        return LabelAnchor((round_length(x), round_length(y)), round_length(2.0 * geometry.radius_m))
    shape = to_shape(geometry)
    assert not isinstance(shape, CircleShape)  # noqa: S101 - circles are handled above
    if isinstance(geometry, PolylineGeometry):
        min_x, _, max_x, _ = bounding_box(geometry)
        x, y = _polyline_midpoint(shape.vertices)
        return LabelAnchor((round_length(x), round_length(y)), round_length(max_x - min_x))
    if isinstance(geometry, RectGeometry):
        local_point: Point2D = (geometry.width_m / 2.0, geometry.length_m / 2.0)
    else:
        assert isinstance(geometry, PolygonGeometry)  # noqa: S101 - the remaining kind
        local = to_local_shape(geometry)
        assert not isinstance(local, CircleShape)  # noqa: S101 - a polygon resolves into vertices
        local_point = pole_of_inaccessibility(local.vertices)
    point = transform_bed_to_plan(local_point, geometry)
    room = centred_room(shape.vertices, point)
    if room is None:
        min_x, _, max_x, _ = bounding_box(geometry)
        room = max_x - min_x
    return LabelAnchor((round_length(point[0]), round_length(point[1])), round_length(room))
