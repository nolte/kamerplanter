"""REQ-053 WP 10.11 (#2832, W-016.6, V-23) - the light-schedule hint of a tent or shelf level, as a pure rule."""

from __future__ import annotations

import pytest

from app.common.enums import PhotoperiodSource
from app.domain.engines.adjacency_engine import effective_adjacency_factor
from app.domain.engines.tent_rules_engine import (
    PHOTOPERIOD_EQUAL_TOLERANCE_HOURS,
    PHOTOPERIOD_SHARED_LOCATION_TYPES,
    has_own_light_schedule,
    judged_photoperiod,
    photoperiod_groups,
    photoperiod_hints,
)
from app.domain.models.site import DEFAULT_ADJACENCY_FACTOR
from app.domain.models.tent_hint import (
    HINT_PHOTOPERIOD_CONFLICT,
    HINT_PHOTOPERIOD_UNKNOWN,
    MAX_NAMED_UNKNOWN_PLANTS,
    PhaseLabel,
    PlantPhotoperiod,
)

LAMP_CM = 40.0
SOURCED = PhotoperiodSource.SOURCED


def plant(
    key: str,
    hours: float | None,
    phase: str | None = None,
    code: str | None = None,
    name: str = "",
    *,
    source: PhotoperiodSource | None,
) -> PlantPhotoperiod:
    """A plant whose profile states ``hours`` with the origin ``source`` (``None``: no profile, or one from before)."""
    return PlantPhotoperiod(
        plant_key=key,
        phase_name=phase,
        photoperiod_hours=hours,
        phase_code=code,
        display_name=name,
        photoperiod_source=source,
    )


def sourced(
    key: str, hours: float, phase: str | None = None, code: str | None = None, name: str = ""
) -> PlantPhotoperiod:
    """A plant whose phase profile carries hours from a Steckbrief or a person's entry - the only judged value."""
    return plant(key, hours, phase, code, name, source=PhotoperiodSource.SOURCED)


def no_profile(key: str, code: str | None = None, name: str = "") -> PlantPhotoperiod:
    """A plant whose current phase resolves no requirement profile."""
    return plant(key, None, code=code, name=name, source=None)


#: Every origin of stored hours that is no statement about the plant (#2857): ``None`` = stored before the provenance.
UNSOURCED_ORIGINS: list[PhotoperiodSource | None] = [PhotoperiodSource.GENERATED, PhotoperiodSource.DEFAULT, None]


