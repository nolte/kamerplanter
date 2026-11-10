"""REQ-053 WP 10.11 (#2832, W-016.6, V-23) - the light-schedule hint of a tent or shelf level, as a pure rule."""

from __future__ import annotations

import pytest

from app.domain.engines.adjacency_engine import effective_adjacency_factor
from app.domain.engines.tent_rules_engine import (
    PHOTOPERIOD_SHARED_LOCATION_TYPES,
    photoperiod_groups,
    photoperiod_hints,
)
from app.domain.models.site import DEFAULT_ADJACENCY_FACTOR
from app.domain.models.tent_hint import HINT_PHOTOPERIOD_CONFLICT, HINT_PHOTOPERIOD_UNKNOWN, PlantPhotoperiod


def plant(key: str, hours: float | None, phase: str | None = None) -> PlantPhotoperiod:
    return PlantPhotoperiod(plant_key=key, phase_name=phase, photoperiod_hours=hours)


class TestPhotoperiodHints:
    def test_two_photoperiods_in_a_tent_are_a_conflict(self) -> None:
        (hint,) = photoperiod_hints("tent", [plant("a", 18, "Vegetative"), plant("b", 12, "Flowering")])

        assert (hint.code, hint.severity, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_CONFLICT, "warning", 0)
        assert [g.photoperiod_hours for g in hint.groups] == [18.0, 12.0]

    def test_a_shelf_level_has_one_schedule_as_well(self) -> None:
        assert photoperiod_hints("shelf", [plant("a", 18), plant("b", 12)])

    @pytest.mark.parametrize("type_key", ["bed", "raised_bed", "room", "greenhouse", ""])
    def test_a_location_without_its_own_schedule_has_no_hint(self, type_key: str) -> None:
        assert photoperiod_hints(type_key, [plant("a", 18), plant("b", 12)]) == []

    def test_one_photoperiod_is_no_conflict(self) -> None:
        assert photoperiod_hints("tent", [plant("a", 12), plant("b", 12.0), plant("c", 12)]) == []

    def test_values_closer_than_a_timer_step_are_one_photoperiod(self) -> None:
        assert photoperiod_hints("tent", [plant("a", 18.0), plant("b", 18.1)]) == []

    def test_unknown_photoperiods_never_count_as_a_conflict(self) -> None:
        (hint,) = photoperiod_hints("tent", [plant("a", 18), plant("b", None), plant("c", None)])

        assert (hint.code, hint.severity, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_UNKNOWN, "info", 2)

    def test_a_conflict_still_names_the_unknown_ones(self) -> None:
        (hint,) = photoperiod_hints("tent", [plant("a", 18), plant("b", 12), plant("c", None)])

        assert (hint.code, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_CONFLICT, 1)

    def test_a_single_plant_has_nothing_to_share(self) -> None:
        assert photoperiod_hints("tent", [plant("a", None)]) == []
        assert photoperiod_hints("tent", []) == []

    def test_groups_carry_counts_and_sorted_phase_names(self) -> None:
        groups = photoperiod_groups(
            [plant("a", 18, "Vegetative"), plant("b", 18, "Seedling"), plant("c", 18), plant("d", 12, "Flowering")]
        )

        assert [(g.photoperiod_hours, g.plant_count, g.phase_names) for g in groups] == [
            (18.0, 3, ("Seedling", "Vegetative")),
            (12.0, 1, ("Flowering",)),
        ]

    def test_the_shared_types_are_tent_and_shelf(self) -> None:
        assert frozenset({"tent", "shelf"}) == PHOTOPERIOD_SHARED_LOCATION_TYPES


class TestEffectiveAdjacencyFactor:
    def test_the_location_factor_wins(self) -> None:
        assert effective_adjacency_factor(2.0, 1.2) == 2.0

    def test_without_one_the_site_factor_applies(self) -> None:
        assert effective_adjacency_factor(None, 1.2) == 1.2

    def test_without_both_the_default_applies(self) -> None:
        assert effective_adjacency_factor(None, None) == DEFAULT_ADJACENCY_FACTOR
