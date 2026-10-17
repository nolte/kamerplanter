"""Embedded geometry value type for the garden plan (REQ-053 §20.1, V-01).

A ``Geometry`` is one of five shapes, discriminated by ``kind``. Lengths are
metres rounded to 0.001 m (GP-FR-004); angles are degrees counter-clockwise
about ``+x`` (GP-FR-008). The model enforces exactly the API-level rule V-01
(``geometry.invalid``): dimension and coordinate ranges, rotation range, point
counts, and no ``rotation_deg`` on ``circle``/``point``/``polyline``. The
domain-level rule V-02 (simple polygon) lives in
:mod:`app.domain.calculators.geometry_calculator` — the spec places it one
layer up, so a self-intersecting polygon *parses* and is rejected by the
service with its own error code.

Frames (REQ-053 §9.2): ``Site.plan.boundary``, ``Location.geometry`` and
``GardenObject.geometry`` are expressed in the plan frame, whose coordinates
V-01 confines to ``0 ≤ x, y ≤ 1 000``. ``Slot.geometry`` is expressed in the
bed frame of its parent location, whose origin is the bed's anchor — the
centre of a circular bed, the first vertex of a polygon bed — so a slot's
coordinates are legitimately negative there. The spec does not state a range
for the bed frame; until that decision lands (placeholder, see the
``needs-decision`` issue linked from #2321) the bed frame accepts
``-1 000 ≤ x, y ≤ 1 000``. Select the frame through the validation context:
``parse_geometry(data, frame=GeometryFrame.BED)``.

Rounding is defined so that the TypeScript port can match it bit for bit:
the exact binary value is rounded to 3 decimals with ties away from zero —
Python ``Decimal(value).quantize(Decimal("0.001"), ROUND_HALF_UP)``,
JavaScript ``Number(value.toFixed(3))``. Python's built-in ``round`` would
break ties to even and disagree on exactly representable halves (2.0625).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    StrictFloat,
    TypeAdapter,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    field_validator,
)

from app.common.enums import GeometryKind

# ── V-01 bounds (REQ-053 §20.1, §22.2) ───────────────────────────────────────

#: Smallest dimension (width, length, radius, polyline width) in metres.
MIN_DIMENSION_M = 0.01
#: Largest dimension in metres; the plan frame spans 1 000 m per axis (GP-FR-013).
MAX_DIMENSION_M = 1000.0
#: Plan-frame coordinates are confined to ``0 ≤ x, y ≤ 1 000``.
MIN_COORDINATE_M = 0.0
MAX_COORDINATE_M = 1000.0
#: ``0 ≤ rotation_deg < 360``; a value that rounds to 360.000 wraps to 0.
FULL_TURN_DEG = 360.0
#: Point-count bounds for polygon (≥ 3) and polyline (≥ 2), both capped at 200.
MIN_POLYGON_POINTS = 3
MIN_POLYLINE_POINTS = 2
MAX_POINTS = 200
#: Storage precision: millimetres (GP-FR-004).
LENGTH_DECIMALS = 3
_QUANTUM = Decimal(1).scaleb(-LENGTH_DECIMALS)

#: A coordinate pair ``(x, y)`` in metres. Components are strict floats (an int is
#: accepted, a string or bool is not) so that V-01 verdicts match the TypeScript port.
Point2D = tuple[StrictFloat, StrictFloat]


class GeometryFrame(StrEnum):
    """The coordinate frame a geometry is validated for (REQ-053 §9.2)."""

    PLAN = "plan"
    BED = "bed"


#: Key under which :func:`parse_geometry` passes the frame in the validation context.
FRAME_CONTEXT_KEY = "geometry_frame"


def round_length(value: float) -> float:
    """Round a length, coordinate or angle to the storage precision (0.001).

    Ties round away from zero on the exact binary value; ``-0.0`` becomes ``0.0``.
    """
    return float(Decimal(value).quantize(_QUANTUM, rounding=ROUND_HALF_UP)) + 0.0


def _frame_from(info: ValidationInfo) -> GeometryFrame:
    context = info.context or {}
    frame = context.get(FRAME_CONTEXT_KEY, GeometryFrame.PLAN)
    return GeometryFrame(frame)


def _validate_point(point: tuple[float, float], info: ValidationInfo) -> tuple[float, float]:
    x, y = (round_length(point[0]), round_length(point[1]))
    minimum = -MAX_COORDINATE_M if _frame_from(info) is GeometryFrame.BED else MIN_COORDINATE_M
    for coordinate in (x, y):
        if not minimum <= coordinate <= MAX_COORDINATE_M:
            raise ValueError(f"Coordinates must lie within {minimum}..{MAX_COORDINATE_M} m, got {point}.")
    return (x, y)


def _validate_dimension(value: float) -> float:
    rounded = round_length(value)
    if not MIN_DIMENSION_M <= rounded <= MAX_DIMENSION_M:
        raise ValueError(f"Dimensions must lie within {MIN_DIMENSION_M}..{MAX_DIMENSION_M} m, got {value}.")
    return rounded


def _validate_rotation(value: float) -> float:
    """V-01 on the *input*: ``0 ≤ value < 360``; an input that rounds to 360.000 wraps to 0.0."""
    if not 0.0 <= value < FULL_TURN_DEG:
        raise ValueError(f"rotation_deg must lie within 0..{FULL_TURN_DEG} (exclusive), got {value}.")
    rounded = round_length(value)
    return 0.0 if rounded == FULL_TURN_DEG else rounded


def _validate_points(
    points: tuple[tuple[float, float], ...], *, minimum: int, info: ValidationInfo
) -> tuple[tuple[float, float], ...]:
    if not minimum <= len(points) <= MAX_POINTS:
        raise ValueError(f"Expected {minimum}..{MAX_POINTS} points, got {len(points)}.")
    return tuple(_validate_point(point, info) for point in points)


class _GeometryBase(BaseModel):
    """Common configuration: unknown fields are an error (a ``rotation_deg`` on a circle is V-01)."""

    model_config = {"extra": "forbid", "frozen": True}


class RectGeometry(_GeometryBase):
    """Axis-aligned rectangle before rotation; ``origin`` is the lower-left corner.

    ``width_m`` runs along ``+x`` and ``length_m`` along ``+y`` before rotation;
    the rotation pivots about ``origin`` (REQ-053 §20.1 worked example).
    """

    kind: Literal[GeometryKind.RECT] = GeometryKind.RECT
    origin: Point2D
    width_m: StrictFloat
    length_m: StrictFloat
    rotation_deg: StrictFloat = 0.0

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, value: tuple[float, float], info: ValidationInfo) -> tuple[float, float]:
        return _validate_point(value, info)

    @field_validator("width_m", "length_m")
    @classmethod
    def validate_dimensions(cls, value: float) -> float:
        return _validate_dimension(value)

    @field_validator("rotation_deg")
    @classmethod
    def validate_rotation(cls, value: float) -> float:
        return _validate_rotation(value)


class CircleGeometry(_GeometryBase):
    """Circle with ``origin`` as its centre. A circle has no rotation."""

    kind: Literal[GeometryKind.CIRCLE] = GeometryKind.CIRCLE
    origin: Point2D
    radius_m: StrictFloat

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, value: tuple[float, float], info: ValidationInfo) -> tuple[float, float]:
        return _validate_point(value, info)

    @field_validator("radius_m")
    @classmethod
    def validate_radius(cls, value: float) -> float:
        return _validate_dimension(value)


class PolygonGeometry(_GeometryBase):
    """Closed polygon of 3..200 vertices; the closing edge is implicit.

    The first vertex is the polygon's anchor: ``rotation_deg`` pivots about it,
    and the bed frame of a polygon location has its origin there (§9.2). The
    editor normally stores polygons with ``rotation_deg = 0`` (GP-FR-005).
    Simplicity (V-02) is a domain rule checked by the calculator, not here.
    """

    kind: Literal[GeometryKind.POLYGON] = GeometryKind.POLYGON
    points: tuple[Point2D, ...]
    rotation_deg: StrictFloat = 0.0

    @field_validator("points")
    @classmethod
    def validate_points(
        cls, value: tuple[tuple[float, float], ...], info: ValidationInfo
    ) -> tuple[tuple[float, float], ...]:
        return _validate_points(value, minimum=MIN_POLYGON_POINTS, info=info)

    @field_validator("rotation_deg")
    @classmethod
    def validate_rotation(cls, value: float) -> float:
        return _validate_rotation(value)


class PolylineGeometry(_GeometryBase):
    """Open line of 2..200 vertices with a stroke width (fence, wall, path axis)."""

    kind: Literal[GeometryKind.POLYLINE] = GeometryKind.POLYLINE
    points: tuple[Point2D, ...]
    width_m: StrictFloat

    @field_validator("points")
    @classmethod
    def validate_points(
        cls, value: tuple[tuple[float, float], ...], info: ValidationInfo
    ) -> tuple[tuple[float, float], ...]:
        return _validate_points(value, minimum=MIN_POLYLINE_POINTS, info=info)

    @field_validator("width_m")
    @classmethod
    def validate_width(cls, value: float) -> float:
        return _validate_dimension(value)


class PointGeometry(_GeometryBase):
    """A position (slot, point object); ``origin`` is the point itself."""

    kind: Literal[GeometryKind.POINT] = GeometryKind.POINT
    origin: Point2D

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, value: tuple[float, float], info: ValidationInfo) -> tuple[float, float]:
        return _validate_point(value, info)


Geometry = Annotated[
    RectGeometry | CircleGeometry | PolygonGeometry | PolylineGeometry | PointGeometry,
    Field(discriminator="kind"),
]

#: Parses a raw mapping (request body, stored document) into the matching shape.
GeometryAdapter: TypeAdapter[Geometry] = TypeAdapter(Geometry)

#: Shapes that enclose an area and therefore carry ``area_m2`` (GP-FR-006).
AREA_KINDS: frozenset[GeometryKind] = frozenset({GeometryKind.RECT, GeometryKind.CIRCLE, GeometryKind.POLYGON})


def parse_geometry(data: object, *, frame: GeometryFrame = GeometryFrame.PLAN) -> Geometry:
    """Validate *data* as a :data:`Geometry` expressed in *frame*.

    Args:
        data: The raw mapping.
        frame: ``PLAN`` (default) confines coordinates to ``0..1 000``; ``BED``
            (slot geometries, §9.2) allows ``-1 000..1 000``.

    Raises:
        pydantic.ValidationError: when the payload violates V-01.
    """
    return GeometryAdapter.validate_python(data, context={FRAME_CONTEXT_KEY: frame})


def _validate_in_bed_frame(value: object, handler: ValidatorFunctionWrapHandler) -> Geometry:
    """Validate a field value in the bed frame whatever context the outer model was validated with.

    The bed frame is a property of the *field* (``Slot.geometry``, §9.2), not of the
    call site, so a slot read from the database or built from a request body must
    not depend on the caller remembering ``context={geometry_frame: bed}``. An
    already-validated instance passes through unchanged (a frozen model cannot
    have drifted); ``handler`` is unused because the frame can only be selected
    through the validation context.
    """
    if isinstance(value, RectGeometry | CircleGeometry | PolygonGeometry | PolylineGeometry | PointGeometry):
        return value
    return parse_geometry(value, frame=GeometryFrame.BED)


#: A :data:`Geometry` field expressed in the bed frame of its parent location
#: (``Slot.geometry``, REQ-053 §9.2): coordinates may be negative, V-01 otherwise unchanged.
BedFrameGeometry = Annotated[Geometry, WrapValidator(_validate_in_bed_frame)]
