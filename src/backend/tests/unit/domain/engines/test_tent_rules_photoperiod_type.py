"""#2857 part B - the species' photoperiod type in the tent rule (REQ-053 §9.2a, W-016.6, V-23).

Acceptance vectors of the issue, each as the rule sees it:

* default-only profiles -> ``tent.photoperiod_unknown``, never a conflict;
* a sourced day-neutral plant beside a short-day plant -> no conflict (the day-neutral plant takes no part);
* sourced 18 h against 12 h -> conflict;
* a short-day plant at 18 h in flowering -> ``tent.photoperiod_data_error``, not a conflict.

``unspecified`` (and a plant without a lifecycle) is no classification: such a plant takes part like before.
"""

from __future__ import annotations

import pytest

from app.common.enums import PhotoperiodSource, PhotoperiodType
from app.domain.engines.phase_role_map import is_flowering_phase
from app.domain.engines.tent_rules_engine import (
    PHOTOPERIOD_EQUAL_TOLERANCE_HOURS,
    SHORT_DAY_FALLBACK_CRITICAL_HOURS,
    is_day_neutral,
    is_photoperiod_data_error,
    light_triggered,
    photoperiod_hints,
)
from app.domain.models.tent_hint import (
    HINT_PHOTOPERIOD_CONFLICT,
    HINT_PHOTOPERIOD_DATA_ERROR,
    HINT_PHOTOPERIOD_UNKNOWN,
    PlantPhotoperiod,
)

SHORT = PhotoperiodType.SHORT_DAY
NEUTRAL = PhotoperiodType.DAY_NEUTRAL
UNSPECIFIED = PhotoperiodType.UNSPECIFIED


def plant(
    key: str,
    hours: float | None,
    code: str = "vegetative",
    *,
    kind: PhotoperiodType | None = None,
    source: PhotoperiodSource | None = PhotoperiodSource.SOURCED,
    critical: float | None = None,
) -> PlantPhotoperiod:
    return PlantPhotoperiod(
        plant_key=key,
        phase_name=code.title(),
        photoperiod_hours=hours,
        phase_code=code,
        display_name=key.title(),
        photoperiod_source=source,
        photoperiod_type=kind,
        critical_day_length_hours=critical,
    )


class TestAcceptanceVectors:
    def test_default_only_profiles_are_unknown_not_a_conflict(self) -> None:
        plants = [
            plant("a", 18.0, kind=UNSPECIFIED, source=PhotoperiodSource.DEFAULT),
            plant("b", 12.0, "flowering", kind=UNSPECIFIED, source=PhotoperiodSource.GENERATED),
        ]

        (hint,) = photoperiod_hints("tent", plants)

        assert (hint.code, hint.unknown_plant_count) == (HINT_PHOTOPERIOD_UNKNOWN, 2)

    def test_a_sourced_day_neutral_plant_beside_a_short_day_plant_is_no_conflict(self) -> None:
        plants = [
            plant("strawberry", 18.0, "flowering", kind=NEUTRAL),
            plant("hemp", 12.0, "flowering", kind=SHORT, critical=12.0),
        ]

        assert photoperiod_hints("tent", plants) == []

    def test_sourced_18_against_12_hours_is_a_conflict(self) -> None:
        plants = [plant("veg", 18.0, kind=SHORT), plant("bloom", 12.0, "flowering", kind=SHORT, critical=12.0)]

        (hint,) = photoperiod_hints("tent", plants)

        assert hint.code == HINT_PHOTOPERIOD_CONFLICT
        assert [group.photoperiod_hours for group in hint.groups] == [18.0, 12.0]

    def test_a_short_day_plant_at_18_hours_in_flowering_is_a_data_error_not_a_conflict(self) -> None:
        plants = [plant("veg", 12.0, kind=SHORT), plant("bloom", 18.0, "flowering", kind=SHORT, critical=12.0)]

        (hint,) = photoperiod_hints("tent", plants)

        assert (hint.code, hint.severity) == (HINT_PHOTOPERIOD_DATA_ERROR, "info")
        assert (hint.data_error_plant_count, hint.data_error_plant_names) == (1, ("Bloom",))
        assert [group.photoperiod_hours for group in hint.groups] == [18.0]
        assert hint.unknown_plant_count == 0


