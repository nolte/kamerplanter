"""REQ-053 WP 3.1 — the planting layout beyond the shared vectors (GP-FR-060/062/073).

The vectors pin concrete layouts; this file pins the rules around them: the axes, the pre-estimate that
refuses before a point exists, the properties every layout must have (inside the bed, ordered, no duplicates)
and the entry fields.
"""

from __future__ import annotations

import math
import time

import pytest
from pydantic import ValidationError

from app.common.enums import DepthKind, LayoutStrategy, PlacementHint, RowDirection, SlotRole
from app.common.exceptions import PlanError
from app.domain.calculators.planting_layout_calculator import (
    MAX_LAYOUT_POSITIONS,
    EntryLayout,
    compute_layout,
    estimate_positions,
)
from app.domain.calculators.slot_capacity_calculator import calculate_plants_per_m2
from app.domain.models.geometry import parse_geometry
from app.domain.models.planting_run import PlantingRunEntry


def rect(width: float, length: float, rotation: float = 0.0):
    return parse_geometry(
        {"kind": "rect", "origin": [1.0, 1.0], "width_m": width, "length_m": length, "rotation_deg": rotation}
    )


def rows(**kw) -> EntryLayout:
    return EntryLayout(LayoutStrategy.ROWS, **{"spacing_cm": 30, "row_spacing_cm": 40, **kw})


def code(raised: pytest.ExceptionInfo[PlanError]) -> str:
    return raised.value.details[0]["code"]


class TestAxes:
    def test_along_length_follows_the_longer_side_and_along_width_the_shorter(self) -> None:
        tall = rect(1.2, 3.0)  # 1.2 wide (x), 3.0 long (y)
        along_length = compute_layout(tall, rows(edge_margin_along_cm=15, edge_margin_across_cm=15))
        along_width = compute_layout(
            tall, rows(row_direction=RowDirection.ALONG_WIDTH, edge_margin_along_cm=15, edge_margin_across_cm=15)
        )
        # Rows along y share one x per row; rows along x share one y per row.
        assert len({s.point[0] for s in along_length.slots if s.point and s.row_index == 0}) == 1
        assert len({s.point[1] for s in along_width.slots if s.point and s.row_index == 0}) == 1

    def test_a_square_bed_runs_along_the_x_axis(self) -> None:
        result = compute_layout(rect(1.0, 1.0), rows())
        assert len({s.point[1] for s in result.slots if s.point and s.row_index == 0}) == 1

    def test_the_layout_does_not_depend_on_where_or_how_the_bed_lies_on_the_plan(self) -> None:
        plain = compute_layout(rect(3.0, 1.2), rows())
        turned = compute_layout(rect(3.0, 1.2, rotation=123.0), rows())
        assert [s.point for s in turned.slots] == [s.point for s in plain.slots]