class TestPhotoperiodHints:
    def test_two_photoperiods_in_a_tent_are_a_conflict(self) -> None:
        (hint,) = photoperiod_hints("tent", [sourced("a", 18, "Vegetative"), sourced("b", 12, "Flowering")])

        assert (hint.code, hint.severity, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_CONFLICT, "warning", 0)
        assert [g.photoperiod_hours for g in hint.groups] == [18.0, 12.0]

    def test_a_lit_shelf_level_has_one_schedule_as_well(self) -> None:
        (hint,) = photoperiod_hints("shelf", [sourced("a", 18), sourced("b", 12)], lamp_height_cm=LAMP_CM)

        assert hint.code == HINT_PHOTOPERIOD_CONFLICT

    def test_an_unlit_shelf_has_no_schedule(self) -> None:
        assert photoperiod_hints("shelf", [sourced("a", 18), sourced("b", 12)]) == []

    @pytest.mark.parametrize(
        ("type_key", "lamp", "expected"),
        [("tent", None, True), ("tent", LAMP_CM, True), ("shelf", LAMP_CM, True), ("shelf", None, False)]
        + [("room", LAMP_CM, False), ("bed", LAMP_CM, False)],
    )
    def test_who_runs_a_light_schedule(self, type_key: str, lamp: float | None, expected: bool) -> None:
        assert has_own_light_schedule(type_key, lamp) is expected

    @pytest.mark.parametrize("type_key", ["bed", "raised_bed", "room", "greenhouse", ""])
    def test_a_location_without_its_own_schedule_has_no_hint(self, type_key: str) -> None:
        assert photoperiod_hints(type_key, [sourced("a", 18), sourced("b", 12)]) == []

    def test_one_photoperiod_is_no_conflict(self) -> None:
        assert photoperiod_hints("tent", [sourced("a", 12), sourced("b", 12.0), sourced("c", 12)]) == []

    def test_values_closer_than_a_timer_step_are_one_photoperiod(self) -> None:
        assert photoperiod_hints("tent", [sourced("a", 18.0), sourced("b", 18.1)]) == []

    def test_less_than_an_hour_apart_is_one_photoperiod(self) -> None:
        assert photoperiod_hints("tent", [sourced("a", 18.0), sourced("b", 17.5), sourced("c", 17.25)]) == []

    @pytest.mark.parametrize(
        ("long", "short"), [(18.0, 12.0), (18.0, 16.0), (17.0, 16.0)], ids=["18-6_vs_12-12", "18-6_vs_16-8", "1h"]
    )
    def test_an_hour_or_more_apart_is_a_conflict(self, long: float, short: float) -> None:
        (hint,) = photoperiod_hints("tent", [sourced("a", long), sourced("b", short)])

        assert hint.code == HINT_PHOTOPERIOD_CONFLICT
        assert [g.photoperiod_hours for g in hint.groups] == [long, short]

    def test_the_tolerance_is_one_hour(self) -> None:
        assert PHOTOPERIOD_EQUAL_TOLERANCE_HOURS == 1.0

    @pytest.mark.parametrize(
        "code", ["germination", "seedling", "rooting", "establishment", "pup_establishment", "bulbil_establishment"]
    )
    def test_a_young_plant_takes_no_part(self, code: str) -> None:
        assert (
            photoperiod_hints("tent", [sourced("a", 12, "Flowering", "flowering"), sourced("b", 18, code=code)]) == []
        )

    def test_a_young_plant_is_not_reported_unknown(self) -> None:
        plants = [sourced("a", 12, code="flowering"), no_profile("b", code="seedling")]

        assert photoperiod_hints("tent", plants) == []

    def test_day_neutral_plants_still_take_part(self) -> None:
        """No exclusion by photoperiod type yet: the stored type defaults to day_neutral (follow-up to #2832)."""
        (hint,) = photoperiod_hints("tent", [sourced("a", 18, code="vegetative"), sourced("b", 12, code="flowering")])

        assert hint.code == HINT_PHOTOPERIOD_CONFLICT

    def test_unknown_photoperiods_never_count_as_a_conflict(self) -> None:
        (hint,) = photoperiod_hints("tent", [sourced("a", 18), no_profile("b"), no_profile("c")])

        assert (hint.code, hint.severity, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_UNKNOWN, "info", 2)

    def test_a_conflict_still_names_the_unknown_ones(self) -> None:
        (hint,) = photoperiod_hints("tent", [sourced("a", 18), sourced("b", 12), no_profile("c", name="Gelato")])

        assert (hint.code, hint.unknown_plant_count, hint.unknown_plant_names) == (
            HINT_PHOTOPERIOD_CONFLICT,
            1,
            ("Gelato",),
        )

    def test_the_unknown_names_are_bounded_and_sorted(self) -> None:
        plants = [sourced("k", 18, name="Known")] + [no_profile(f"u{i}", name=f"Plant {i}") for i in range(7, 0, -1)]

        (hint,) = photoperiod_hints("tent", plants)

        assert hint.unknown_plant_count == 7
        assert hint.unknown_plant_names == tuple(f"Plant {i}" for i in range(1, MAX_NAMED_UNKNOWN_PLANTS + 1))

    def test_a_plant_without_a_name_is_named_by_its_key(self) -> None:
        (hint,) = photoperiod_hints("tent", [sourced("a", 18), no_profile("b")])

        assert hint.unknown_plant_names == ("b",)

    def test_a_single_plant_has_nothing_to_share(self) -> None:
        assert photoperiod_hints("tent", [no_profile("a")]) == []
        assert photoperiod_hints("tent", []) == []

    def test_groups_carry_counts_and_sorted_phase_names(self) -> None:
        groups = photoperiod_groups(
            [
                sourced("a", 18, "Vegetative"),
                sourced("b", 18, "Seedling"),
                sourced("c", 18),
                sourced("d", 12, "Flowering"),
            ]
        )

        assert [(g.photoperiod_hours, g.plant_count, g.phase_names) for g in groups] == [
            (18.0, 3, ("Seedling", "Vegetative")),
            (12.0, 1, ("Flowering",)),
        ]

    def test_groups_carry_each_phase_once_with_both_display_names(self) -> None:
        """#2889: the group names its phases by code with both catalogue names, never a server-picked language.

        A legacy growth phase (English name only) and a sequence entry of the same code (both names) are one phase:
        the German name is taken from the entry, whichever plant comes first.
        """
        legacy = PhaseLabel("vegetative", display_name="Vegetative")
        sequence = PhaseLabel("vegetative", display_name="", display_name_de="Vegetative Phase")
        flowering = PhaseLabel("flowering", display_name="Flowering", display_name_de="Blüte")
        groups = photoperiod_groups(
            [
                PlantPhotoperiod("a", "Vegetative", 18.0, "vegetative", phase_label=legacy, photoperiod_source=SOURCED),
                PlantPhotoperiod(
                    "b", "vegetative", 18.0, "vegetative", phase_label=sequence, photoperiod_source=SOURCED
                ),
                PlantPhotoperiod("c", None, 18.0, photoperiod_source=SOURCED),
                PlantPhotoperiod(
                    "d", "Flowering", 12.0, "flowering", phase_label=flowering, photoperiod_source=SOURCED
                ),
            ]
        )

        assert [g.phases for g in groups] == [
            (PhaseLabel("vegetative", display_name="Vegetative", display_name_de="Vegetative Phase"),),
            (flowering,),
        ]

    def test_a_group_without_a_resolved_phase_names_none(self) -> None:
        (group,) = photoperiod_groups([sourced("a", 18), sourced("b", 18)])

        assert group.phases == ()

    def test_the_shared_types_are_tent_and_shelf(self) -> None:
        assert frozenset({"tent", "shelf"}) == PHOTOPERIOD_SHARED_LOCATION_TYPES