class TestDayNeutral:
    def test_only_a_stated_day_neutral_leaves_the_check(self) -> None:
        assert is_day_neutral(plant("a", 18.0, kind=NEUTRAL))
        assert not is_day_neutral(plant("a", 18.0, kind=UNSPECIFIED))
        assert not is_day_neutral(plant("a", 18.0, kind=None))

    @pytest.mark.parametrize("kind", [UNSPECIFIED, None])
    def test_an_unclassified_plant_still_takes_part_in_the_conflict(self, kind: PhotoperiodType | None) -> None:
        plants = [plant("a", 18.0, kind=kind), plant("b", 12.0, "flowering", kind=kind)]

        (hint,) = photoperiod_hints("tent", plants)

        assert hint.code == HINT_PHOTOPERIOD_CONFLICT

    def test_day_neutral_plants_do_not_count_towards_the_unknown_hint(self) -> None:
        plants = [
            plant("unknown", 18.0, kind=SHORT, source=PhotoperiodSource.GENERATED),
            plant("auto", 18.0, "flowering", kind=NEUTRAL),
        ]

        assert light_triggered(plants) == [plants[0]]
        assert photoperiod_hints("tent", plants) == []

    def test_a_day_neutral_plant_is_never_a_data_error(self) -> None:
        assert not is_photoperiod_data_error(plant("auto", 18.0, "flowering", kind=NEUTRAL))


class TestDataError:
    def test_the_threshold_is_the_critical_day_length_plus_the_tolerance(self) -> None:
        critical = 12.0
        at = critical + PHOTOPERIOD_EQUAL_TOLERANCE_HOURS

        assert is_photoperiod_data_error(plant("a", at, "flowering", kind=SHORT, critical=critical))
        assert not is_photoperiod_data_error(plant("a", at - 0.5, "flowering", kind=SHORT, critical=critical))

    def test_a_stated_critical_day_length_moves_the_threshold(self) -> None:
        assert not is_photoperiod_data_error(plant("a", 14.0, "flowering", kind=SHORT, critical=14.5))
        assert is_photoperiod_data_error(plant("a", 15.5, "flowering", kind=SHORT, critical=14.5))

    def test_without_a_critical_day_length_the_short_day_fallback_applies(self) -> None:
        fallback = SHORT_DAY_FALLBACK_CRITICAL_HOURS + PHOTOPERIOD_EQUAL_TOLERANCE_HOURS

        assert is_photoperiod_data_error(plant("a", fallback, "flowering", kind=SHORT))
        assert not is_photoperiod_data_error(plant("a", fallback - 0.5, "flowering", kind=SHORT))

    @pytest.mark.parametrize("code", ["flowering", "pre_bloom", "bud_formation", "short_day_induction"])
    def test_every_flowering_phase_counts(self, code: str) -> None:
        assert is_flowering_phase(code)
        assert is_photoperiod_data_error(plant("a", 18.0, code, kind=SHORT))

    @pytest.mark.parametrize("code", ["vegetative", "ripening", "fruit_development", "seedling"])
    def test_other_phases_are_no_data_error(self, code: str) -> None:
        assert not is_photoperiod_data_error(plant("a", 18.0, code, kind=SHORT))

    @pytest.mark.parametrize("source", [PhotoperiodSource.GENERATED, PhotoperiodSource.DEFAULT, None])
    def test_only_sourced_hours_are_judged(self, source: PhotoperiodSource | None) -> None:
        assert not is_photoperiod_data_error(plant("a", 18.0, "flowering", kind=SHORT, source=source))

    @pytest.mark.parametrize("kind", [PhotoperiodType.LONG_DAY, UNSPECIFIED, None])
    def test_only_a_short_day_plant_is_checked(self, kind: PhotoperiodType | None) -> None:
        assert not is_photoperiod_data_error(plant("a", 18.0, "flowering", kind=kind))

    def test_a_data_error_comes_beside_a_conflict_of_the_other_plants(self) -> None:
        plants = [
            plant("veg", 18.0, kind=SHORT),
            plant("bloom", 12.0, "flowering", kind=SHORT, critical=12.0),
            plant("wrong", 18.0, "flowering", kind=SHORT, critical=12.0),
        ]

        conflict, data_error = photoperiod_hints("tent", plants)

        assert conflict.code == HINT_PHOTOPERIOD_CONFLICT
        assert [group.plant_count for group in conflict.groups] == [1, 1]
        assert data_error.code == HINT_PHOTOPERIOD_DATA_ERROR
        assert data_error.data_error_plant_names == ("Wrong",)

    def test_a_location_without_a_schedule_gives_no_data_error(self) -> None:
        assert photoperiod_hints("bed", [plant("wrong", 18.0, "flowering", kind=SHORT)]) == []