class TestStrategies:
    def test_grid_uses_the_spacing_as_row_spacing(self) -> None:
        grid = compute_layout(rect(2.0, 2.0), EntryLayout(LayoutStrategy.GRID, spacing_cm=50))
        explicit = compute_layout(
            rect(2.0, 2.0), rows(spacing_cm=50, row_spacing_cm=50, edge_margin_along_cm=25, edge_margin_across_cm=25)
        )
        assert [s.point for s in grid.slots] == [s.point for s in explicit.slots]

    def test_triangular_derives_the_row_spacing_and_shifts_every_second_row(self) -> None:
        result = compute_layout(rect(2.0, 1.0), EntryLayout(LayoutStrategy.TRIANGULAR, spacing_cm=40))
        first = [s.point for s in result.slots if s.row_index == 0]
        second = [s.point for s in result.slots if s.row_index == 1]
        assert second[0][0] - first[0][0] == pytest.approx(0.2)
        assert second[0][1] - first[0][1] == pytest.approx(0.4 * 0.866, abs=0.001)

    def test_triangular_packs_more_than_a_grid_of_the_same_spacing(self) -> None:
        bed = rect(3.0, 3.0)
        grid = compute_layout(
            bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=30, edge_margin_along_cm=0, edge_margin_across_cm=0)
        )
        tri = compute_layout(
            bed, EntryLayout(LayoutStrategy.TRIANGULAR, spacing_cm=30, edge_margin_along_cm=0, edge_margin_across_cm=0)
        )
        assert tri.capacity_max > grid.capacity_max

    def test_free_places_nothing_and_reports_the_capacity(self) -> None:
        result = compute_layout(rect(3.0, 1.2), EntryLayout(LayoutStrategy.FREE, spacing_cm=60))
        assert (result.slots, result.count, result.capacity_max) == ([], 0, 10)

    def test_a_zone_is_one_slot_whose_capacity_is_the_count(self) -> None:
        result = compute_layout(rect(3.0, 1.2), EntryLayout(LayoutStrategy.ZONE, spacing_cm=10), max_count=100)
        (zone,) = result.slots
        assert zone.slot_role is SlotRole.ZONE
        assert (zone.capacity_plants, result.count, result.capacity_max) == (100, 100, 360)

    def test_a_zone_margin_insets_a_rectangle(self) -> None:
        result = compute_layout(
            rect(3.0, 1.2),
            EntryLayout(LayoutStrategy.ZONE, spacing_cm=10, edge_margin_along_cm=10, edge_margin_across_cm=10),
        )
        (zone,) = result.slots
        assert zone.outline == ((0.1, 0.1), (2.9, 0.1), (2.9, 1.1), (0.1, 1.1))
        assert result.capacity_max == 280


class TestInsetIsDistanceToTheEdge:
    def test_every_position_keeps_its_margin_from_every_side_of_a_rectangle(self) -> None:
        result = compute_layout(
            rect(2.0, 1.6), rows(spacing_cm=40, row_spacing_cm=50, edge_margin_along_cm=30, edge_margin_across_cm=40)
        )
        for slot in result.slots:
            x, y = slot.point
            assert 0.3 - 1e-9 <= x <= 2.0 - 0.3 + 1e-9
            assert 0.4 - 1e-9 <= y <= 1.6 - 0.4 + 1e-9

    def test_a_circle_keeps_the_whole_margin_box_inside_the_disc(self) -> None:
        bed = parse_geometry({"kind": "circle", "origin": [5.0, 5.0], "radius_m": 1.0})
        result = compute_layout(bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=30))
        assert result.count > 0
        for slot in result.slots:
            x, y = slot.point
            assert math.hypot(abs(x) + 0.15, abs(y) + 0.15) <= 1.0 + 1e-6

    def test_a_polygon_position_never_leaves_the_polygon(self) -> None:
        bed = parse_geometry({"kind": "polygon", "points": [[0, 0], [4, 0], [0, 3]]})
        result = compute_layout(
            bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=40, edge_margin_along_cm=10, edge_margin_across_cm=10)
        )
        for slot in result.slots:
            x, y = slot.point
            assert x >= 0.1 - 1e-9 and y >= 0.1 - 1e-9
            # distance to the hypotenuse 3x + 4y = 12 is (12 - 3x - 4y) / 5
            assert (12 - 3 * x - 4 * y) / 5 >= 0.1 - 1e-6


class TestRowAssignmentAndMaxCount:
    def test_rows_not_assigned_to_the_entry_stay_free_for_another(self) -> None:
        bed = rect(3.0, 1.2)
        entry = rows(edge_margin_along_cm=15, edge_margin_across_cm=15)
        everything = compute_layout(bed, entry)
        mine = compute_layout(bed, rows(edge_margin_along_cm=15, edge_margin_across_cm=15, row_assignment=(1,)))
        assert {s.row_index for s in mine.slots} == {1}
        assert mine.count == everything.count // 3

    def test_max_count_keeps_the_first_positions_in_layout_order(self) -> None:
        bed = rect(3.0, 1.2)
        full = compute_layout(bed, rows())
        part = compute_layout(bed, rows(), max_count=5)
        assert [s.point for s in part.slots] == [s.point for s in full.slots][:5]
        assert [s.sequence for s in part.slots] == [1, 2, 3, 4, 5]
        assert part.capacity_max == full.capacity_max

    def test_a_larger_max_count_changes_nothing(self) -> None:
        full = compute_layout(rect(1.0, 1.0), rows(spacing_cm=50, row_spacing_cm=50))
        assert compute_layout(rect(1.0, 1.0), rows(spacing_cm=50, row_spacing_cm=50), max_count=999).count == full.count


