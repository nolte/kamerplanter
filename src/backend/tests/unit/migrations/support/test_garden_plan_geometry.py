"""The pure derivations of migration M1 (#2323, REQ-053 §9.2a / §20.8, GP-ACC-035/036 data side)."""

from __future__ import annotations

import pytest

from app.common.enums import GeometryKind, GeometrySource
from app.migrations.support.garden_plan_geometry import (
    DEFAULT_PITCH_M,
    MIGRATED_GRID,
    effective_pitch,
    grid_cell,
    has_dimensions,
    height_from_dimensions,
    height_is_unset,
    natural_key,
    point_from_grid,
    rect_from_dimensions,
    sequence_ranks,
)


class TestLocationDimensions:
    def test_a_legacy_triple_becomes_a_rect_at_the_plan_origin_with_the_height_apart(self) -> None:
        # The frontend labels the triple "L × B × H": length along +y, width along +x (§20.1).
        rect = rect_from_dimensions([2.4, 1.2, 0.3])

        assert rect == {
            "kind": GeometryKind.RECT,
            "origin": [0.0, 0.0],
            "width_m": 1.2,
            "length_m": 2.4,
            "rotation_deg": 0.0,
        }
        assert height_from_dimensions([2.4, 1.2, 0.3]) == 0.3

    def test_the_tent_of_gp_acc_036_is_a_square(self) -> None:
        rect = rect_from_dimensions((1.2, 1.2, 2.0))

        assert rect is not None
        assert (rect["width_m"], rect["length_m"]) == (1.2, 1.2)

    def test_lengths_are_rounded_to_the_storage_precision(self) -> None:
        rect = rect_from_dimensions([1.23456, 0.98765, 0.0])

        assert rect is not None
        assert (rect["width_m"], rect["length_m"]) == (0.988, 1.235)

    @pytest.mark.parametrize("dimensions", [(0.0, 0.0, 0.0), [0, 0, 0]])
    def test_the_legacy_unset_triple_has_no_dimensions(self, dimensions: object) -> None:
        assert has_dimensions(dimensions) is False

    @pytest.mark.parametrize(
        "dimensions",
        [
            [0.0, 0.0, 2.5],  # height only: no footprint to draw (V-01 refuses a 0 m width)
            [1.2, 0.004, 0.0],  # below the 1 cm floor
            [1200.0, 1.0, 0.0],  # beyond the 1 000 m plan frame
            [1.2, 1.2],  # not a triple
            ["1.2", 1.2, 0.0],  # not numeric
            [True, 1.2, 0.0],  # a bool is not a length
            None,
        ],
    )
    def test_a_triple_v01_refuses_yields_no_geometry(self, dimensions: object) -> None:
        assert rect_from_dimensions(dimensions) is None

    def test_a_height_only_triple_still_counts_as_dimensions_and_yields_the_height(self) -> None:
        assert has_dimensions([0.0, 0.0, 2.5]) is True
        assert height_from_dimensions([0.0, 0.0, 2.5]) == 2.5

    @pytest.mark.parametrize(
        "dimensions", [[1.2, 1.2, 0.0], [1.2, 1.2, 0.004], [1.2, 1.2, -1.0], [1.2, 1.2, 1500.0], "x"]
    )
    def test_a_height_outside_a_centimetre_to_a_kilometre_is_none(self, dimensions: object) -> None:
        assert height_from_dimensions(dimensions) is None

    def test_a_zero_height_is_unset_and_a_refused_one_is_not(self) -> None:
        assert height_is_unset([1.2, 1.2, 0.0]) is True
        assert height_is_unset([1.2, 1.2, 0.004]) is False
        assert height_is_unset("x") is False


