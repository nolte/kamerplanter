"""Pure geometry calculations for the garden plan (REQ-053 GP-FR-006/007, GP-NFR-012).

No I/O, no external geometry library (decision D-04). Every function here is
the Python reference of the shared Backend ↔ Frontend logic (§19.6): the
TypeScript port in ``features/gardenPlanner/model/geometry.ts`` runs against
the same vectors in ``spec/e2e-testcases/fixtures/garden-plan-vectors.json``.

Conventions (REQ-053 §9.2, §20.1):

* Lengths in metres, angles in degrees counter-clockwise about ``+x``.
* A geometry's **anchor** is ``rect.origin`` (lower-left corner before
  rotation), ``circle.origin``/``point.origin`` (the centre) and the first
  vertex of a ``polygon``/``polyline``. Rotation pivots about the anchor.
* A geometry's **local frame** has the anchor at ``(0, 0)`` and no rotation.
  That is the *bed frame* of a location: slot geometries are expressed in it
  (§9.2), and ``p_plan = anchor + R(rotation_deg) · p_bed``.
* A :class:`Shape` is a geometry resolved into plain coordinates — either a
  vertex list (``closed`` when it encloses an area) or an exact circle.
  Circles are never polygonised; the containment and overlap rules use the
  distance formulas instead, so a ``circle`` is exact in both directions.
* Tolerance (V-03): a child may stick out by at most ``tolerance_m`` (default
  1 cm); two objects *overlap* only when they penetrate by more than it, so
  beds that share an edge do not overlap (V-05).
* Derived values that are stored (``area_m2``, ``bbox``, ``centroid``) are
  rounded to the storage precision of 0.001 m (GP-FR-004); the predicates
  (``contains``, ``overlaps``, ``is_simple_polygon``) work on unrounded floats.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.models.geometry import (
    LENGTH_DECIMALS,
    CircleGeometry,
    Geometry,
    Point2D,
    PointGeometry,
    PolygonGeometry,
    PolylineGeometry,
    RectGeometry,
)

#: ``[min_x, min_y, max_x, max_y]`` in the frame of the geometry (GP-FR-007).
BoundingBox = tuple[float, float, float, float]

#: V-03: a child may protrude from its parent by at most 1 cm.
DEFAULT_TOLERANCE_M = 0.01
#: Numerical noise floor for orientation tests, well below the storage precision.
_EPSILON = 1e-9

#: V-02 error code (REQ-053 §22.2).
ERROR_SELF_INTERSECTING = "geometry.self_intersecting"


# ── Resolved shapes ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class VertexShape:
    """A geometry resolved into vertices.

    ``closed`` is true for area shapes (rect, polygon): the edge from the last
    vertex back to the first is implicit. A polyline (``closed=False``) has no
    area and therefore no overlap notion; a point is a one-vertex open shape.
    """

    vertices: tuple[Point2D, ...]
    closed: bool


@dataclass(frozen=True)
class CircleShape:
    """A circle resolved into centre and radius; exact, never polygonised."""

    center: Point2D
    radius_m: float


Shape = VertexShape | CircleShape


# ── Vector helpers ───────────────────────────────────────────────────────────


def rotate_point(point: Point2D, angle_deg: float, pivot: Point2D = (0.0, 0.0)) -> Point2D:
    """Rotate *point* counter-clockwise by *angle_deg* about *pivot*."""
    radians = math.radians(angle_deg)
    cos_a, sin_a = math.cos(radians), math.sin(radians)
    dx, dy = point[0] - pivot[0], point[1] - pivot[1]
    return (pivot[0] + dx * cos_a - dy * sin_a, pivot[1] + dx * sin_a + dy * cos_a)


def _distance(a: Point2D, b: Point2D) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _round_point(point: Point2D) -> Point2D:
    return (round(point[0], LENGTH_DECIMALS), round(point[1], LENGTH_DECIMALS))


def _cross(o: Point2D, a: Point2D, b: Point2D) -> float:
    """Z component of ``(a - o) × (b - o)``: > 0 when ``o→a→b`` turns left."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _point_segment_distance(point: Point2D, a: Point2D, b: Point2D) -> float:
    """Euclidean distance from *point* to the segment ``a–b``."""
    abx, aby = b[0] - a[0], b[1] - a[1]
    length_sq = abx * abx + aby * aby
    if length_sq <= _EPSILON:
        return _distance(point, a)
    t = ((point[0] - a[0]) * abx + (point[1] - a[1]) * aby) / length_sq
    t = max(0.0, min(1.0, t))
    return _distance(point, (a[0] + t * abx, a[1] + t * aby))