class TestWarnings:
    def test_spacing_below_seventy_percent_of_the_mature_width_warns(self) -> None:
        bed = rect(1.0, 1.0)
        below = compute_layout(bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=34, mature_width_cm=50))
        at_limit = compute_layout(bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=35, mature_width_cm=50))
        assert [w.code for w in below.warnings] == ["layout.spacing_below_mature_width"]
        assert at_limit.warnings == []

    def test_nothing_fitting_is_a_warning_not_an_error(self) -> None:
        result = compute_layout(rect(0.2, 0.2), EntryLayout(LayoutStrategy.GRID, spacing_cm=50))
        assert (result.count, result.capacity_max, [w.code for w in result.warnings]) == (
            0,
            0,
            ["layout.no_position_fits"],
        )

    def test_v07_rows_closer_than_the_spacing_are_a_hint(self) -> None:
        result = compute_layout(rect(1.2, 1.2), rows(spacing_cm=40, row_spacing_cm=20))
        assert "planting.spacing_below_minimum" in [w.code for w in result.warnings]

    def test_a_regular_grid_raises_no_v07_hint(self) -> None:
        result = compute_layout(rect(2.0, 2.0), EntryLayout(LayoutStrategy.GRID, spacing_cm=30))
        assert result.warnings == []


class TestTheUpperBound:
    def test_the_estimate_is_area_over_spacing_times_row_spacing(self) -> None:
        assert estimate_positions(rect(3.0, 1.2), rows()) == 30
        assert estimate_positions(rect(3.0, 1.2), EntryLayout(LayoutStrategy.TRIANGULAR, spacing_cm=30)) == math.floor(
            3.6 / (0.3 * 0.3 * 0.866) + 1e-6
        )

    def test_more_than_2000_estimated_positions_is_refused_with_the_estimate(self) -> None:
        with pytest.raises(PlanError) as raised:
            compute_layout(rect(5.01, 1.0), EntryLayout(LayoutStrategy.GRID, spacing_cm=5))
        detail = raised.value.details[0]
        assert (raised.value.status_code, detail["code"], detail["estimated"], detail["limit"]) == (
            422,
            "layout.too_many_positions",
            2004,
            MAX_LAYOUT_POSITIONS,
        )

    def test_the_estimate_runs_before_any_point_is_generated(self) -> None:
        field = parse_geometry({"kind": "rect", "origin": [0, 0], "width_m": 1000, "length_m": 1000})
        started = time.perf_counter()
        with pytest.raises(PlanError):
            compute_layout(field, EntryLayout(LayoutStrategy.GRID, spacing_cm=5))
        assert time.perf_counter() - started < 0.05

    def test_a_full_layout_of_2000_positions_stays_fast(self) -> None:
        started = time.perf_counter()
        result = compute_layout(
            rect(5.0, 1.0),
            EntryLayout(LayoutStrategy.GRID, spacing_cm=10, edge_margin_along_cm=0, edge_margin_across_cm=0),
        )
        assert result.count == 51 * 11
        assert time.perf_counter() - started < 1.0

    def test_the_result_never_exceeds_the_limit(self) -> None:
        # The estimate says 2000, not above the limit; the margin-free grid has 2121 points, the real count refuses it.
        with pytest.raises(PlanError) as raised:
            compute_layout(
                rect(5.0, 1.0),
                EntryLayout(LayoutStrategy.GRID, spacing_cm=5, edge_margin_along_cm=0, edge_margin_across_cm=0),
            )
        assert code(raised) == "layout.too_many_positions"

    def test_a_sliver_does_not_walk_a_huge_bounding_box(self) -> None:
        bed = parse_geometry({"kind": "polygon", "points": [[0, 0], [100, 100], [100, 100.2]]})
        started = time.perf_counter()
        with pytest.raises(PlanError) as raised:
            compute_layout(bed, EntryLayout(LayoutStrategy.GRID, spacing_cm=20))
        assert code(raised) == "layout.too_many_positions"
        assert time.perf_counter() - started < 0.05


