"""Planting layout of a bed — a pure function of geometry and spacing (REQ-053 GP-FR-060/062/063/073).

``compute_layout(bed, entry, max_count)`` returns the positions a planting-run entry
occupies in the **bed frame** of a location (§9.2): the anchor of the bed at ``(0, 0)``,
no rotation, so the result does not change when the bed is moved or rotated on the plan.
No I/O, no external geometry library (decision D-04). This module is the Python
reference of the shared Backend <-> Frontend logic (§19.6): the TypeScript port in
``features/gardenPlanner/model/layout.ts`` runs against the same vectors in
``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (GP-ACC-017/018/043), and the
server answer wins on any difference (GP-FR-063).

**Rows and axes.** Rows run along one axis of the bed frame (``u``); consecutive rows stack
along the other (``v``). ``along_length`` follows the longer side of the bed's bounding box,
``along_width`` the shorter one (a tie: the x axis). The first position of a row sits
``edge_margin_along`` from the start of the bed, the first row ``edge_margin_across`` from
its side; defaults are ``spacing / 2`` and ``row_spacing / 2`` (a convention, GP-FR-060).

**Inset = distance to the edge, not Point-in-Polygon (GP-FR-062, W-002).** A candidate is kept
when the box of half-extents ``(margin_along, margin_across)`` around it lies inside the bed,
i.e. the point is inside and no boundary edge enters the box. For an axis-aligned rectangle
that is exactly "margin from every side"; for a circle the four corners of the box lie in the
disc; for any polygon an edge crossing the box rejects the candidate. A candidate may sit on
the edge when both margins are 0 (GP-ACC-018).

**Strategies.**

* ``grid`` — ``row_spacing = spacing``; ``rows`` — its own ``row_spacing_cm`` (required);
  ``triangular`` — ``row_spacing = spacing x 0.866``, every second row shifted by ``spacing / 2``.
* ``zone`` — no per-plant geometry: one ``zone`` slot with a ``capacity_plants`` taken from the
  area (rectangle: inset by the margins; every other bed: the bed outline, margins default to 0
  here and a margin on a non-rectangle is reported as ``layout.zone_inset_not_applied``).
* ``free`` — the user places the points (GP-FR-072): no slots, only the capacity estimate.

**Upper bound (SR-004, GP-FR-062).** The estimate ``area / (spacing x row_spacing)`` is taken
**before** a single point exists; more than 2 000 positions is 422
``layout.too_many_positions {estimated, limit}``. That is O(1) in the bed size, which is what
makes a 1 000 m x 1 000 m bed at 5 cm answerable in < 50 ms (GP-ACC-043). Two further guards
keep a thin diagonal polygon (small area, huge bounding box) from walking a huge candidate grid,
and cap the real result. The cap bounds **generated positions**: ``zone`` and ``free`` generate none
(a zone's ``capacity_plants`` is a plant count of one slot, not a number of slots), so they are not
refused. An entry with a ``row_assignment`` takes only some rows and is bounded by the candidate
walk and its real count instead of the whole-area estimate.

**V-07.** ``planting.spacing_below_minimum`` is raised whenever two planned positions are closer
than ``spacing_cm`` - also for a ``rows`` layout whose ``row_spacing_cm`` is below ``spacing_cm``;
it is a hint, never an error.

Output coordinates are rounded to the storage precision of 0.001 m (GP-FR-004) with the
rounding of :func:`app.domain.models.geometry.round_length`, so the TypeScript port matches.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.common.enums import LayoutStrategy, RowDirection, SlotRole
from app.common.exceptions import PlanError
from app.domain.calculators.geometry_calculator import (
    CircleShape,
    VertexShape,
    area_m2,
    shoelace_area,
    signed_distance_to_polygon,
    to_local_shape,
)
from app.domain.calculators.slot_capacity_calculator import TRIANGULAR_ROW_FACTOR
from app.domain.models.garden_plan import MAX_SLOTS_PER_BATCH
from app.domain.models.geometry import Geometry, Point2D, round_length
from app.domain.models.planting_run import MAX_SPACING_CM, MIN_SPACING_CM

#: GP-FR-062 / V-22: positions one layout (and one slot batch) may carry - one number for both.
MAX_LAYOUT_POSITIONS = MAX_SLOTS_PER_BATCH
#: Candidates the grid walk may visit (5x the position cap); a guard for slivers whose bounding box dwarfs their area.
MAX_LAYOUT_CANDIDATES = 10_000
#: GP-FR-062: ``spacing < mature_width x 0.7`` is worth a warning.
MATURE_WIDTH_FACTOR = 0.7
#: Numerical noise floor for the margin tests, well below the storage precision.
_EPSILON = 1e-9
#: Added before flooring a position count, so ``3.6 / 0.01`` is 360 and not 359.
_COUNT_EPSILON = 1e-6
#: V-07: positions rounded to the millimetre may differ from the spacing by that much without a hint.
_SPACING_TOLERANCE_M = 0.002
#: Vertices of the polygon a circular zone is drawn with.
_CIRCLE_ZONE_VERTICES = 32

CODE_TOO_MANY_POSITIONS = "layout.too_many_positions"
CODE_BED_NOT_AN_AREA = "layout.bed_not_an_area"
CODE_ROW_SPACING_REQUIRED = "layout.row_spacing_required"
CODE_SPACING_OUT_OF_RANGE = "layout.spacing_out_of_range"
#: GP-FR-070: two entries laid out together claim the same row.
CODE_ROW_ASSIGNMENT_OVERLAP = "layout.row_assignment_overlap"
WARNING_SPACING_BELOW_MATURE_WIDTH = "layout.spacing_below_mature_width"
WARNING_NO_POSITION_FITS = "layout.no_position_fits"
#: V-07: two planned positions are closer than ``spacing_cm`` — a hint, never an error.
WARNING_SPACING_BELOW_MINIMUM = "planting.spacing_below_minimum"
WARNING_ZONE_INSET_NOT_APPLIED = "layout.zone_inset_not_applied"


@dataclass(frozen=True)
class EntryLayout:
    """The layout-relevant fields of a planting-run entry (GP-FR-060), in centimetres."""

    layout_strategy: LayoutStrategy
    spacing_cm: float
    row_spacing_cm: float | None = None
    row_direction: RowDirection = RowDirection.ALONG_LENGTH
    edge_margin_along_cm: float | None = None
    edge_margin_across_cm: float | None = None
    #: Reihenindizes (0-based) this entry occupies when rows alternate between entries (GP-FR-070).
    row_assignment: tuple[int, ...] | None = None
    #: Steckbrief ``mature_width_cm`` (lower bound) — only used for the warning.
    mature_width_cm: float | None = None


@dataclass(frozen=True)
class LayoutSlot:
    """One planned slot in the bed frame: a ``position`` point or a ``zone`` polygon."""

    slot_role: SlotRole
    #: ``[x, y]`` of a position; ``None`` for a zone.
    point: Point2D | None = None
    #: Outline of a zone, closed implicitly; ``None`` for a position.
    outline: tuple[Point2D, ...] | None = None
    row_index: int | None = None
    #: 1-based rank in layout order (row by row, §20.5 ``sequence``).
    sequence: int = 1
    capacity_plants: int = 1


@dataclass(frozen=True)
class LayoutWarning:
    code: str
    detail: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class LayoutResult:
    slots: list[LayoutSlot]
    #: Plants the slots hold (positions: one each; zone: its capacity); after ``max_count``.
    count: int
    #: The most this entry could place in the bed before ``max_count`` truncates (GP-FR-073).
    capacity_max: int
    warnings: list[LayoutWarning]


# ── Parameters ───────────────────────────────────────────────────────────────


def _row_spacing_m(entry: EntryLayout) -> float:
    """The distance between rows for the entry's strategy, in metres."""
    spacing = entry.spacing_cm / 100.0
    strategy = entry.layout_strategy
    if strategy is LayoutStrategy.ROWS:
        return (entry.row_spacing_cm or 0.0) / 100.0
    if strategy is LayoutStrategy.TRIANGULAR:
        return spacing * TRIANGULAR_ROW_FACTOR
    if strategy is LayoutStrategy.ZONE and entry.row_spacing_cm:
        return entry.row_spacing_cm / 100.0
    return spacing


