"""#2857 (REQ-053 W-016.6) - the provenance a Steckbrief seed gives a phase photoperiod on the patch paths.

``stamp_steckbrief_photoperiod`` is the patch path of ``seed_plant_info`` / ``seed_plant_info_extended``: a phase that
states ``photoperiod_hours`` makes the profile ``sourced`` (also when the value is unchanged - that is how a legacy
installation gets labelled on the next seed run); a phase that leaves the hours out keeps value and origin.
``stamp_unchanged_photoperiods`` is the ``seed_adventskalender`` path, which never overwrites a stored value: it
vouches only for a value that still equals the stated one.
"""

from __future__ import annotations

import pytest

from app.common.enums import PhotoperiodSource, StressTolerance
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.phase import RequirementProfile
from app.migrations.seed_photoperiod_source import stamp_steckbrief_photoperiod, stamp_unchanged_photoperiods


def _profile(hours: float, source: PhotoperiodSource | None) -> RequirementProfile:
    return RequirementProfile(_key="rp", phase_key="ph", photoperiod_hours=hours, photoperiod_source=source)


class TestStampSteckbriefPhotoperiod:
    @pytest.mark.parametrize("origin", [PhotoperiodSource.GENERATED, PhotoperiodSource.DEFAULT, None])
    def test_stated_hours_make_the_profile_sourced(self, origin: PhotoperiodSource | None) -> None:
        profile = _profile(12.0, origin)

        assert stamp_steckbrief_photoperiod(profile, {"photoperiod_hours": 12.0}) is True
        assert profile.photoperiod_source == PhotoperiodSource.SOURCED

    @pytest.mark.parametrize("origin", [PhotoperiodSource.GENERATED, PhotoperiodSource.DEFAULT, None])
    def test_a_phase_without_hours_does_not_relabel_the_kept_value(self, origin: PhotoperiodSource | None) -> None:
        """The generator's 18 h stays the generator's: the Steckbrief said nothing about it."""
        profile = _profile(18.0, origin)

        assert stamp_steckbrief_photoperiod(profile, {"temperature_day_c": 22.0}) is False
        assert (profile.photoperiod_hours, profile.photoperiod_source) == (18.0, origin)

    def test_explicit_null_hours_state_nothing(self) -> None:
        profile = _profile(18.0, PhotoperiodSource.GENERATED)

        assert stamp_steckbrief_photoperiod(profile, {"photoperiod_hours": None}) is False
        assert profile.photoperiod_source == PhotoperiodSource.GENERATED

    def test_an_already_sourced_profile_is_no_change(self) -> None:
        profile = _profile(12.0, PhotoperiodSource.SOURCED)

        assert stamp_steckbrief_photoperiod(profile, {"photoperiod_hours": 12.0}) is False


class _Repo:
    def __init__(self, profiles: dict[str, RequirementProfile]) -> None:
        self.profiles = profiles
        self.updates: list[tuple[str, RequirementProfile]] = []

    def get_requirement_profile(self, phase_key: str) -> RequirementProfile | None:
        return self.profiles.get(phase_key)

    def update_requirement_profile(self, key: str, profile: RequirementProfile) -> RequirementProfile:
        self.updates.append((key, profile))
        return profile


def _phase(key: str, name: str) -> GrowthPhase:
    return GrowthPhase(
        _key=key,
        name=name,
        display_name=name,
        lifecycle_key="lc",
        typical_duration_days=10,
        sequence_order=1,
        stress_tolerance=StressTolerance.MEDIUM,
    )


class TestStampUnchangedPhotoperiods:
    def test_only_a_value_equal_to_the_stated_one_is_vouched_for(self) -> None:
        repo = _Repo(
            {
                "ph_veg": RequirementProfile(_key="rp_veg", phase_key="ph_veg", photoperiod_hours=14.0),
                "ph_flower": RequirementProfile(_key="rp_flower", phase_key="ph_flower", photoperiod_hours=10.0),
                "ph_rest": RequirementProfile(_key="rp_rest", phase_key="ph_rest", photoperiod_hours=8.0),
            }
        )
        phases = [_phase("ph_veg", "vegetative"), _phase("ph_flower", "flowering"), _phase("ph_rest", "dormancy")]

        # flowering: the stored 10 h differs from the stated 12 h (perhaps a person's old edit) - left alone;
        # dormancy: the Steckbrief states nothing - left alone.
        stamped = stamp_unchanged_photoperiods(repo, phases, {"vegetative": 14.0, "flowering": 12.0})  # type: ignore[arg-type]

        assert stamped == 1
        assert [(key, p.photoperiod_hours, p.photoperiod_source) for key, p in repo.updates] == [
            ("rp_veg", 14.0, PhotoperiodSource.SOURCED)
        ]

    def test_a_sourced_profile_is_not_written_again(self) -> None:
        repo = _Repo({"ph_veg": _profile(14.0, PhotoperiodSource.SOURCED).model_copy(update={"phase_key": "ph_veg"})})

        assert stamp_unchanged_photoperiods(repo, [_phase("ph_veg", "vegetative")], {"vegetative": 14.0}) == 0  # type: ignore[arg-type]
        assert repo.updates == []

    def test_a_phase_without_a_profile_is_skipped(self) -> None:
        repo = _Repo({})

        assert stamp_unchanged_photoperiods(repo, [_phase("ph_veg", "vegetative")], {"vegetative": 14.0}) == 0  # type: ignore[arg-type]
