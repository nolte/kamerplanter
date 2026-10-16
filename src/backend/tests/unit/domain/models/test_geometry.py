"""V-01 on the ``Geometry`` value type (REQ-053 §20.1, §22.2).

The shared vectors (``test_geometry_vectors.py``) pin the cases the TypeScript
port must match; this file covers what only the Python model owns — the point
cap at 200, immutability and hashing, the frame context, the adapter and the
``AREA_KINDS`` set.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import GeometryKind
from app.domain.models.geometry import (
    AREA_KINDS,
    MAX_POINTS,
    CircleGeometry,
    GeometryFrame,
    PointGeometry,
    PolygonGeometry,
    PolylineGeometry,
    RectGeometry,
    parse_geometry,
    round_length,
)


def _points(count: int) -> list[tuple[float, float]]:
    """*count* distinct in-frame points (not necessarily a simple polygon)."""
    return [(float(i), float(i * i % 7)) for i in range(count)]


class TestDiscriminator:
    def test_parse_returns_the_matching_class(self) -> None:
        assert isinstance(parse_geometry({"kind": "rect", "origin": [0, 0], "width_m": 1, "length_m": 1}), RectGeometry)
        assert isinstance(parse_geometry({"kind": "circle", "origin": [0, 0], "radius_m": 1}), CircleGeometry)
        assert isinstance(parse_geometry({"kind": "polygon", "points": _points(3)}), PolygonGeometry)
        assert isinstance(parse_geometry({"kind": "polyline", "points": _points(2), "width_m": 0.5}), PolylineGeometry)
        assert isinstance(parse_geometry({"kind": "point", "origin": [0, 0]}), PointGeometry)

    def test_kind_defaults_per_class(self) -> None:
        assert RectGeometry(origin=(0, 0), width_m=1, length_m=1).kind == GeometryKind.RECT
        assert CircleGeometry(origin=(0, 0), radius_m=1).kind == GeometryKind.CIRCLE

    def test_missing_kind_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            parse_geometry({"origin": [0, 0], "width_m": 1, "length_m": 1})

    def test_area_kinds(self) -> None:
        assert {GeometryKind.RECT, GeometryKind.CIRCLE, GeometryKind.POLYGON} == AREA_KINDS


class TestPointCap:
    def test_polygon_accepts_200_points(self) -> None:
        assert len(PolygonGeometry(points=_points(MAX_POINTS)).points) == MAX_POINTS

    def test_polygon_rejects_201_points(self) -> None:
        with pytest.raises(ValidationError, match="points"):
            PolygonGeometry(points=_points(MAX_POINTS + 1))

    def test_polyline_rejects_201_points(self) -> None:
        with pytest.raises(ValidationError, match="points"):
            PolylineGeometry(points=_points(MAX_POINTS + 1), width_m=0.5)

    def test_polygon_point_outside_frame_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Coordinates"):
            PolygonGeometry(points=[(0, 0), (1, 0), (1, 1000.5)])


class TestFrames:
    def test_plan_frame_rejects_negative_coordinates(self) -> None:
        with pytest.raises(ValidationError, match="Coordinates"):
            parse_geometry({"kind": "point", "origin": [-0.1, 0.2]})

    def test_bed_frame_accepts_negative_coordinates(self) -> None:
        slot = parse_geometry({"kind": "point", "origin": [-0.1, 0.2]}, frame=GeometryFrame.BED)
        assert isinstance(slot, PointGeometry)
        assert slot.origin == (-0.1, 0.2)

    def test_bed_frame_applies_to_polygon_points(self) -> None:
        zone = parse_geometry({"kind": "polygon", "points": [[-1, -1], [1, -1], [0, 1]]}, frame=GeometryFrame.BED)
        assert isinstance(zone, PolygonGeometry)
        assert zone.points[0] == (-1.0, -1.0)

    def test_direct_construction_is_the_plan_frame(self) -> None:
        with pytest.raises(ValidationError, match="Coordinates"):
            PointGeometry(origin=(-0.1, 0.2))


class TestImmutability:
    def test_models_are_frozen(self) -> None:
        rect = RectGeometry(origin=(0, 0), width_m=1, length_m=1)
        with pytest.raises(ValidationError):
            rect.width_m = 2  # type: ignore[misc]

    def test_points_are_a_tuple_so_v01_cannot_be_bypassed_by_mutation(self) -> None:
        polygon = PolygonGeometry(points=_points(3))
        assert isinstance(polygon.points, tuple)
        with pytest.raises(AttributeError):
            polygon.points.append((5000.0, 0.0))  # type: ignore[attr-defined]

    def test_every_shape_is_hashable(self) -> None:
        shapes = (
            RectGeometry(origin=(0, 0), width_m=1, length_m=1),
            CircleGeometry(origin=(0, 0), radius_m=1),
            PolygonGeometry(points=_points(3)),
            PolylineGeometry(points=_points(2), width_m=0.5),
            PointGeometry(origin=(0, 0)),
        )
        assert len({hash(shape) for shape in shapes}) == len(shapes)

    def test_unknown_field_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            RectGeometry(origin=(0, 0), width_m=1, length_m=1, height_m=0.5)  # type: ignore[call-arg]


class TestStrictNumbers:
    def test_string_dimension_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            parse_geometry({"kind": "rect", "origin": [0, 0], "width_m": "1.5", "length_m": 1})

    def test_boolean_coordinate_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            parse_geometry({"kind": "point", "origin": [True, 0]})

    def test_integer_is_accepted_as_float(self) -> None:
        rect = parse_geometry({"kind": "rect", "origin": [1, 2], "width_m": 3, "length_m": 4})
        assert isinstance(rect, RectGeometry)
        assert rect.width_m == 3.0


class TestRounding:
    def test_round_length_is_millimetres(self) -> None:
        assert round_length(1.23456) == 1.235
        assert round_length(0.0004) == 0.0

    def test_ties_round_away_from_zero_on_the_exact_binary_value(self) -> None:
        """2.0625 is exactly representable → a true tie → 2.063 (Python's round() would give 2.062)."""
        assert round_length(2.0625) == 2.063
        assert round_length(-2.0625) == -2.063
        assert round_length(1.0005) == 1.0  # binary 1.000499999… lies below the tie

    def test_negative_zero_is_normalised(self) -> None:
        assert str(round_length(-0.0004)) == "0.0"

    def test_points_are_rounded_before_the_range_check(self) -> None:
        """1000.0004 rounds to 1000.0 and is therefore inside the frame."""
        point = PointGeometry(origin=(1000.0004, 0.0))
        assert point.origin == (1000.0, 0.0)

    def test_rotation_that_rounds_to_a_full_turn_wraps_to_zero(self) -> None:
        assert RectGeometry(origin=(0, 0), width_m=1, length_m=1, rotation_deg=359.9996).rotation_deg == 0.0

    def test_negative_rotation_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="rotation_deg"):
            RectGeometry(origin=(0, 0), width_m=1, length_m=1, rotation_deg=-0.0004)

    def test_dump_round_trips_through_the_adapter(self) -> None:
        rect = RectGeometry(origin=(2.0, 3.5), width_m=3.0, length_m=1.2, rotation_deg=90.0)
        assert parse_geometry(rect.model_dump(mode="json")) == rect
