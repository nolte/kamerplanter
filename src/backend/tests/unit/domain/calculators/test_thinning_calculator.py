"""REQ-053 W-015 — how many plants a sown row or zone holds after thinning (``thinning_calculator``)."""

from __future__ import annotations

import pytest

from app.common.enums import SlotRole
from app.domain.calculators.thinning_calculator import SownMeasure, sown_measure, thinning_count, thinning_formula
from app.domain.models.geometry import PointGeometry, PolygonGeometry, PolylineGeometry, RectGeometry


def row(*points: tuple[float, float]) -> PolylineGeometry:
    return PolylineGeometry(points=points, width_m=0.05)


class TestSownMeasure:
    def test_a_row_is_measured_along_all_its_segments(self) -> None:
        measure = sown_measure(SlotRole.ROW, row((0.0, 0.0), (0.6, 0.0), (0.6, 0.8)))
        assert measure is not None
        assert measure.kind == "length"
        assert measure.value == pytest.approx(1.4)

    def test_a_zone_is_measured_by_its_area(self) -> None:
        zone = PolygonGeometry(points=((0.0, 0.0), (2.0, 0.0), (2.0, 0.5), (0.0, 0.5)))
        measure = sown_measure(SlotRole.ZONE, zone)
        assert measure == SownMeasure("area", 1.0)

    def test_a_position_slot_is_never_sown(self) -> None:
        assert sown_measure(SlotRole.POSITION, PointGeometry(origin=(0.0, 0.0))) is None

    def test_an_unplaced_slot_has_no_measure(self) -> None:
        assert sown_measure(SlotRole.ROW, None) is None

    def test_a_row_drawn_as_an_area_is_measured_by_its_area(self) -> None:
        measure = sown_measure(SlotRole.ROW, RectGeometry(origin=(0.0, 0.0), width_m=1.0, length_m=0.2))
        assert measure is not None
        assert measure.kind == "area"


class TestThinningCount:
    def test_a_row_holds_one_plant_per_spacing_along_its_length(self) -> None:
        # 1.20 m thinned to 5 cm: 24 carrots.
        assert thinning_count(SownMeasure("length", 1.2), 5.0) == 24

    def test_float_noise_does_not_lose_a_plant(self) -> None:
        # 1.0 / 0.1 is 9.999… in binary floating point; the row still holds ten.
        assert thinning_count(SownMeasure("length", 1.0), 10.0) == 10

    def test_a_zone_holds_one_plant_per_square_of_the_spacing(self) -> None:
        # 1 m² thinned to 10 cm: a 10 × 10 grid.
        assert thinning_count(SownMeasure("area", 1.0), 10.0) == 100

    def test_a_slot_smaller_than_one_spacing_keeps_one_seedling(self) -> None:
        assert thinning_count(SownMeasure("length", 0.02), 5.0) == 1

    @pytest.mark.parametrize("spacing", [0.0, -5.0])
    def test_a_spacing_that_is_not_positive_is_refused(self, spacing: float) -> None:
        with pytest.raises(ValueError, match="positive"):
            thinning_count(SownMeasure("length", 1.0), spacing)


class TestRowSpacing:
    """#2862 — a zone sown in rows or bands counts row spacing x in-row spacing, not a square grid."""

    def test_carrot_in_rows_holds_about_one_hundred_plants_per_square_metre(self) -> None:
        # The issue's example: 4 cm in the row, 25 cm between rows — 1 / (0.04 x 0.25) = 100 per m².
        assert thinning_count(SownMeasure("area", 1.0), 4.0, row_spacing_cm=25.0) == 100

    def test_without_a_row_spacing_the_zone_is_the_square_grid_estimate(self) -> None:
        # The same carrot on the square grid of its in-row spacing: 625 per m² — the overstatement #2862 names.
        assert thinning_count(SownMeasure("area", 1.0), 4.0) == 625

    def test_a_row_ignores_the_row_spacing(self) -> None:
        assert thinning_count(SownMeasure("length", 1.2), 5.0, row_spacing_cm=25.0) == 24

    def test_a_zone_smaller_than_one_cell_keeps_one_seedling(self) -> None:
        assert thinning_count(SownMeasure("area", 0.005), 4.0, row_spacing_cm=25.0) == 1

    @pytest.mark.parametrize("row_spacing", [0.0, -25.0])
    def test_a_row_spacing_that_is_not_positive_is_refused(self, row_spacing: float) -> None:
        with pytest.raises(ValueError, match="row_spacing_cm"):
            thinning_count(SownMeasure("area", 1.0), 4.0, row_spacing_cm=row_spacing)

    @pytest.mark.parametrize(
        ("measure", "row_spacing", "formula"),
        [
            (SownMeasure("length", 1.0), None, "along_row"),
            (SownMeasure("length", 1.0), 25.0, "along_row"),
            (SownMeasure("area", 1.0), 25.0, "rows"),
            (SownMeasure("area", 1.0), None, "square_grid"),
        ],
    )
    def test_the_formula_names_the_rule_the_count_applied(self, measure, row_spacing, formula) -> None:
        assert thinning_formula(measure, row_spacing) == formula
