"""REQ-053 WP 8.14 (#2657) - the feeder cycle of the follow-up crop recommendation (GP-FR-133, §16.3).

Pinned as a table: previous year -> next step. The engine decides the order only; a missing level is reported, never
defaulted, and a species qualifies only by its own stored level.
"""

from __future__ import annotations

import pytest

from app.common.enums import NutrientDemand
from app.domain.engines.crop_rotation_validator import TimelineEntry
from app.domain.engines.succession_recommendation_engine import (
    basis_family_keys,
    pause_held_back,
    planting_year,
    previous_year,
    species_fits,
    target_after,
)
from tests.support.rotation_fakes import make_species


def row(year: int, family: str | None, demand: str | None, role: str = "main_crop") -> TimelineEntry:
    return TimelineEntry(year, None, family, family, None, demand, role, "plant")


class TestTheCycle:
    @pytest.mark.parametrize(
        ("rows", "target"),
        [
            ([row(2025, "sol", "heavy_feeder")], "medium_feeder"),
            ([row(2025, "api", "medium_feeder")], "light_feeder"),
            ([row(2025, "fab", "light_feeder")], "restoring"),
            ([row(2025, "fab", None, "green_manure")], "heavy_feeder"),
            ([row(2025, None, None, "fallow")], "heavy_feeder"),
        ],
    )
    def test_previous_year_to_next_step(self, rows, target) -> None:
        previous = previous_year(rows)
        assert previous is not None
        assert target_after(previous) == target

    def test_the_strongest_feeder_of_a_mixed_year_sets_the_step(self) -> None:
        previous = previous_year([row(2025, "fab", "light_feeder"), row(2025, "sol", "heavy_feeder")])
        assert previous is not None and previous.nutrient_demand == "heavy_feeder"
        assert target_after(previous) == "medium_feeder"

    def test_a_green_manure_beside_a_main_crop_does_not_make_the_year_a_restoring_one(self) -> None:
        previous = previous_year([row(2025, "sol", "heavy_feeder"), row(2025, "fab", None, "green_manure")])
        assert previous is not None and previous.step == "main_crop"
        assert previous.family_keys == ("sol", "fab")

    def test_the_latest_year_decides(self) -> None:
        previous = previous_year([row(2023, "sol", "heavy_feeder"), row(2025, "fab", "light_feeder")])
        assert previous is not None and previous.year == 2025
        assert target_after(previous) == "restoring"

    def test_a_main_crop_without_a_stated_level_gives_no_step_and_no_default(self) -> None:
        previous = previous_year([row(2025, "ghost", None)])
        assert previous is not None
        assert target_after(previous) is None

    def test_no_rows_no_previous_year(self) -> None:
        assert previous_year([]) is None


class TestSpeciesAndPauses:
    def test_a_species_fits_only_by_its_own_stored_level(self) -> None:
        medium = make_species("a", "f", nutrient_demand=NutrientDemand.MEDIUM_FEEDER)
        unstated = make_species("b", "f")
        assert species_fits(medium, "medium_feeder") is True
        assert species_fits(medium, "light_feeder") is False
        assert species_fits(unstated, "medium_feeder") is False  # no silent default
        assert species_fits(unstated, "heavy_feeder") is False

    def test_the_restoring_step_takes_green_manure_species_whatever_their_level(self) -> None:
        clover = make_species("c", "f", green_manure_suitable=True)
        bean = make_species("d", "f", nutrient_demand=NutrientDemand.LIGHT_FEEDER)
        assert species_fits(clover, "restoring") is True
        assert species_fits(bean, "restoring") is False

    @pytest.mark.parametrize(
        ("last", "pause", "held"),
        [(2024, 4, True), (2022, 4, False), (2023, 3, False), (2024, 3, True), (None, 4, False), (2025, None, False)],
    )
    def test_a_family_is_held_back_only_with_a_known_unfinished_pause(self, last, pause, held) -> None:
        assert pause_held_back(last, pause, 2026) is held


class TestBasisAndYear:
    def test_after_a_main_crop_the_candidates_come_from_that_years_families(self) -> None:
        rows = [row(2025, "sol", "heavy_feeder")]
        previous = previous_year(rows)
        assert previous is not None
        assert basis_family_keys(rows, previous) == ("sol",)

    def test_after_a_green_manure_they_come_from_the_latest_crop_not_from_the_cover(self) -> None:
        rows = [row(2024, "sol", "heavy_feeder"), row(2025, "fab", None, "green_manure")]
        previous = previous_year(rows)
        assert previous is not None and previous.step == "restoring"
        assert basis_family_keys(rows, previous) == ("sol",)

    def test_a_bed_that_only_ever_had_a_cover_keeps_the_cover_families(self) -> None:
        rows = [row(2025, "fab", None, "green_manure")]
        previous = previous_year(rows)
        assert previous is not None
        assert basis_family_keys(rows, previous) == ("fab",)

    @pytest.mark.parametrize(("last", "year"), [(2023, 2026), (2025, 2026), (2026, 2027)])
    def test_the_recommendation_is_for_this_year_or_the_next_when_this_one_is_recorded(self, last, year) -> None:
        previous = previous_year([row(last, "sol", "heavy_feeder")])
        assert previous is not None
        assert planting_year(previous, 2026) == year