class TestOnlySourcedHoursAreJudged:
    """#2857 (REQ-053 §9.2a): only hours from a Steckbrief or a person's entry form groups; the rest is unknown."""

    def test_default_only_profiles_are_unknown_not_a_conflict(self) -> None:
        """Acceptance vector: two plants whose profiles carry the fallback 18 h and a table 12 h - nobody chose them."""
        plants = [
            plant("a", 18.0, "Vegetative", "vegetative", "Lemon", source=PhotoperiodSource.DEFAULT),
            plant("b", 12.0, "Flowering", "flowering", "Gelato", source=PhotoperiodSource.DEFAULT),
        ]

        (hint,) = photoperiod_hints("tent", plants)

        assert (hint.code, hint.severity, hint.groups) == (HINT_PHOTOPERIOD_UNKNOWN, "info", ())
        assert (hint.unknown_plant_count, hint.unknown_plant_names) == (2, ("Gelato", "Lemon"))

    def test_sourced_18_against_sourced_12_is_a_conflict(self) -> None:
        """Acceptance vector: both values are statements about the plants - the conflict stands."""
        (hint,) = photoperiod_hints(
            "tent", [sourced("a", 18.0, code="vegetative"), sourced("b", 12.0, code="flowering")]
        )

        assert (hint.code, hint.severity, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_CONFLICT, "warning", 0)
        assert [g.photoperiod_hours for g in hint.groups] == [18.0, 12.0]

    @pytest.mark.parametrize("origin", UNSOURCED_ORIGINS, ids=["generated", "default", "legacy_none"])
    def test_an_unsourced_value_is_unknown_like_a_missing_profile(self, origin: PhotoperiodSource | None) -> None:
        """One sourced plant against one whose 12 h nobody stated: unknown (info), never a conflict."""
        plants = [
            sourced("a", 18.0, code="vegetative"),
            plant("b", 12.0, code="flowering", name="Gelato", source=origin),
        ]

        (hint,) = photoperiod_hints("tent", plants)

        assert (hint.code, hint.severity, hint.unknown_plant_count, hint.unknown_plant_names) == (
            HINT_PHOTOPERIOD_UNKNOWN,
            "info",
            1,
            ("Gelato",),
        )
        assert [g.photoperiod_hours for g in hint.groups] == [18.0]

    @pytest.mark.parametrize("origin", UNSOURCED_ORIGINS, ids=["generated", "default", "legacy_none"])
    def test_a_sourced_conflict_still_counts_the_unsourced_plants(self, origin: PhotoperiodSource | None) -> None:
        """Mixed case: two sourced groups conflict; a third plant with an unsourced value is counted and named on it."""
        plants = [
            sourced("a", 18.0, code="vegetative"),
            sourced("b", 12.0, code="flowering"),
            plant("c", 12.0, code="flowering", name="Gelato", source=origin),
        ]

        (hint,) = photoperiod_hints("tent", plants)

        assert (hint.code, hint.unknown_plant_count, hint.unknown_plant_names) == (
            HINT_PHOTOPERIOD_CONFLICT,
            1,
            ("Gelato",),
        )
        assert [(g.photoperiod_hours, g.plant_count) for g in hint.groups] == [(18.0, 1), (12.0, 1)]

    def test_generated_values_alone_never_conflict(self) -> None:
        """The generator's table gives vegetative 18 h and flowering 12 h to every species - that is no conflict."""
        plants = [
            plant("a", 18.0, code="vegetative", source=PhotoperiodSource.GENERATED),
            plant("b", 12.0, code="flowering", source=PhotoperiodSource.GENERATED),
        ]

        (hint,) = photoperiod_hints("tent", plants)

        assert (hint.code, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_UNKNOWN, 2)

    def test_a_young_plant_stays_out_whatever_its_source(self) -> None:
        plants = [sourced("a", 12.0, code="flowering"), plant("b", 18.0, code="seedling", source=None)]

        assert photoperiod_hints("tent", plants) == []

    def test_an_unlit_shelf_stays_silent_about_unsourced_values(self) -> None:
        plants = [plant("a", 18.0, source=None), plant("b", 12.0, source=None)]

        assert photoperiod_hints("shelf", plants) == []

    @pytest.mark.parametrize(
        ("origin", "expected"),
        [(PhotoperiodSource.SOURCED, 12.0), (PhotoperiodSource.GENERATED, None)]
        + [(PhotoperiodSource.DEFAULT, None), (None, None)],
        ids=["sourced", "generated", "default", "legacy_none"],
    )
    def test_judged_photoperiod_passes_only_a_sourced_value(
        self, origin: PhotoperiodSource | None, expected: float | None
    ) -> None:
        assert judged_photoperiod(plant("a", 12.0, source=origin)) == expected

    def test_groups_leave_unsourced_values_out(self) -> None:
        groups = photoperiod_groups([sourced("a", 18.0), plant("b", 12.0, source=PhotoperiodSource.GENERATED)])

        assert [(g.photoperiod_hours, g.plant_count) for g in groups] == [(18.0, 1)]


class TestEffectiveAdjacencyFactor:
    def test_the_location_factor_wins(self) -> None:
        assert effective_adjacency_factor(2.0, 1.2) == 2.0

    def test_without_one_the_site_factor_applies(self) -> None:
        assert effective_adjacency_factor(None, 1.2) == 1.2

    def test_without_both_the_default_applies(self) -> None:
        assert effective_adjacency_factor(None, None) == DEFAULT_ADJACENCY_FACTOR
