"""#2857 (REQ-053 W-016.6) - Steckbrief light hours for the default phases of a species reach its profiles as sourced.

``species.yaml`` ``steckbrief_phase_photoperiods`` lists, per species seeded with the generic ``default_phases``, the
hours its Steckbrief states for those phases. Pinned here: the consistency check compares every listed value with the
Steckbrief row it cites (so seed and Steckbrief cannot drift, and no value the Steckbrief does not state can enter);
the real block matches the real hemp Steckbrief; the loader writes the hours as ``sourced`` without overriding a
person's value; and no listed species has phases a Steckbrief seed file already carries.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from app.common.enums import PhotoperiodSource
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import RequirementProfile
from app.migrations.seed_phase_ownership import species_with_seeded_phases
from app.migrations.seed_photoperiod_source import (
    StatedPhotoperiod,
    apply_steckbrief_phase_photoperiods,
    parse_steckbrief_phase_photoperiods,
)
from app.migrations.seed_steckbrief_consistency import check, find_phase_photoperiod_drifts
from app.migrations.yaml_loader import load_yaml

_STECKBRIEF = textwrap.dedent(
    """\
    # Hanf

    #### Phase: Vegetativ

    | Parameter | Wert | KA-Feld |
    |-----------|------|---------|
    | Photoperiode (Stunden) | 18/6 (Photoperiod); 18–20 (Autoflower) | `requirement_profiles.photoperiod_hours` |

    #### Phase: Hauptbluete (Flowering)

    | Parameter | Wert | KA-Feld |
    |-----------|------|---------|
    | Photoperiode (Stunden) | 12/12 <!-- Quelle: X --> | `requirement_profiles.photoperiod_hours` |

    #### Phase: Ohne Licht

    | Parameter | Wert | KA-Feld |
    |-----------|------|---------|
    | Temperatur | 20 | `requirement_profiles.temperature_day_c` |
    """
)


def _tree(tmp_path: Path, phases: dict[str, dict[str, object]]) -> Path:
    plants = tmp_path / "spec" / "knowledge" / "plants"
    seed = tmp_path / "src" / "backend" / "app" / "migrations" / "seed_data"
    plants.mkdir(parents=True)
    seed.mkdir(parents=True)
    (plants / "cannabis_sativa.md").write_text(_STECKBRIEF, encoding="utf-8")
    block = {"Cannabis sativa": {"steckbrief": "cannabis_sativa.md", "phases": phases}}
    (seed / "species.yaml").write_text(
        yaml.safe_dump({"species": [], "steckbrief_phase_photoperiods": block}), encoding="utf-8"
    )
    return tmp_path


class TestTheConsistencyCheck:
    def test_values_equal_to_the_steckbrief_pass(self, tmp_path: Path) -> None:
        root = _tree(
            tmp_path,
            {
                "vegetative": {"hours": 18, "steckbrief_phase": "Vegetativ"},
                "flowering": {"hours": 12, "steckbrief_phase": "Hauptbluete (Flowering)"},
            },
        )

        assert find_phase_photoperiod_drifts(root) == []

    def test_a_different_value_is_a_drift(self, tmp_path: Path) -> None:
        root = _tree(tmp_path, {"flowering": {"hours": 13, "steckbrief_phase": "Hauptbluete (Flowering)"}})

        (drift,) = find_phase_photoperiod_drifts(root)

        assert (drift.attribute, drift.steckbrief_value, drift.seed_value) == (
            "photoperiod_hours[flowering]",
            "12",
            "13",
        )
        assert not check(root=root).ok

    @pytest.mark.parametrize("heading", ["Keimung", "Ohne Licht"], ids=["heading_missing", "row_missing"])
    def test_hours_the_steckbrief_does_not_state_are_a_drift(self, tmp_path: Path, heading: str) -> None:
        """E-10: a seed value without a Steckbrief row cannot enter."""
        root = _tree(tmp_path, {"seedling": {"hours": 18, "steckbrief_phase": heading}})

        (drift,) = find_phase_photoperiod_drifts(root)

        assert drift.steckbrief_value == "<no row>"

    def test_the_real_seed_matches_the_real_steckbriefe(self) -> None:
        assert find_phase_photoperiod_drifts(Path(__file__).resolve().parents[5]) == []


class TestTheRealBlock:
    def test_hemp_carries_the_steckbrief_hours_of_its_default_phases(self) -> None:
        stated = parse_steckbrief_phase_photoperiods(load_yaml("species.yaml")["steckbrief_phase_photoperiods"])

        assert {p.phase_name: p.hours for p in stated["Cannabis sativa"]} == {
            "seedling": 18.0,
            "vegetative": 18.0,
            "flowering": 12.0,
            "ripening": 12.0,
        }

    def test_every_listed_phase_is_a_default_phase(self) -> None:
        data = load_yaml("species.yaml")
        default_names = {phase["name"] for phase in data["default_phases"]}
        listed = {name for entry in data["steckbrief_phase_photoperiods"].values() for name in entry["phases"]}

        assert listed <= default_names

    def test_no_listed_species_has_steckbrief_phases_elsewhere(self) -> None:
        """Those phases are sourced by their own seed file; one mechanism per species."""
        listed = set(load_yaml("species.yaml")["steckbrief_phase_photoperiods"])

        assert listed & species_with_seeded_phases() == set()


class _Repo:
    def __init__(self, profiles: dict[str, RequirementProfile]) -> None:
        self.profiles = profiles
        self.updates: list[RequirementProfile] = []

    def get_lifecycle_by_species(self, species_key: str) -> LifecycleConfig | None:
        return LifecycleConfig(_key="lc", species_key=species_key) if species_key == "sp_hemp" else None

    def get_phases_by_lifecycle(self, lifecycle_key: str) -> list[GrowthPhase]:
        return [
            GrowthPhase(
                _key=key,
                name=key.removeprefix("ph_"),
                display_name=key,
                lifecycle_key=lifecycle_key,
                typical_duration_days=10,
                sequence_order=1,
            )
            for key in self.profiles
        ]

    def get_requirement_profile(self, phase_key: str) -> RequirementProfile | None:
        return self.profiles.get(phase_key)

    def update_requirement_profile(self, key: str, profile: RequirementProfile) -> RequirementProfile:
        self.updates.append(profile)
        return profile


def _profile(phase: str, hours: float, source: PhotoperiodSource | None) -> RequirementProfile:
    return RequirementProfile(_key=f"rp_{phase}", phase_key=phase, photoperiod_hours=hours, photoperiod_source=source)


_STATED = {
    "Cannabis sativa": [
        StatedPhotoperiod("vegetative", 18.0, "Vegetativ"),
        StatedPhotoperiod("flowering", 12.0, "Hauptbluete (Flowering)"),
    ]
}


class TestTheLoader:
    @pytest.mark.parametrize("origin", [PhotoperiodSource.GENERATED, PhotoperiodSource.DEFAULT])
    def test_nobodys_value_is_replaced_and_sourced(self, origin: PhotoperiodSource) -> None:
        repo = _Repo(
            {"ph_vegetative": _profile("ph_vegetative", 20.0, origin), "ph_flush": _profile("ph_flush", 12, origin)}
        )

        changed = apply_steckbrief_phase_photoperiods(repo, _STATED, {"Cannabis sativa": "sp_hemp"})  # type: ignore[arg-type]

        assert changed == 1
        assert (
            repo.profiles["ph_vegetative"].photoperiod_hours,
            repo.profiles["ph_vegetative"].photoperiod_source,
        ) == (
            18.0,
            PhotoperiodSource.SOURCED,
        )
        # A phase the Steckbrief states nothing for keeps its value and origin.
        assert repo.profiles["ph_flush"].photoperiod_source == origin

    def test_a_legacy_profile_with_the_stated_value_is_stamped(self) -> None:
        repo = _Repo({"ph_flowering": _profile("ph_flowering", 12.0, None)})

        assert apply_steckbrief_phase_photoperiods(repo, _STATED, {"Cannabis sativa": "sp_hemp"}) == 1  # type: ignore[arg-type]
        assert repo.profiles["ph_flowering"].photoperiod_source == PhotoperiodSource.SOURCED

    def test_a_legacy_profile_with_another_value_is_left_alone(self) -> None:
        """It may be a person's edit from before the provenance - nobody can tell."""
        repo = _Repo({"ph_flowering": _profile("ph_flowering", 11.0, None)})

        assert apply_steckbrief_phase_photoperiods(repo, _STATED, {"Cannabis sativa": "sp_hemp"}) == 0  # type: ignore[arg-type]
        assert (repo.profiles["ph_flowering"].photoperiod_hours, repo.updates) == (11.0, [])

    def test_a_persons_sourced_value_stays(self) -> None:
        repo = _Repo({"ph_flowering": _profile("ph_flowering", 11.0, PhotoperiodSource.SOURCED)})

        assert apply_steckbrief_phase_photoperiods(repo, _STATED, {"Cannabis sativa": "sp_hemp"}) == 0  # type: ignore[arg-type]
        assert repo.profiles["ph_flowering"].photoperiod_hours == 11.0

    def test_an_unseeded_species_is_skipped(self) -> None:
        repo = _Repo({"ph_flowering": _profile("ph_flowering", 12.0, PhotoperiodSource.GENERATED)})

        assert apply_steckbrief_phase_photoperiods(repo, _STATED, {}) == 0  # type: ignore[arg-type]