def _validate(entry: EntryLayout) -> None:
    if not MIN_SPACING_CM <= entry.spacing_cm <= MAX_SPACING_CM:
        raise PlanError(
            CODE_SPACING_OUT_OF_RANGE,
            f"spacing_cm must lie within {MIN_SPACING_CM:g}..{MAX_SPACING_CM:g}.",
            status_code=422,
            field="spacing_cm",
        )
    if entry.layout_strategy is LayoutStrategy.ROWS:
        row_spacing = entry.row_spacing_cm
        if row_spacing is None:
            raise PlanError(
                CODE_ROW_SPACING_REQUIRED,
                "The rows layout needs a row_spacing_cm.",
                status_code=422,
                field="row_spacing_cm",
            )
        if not MIN_SPACING_CM <= row_spacing <= MAX_SPACING_CM:
            raise PlanError(
                CODE_SPACING_OUT_OF_RANGE,
                f"row_spacing_cm must lie within {MIN_SPACING_CM:g}..{MAX_SPACING_CM:g}.",
                status_code=422,
                field="row_spacing_cm",
            )


def _margins_m(entry: EntryLayout, row_spacing_m: float) -> tuple[float, float]:
    """``(along, across)`` edge margins in metres; the defaults are half a spacing (GP-FR-060)."""
    zone = entry.layout_strategy is LayoutStrategy.ZONE
    default_along = 0.0 if zone else entry.spacing_cm / 200.0
    default_across = 0.0 if zone else row_spacing_m / 2.0
    along = default_along if entry.edge_margin_along_cm is None else entry.edge_margin_along_cm / 100.0
    across = default_across if entry.edge_margin_across_cm is None else entry.edge_margin_across_cm / 100.0
    return (along, across)