def _signed_side(point: Point2D, a: Point2D, b: Point2D) -> float:
    """Signed perpendicular distance of *point* from the line through ``a–b`` (left positive)."""
    length = _distance(a, b)
    if length <= _EPSILON:
        return 0.0
    return _cross(a, b, point) / length


def _edges(vertices: tuple[Point2D, ...], *, closed: bool) -> list[tuple[Point2D, Point2D]]:
    count = len(vertices)
    if count < 2:
        return []
    last = count if closed else count - 1
    return [(vertices[i], vertices[(i + 1) % count]) for i in range(last)]


# ── Anchor, frames and transformation (§9.2) ────────────────────────────────


def anchor(geometry: Geometry) -> Point2D:
    """The pivot of the geometry: origin for rect/circle/point, first vertex otherwise."""
    if isinstance(geometry, RectGeometry | CircleGeometry | PointGeometry):
        return geometry.origin
    return geometry.points[0]


def rotation_deg(geometry: Geometry) -> float:
    """Rotation of the geometry; shapes without a rotation field rotate by 0."""
    if isinstance(geometry, RectGeometry | PolygonGeometry):
        return geometry.rotation_deg
    return 0.0


def transform_bed_to_plan(point: Point2D, bed: Geometry) -> Point2D:
    """Map a point from the bed frame of *bed* into the frame *bed* is expressed in.

    ``p_plan = anchor + R(rotation_deg) · p_bed`` (REQ-053 §9.2).
    """
    ax, ay = anchor(bed)
    rx, ry = rotate_point(point, rotation_deg(bed))
    return (ax + rx, ay + ry)


def transform_plan_to_bed(point: Point2D, bed: Geometry) -> Point2D:
    """Inverse of :func:`transform_bed_to_plan`."""
    ax, ay = anchor(bed)
    return rotate_point((point[0] - ax, point[1] - ay), -rotation_deg(bed))


def to_local_shape(geometry: Geometry) -> Shape:
    """Resolve *geometry* in its own local frame: anchor at ``(0, 0)``, no rotation.

    This is the bed frame of a location (§9.2) — the frame its slots live in.
    """
    if isinstance(geometry, RectGeometry):
        w, length = geometry.width_m, geometry.length_m
        return VertexShape(((0.0, 0.0), (w, 0.0), (w, length), (0.0, length)), closed=True)
    if isinstance(geometry, CircleGeometry):
        return CircleShape((0.0, 0.0), geometry.radius_m)
    if isinstance(geometry, PointGeometry):
        return VertexShape(((0.0, 0.0),), closed=False)
    ax, ay = geometry.points[0]
    vertices = tuple((x - ax, y - ay) for x, y in geometry.points)
    return VertexShape(vertices, closed=isinstance(geometry, PolygonGeometry))


def to_shape(geometry: Geometry) -> Shape:
    """Resolve *geometry* in the frame its coordinates are expressed in (rotation applied)."""
    local = to_local_shape(geometry)
    if isinstance(local, CircleShape):
        return CircleShape(anchor(geometry), local.radius_m)
    return VertexShape(tuple(transform_bed_to_plan(v, geometry) for v in local.vertices), closed=local.closed)


# ── Derived values (GP-FR-006/007) ───────────────────────────────────────────


def shoelace_area(points: list[Point2D] | tuple[Point2D, ...]) -> float:
    """Unsigned area of the closed polygon *points* (shoelace formula), 0 for < 3 points."""
    count = len(points)
    if count < 3:
        return 0.0
    total = 0.0
    for i in range(count):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % count]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def area_m2(geometry: Geometry) -> float:
    """Area in m², rounded to 0.001; polylines and points have none (GP-FR-006)."""
    if isinstance(geometry, RectGeometry):
        raw = geometry.width_m * geometry.length_m
    elif isinstance(geometry, CircleGeometry):
        raw = math.pi * geometry.radius_m**2
    elif isinstance(geometry, PolygonGeometry):
        raw = shoelace_area(geometry.points)
    else:
        raw = 0.0
    return round(raw, LENGTH_DECIMALS)


def _shape_bbox(shape: Shape) -> BoundingBox:
    if isinstance(shape, CircleShape):
        cx, cy = shape.center
        r = shape.radius_m
        return (cx - r, cy - r, cx + r, cy + r)
    xs = [v[0] for v in shape.vertices]
    ys = [v[1] for v in shape.vertices]
    return (min(xs), min(ys), max(xs), max(ys))