class TestRowAssignmentIsBoundedByTheRealCount:
    def test_an_entry_taking_one_row_is_not_refused_by_the_whole_area_estimate(self) -> None:
        bed = rect(8.0, 1.0)
        everything = EntryLayout(
            LayoutStrategy.ROWS, spacing_cm=5, row_spacing_cm=5, edge_margin_along_cm=0, edge_margin_across_cm=0
        )
        with pytest.raises(PlanError):
            compute_layout(bed, everything)
        one_row = EntryLayout(
            LayoutStrategy.ROWS,
            spacing_cm=5,
            row_spacing_cm=5,
            edge_margin_along_cm=0,
            edge_margin_across_cm=0,
            row_assignment=(0,),
        )
        assert compute_layout(bed, one_row).count == 161

    def test_a_huge_bed_is_still_refused_with_a_row_assignment(self) -> None:
        field = parse_geometry({"kind": "rect", "origin": [0, 0], "width_m": 1000, "length_m": 1000})
        started = time.perf_counter()
        with pytest.raises(PlanError) as raised:
            compute_layout(field, EntryLayout(LayoutStrategy.GRID, spacing_cm=5, row_assignment=(0,)))
        assert code(raised) == "layout.too_many_positions"
        assert time.perf_counter() - started < 0.05


class TestZoneCapacity:
    def test_a_circular_zone_agrees_with_the_free_estimate_of_the_same_bed(self) -> None:
        bed = parse_geometry({"kind": "circle", "origin": [5.0, 5.0], "radius_m": 2.0})
        zone = compute_layout(bed, EntryLayout(LayoutStrategy.ZONE, spacing_cm=7))
        free = compute_layout(bed, EntryLayout(LayoutStrategy.FREE, spacing_cm=7))
        assert zone.capacity_max == free.capacity_max


class TestRefusals:
    @pytest.mark.parametrize("spacing", [0, 4.99, 1500.01, -3])
    def test_a_spacing_outside_5_to_1500_cm_is_refused(self, spacing: float) -> None:
        with pytest.raises(PlanError) as raised:
            compute_layout(rect(1.0, 1.0), EntryLayout(LayoutStrategy.GRID, spacing_cm=spacing))
        assert code(raised) == "layout.spacing_out_of_range"

    def test_rows_need_a_row_spacing(self) -> None:
        with pytest.raises(PlanError) as raised:
            compute_layout(rect(1.0, 1.0), EntryLayout(LayoutStrategy.ROWS, spacing_cm=30))
        assert code(raised) == "layout.row_spacing_required"

    def test_a_row_spacing_outside_the_range_is_refused(self) -> None:
        with pytest.raises(PlanError) as raised:
            compute_layout(rect(1.0, 1.0), rows(row_spacing_cm=2))
        assert code(raised) == "layout.spacing_out_of_range"

    def test_a_polyline_is_no_bed(self) -> None:
        with pytest.raises(PlanError) as raised:
            compute_layout(parse_geometry({"kind": "polyline", "points": [[0, 0], [3, 0]], "width_m": 0.5}), rows())
        assert code(raised) == "layout.bed_not_an_area"