def estimate_positions(bed: Geometry, entry: EntryLayout) -> int:
    """``area / (spacing x row_spacing)`` — the pre-estimate of GP-FR-062, no point is generated."""
    _validate(entry)
    area = area_m2(bed)
    cell = (entry.spacing_cm / 100.0) * _row_spacing_m(entry)
    if area <= 0.0 or cell <= 0.0:
        return 0
    return math.floor(area / cell + _COUNT_EPSILON)


# ── Geometry of the bed frame ────────────────────────────────────────────────


def _bbox(shape: VertexShape | CircleShape) -> tuple[float, float, float, float]:
    if isinstance(shape, CircleShape):
        cx, cy = shape.center
        r = shape.radius_m
        return (cx - r, cy - r, cx + r, cy + r)
    xs = [x for x, _ in shape.vertices]
    ys = [y for _, y in shape.vertices]
    return (min(xs), min(ys), max(xs), max(ys))


def _segment_hits_box(a: Point2D, b: Point2D, x0: float, x1: float, y0: float, y1: float) -> bool:
    """Whether the segment ``a-b`` meets the box (Liang-Barsky).

    A degenerate side (``x0 == x1`` or ``y0 == y1``, a margin of 0) has no interior: an edge
    lying along it does not count, one crossing it does.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    if (x0 == x1 and dx == 0.0) or (y0 == y1 and dy == 0.0):
        return False
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0.0:
            if q < 0.0:
                return False
            continue
        r = q / p
        if p < 0.0:
            if r > t1:
                return False
            t0 = max(t0, r)
        else:
            if r < t0:
                return False
            t1 = min(t1, r)
    return t0 <= t1


def _box_fits(shape: VertexShape | CircleShape, x: float, y: float, half_x: float, half_y: float) -> bool:
    """Whether the box of half-extents ``(half_x, half_y)`` around ``(x, y)`` lies inside *shape*."""
    if isinstance(shape, CircleShape):
        cx, cy = shape.center
        reach = math.hypot(abs(x - cx) + half_x, abs(y - cy) + half_y)
        return reach <= shape.radius_m + _EPSILON
    vertices = shape.vertices
    if signed_distance_to_polygon((x, y), vertices) < -_EPSILON:
        return False
    if half_x <= 0.0 and half_y <= 0.0:
        return True
    hx = max(half_x - _EPSILON, 0.0)
    hy = max(half_y - _EPSILON, 0.0)
    count = len(vertices)
    return not any(
        _segment_hits_box(vertices[i], vertices[(i + 1) % count], x - hx, x + hx, y - hy, y + hy) for i in range(count)
    )


def _closest_pair_m(points: list[Point2D], cell_m: float) -> float | None:
    """Smallest distance between two of *points* (``None`` for fewer than two); O(n) via a cell hash.

    The hash cell is the spacing, so the nearest neighbour of a point lies in its own or one of the
    eight surrounding cells — as long as the nearest pair is closer than a cell, which is the only
    case the V-07 hint needs.
    """
    cells: dict[tuple[int, int], list[Point2D]] = {}
    for point in points:
        cells.setdefault((math.floor(point[0] / cell_m), math.floor(point[1] / cell_m)), []).append(point)
    best: float | None = None
    for (cx, cy), members in cells.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in cells.get((cx + dx, cy + dy), ()):
                    for point in members:
                        if point is other:
                            continue
                        distance = math.hypot(point[0] - other[0], point[1] - other[1])
                        if best is None or distance < best:
                            best = distance
    return best


def _round_point(x: float, y: float) -> Point2D:
    return (round_length(x), round_length(y))


# ── Layout ───────────────────────────────────────────────────────────────────


def _too_many(estimated: int) -> PlanError:
    return PlanError(
        CODE_TOO_MANY_POSITIONS,
        f"A layout holds at most {MAX_LAYOUT_POSITIONS} positions; this one would need about {estimated}.",
        status_code=422,
        estimated=estimated,
        limit=MAX_LAYOUT_POSITIONS,
    )


def _mature_width_warnings(entry: EntryLayout) -> list[LayoutWarning]:
    width = entry.mature_width_cm
    if width is not None and width > 0 and entry.spacing_cm < width * MATURE_WIDTH_FACTOR:
        return [
            LayoutWarning(
                WARNING_SPACING_BELOW_MATURE_WIDTH,
                {"spacing_cm": entry.spacing_cm, "mature_width_cm": width},
            )
        ]
    return []


def compute_layout(bed: Geometry, entry: EntryLayout, max_count: int | None = None) -> LayoutResult:
    """The positions of *entry* in the bed frame of *bed* (GP-FR-062).

    ``max_count`` truncates the result to the first n slots in layout order (GP-FR-073);
    ``capacity_max`` stays the untruncated maximum.
    """
    estimated = estimate_positions(bed, entry)  # validates the entry
    strategy = entry.layout_strategy
    warnings = _mature_width_warnings(entry)
    shape = to_local_shape(bed)
    if isinstance(shape, VertexShape) and not shape.closed:
        raise PlanError(
            CODE_BED_NOT_AN_AREA,
            "A planting layout needs a bed that encloses an area (rect, circle or polygon).",
            status_code=422,
            field="geometry",
        )

    if strategy is LayoutStrategy.FREE:
        return LayoutResult(slots=[], count=0, capacity_max=estimated, warnings=warnings)
    if strategy is LayoutStrategy.ZONE:
        return _zone_layout(shape, entry, max_count, warnings)

    # An entry that takes only some rows (GP-FR-070) holds a fraction of the area estimate, so it is
    # bounded by the candidate walk and the count of the real result instead.
    if estimated > MAX_LAYOUT_POSITIONS and entry.row_assignment is None:
        raise _too_many(estimated)
    return _point_layout(shape, entry, max_count, warnings)


def check_disjoint_row_assignments(assignments: Sequence[Sequence[int] | None], *, field_template: str) -> None:
    """GP-FR-070 / GP-ACC-054: the row sets of entries laid out together are pairwise disjoint.

    ``assignments`` holds the ``row_assignment`` of each entry in body order; an entry without one (``None``,
    a monoculture or a zone/free entry) takes no rows and is not part of the check. An overlap is 422
    ``layout.row_assignment_overlap``; ``conflicts`` names every overlapping pair by the positions of the entries
    and the rows they share, and ``field_template`` (with ``{index}``) points at the later entry of the first pair.
    """
    rows = [(index, set(value)) for index, value in enumerate(assignments) if value is not None]
    conflicts = [
        {"runs": [first, second], "rows": sorted(first_rows & second_rows)}
        for position, (first, first_rows) in enumerate(rows)
        for second, second_rows in rows[position + 1 :]
        if first_rows & second_rows
    ]
    if conflicts:
        raise PlanError(
            CODE_ROW_ASSIGNMENT_OVERLAP,
            "Two entries of one mixed culture claim the same row; every row belongs to one entry.",
            status_code=422,
            field=field_template.format(index=conflicts[0]["runs"][1]),
            conflicts=conflicts,
        )


def _point_layout(
    shape: VertexShape | CircleShape,
    entry: EntryLayout,
    max_count: int | None,
    warnings: list[LayoutWarning],
) -> LayoutResult:
    spacing = entry.spacing_cm / 100.0
    row_spacing = _row_spacing_m(entry)
    margin_along, margin_across = _margins_m(entry, row_spacing)
    x_min, y_min, x_max, y_max = _bbox(shape)
    longer_is_x = (x_max - x_min) >= (y_max - y_min)
    rows_along_x = (entry.row_direction is RowDirection.ALONG_LENGTH) == longer_is_x
    if rows_along_x:
        u_min, u_max, v_min, v_max = x_min, x_max, y_min, y_max
        half_x, half_y = margin_along, margin_across
    else:
        u_min, u_max, v_min, v_max = y_min, y_max, x_min, x_max
        half_x, half_y = margin_across, margin_along

    u_span = (u_max - u_min) - 2.0 * margin_along
    v_span = (v_max - v_min) - 2.0 * margin_across
    shift = spacing / 2.0 if entry.layout_strategy is LayoutStrategy.TRIANGULAR else 0.0
    candidates = (math.floor(u_span / spacing + _EPSILON) + 1) * (math.floor(v_span / row_spacing + _EPSILON) + 1)
    if u_span >= -_EPSILON and v_span >= -_EPSILON and candidates > MAX_LAYOUT_CANDIDATES:
        raise _too_many(candidates)

    wanted_rows = None if entry.row_assignment is None else set(entry.row_assignment)
    points: list[tuple[int, Point2D]] = []
    row = 0
    v = v_min + margin_across
    while v <= v_max - margin_across + _EPSILON:
        if wanted_rows is None or row in wanted_rows:
            offset = shift if row % 2 == 1 else 0.0
            u = u_min + margin_along + offset
            step = 0
            while u <= u_max - margin_along + _EPSILON:
                x, y = (u, v) if rows_along_x else (v, u)
                if _box_fits(shape, x, y, half_x, half_y):
                    points.append((row, _round_point(x, y)))
                    if len(points) > MAX_LAYOUT_POSITIONS:
                        raise _too_many(len(points))
                step += 1
                u = u_min + margin_along + offset + step * spacing
        row += 1
        v = v_min + margin_across + row * row_spacing

    capacity_max = len(points)
    closest = _closest_pair_m([point for _, point in points], spacing)
    if closest is not None and closest < spacing - _SPACING_TOLERANCE_M:
        warnings = [
            *warnings,
            LayoutWarning(
                WARNING_SPACING_BELOW_MINIMUM,
                {"spacing_cm": entry.spacing_cm, "closest_cm": round(closest * 100.0, 1)},
            ),
        ]
    if max_count is not None:
        points = points[: max(max_count, 0)]
    slots = [
        LayoutSlot(slot_role=SlotRole.POSITION, point=point, row_index=row_index, sequence=index + 1)
        for index, (row_index, point) in enumerate(points)
    ]
    if capacity_max == 0:
        warnings = [*warnings, LayoutWarning(WARNING_NO_POSITION_FITS)]
    return LayoutResult(slots=slots, count=len(slots), capacity_max=capacity_max, warnings=warnings)


def _zone_outline(
    shape: VertexShape | CircleShape, margin_x: float, margin_y: float
) -> tuple[tuple[Point2D, ...], float, bool]:
    """The outline of a zone slot, the area it stands for and whether the requested margins were applied.

    A circle is drawn as a polygon, but its area is the circle's, so the capacity agrees with
    :func:`estimate_positions` and ``area_m2`` of the same bed.
    """
    insets = margin_x > 0.0 or margin_y > 0.0
    if isinstance(shape, CircleShape):
        cx, cy = shape.center
        steps = _CIRCLE_ZONE_VERTICES
        angles = [2.0 * math.pi * i / steps for i in range(steps)]
        outline = tuple((cx + shape.radius_m * math.cos(a), cy + shape.radius_m * math.sin(a)) for a in angles)
        return (outline, math.pi * shape.radius_m**2, not insets)
    x_min, y_min, x_max, y_max = _bbox(shape)
    if _is_axis_aligned_rect(shape.vertices, (x_min, y_min, x_max, y_max)):
        lo_x, hi_x = x_min + margin_x, x_max - margin_x
        lo_y, hi_y = y_min + margin_y, y_max - margin_y
        if hi_x <= lo_x or hi_y <= lo_y:
            return ((), 0.0, True)
        return (((lo_x, lo_y), (hi_x, lo_y), (hi_x, hi_y), (lo_x, hi_y)), (hi_x - lo_x) * (hi_y - lo_y), True)
    return (shape.vertices, shoelace_area(shape.vertices), not insets)


def _is_axis_aligned_rect(vertices: tuple[Point2D, ...], box: tuple[float, float, float, float]) -> bool:
    """Four vertices that are exactly the four corners of their bounding box."""
    x_min, y_min, x_max, y_max = box
    corners = {(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)}
    return len(vertices) == 4 and set(vertices) == corners


def _zone_layout(
    shape: VertexShape | CircleShape,
    entry: EntryLayout,
    max_count: int | None,
    warnings: list[LayoutWarning],
) -> LayoutResult:
    row_spacing = _row_spacing_m(entry)
    margin_along, margin_across = _margins_m(entry, row_spacing)
    x_min, y_min, x_max, y_max = _bbox(shape)
    longer_is_x = (x_max - x_min) >= (y_max - y_min)
    rows_along_x = (entry.row_direction is RowDirection.ALONG_LENGTH) == longer_is_x
    margin_x, margin_y = (margin_along, margin_across) if rows_along_x else (margin_across, margin_along)

    outline, zone_area, applied = _zone_outline(shape, margin_x, margin_y)
    if not applied:
        warnings = [*warnings, LayoutWarning(WARNING_ZONE_INSET_NOT_APPLIED)]
    cell = (entry.spacing_cm / 100.0) * row_spacing
    capacity_max = math.floor(zone_area / cell + _COUNT_EPSILON) if cell > 0.0 else 0
    if capacity_max == 0:
        return LayoutResult(
            slots=[], count=0, capacity_max=0, warnings=[*warnings, LayoutWarning(WARNING_NO_POSITION_FITS)]
        )
    count = capacity_max if max_count is None else max(min(max_count, capacity_max), 0)
    if count == 0:
        return LayoutResult(slots=[], count=0, capacity_max=capacity_max, warnings=warnings)
    rounded = tuple(_round_point(x, y) for x, y in outline)
    slot = LayoutSlot(slot_role=SlotRole.ZONE, outline=rounded, sequence=1, capacity_plants=count)
    return LayoutResult(slots=[slot], count=count, capacity_max=capacity_max, warnings=warnings)