def bounding_box(geometry: Geometry) -> BoundingBox:
    """Axis-aligned bounding box after rotation, rounded to 0.001 m (GP-FR-007).

    A polyline's box includes its stroke (``± width_m / 2``) so that culling
    and the mini-map see what is drawn.
    """
    min_x, min_y, max_x, max_y = _shape_bbox(to_shape(geometry))
    if isinstance(geometry, PolylineGeometry):
        half = geometry.width_m / 2.0
        min_x, min_y, max_x, max_y = min_x - half, min_y - half, max_x + half, max_y + half
    return (
        round(min_x, LENGTH_DECIMALS),
        round(min_y, LENGTH_DECIMALS),
        round(max_x, LENGTH_DECIMALS),
        round(max_y, LENGTH_DECIMALS),
    )


def centroid(geometry: Geometry) -> Point2D:
    """Centroid after rotation, rounded to 0.001 m.

    Area shapes use the area centroid (a polygon's weighted centroid, the
    centre of a rect or circle); a polyline uses the mean of its vertices.
    Computed in the local frame (small numbers) and transformed afterwards,
    so a 1 cm object at the far corner of a 1 000 m plan keeps its precision.
    """
    local = to_local_shape(geometry)
    if isinstance(local, CircleShape):
        return _round_point(anchor(geometry))
    vertices = local.vertices
    count = len(vertices)
    local_centroid: Point2D | None = None
    if local.closed:
        doubled_area = 0.0
        cx = cy = 0.0
        for i in range(count):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % count]
            cross = x1 * y2 - x2 * y1
            doubled_area += cross
            cx += (x1 + x2) * cross
            cy += (y1 + y2) * cross
        if abs(doubled_area) > _EPSILON:
            local_centroid = (cx / (3.0 * doubled_area), cy / (3.0 * doubled_area))
    if local_centroid is None:
        local_centroid = (sum(v[0] for v in vertices) / count, sum(v[1] for v in vertices) / count)
    return _round_point(transform_bed_to_plan(local_centroid, geometry))


# ── Simplicity (V-02) ────────────────────────────────────────────────────────


def _on_segment(p: Point2D, a: Point2D, b: Point2D) -> bool:
    """Whether collinear *p* lies within the bounding box of segment ``a–b``."""
    return (
        min(a[0], b[0]) - _EPSILON <= p[0] <= max(a[0], b[0]) + _EPSILON
        and min(a[1], b[1]) - _EPSILON <= p[1] <= max(a[1], b[1]) + _EPSILON
    )


def _orientation(o: Point2D, a: Point2D, b: Point2D) -> int:
    cross = _cross(o, a, b)
    if abs(cross) <= _EPSILON:
        return 0
    return 1 if cross > 0 else -1


def segments_intersect(a: Point2D, b: Point2D, c: Point2D, d: Point2D) -> bool:
    """Whether segments ``a–b`` and ``c–d`` share at least one point (touching counts)."""
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    if o1 != o2 and o3 != o4 and o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        return True
    if o1 == 0 and _on_segment(c, a, b):
        return True
    if o2 == 0 and _on_segment(d, a, b):
        return True
    if o3 == 0 and _on_segment(a, c, d):
        return True
    return bool(o4 == 0 and _on_segment(b, c, d))


def is_simple_polygon(points: list[Point2D] | tuple[Point2D, ...]) -> bool:
    """V-02: the closed polygon *points* has no self-intersection and encloses an area.

    O(n²) segment test, acceptable for n ≤ 200 (REQ-053 §22.2). Non-adjacent
    edges may not meet at all (a vertex revisited counts as a self-touch);
    adjacent edges may not fold back onto each other; every edge has a length,
    and a degenerate (collinear) polygon is not simple.
    """
    count = len(points)
    if count < 3:
        return False
    edges = _edges(tuple(points), closed=True)
    for a, b in edges:
        if _distance(a, b) <= _EPSILON:
            return False
    if shoelace_area(points) <= _EPSILON:
        return False
    for i in range(count):
        a, b = edges[i]
        for j in range(i + 1, count):
            c, d = edges[j]
            adjacent = j == i + 1 or (i == 0 and j == count - 1)
            if adjacent:
                # The shared vertex is legitimate; folding back onto the previous edge is not.
                shared, prev_end, next_end = (b, a, d) if j == i + 1 else (a, b, c)
                if _orientation(prev_end, shared, next_end) == 0:
                    dot = (prev_end[0] - shared[0]) * (next_end[0] - shared[0]) + (prev_end[1] - shared[1]) * (
                        next_end[1] - shared[1]
                    )
                    if dot > 0:
                        return False
                continue
            if segments_intersect(a, b, c, d):
                return False
    return True


