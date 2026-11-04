"""Site settings for the sun classes and the reach, and the orientation a bed's aspect derives (WP 8.24, #2667).

REQ-053 GP-FR-164 (sun-class bounds and reference day, RHS defaults > 6 h / 3-6 h / 2-3 h / < 2 h on 21 June),
GP-FR-166 (reach 1.2 m from two opposite sides, 0.6 m from one), GP-FR-017/168 (orientation from ``aspect_deg``).
"""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from app.common.enums import Orientation
from app.domain.calculators.reach_calculator import REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M
from app.domain.models.site import Location, ReachThresholds, Site, SunClassThresholds


class TestSunClassThresholds:
    def test_the_defaults_are_the_rhs_classes_on_21_june(self) -> None:
        defaults = SunClassThresholds()

        assert (defaults.full_sun_min_hours, defaults.partial_shade_min_hours, defaults.shade_min_hours) == (6, 3, 2)
        assert (defaults.reference_month, defaults.reference_day) == (6, 21)

    def test_other_descending_bounds_are_taken(self) -> None:
        custom = SunClassThresholds(full_sun_min_hours=8, partial_shade_min_hours=4.5, shade_min_hours=1.5)

        assert (custom.full_sun_min_hours, custom.partial_shade_min_hours, custom.shade_min_hours) == (8, 4.5, 1.5)

    @pytest.mark.parametrize("field", ["full_sun_min_hours", "partial_shade_min_hours", "shade_min_hours"])
    @pytest.mark.parametrize("value", [0, -1, -0.5])
    def test_a_bound_of_zero_or_less_is_refused(self, field: str, value: float) -> None:
        """``shade_min_hours`` reaches ``> 0`` alone; for the other two the ordering rule refuses as well."""
        with pytest.raises(ValidationError):
            SunClassThresholds(**{field: value})

    @pytest.mark.parametrize("value", [math.nan, math.inf, 24.5])
    def test_a_bound_that_is_no_hour_count_of_a_day_is_refused(self, value: float) -> None:
        with pytest.raises(ValidationError):
            SunClassThresholds(full_sun_min_hours=value)

    @pytest.mark.parametrize(
        "bounds",
        [
            {"full_sun_min_hours": 3, "partial_shade_min_hours": 6, "shade_min_hours": 2},
            {"full_sun_min_hours": 6, "partial_shade_min_hours": 2, "shade_min_hours": 3},
            {"full_sun_min_hours": 6, "partial_shade_min_hours": 6, "shade_min_hours": 2},
            {"full_sun_min_hours": 6, "partial_shade_min_hours": 3, "shade_min_hours": 3},
        ],
    )
    def test_bounds_that_are_not_strictly_descending_are_refused(self, bounds: dict[str, float]) -> None:
        with pytest.raises(ValidationError, match="strictly descending"):
            SunClassThresholds(**bounds)

    @pytest.mark.parametrize(("month", "day"), [(2, 30), (4, 31), (13, 1), (0, 1), (6, 0)])
    def test_a_reference_day_that_does_not_exist_is_refused(self, month: int, day: int) -> None:
        with pytest.raises(ValidationError):
            SunClassThresholds(reference_month=month, reference_day=day)

    def test_29_february_is_a_valid_reference_day(self) -> None:
        assert SunClassThresholds(reference_month=2, reference_day=29).reference_day == 29


class TestReachThresholds:
    def test_the_defaults_are_the_confirmed_reach_values(self) -> None:
        defaults = ReachThresholds()

        assert (defaults.both_sides_m, defaults.one_side_m) == (REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M) == (1.2, 0.6)

    @pytest.mark.parametrize("field", ["both_sides_m", "one_side_m"])
    @pytest.mark.parametrize("value", [0, -0.6, math.nan, math.inf])
    def test_a_threshold_of_zero_or_less_is_refused(self, field: str, value: float) -> None:
        with pytest.raises(ValidationError):
            ReachThresholds(**{field: value})

    def test_one_side_may_not_reach_farther_than_two(self) -> None:
        with pytest.raises(ValidationError, match="one_side_m must not exceed both_sides_m"):
            ReachThresholds(both_sides_m=1.0, one_side_m=1.1)

    def test_equal_thresholds_are_taken(self) -> None:
        assert ReachThresholds(both_sides_m=0.8, one_side_m=0.8).one_side_m == 0.8


class TestTheSiteCarriesThem:
    def test_a_stored_site_without_them_stays_valid_and_reads_the_defaults(self) -> None:
        """Sites stored before WP 8.24 hold neither field: no migration, the defaults apply."""
        site = Site.model_validate({"_key": "s1", "tenant_key": "t1", "name": "Garten", "type": "outdoor"})

        assert site.sun_class_thresholds is None and site.reach_thresholds is None
        assert site.effective_sun_class_thresholds == SunClassThresholds()
        assert site.effective_reach_thresholds == ReachThresholds()

    def test_stored_values_win_over_the_defaults(self) -> None:
        site = Site(
            name="Garten",
            sun_class_thresholds={"full_sun_min_hours": 7, "partial_shade_min_hours": 4, "shade_min_hours": 1},
            reach_thresholds={"both_sides_m": 1.5, "one_side_m": 0.8},
        )

        assert site.effective_sun_class_thresholds.full_sun_min_hours == 7
        assert site.effective_reach_thresholds.both_sides_m == 1.5


def _bed(**fields: object) -> Location:
    return Location.model_validate({"_key": "bed", "name": "Beet", "site_key": "s1", "area_m2": 2.0, **fields})


class TestOrientationFromAspect:
    @pytest.mark.parametrize(
        ("aspect", "expected"),
        [
            (0.0, "north"),
            (22.5, "northeast"),
            (135.0, "southeast"),
            (200.0, "south"),
            (250.0, "west"),
            (359.9, "north"),
        ],
    )
    def test_a_set_aspect_derives_the_orientation(self, aspect: float, expected: str) -> None:
        assert _bed(site_conditions={"aspect_deg": aspect}).orientation == expected

    def test_the_aspect_wins_over_a_manually_set_orientation(self) -> None:
        bed = _bed(orientation="north", site_conditions={"aspect_deg": 180.0})

        assert bed.orientation is Orientation.SOUTH

    @pytest.mark.parametrize("conditions", [None, {}, {"aspect_deg": None}, {"slope_deg": 10.0}])
    def test_without_an_aspect_the_manual_orientation_is_never_touched(self, conditions: object) -> None:
        assert _bed(orientation="west", site_conditions=conditions).orientation is Orientation.WEST
        assert _bed(site_conditions=conditions).orientation is None

    def test_a_stored_document_with_the_old_four_values_still_reads(self) -> None:
        for value in ("north", "south", "east", "west"):
            assert _bed(orientation=value).orientation == value

    def test_an_aspect_outside_the_turn_is_refused_at_the_model(self) -> None:
        with pytest.raises(ValidationError):
            _bed(site_conditions={"aspect_deg": 360.0})
