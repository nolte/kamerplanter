"""Property-style tests for the geometry calculator (REQ-053 GP-NFR-012).

GP-NFR-012 asks for Hypothesis properties (area ≥ 0, shoelace = rect formula,
rotation preserves area). ``hypothesis`` is not a dev dependency of the
backend, so the properties run over a seeded sample of generated shapes
instead — deterministic, so a failure reproduces. The example-based cases
live in the shared vectors (``test_geometry_vectors.py``).
"""

from __future__ import annotations

import math
import random

import pytest

from app.domain.calculators import geometry_calculator as calc
from app.domain.models.geometry import (
    CircleGeometry,
    Geometry,
    PointGeometry,
    PolygonGeometry,
    RectGeometry,
    parse_geometry,
)

SEED = 20261016
SAMPLES = 150


def _rng() -> random.Random:
    return random.Random(SEED)


def _random_rect(rng: random.Random) -> RectGeometry:
    return RectGeometry(
        origin=(rng.uniform(10, 900), rng.uniform(10, 900)),
        width_m=rng.uniform(0.05, 50),
        length_m=rng.uniform(0.05, 50),
        rotation_deg=rng.uniform(0, 359.999),
    )


def _random_star_polygon(rng: random.Random, *, rotation_deg: float = 0.0) -> PolygonGeometry:
    """A star-shaped polygon around a centre is always simple.

    Vertices go round the centre at increasing angles with every angular gap
    below π (evenly spaced, jittered by at most ±20 % of the spacing) — a gap
    above π would send an edge past the centre and could cross another edge.
    """
    cx, cy = rng.uniform(100, 900), rng.uniform(100, 900)
    count = rng.randint(3, 12)
    spacing = 2 * math.pi / count
    angles = [i * spacing + rng.uniform(-0.2, 0.2) * spacing for i in range(count)]
    radii = [rng.uniform(1, 40) for _ in angles]
    points = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a, r in zip(angles, radii, strict=True)]
    return PolygonGeometry(points=points, rotation_deg=rotation_deg)


def _random_circle(rng: random.Random) -> CircleGeometry:
    return CircleGeometry(origin=(rng.uniform(100, 900), rng.uniform(100, 900)), radius_m=rng.uniform(0.05, 40))


def _rects() -> list[RectGeometry]:
    rng = _rng()
    return [_random_rect(rng) for _ in range(SAMPLES)]


def _polygons() -> list[PolygonGeometry]:
    rng = _rng()
    return [_random_star_polygon(rng) for _ in range(SAMPLES)]


def _shape_vertices(geometry: Geometry) -> tuple[tuple[float, float], ...]:
    shape = calc.to_shape(geometry)
    assert isinstance(shape, calc.VertexShape)
    return shape.vertices


def _with(geometry: RectGeometry | PolygonGeometry, **changes: object) -> Geometry:
    """A validated copy — ``model_copy(update=...)`` would skip V-01 and the rounding."""
    return parse_geometry({**geometry.model_dump(mode="json"), **changes})


def _rect_pair_with_penetration(rect: RectGeometry, depth_m: float) -> tuple[calc.VertexShape, calc.VertexShape]:
    """*rect* and a copy of it shifted along its own width so that they penetrate by *depth_m*.

    Shifting in the bed frame keeps the pair's edges parallel under any
    rotation, so the penetration is *depth_m* on the separating axis (up to
    the millimetre rounding of the origin, well below the ±2 mm steps used).
    """
    shift = calc.transform_bed_to_plan((rect.width_m - depth_m, 0.0), rect)
    moved = _with(rect, origin=list(shift))
    a, b = calc.to_shape(rect), calc.to_shape(moved)
    assert isinstance(a, calc.VertexShape)
    assert isinstance(b, calc.VertexShape)
    return a, b