def validate_geometry(geometry: Geometry) -> list[str]:
    """Domain-level validation codes for *geometry* (empty = valid).

    V-01 is enforced by the Pydantic model; this reports the rules the spec
    places in the domain layer, today V-02 ``geometry.self_intersecting``.
    """
    if isinstance(geometry, PolygonGeometry) and not is_simple_polygon(geometry.points):
        return [ERROR_SELF_INTERSECTING]
    return []


def is_convex(vertices: tuple[Point2D, ...]) -> bool:
    """Whether the closed *simple* polygon *vertices* is convex (collinear runs allowed).

    Precondition: the polygon passed V-02. A self-intersecting star turns the
    same way at every vertex and would be reported convex.
    """
    count = len(vertices)
    if count < 3:
        return False
    sign = 0
    for i in range(count):
        turn = _orientation(vertices[i], vertices[(i + 1) % count], vertices[(i + 2) % count])
        if turn == 0:
            continue
        if sign == 0:
            sign = turn
        elif turn != sign:
            return False
    return sign != 0


# ── Point-in-polygon and signed distance ─────────────────────────────────────


def point_in_polygon(point: Point2D, vertices: tuple[Point2D, ...]) -> bool:
    """Even-odd ray cast; points on the boundary may land on either side (use the distance)."""
    inside = False
    px, py = point
    count = len(vertices)
    for i in range(count):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % count]
        if (y1 > py) != (y2 > py):
            x_at = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < x_at:
                inside = not inside
    return inside


def signed_distance_to_polygon(point: Point2D, vertices: tuple[Point2D, ...]) -> float:
    """Distance from *point* to the polygon boundary: positive inside, negative outside."""
    distance = min(_point_segment_distance(point, a, b) for a, b in _edges(vertices, closed=True))
    return distance if point_in_polygon(point, vertices) else -distance


def _signed_distance(point: Point2D, shape: Shape) -> float:
    """Signed distance of *point* to the boundary of an area *shape* (positive inside)."""
    if isinstance(shape, CircleShape):
        return shape.radius_m - _distance(point, shape.center)
    return signed_distance_to_polygon(point, shape.vertices)


def _proper_crossing(a: Point2D, b: Point2D, c: Point2D, d: Point2D, tolerance_m: float) -> bool:
    """Whether ``a–b`` and ``c–d`` cross with both ends clear of the other line by more than the tolerance."""
    side_c, side_d = _signed_side(c, a, b), _signed_side(d, a, b)
    side_a, side_b = _signed_side(a, c, d), _signed_side(b, c, d)
    return (
        side_c * side_d < 0
        and side_a * side_b < 0
        and min(abs(side_c), abs(side_d), abs(side_a), abs(side_b)) > tolerance_m
    )


def _any_proper_crossing(a: VertexShape, b: VertexShape, tolerance_m: float) -> bool:
    edges_b = _edges(b.vertices, closed=b.closed)
    return any(
        _proper_crossing(p, q, r, s, tolerance_m) for p, q in _edges(a.vertices, closed=a.closed) for r, s in edges_b
    )


def _intersection_parameters(a: Point2D, b: Point2D, c: Point2D, d: Point2D) -> list[float]:
    """Positions ``t ∈ [0, 1]`` along ``a–b`` where it meets ``c–d`` (touching and collinear overlap included)."""
    abx, aby = b[0] - a[0], b[1] - a[1]
    cdx, cdy = d[0] - c[0], d[1] - c[1]
    denominator = abx * cdy - aby * cdx
    acx, acy = c[0] - a[0], c[1] - a[1]
    length_sq = abx * abx + aby * aby
    if length_sq <= _EPSILON:
        return []
    if abs(denominator) <= _EPSILON:
        if abs(acx * aby - acy * abx) > _EPSILON:
            return []  # parallel but not collinear
        parameters = []
        for point in (c, d):
            t = ((point[0] - a[0]) * abx + (point[1] - a[1]) * aby) / length_sq
            if -_EPSILON <= t <= 1.0 + _EPSILON:
                parameters.append(min(1.0, max(0.0, t)))
        return parameters
    t = (acx * cdy - acy * cdx) / denominator
    u = (acx * aby - acy * abx) / denominator
    if -_EPSILON <= t <= 1.0 + _EPSILON and -_EPSILON <= u <= 1.0 + _EPSILON:
        return [min(1.0, max(0.0, t))]
    return []


