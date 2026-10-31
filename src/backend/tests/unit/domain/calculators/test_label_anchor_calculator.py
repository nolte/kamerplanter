"""Edge cases of the label anchor (REQ-053 GP-UX-047, #2490) that the shared vectors do not need to carry."""

from __future__ import annotations

import math
import time

import pytest

from app.domain.calculators.geometry_calculator import point_in_polygon, signed_distance_to_polygon
from app.domain.calculators.label_anchor_calculator import (
    MAX_START_CELLS_PER_AXIS,
    POLE_PRECISION_M,
    centred_room,
    label_anchor,
    pole_of_inaccessibility,
)
from app.domain.models.geometry import PolygonGeometry, RectGeometry

_L_SHAPE = ((0.0, 0.0), (4.0, 0.0), (4.0, 1.0), (1.0, 1.0), (1.0, 4.0), (0.0, 4.0))


class TestPoleOfInaccessibility:
    def test_the_pole_of_an_l_shape_lies_inside_and_beats_the_centroid(self) -> None:
        pole = pole_of_inaccessibility(_L_SHAPE)

        assert point_in_polygon(pole, _L_SHAPE)
        # analytic: (t, t) with t = sqrt2 / (1 + sqrt2) = 0.586 - the largest circle of the corner square
        assert pole == pytest.approx((0.586, 0.586), abs=0.01)
        assert signed_distance_to_polygon(pole, _L_SHAPE) > 0.5

    def test_a_polygon_without_area_falls_back_to_its_first_vertex(self) -> None:
        assert pole_of_inaccessibility(((1.0, 1.0), (2.0, 1.0), (3.0, 1.0))) == (1.0, 1.0)

    @pytest.mark.parametrize(
        "vertices",
        [
            pytest.param(((0.0, 0.0), (1000.0, 0.0), (1000.0, 0.001), (0.0, 0.001)), id="sliver-rect-1000x0.001"),
            pytest.param(((0.0, 0.0), (1000.0, 0.0), (0.0, 0.002)), id="sliver-triangle-1000x0.002"),
            pytest.param(((0.0, 0.0), (0.001, 0.0), (0.001, 1000.0), (0.0, 1000.0)), id="sliver-upright-0.001x1000"),
        ],
    )
    def test_a_sliver_is_searched_within_the_time_budget(self, vertices: tuple[tuple[float, float], ...]) -> None:
        """SCR-001: the textbook start grid (squares as wide as the short side) holds a million cells for a
        1000 x 0.001 m sliver and took about 4-5 s; capped grid plus inradius ceiling keep it far below a frame."""
        started = time.perf_counter()
        pole = pole_of_inaccessibility(vertices)
        elapsed = time.perf_counter() - started

        assert elapsed < 0.25
        assert point_in_polygon(pole, vertices)

    def test_the_start_grid_is_the_textbook_one_up_to_the_cap(self) -> None:
        """A 64:1 strip still starts on squares as wide as its short side: the cap only touches slivers, so the
        search - and every shared vector - is unchanged for beds of ordinary proportions."""
        strip = ((0.0, 0.0), (MAX_START_CELLS_PER_AXIS * 0.3, 0.0), (MAX_START_CELLS_PER_AXIS * 0.3, 0.3), (0.0, 0.3))

        pole = pole_of_inaccessibility(strip)

        assert pole[1] == pytest.approx(0.15, abs=POLE_PRECISION_M)
        assert signed_distance_to_polygon(pole, strip) == pytest.approx(0.15, abs=POLE_PRECISION_M)

    @pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
    def test_a_vertex_that_is_not_finite_falls_back_to_the_first_vertex(self, bad: float) -> None:
        """The models reject NaN and infinity; the pure function still answers instead of searching NaN distances."""
        vertices = ((1.0, 2.0), (4.0, 2.0), (bad, 4.0), (1.0, 4.0))

        assert pole_of_inaccessibility(vertices) == (1.0, 2.0)

    def test_a_coarser_precision_still_ends_inside(self) -> None:
        pole = pole_of_inaccessibility(_L_SHAPE, precision_m=0.5)

        assert point_in_polygon(pole, _L_SHAPE)


class TestCentredRoom:
    def test_the_room_is_symmetric_about_the_point(self) -> None:
        # chord 0..4 at y = 0.5; centred at x = 1 the label may run 1 m to each side
        assert centred_room(_L_SHAPE, (1.0, 0.5)) == pytest.approx(2.0)

    def test_a_point_outside_has_no_room(self) -> None:
        assert centred_room(_L_SHAPE, (3.0, 3.0)) is None

    def test_a_line_through_a_vertex_meets_it_once(self) -> None:
        # y = 1 runs through the vertices (4, 1) and (1, 1): half-open edges count each crossing once
        assert centred_room(_L_SHAPE, (0.5, 1.0)) == pytest.approx(1.0)


class TestLabelAnchor:
    def test_a_rect_turned_by_90_degrees_keeps_its_centre(self) -> None:
        anchor = label_anchor(RectGeometry(origin=(5.0, 5.0), width_m=4.0, length_m=1.0, rotation_deg=90.0))

        assert anchor.point == pytest.approx((4.5, 7.0), abs=0.001)
        # turned upright the 4 x 1 m bed is 1 m wide on the page
        assert anchor.width_m == pytest.approx(1.0, abs=0.001)

    def test_the_result_is_rounded_to_the_storage_precision(self) -> None:
        anchor = label_anchor(PolygonGeometry(points=_L_SHAPE))

        for value in (*anchor.point, anchor.width_m):
            assert value == round(value, 3)

    def test_the_same_geometry_gives_the_same_anchor(self) -> None:
        """GP-FR-003: deterministic - the PDF of the same plan places its names identically every time."""
        geometry = PolygonGeometry(points=_L_SHAPE)

        assert label_anchor(geometry) == label_anchor(geometry)