class TestAreaProperties:
    @pytest.mark.parametrize("rect", _rects())
    def test_shoelace_equals_rect_formula(self, rect: RectGeometry) -> None:
        """GP-NFR-012: shoelace over the resolved corners equals width × length.

        Absolute tolerance: the shoelace sums products of plan coordinates up to
        1 000 m, so cancellation leaves ~1e-7 m² of noise on a 0.0025 m² rect.
        """
        assert calc.shoelace_area(_shape_vertices(rect)) == pytest.approx(rect.width_m * rect.length_m, abs=1e-6)
        assert calc.area_m2(rect) == pytest.approx(rect.width_m * rect.length_m, abs=0.0006)  # rounded to 0.001

    @pytest.mark.parametrize("polygon", _polygons())
    def test_area_is_non_negative_and_rotation_invariant(self, polygon: PolygonGeometry) -> None:
        """GP-NFR-012: the shoelace over the *rotated* vertices equals the unrotated one.

        ``area_m2`` reads the stored points and never the rotation, so comparing
        it before and after would prove nothing; the resolved shape is the path
        that actually rotates.
        """
        area = calc.area_m2(polygon)
        assert area >= 0.0
        rotated = _with(polygon, rotation_deg=137.5)
        assert calc.shoelace_area(_shape_vertices(rotated)) == pytest.approx(
            calc.shoelace_area(_shape_vertices(polygon)), abs=1e-6
        )
        assert calc.shoelace_area(_shape_vertices(rotated)) == pytest.approx(area, abs=0.0006)

    @pytest.mark.parametrize("polygon", _polygons())
    def test_generated_polygons_are_simple(self, polygon: PolygonGeometry) -> None:
        assert calc.validate_geometry(polygon) == []

    def test_circle_area(self) -> None:
        rng = _rng()
        for _ in range(SAMPLES):
            circle = _random_circle(rng)
            assert calc.area_m2(circle) == pytest.approx(math.pi * circle.radius_m**2, abs=0.0006)  # rounded to 0.001


class TestBoundingBoxProperties:
    @pytest.mark.parametrize("rect", _rects())
    def test_bbox_encloses_every_corner_and_is_never_smaller_than_the_area(self, rect: RectGeometry) -> None:
        min_x, min_y, max_x, max_y = calc.bounding_box(rect)
        for x, y in _shape_vertices(rect):
            assert min_x - 0.001 <= x <= max_x + 0.001
            assert min_y - 0.001 <= y <= max_y + 0.001
        assert (max_x - min_x) * (max_y - min_y) >= calc.area_m2(rect) - 0.01

    @pytest.mark.parametrize("rect", _rects())
    def test_centroid_lies_inside_the_rect(self, rect: RectGeometry) -> None:
        assert calc.contains(calc.to_shape(rect), calc.VertexShape((calc.centroid(rect),), closed=False))


class TestTransformProperties:
    @pytest.mark.parametrize("rect", _rects())
    def test_bed_to_plan_round_trips(self, rect: RectGeometry) -> None:
        rng = random.Random(hash((rect.origin, rect.rotation_deg)) & 0xFFFF)
        for _ in range(5):
            bed_point = (rng.uniform(0, rect.width_m), rng.uniform(0, rect.length_m))
            plan_point = calc.transform_bed_to_plan(bed_point, rect)
            back = calc.transform_plan_to_bed(plan_point, rect)
            assert back == pytest.approx(bed_point, abs=1e-9)
            # Any point of the bed frame rectangle lands inside the rotated rect in the plan.
            assert calc.contains(calc.to_shape(rect), calc.VertexShape((plan_point,), closed=False))

    def test_rotate_point_by_zero_is_identity(self) -> None:
        assert calc.rotate_point((3.0, 4.0), 0.0, (1.0, 1.0)) == (3.0, 4.0)

    def test_rotate_point_quarter_turn(self) -> None:
        assert calc.rotate_point((1.0, 0.0), 90.0) == pytest.approx((0.0, 1.0), abs=1e-12)


class TestContainmentProperties:
    @pytest.mark.parametrize("polygon", _polygons())
    def test_a_shape_contains_itself(self, polygon: PolygonGeometry) -> None:
        shape = calc.to_shape(polygon)
        assert calc.contains(shape, shape)

    @pytest.mark.parametrize("polygon", _polygons())
    def test_a_shape_does_not_contain_itself_with_an_inset(self, polygon: PolygonGeometry) -> None:
        shape = calc.to_shape(polygon)
        assert not calc.contains(shape, shape, inset_m=0.5)

    @pytest.mark.parametrize("rect", _rects())
    def test_rect_contains_its_local_frame_corners(self, rect: RectGeometry) -> None:
        local = calc.to_local_shape(rect)
        assert isinstance(local, calc.VertexShape)
        for corner in local.vertices:
            assert calc.contains(local, calc.VertexShape((corner,), closed=False))

    def test_open_parent_is_refused(self) -> None:
        polyline = calc.VertexShape(((0.0, 0.0), (1.0, 0.0)), closed=False)
        with pytest.raises(ValueError, match="area"):
            calc.contains(polyline, calc.to_shape(PointGeometry(origin=(0.5, 0.0))))