def _segment_inside_polygon(p: Point2D, q: Point2D, parent: VertexShape, margin: float) -> bool:
    """Whether every point of ``p–q`` is at least *margin* inside *parent*.

    The segment is split at every meeting point with a parent edge (a crossing,
    a touch, a run along an edge); between two consecutive splits it is either
    wholly inside or wholly outside, so the midpoint of each piece decides. This
    catches a child edge that passes exactly through parent vertices into a
    concave notch, where no crossing is "proper" and every vertex is inside.
    """
    parameters = [0.0, 1.0]
    for c, d in _edges(parent.vertices, closed=True):
        parameters.extend(_intersection_parameters(p, q, c, d))
    parameters.sort()
    for start, end in zip(parameters, parameters[1:], strict=False):
        if end - start <= _EPSILON:
            continue
        middle = (start + end) / 2.0
        probe = (p[0] + (q[0] - p[0]) * middle, p[1] + (q[1] - p[1]) * middle)
        if signed_distance_to_polygon(probe, parent.vertices) < margin:
            return False
    return True


# ── Containment (V-03 / V-04) ────────────────────────────────────────────────


def contains(
    parent: Shape,
    child: Shape,
    *,
    tolerance_m: float = DEFAULT_TOLERANCE_M,
    inset_m: float = 0.0,
) -> bool:
    """Whether *child* lies completely inside *parent*, at least ``inset_m`` from its edge.

    V-03 (``geometry.outside_parent``): every child vertex is inside the
    parent (the four transformed corners for a rotated rect), with a 1 cm
    tolerance — ``inset_m = 0``. V-04 (``slot.outside_bed``): the edge margin
    is passed as ``inset_m`` and the parent is the bed in its own frame
    (:func:`to_local_shape`). Beyond the vertex test the spec names, every
    child edge is checked piecewise against a polygon parent (a child edge
    through a concave notch is rejected) and, with an inset, against the
    parent's vertices (a reflex corner closer than the inset to a child edge
    is rejected). Both shapes are assumed to have passed V-02.

    Args:
        parent: An area shape (closed vertex shape or circle).
        child: Any shape; a polyline or point is checked by its vertices.
        tolerance_m: How far the child may protrude (default 1 cm).
        inset_m: Required distance between child and parent boundary.

    Raises:
        ValueError: when *parent* has no area (an open vertex shape).
    """
    if isinstance(parent, VertexShape) and not parent.closed:
        raise ValueError("Only an area shape (closed polygon or circle) can contain another geometry.")
    margin = inset_m - tolerance_m
    if isinstance(child, CircleShape):
        return _signed_distance(child.center, parent) >= child.radius_m + margin
    if not all(_signed_distance(v, parent) >= margin for v in child.vertices):
        return False
    if isinstance(parent, CircleShape) or len(child.vertices) < 2:
        return True  # a circle is convex: a segment with both ends inside lies inside
    child_edges = _edges(child.vertices, closed=child.closed)
    if not all(_segment_inside_polygon(p, q, parent, margin) for p, q in child_edges):
        return False
    if margin > 0.0:
        return all(_point_segment_distance(v, p, q) >= margin for v in parent.vertices for p, q in child_edges)
    return True


# ── Overlap (V-05 / V-06) ────────────────────────────────────────────────────


def _bboxes_overlap(a: BoundingBox, b: BoundingBox, tolerance_m: float) -> bool:
    return (
        a[2] > b[0] + tolerance_m
        and b[2] > a[0] + tolerance_m
        and a[3] > b[1] + tolerance_m
        and b[3] > a[1] + tolerance_m
    )


def _project(vertices: tuple[Point2D, ...], axis: Point2D) -> tuple[float, float]:
    dots = [v[0] * axis[0] + v[1] * axis[1] for v in vertices]
    return (min(dots), max(dots))


def _sat_overlap(a: VertexShape, b: VertexShape, tolerance_m: float) -> bool:
    """Separating-axis test for two convex polygons; overlap must exceed the tolerance on every axis."""
    for p, q in _edges(a.vertices, closed=True) + _edges(b.vertices, closed=True):
        edge_x, edge_y = q[0] - p[0], q[1] - p[1]
        length = math.hypot(edge_x, edge_y)
        if length <= _EPSILON:
            continue
        axis = (-edge_y / length, edge_x / length)
        min_a, max_a = _project(a.vertices, axis)
        min_b, max_b = _project(b.vertices, axis)
        if min(max_a, max_b) - max(min_a, min_b) <= tolerance_m:
            return False
    return True


