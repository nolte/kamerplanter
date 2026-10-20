"""REQ-053 WP 7.9 (#2475) - putting a template's bed-frame geometry on the plan."""

from __future__ import annotations

import pytest

from app.domain.calculators.template_placement_calculator import place_geometry
from app.domain.models.geometry import PointGeometry, parse_geometry


def _geo(raw: dict):
    return parse_geometry(raw)


class TestRect:
    def test_the_anchor_lands_on_the_origin_and_the_size_is_kept(self) -> None:
        placed = place_geometry(
            _geo({"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}),
            origin=(4.0, 1.5),
            rotation_deg=0,
        )

        assert placed == {
            "kind": "rect",
            "origin": [4.0, 1.5],
            "width_m": 2.0,
            "length_m": 1.0,
            "rotation_deg": 0.0,
        }

    def test_the_requested_rotation_is_added_to_the_templates_own(self) -> None:
        placed = place_geometry(
            _geo({"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 300}),
            origin=(1, 1),
            rotation_deg=90,
        )

        assert placed["rotation_deg"] == 30.0

    def test_a_turn_that_rounds_to_a_full_circle_wraps_to_zero(self) -> None:
        placed = place_geometry(
            _geo({"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 359.9996}),
            origin=(1, 1),
            rotation_deg=0,
        )

        assert placed["rotation_deg"] == 0.0


class TestCircle:
    def test_the_centre_lands_on_the_origin_and_a_rotation_changes_nothing(self) -> None:
        raw = {"kind": "circle", "origin": [0, 0], "radius_m": 0.2}

        assert place_geometry(_geo(raw), origin=(3, 3), rotation_deg=0) == place_geometry(
            _geo(raw), origin=(3, 3), rotation_deg=123
        )
        assert place_geometry(_geo(raw), origin=(3, 3), rotation_deg=0) == {
            "kind": "circle",
            "origin": [3, 3],
            "radius_m": 0.2,
        }


class TestPolygon:
    def test_the_first_vertex_is_the_anchor_and_the_other_vertices_keep_their_offsets(self) -> None:
        polygon = _geo({"kind": "polygon", "points": [[1, 1], [3, 1], [3, 2], [1, 2]], "rotation_deg": 0})

        placed = place_geometry(polygon, origin=(10, 10), rotation_deg=45)

        assert placed["points"] == [[10, 10], [12, 10], [12, 11], [10, 11]]
        assert placed["rotation_deg"] == 45.0


def test_a_shape_that_is_no_bed_is_refused() -> None:
    with pytest.raises(ValueError, match="rect, circle or polygon"):
        place_geometry(PointGeometry(origin=(1.0, 1.0)), origin=(1, 1), rotation_deg=0)