class TestCapacityAgreesWithTheDensityCalculator:
    """GP-FR-073: the capacity display takes the count from the layout; far from the edges both agree."""

    @pytest.mark.parametrize(
        ("strategy", "spacing", "row_spacing"),
        [(LayoutStrategy.GRID, 25, None), (LayoutStrategy.ROWS, 30, 60), (LayoutStrategy.TRIANGULAR, 20, None)],
    )
    def test_a_large_bed_approaches_the_density(
        self, strategy: LayoutStrategy, spacing: float, row_spacing: float | None
    ) -> None:
        bed = rect(8.0, 6.0)
        entry = EntryLayout(
            strategy, spacing_cm=spacing, row_spacing_cm=row_spacing, edge_margin_along_cm=0, edge_margin_across_cm=0
        )
        density = calculate_plants_per_m2(spacing, row_spacing, strategy)
        count = compute_layout(bed, entry).capacity_max
        # Positions on the closed edges add one row/column each side: the layout is at least the density.
        assert count >= math.floor(48.0 * density) * 0.95


class TestPlantingRunEntryLayoutFields:
    base = {"species_key": "sp1", "quantity": 3, "id_prefix": "TOM"}

    def test_the_layout_fields_are_optional(self) -> None:
        entry = PlantingRunEntry(**self.base)
        assert entry.layout_strategy is None and entry.row_spacing_cm is None and entry.row_assignment is None

    def test_a_full_layout_parses(self) -> None:
        entry = PlantingRunEntry(
            **self.base,
            spacing_cm=60,
            row_spacing_cm=80,
            row_direction="along_length",
            edge_margin_along_cm=30,
            edge_margin_across_cm=40,
            depth_cm=10,
            depth_kind="planting",
            sowing_spacing_cm=5,
            thinning_to_cm=20,
            layout_strategy="rows",
            placement_hint="interior",
            row_assignment=[0, 2],
        )
        assert entry.row_direction is RowDirection.ALONG_LENGTH
        assert entry.depth_kind is DepthKind.PLANTING
        assert entry.layout_strategy is LayoutStrategy.ROWS
        assert entry.placement_hint is PlacementHint.INTERIOR

    def test_a_stored_spacing_above_1500_cm_still_loads(self) -> None:
        """The 1 500 cm bound is the API's (``EntryCreate``); a row stored before it must keep loading."""
        assert PlantingRunEntry(**self.base, spacing_cm=2000).spacing_cm == 2000

    def test_the_api_allows_1500_cm_for_woody_plants_and_refuses_more(self) -> None:
        from app.api.v1.planting_runs.schemas import EntryCreate, EntryUpdate

        assert EntryCreate(**self.base, spacing_cm=1500).spacing_cm == 1500
        for schema in (EntryCreate, EntryUpdate):
            with pytest.raises(ValidationError):
                schema(**self.base, spacing_cm=1501)

    @pytest.mark.parametrize("assignment", [[-1], [0, 0]])
    def test_the_api_refuses_a_bad_row_assignment_instead_of_failing_later(self, assignment: list[int]) -> None:
        """Validated at the request, not only in the domain model: a model error after parsing is a 500."""
        from app.api.v1.planting_runs.schemas import EntryCreate, EntryUpdate

        for schema in (EntryCreate, EntryUpdate):
            with pytest.raises(ValidationError):
                schema(**self.base, row_assignment=assignment)

    @pytest.mark.parametrize(
        "field",
        [
            {"row_spacing_cm": 4},
            {"row_spacing_cm": 1501},
            {"edge_margin_along_cm": -1},
            {"edge_margin_across_cm": 201},
            {"depth_cm": 101},
            {"sowing_spacing_cm": 0},
            {"thinning_to_cm": 1501},
            {"row_direction": "diagonal"},
            {"layout_strategy": "spiral"},
            {"row_assignment": [0, 0]},
            {"row_assignment": [-1]},
        ],
    )
    def test_out_of_range_layout_fields_are_refused(self, field: dict) -> None:
        with pytest.raises(ValidationError):
            PlantingRunEntry(**self.base, **field)