class TestOverlapProperties:
    @pytest.mark.parametrize("polygon", _polygons())
    def test_overlap_is_reflexive(self, polygon: PolygonGeometry) -> None:
        shape = calc.to_shape(polygon)
        assert calc.overlaps(shape, shape)

    @pytest.mark.parametrize("polygon", _polygons())
    def test_overlap_is_symmetric_against_a_near_partner(self, polygon: PolygonGeometry) -> None:
        """A partner whose bbox meets the polygon's, so both the convex and the concave branch are reached."""
        shape = calc.to_shape(polygon)
        assert isinstance(shape, calc.VertexShape)
        rng = random.Random(hash(polygon.points[0]) & 0xFFFF)
        min_x, min_y, max_x, max_y = calc.bounding_box(polygon)
        near_circle = calc.CircleShape((rng.uniform(min_x, max_x), rng.uniform(min_y, max_y)), rng.uniform(0.05, 5))
        near_polygon = calc.VertexShape(
            tuple((x + rng.uniform(-5, 5), y + rng.uniform(-5, 5)) for x, y in shape.vertices[:3]), closed=True
        )
        for partner in (near_circle, near_polygon):
            assert calc.overlaps(shape, partner) == calc.overlaps(partner, shape)

    @pytest.mark.parametrize("rect", _rects())
    def test_translated_copy_beyond_its_own_extent_does_not_overlap(self, rect: RectGeometry) -> None:
        min_x, _, max_x, _ = calc.bounding_box(rect)
        shift = (max_x - min_x) + 0.05
        if rect.origin[0] + shift > 1000.0:
            pytest.skip("sample runs into the frame edge")
        moved = _with(rect, origin=[rect.origin[0] + shift, rect.origin[1]])
        assert not calc.overlaps(calc.to_shape(rect), calc.to_shape(moved))

    @pytest.mark.parametrize("rect", _rects())
    def test_sat_and_edge_test_agree_on_random_convex_pairs(self, rect: RectGeometry) -> None:
        """The two overlap algorithms are one semantic: a convex pair gives the same verdict either way."""
        a = calc.to_shape(rect)
        rng = random.Random(hash(rect.origin) & 0xFFFF)
        b = calc.to_shape(
            _with(
                rect,
                origin=[rect.origin[0] + rng.uniform(-5, 5), rect.origin[1] + rng.uniform(-5, 5)],
                rotation_deg=rng.uniform(0, 359.999),
            )
        )
        assert isinstance(a, calc.VertexShape)
        assert isinstance(b, calc.VertexShape)
        assert calc._sat_overlap(a, b, calc.DEFAULT_TOLERANCE_M) == calc._edge_overlap(a, b, calc.DEFAULT_TOLERANCE_M)

    @pytest.mark.parametrize("rect", _rects()[:40])
    @pytest.mark.parametrize("depth_offset_mm", [-6, -4, -2, 2, 4, 6])
    def test_sat_and_edge_test_agree_in_the_tolerance_band(self, rect: RectGeometry, depth_offset_mm: int) -> None:
        """Penetrations of 1 cm ± 2/4/6 mm: exactly where the two semantics could drift apart."""
        depth = calc.DEFAULT_TOLERANCE_M + depth_offset_mm / 1000.0
        a, b = _rect_pair_with_penetration(rect, depth)
        expected = depth > calc.DEFAULT_TOLERANCE_M
        assert calc._sat_overlap(a, b, calc.DEFAULT_TOLERANCE_M) is expected
        assert calc._edge_overlap(a, b, calc.DEFAULT_TOLERANCE_M) is expected
        assert calc.overlaps(a, b) is expected