class TestSlotGrid:
    def test_the_middle_slot_of_a_three_by_three_tent_sits_at_thirty_centimetres(self) -> None:
        # GP-ACC-036: after M1 the middle slot of the 3 × 3 grid at 0.30 m is at (0.30, 0.30);
        # the 10 cm drag the criterion describes lands it on (0.40, 0.30).
        point = point_from_grid((1, 1), DEFAULT_PITCH_M)

        assert point == {"kind": GeometryKind.POINT, "origin": [0.3, 0.3]}

    def test_x_is_the_column_and_y_the_row(self) -> None:
        point = point_from_grid((2, 0), 0.25)

        assert point is not None
        assert point["origin"] == [0.0, 0.5]

    def test_the_rounding_matches_the_typescript_port(self) -> None:
        # 3 × 0.3 is 0.8999999999999999 in binary; the storage rule rounds half away from zero.
        point = point_from_grid((3, 3), 0.3)

        assert point is not None
        assert point["origin"] == [0.9, 0.9]

    def test_a_negative_cell_is_a_legal_bed_frame_coordinate(self) -> None:
        point = point_from_grid((-1, -2), 0.3)

        assert point is not None
        assert point["origin"] == [-0.6, -0.3]

    def test_a_cell_beyond_the_bed_frame_is_refused(self) -> None:
        assert point_from_grid((0, 100_000), 0.3) is None

    @pytest.mark.parametrize("position", [[0, 0], (2, 5), [1.0, 2.0]])
    def test_an_integer_pair_is_a_grid_cell(self, position: object) -> None:
        assert grid_cell(position) is not None

    @pytest.mark.parametrize("position", [None, [1], [1, 2, 3], [0.5, 1], ["1", "2"], [True, False], "a1"])
    def test_anything_else_is_not_a_grid_cell(self, position: object) -> None:
        assert grid_cell(position) is None

    def test_the_location_pitch_is_used_when_it_is_a_usable_length(self) -> None:
        assert effective_pitch(0.25) == (0.25, False)

    @pytest.mark.parametrize("pitch", [None, 0.0, -0.3, 0.004, "0.3", True, float("nan")])
    def test_otherwise_the_default_pitch_is_assumed(self, pitch: object) -> None:
        assert effective_pitch(pitch) == (DEFAULT_PITCH_M, True)

    def test_the_source_marker_is_the_enum_value(self) -> None:
        assert MIGRATED_GRID == GeometrySource.MIGRATED_GRID == "migrated_grid"


class TestSequenceRanks:
    def test_slots_are_ranked_per_location_by_row_then_column(self) -> None:
        # The spec's own example (§20.5): R2P05 in a bed of six slots per row is sequence 11.
        slots = [
            {"_key": f"r{row}p{col}", "location_key": "bed", "position": [row, col]}
            for row in (2, 1)
            for col in (6, 5, 4, 3, 2, 1)
        ]

        ranks = sequence_ranks(slots)

        assert ranks["r1p1"] == 1
        assert ranks["r1p6"] == 6
        assert ranks["r2p5"] == 11
        assert ranks["r2p6"] == 12

    def test_locations_are_ranked_independently(self) -> None:
        ranks = sequence_ranks(
            [
                {"_key": "a", "location_key": "x", "position": [0, 1]},
                {"_key": "b", "location_key": "y", "position": [0, 0]},
                {"_key": "c", "location_key": "x", "position": [0, 0]},
            ]
        )

        assert ranks == {"c": 1, "a": 2, "b": 1}

    def test_a_slot_with_an_unreadable_position_sorts_last_and_ties_break_on_the_key(self) -> None:
        ranks = sequence_ranks(
            [
                {"_key": "z", "location_key": "x", "position": None},
                {"_key": "b", "location_key": "x", "position": [0, 0]},
                {"_key": "a", "location_key": "x", "position": [0, 0]},
            ]
        )

        assert ranks == {"a": 1, "b": 2, "z": 3}

    def test_within_one_cell_the_slot_id_decides_in_natural_order_before_the_key(self) -> None:
        # The real-volume case: every slot at (0, 0). Keys are numeric strings in insertion
        # order, so a lexicographic key order would put "10234" before "9876".
        ranks = sequence_ranks(
            [
                {"_key": "10234", "slot_id": "TENT01_A10", "location_key": "x", "position": [0, 0]},
                {"_key": "9876", "slot_id": "TENT01_A1", "location_key": "x", "position": [0, 0]},
                {"_key": "9877", "slot_id": "TENT01_A2", "location_key": "x", "position": [0, 0]},
            ]
        )

        assert ranks == {"9876": 1, "9877": 2, "10234": 3}

    @pytest.mark.parametrize(
        ("lower", "higher"),
        [("BED_2", "BED_10"), ("A1", "A2"), ("A9", "B1"), ("", "A"), (None, "A"), ("R2P05", "R2P6")],
    )
    def test_the_natural_key_orders_digit_runs_numerically(self, lower: object, higher: object) -> None:
        assert natural_key(lower) < natural_key(higher)

    def test_slots_that_already_carry_a_geometry_take_part_in_the_ranking(self) -> None:
        # Ranked over every slot of the location, so an interrupted run numbers the rest the same way.
        ranks = sequence_ranks(
            [
                {"_key": "done", "location_key": "x", "position": [0, 0], "has_geometry": True},
                {"_key": "todo", "location_key": "x", "position": [0, 1], "has_geometry": False},
            ]
        )

        assert ranks == {"done": 1, "todo": 2}
