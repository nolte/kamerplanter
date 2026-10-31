"""Edge cases of the label anchor (REQ-053 GP-UX-047, #2490) that the shared vectors do not need to carry."""

from __future__ import annotations

import pytest

from app.domain.calculators.geometry_calculator import point_in_polygon, signed_distance_to_polygon
from app.domain.calculators.label_anchor_calculator import (
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