def _inward_edge_probes(vertices: tuple[Point2D, ...], offset_m: float) -> list[Point2D]:
    """The midpoint of every edge, moved *offset_m* into the polygon's interior.

    Two polygons can share area without any vertex of one lying strictly
    inside the other and without any proper edge crossing — identical shapes,
    or one that covers a whole bar of a concave other along its edges. A point
    just inside an edge of A that is also inside B proves shared interior.
    """
    count = len(vertices)
    signed = 0.0
    for i in range(count):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % count]
        signed += x1 * y2 - x2 * y1
    orientation = 1.0 if signed >= 0 else -1.0  # counter-clockwise → the interior is to the left
    probes: list[Point2D] = []
    for p, q in _edges(vertices, closed=True):
        edge_x, edge_y = q[0] - p[0], q[1] - p[1]
        length = math.hypot(edge_x, edge_y)
        if length <= _EPSILON:
            continue
        normal_x, normal_y = -edge_y / length * orientation, edge_x / length * orientation
        probes.append(((p[0] + q[0]) / 2 + normal_x * offset_m, (p[1] + q[1]) / 2 + normal_y * offset_m))
    return probes


def _probes_share_interior(own: VertexShape, other: VertexShape, tolerance_m: float) -> bool:
    """Whether an inward probe of some *own* edge lies inside *other* as well.

    The probe sits half the tolerance inside the edge and must be at least
    half the tolerance inside the other shape. That is the same verdict SAT
    gives two parallel edges: a penetration of ``p`` puts the probe ``p − tol/2``
    inside the other shape, so ``p > tol`` ⇔ overlap — the two algorithms
    agree on the configuration beds usually meet in (side by side), and a
    narrow concave shape still overlaps its identical twin. A probe that is
    not inside *own* itself (an arm thinner than the tolerance) is skipped.
    """
    half = 0.5 * tolerance_m
    slack = 1e-6  # below storage precision; lets the identical twin pass the ≥ test
    for probe in _inward_edge_probes(own.vertices, half):
        if signed_distance_to_polygon(probe, own.vertices) < half - slack:
            continue
        if signed_distance_to_polygon(probe, other.vertices) > half - slack:
            return True
    return False


def _edge_overlap(a: VertexShape, b: VertexShape, tolerance_m: float) -> bool:
    """General (concave-safe) test: a deep edge crossing, a vertex clearly inside the other, or shared edge interior."""
    if _any_proper_crossing(a, b, tolerance_m):
        return True
    if any(signed_distance_to_polygon(v, b.vertices) > tolerance_m for v in a.vertices):
        return True
    if any(signed_distance_to_polygon(v, a.vertices) > tolerance_m for v in b.vertices):
        return True
    return _probes_share_interior(a, b, tolerance_m) or _probes_share_interior(b, a, tolerance_m)


def overlaps(a: Shape, b: Shape, *, tolerance_m: float = DEFAULT_TOLERANCE_M) -> bool:
    """Whether two area shapes share more than a sliver (penetration > ``tolerance_m``).

    V-05 (``bed.overlap``) / V-06 (``slot.overlap``): bounding-box pre-test,
    then separating-axis test for convex polygons or the edge test for concave
    ones; circles are compared by distance. Shapes without an area (point,
    polyline) never overlap anything — a position has no overlap notion.
    Both shapes are assumed to have passed V-02 (see :func:`is_convex`).
    """
    if (isinstance(a, VertexShape) and not a.closed) or (isinstance(b, VertexShape) and not b.closed):
        return False
    if not _bboxes_overlap(_shape_bbox(a), _shape_bbox(b), tolerance_m):
        return False
    if isinstance(a, CircleShape) and isinstance(b, CircleShape):
        return _distance(a.center, b.center) < a.radius_m + b.radius_m - tolerance_m
    if isinstance(a, CircleShape):
        return _signed_distance(a.center, b) > tolerance_m - a.radius_m
    if isinstance(b, CircleShape):
        return _signed_distance(b.center, a) > tolerance_m - b.radius_m
    if is_convex(a.vertices) and is_convex(b.vertices):
        return _sat_overlap(a, b, tolerance_m)
    return _edge_overlap(a, b, tolerance_m)
