"""FAMILY_CARE_MAP covers every botanical family the seeds create (#1505).

Until 2026-09-18 the map was a houseplant map. With #1489 fixed (the bootstrap
finally hands the engine the family *name*), the families it does not know became
visible: a tomato, a cabbage and a rose were answered with the tier-3 ``TROPICAL``
7-day houseplant preset.

What this module measures, and why not the way the issue did
============================================================

Issue #1505 counted the population from ``app/migrations/seed_data/botanical_families.yaml``
alone — 18 families, 4 mapped. That file is **not** the catalogue: seven more seed
files carry their own ``new_families:`` block (``plant_info_*.yaml``,
``adventskalender.yaml``), every one of them applied at startup by
``app/migrations/seeds/registry.py``, and six further families are named only by a
species' ``family`` field and never declared as a document at all. Measured over
all of them: **63 seeded families, 14 mapped before this change.**

So the guard derives its population from *every* YAML file in ``seed_data/``, and
from three spellings of "this record names a family":

* any top-level list whose key ends in ``families`` holding ``{name: ...}`` records
  (``families:`` in ``botanical_families.yaml``, ``new_families:`` elsewhere),
* any top-level list of species-shaped records carrying a ``family:`` field,
* the ``new_species_family_map:`` mapping (``scientific name -> family name``).

That triple is the answer to "name a spelling of the same thing my pattern does not
match": the first alone misses the six species-only families, the second alone
misses families seeded ahead of their species, and the third is the only place the
``plant_info_indoor_3.yaml`` / ``plant_info_supplement_1.yaml`` species name theirs.

The reverse direction — a map entry naming no seeded family — is **reported, never
red**. Such an entry costs one dict lookup and serves a user-created or imported
species; making it fail would push the map to shrink to the seeds, which is the
opposite of what this issue is about.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.common.enums import CareStyleType, WateringMethod
from app.domain.engines.care_reminder_engine import (
    CARE_STYLE_PRESETS,
    FAMILY_CARE_MAP,
    CareReminderEngine,
)

_SEED_DIR = Path(__file__).resolve().parents[4] / "app" / "migrations" / "seed_data"


def _seeded_family_names() -> dict[str, set[str]]:
    """``family name -> the seed files that name it``, over every spelling."""
    found: dict[str, set[str]] = {}

    def record(name: Any, source: str) -> None:
        if isinstance(name, str) and name.strip():
            found.setdefault(name.strip(), set()).add(source)

    for path in sorted(_SEED_DIR.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            continue
        for key, value in document.items():
            if key.endswith("families") and isinstance(value, list):
                for entry in value:
                    if isinstance(entry, dict):
                        record(entry.get("name"), path.name)
            elif key == "new_species_family_map" and isinstance(value, dict):
                for family in value.values():
                    record(family, path.name)
            elif isinstance(value, list):
                for entry in value:
                    if isinstance(entry, dict) and entry.get("scientific_name"):
                        record(entry.get("family"), path.name)
    return found


class TestSeededFamilyCoverage:
    def test_the_seed_corpus_is_read_at_all(self):
        """The measuring tool has to be able to fail.

        A guard whose population is empty is green for the wrong reason. The
        floor is deliberately far below the measured 63 so that adding or
        removing one seed file never touches this number.
        """
        seeded = _seeded_family_names()
        assert len(seeded) >= 50, f"only {len(seeded)} families found under {_SEED_DIR} — the reader is broken"
        assert "Solanaceae" in seeded and "Araceae" in seeded

    def test_every_seeded_family_is_mapped(self):
        """#1505 — 14 of 63 before this change; 63 of 63 after it."""
        seeded = _seeded_family_names()
        unmapped = sorted(name for name in seeded if name not in FAMILY_CARE_MAP)
        assert not unmapped, (
            f"{len(unmapped)} seeded botanical families fall through to the TROPICAL houseplant "
            f"fallback: {unmapped}. Add them to FAMILY_CARE_MAP with the style their Steckbriefe "
            "in spec/knowledge/plants/*.md §4.1 declare."
        )

    def test_every_mapped_style_has_a_preset(self):
        missing = sorted({style.value for style in FAMILY_CARE_MAP.values() if style not in CARE_STYLE_PRESETS})
        assert not missing, f"FAMILY_CARE_MAP names care styles with no preset: {missing}"

    def test_every_care_style_has_a_preset(self):
        """``auto_generate_profile`` indexes CARE_STYLE_PRESETS without a default."""
        missing = sorted({style.value for style in CareStyleType if style not in CARE_STYLE_PRESETS})
        assert not missing, f"CareStyleType members with no preset: {missing}"

    def test_map_entries_naming_no_seeded_family_are_reported_not_failed(self, capsys):
        """Report-only, by design — see the module docstring."""
        seeded = _seeded_family_names()
        unseeded = sorted(name for name in FAMILY_CARE_MAP if name not in seeded)
        print(f"FAMILY_CARE_MAP entries naming no seeded family ({len(unseeded)}): {unseeded}")
        assert len(unseeded) <= len(FAMILY_CARE_MAP) // 2, (
            "more than half the map names families no seed creates — the map and the catalogue "
            f"have drifted apart: {unseeded}"
        )


class TestFamilyPresetsForTheSeededCatalogue:
    """The styles the issue's headline plants now get instead of TROPICAL."""

    @pytest.mark.parametrize(
        ("family", "expected"),
        [
            ("Solanaceae", CareStyleType.OUTDOOR_ANNUAL_VEG),
            ("Brassicaceae", CareStyleType.OUTDOOR_ANNUAL_VEG),
            ("Cucurbitaceae", CareStyleType.OUTDOOR_ANNUAL_VEG),
            ("Apiaceae", CareStyleType.OUTDOOR_ANNUAL_VEG),
            ("Fabaceae", CareStyleType.OUTDOOR_ANNUAL_VEG),
            ("Poaceae", CareStyleType.OUTDOOR_ANNUAL_VEG),
            ("Rosaceae", CareStyleType.FRUIT_TREE),
            ("Grossulariaceae", CareStyleType.BERRY_SHRUB),
            ("Ranunculaceae", CareStyleType.OUTDOOR_PERENNIAL),
            ("Bromeliaceae", CareStyleType.BROMELIAD),
            ("Nymphaeaceae", CareStyleType.AQUATIC),
        ],
    )
    def test_family_resolves_to_its_style(self, family: str, expected: CareStyleType):
        profile = CareReminderEngine().auto_generate_profile(botanical_family=family, plant_key="p1")
        assert profile.care_style is expected

    def test_a_tomato_is_not_a_tropical_houseplant(self):
        """The #1505 headline, end to end through the generator.

        Red before the change: ``care_style`` was ``tropical`` and the watering
        interval 7 days — a tomato in July watered once a week.
        """
        profile = CareReminderEngine().auto_generate_profile(
            species_name="Solanum lycopersicum",
            botanical_family="Solanaceae",
            plant_key="tomato-1",
        )
        assert profile.care_style is CareStyleType.OUTDOOR_ANNUAL_VEG
        assert profile.care_style is not CareStyleType.TROPICAL
        assert profile.watering_interval_days == 3
        assert profile.humidity_check_enabled is False

    def test_an_unknown_family_still_falls_back_to_tropical(self):
        """Tier 3 is unchanged — the decision in #1505 kept it as the last tier."""
        profile = CareReminderEngine().auto_generate_profile(
            botanical_family="Nothofagaceae",
            plant_key="p1",
        )
        assert profile.care_style is CareStyleType.TROPICAL


class TestNewPresets:
    """Values sourced per field from the seeded species' own Steckbriefe."""

    def test_bromeliad_waters_the_funnel_and_feeds_sparingly(self):
        preset = CARE_STYLE_PRESETS[CareStyleType.BROMELIAD]
        # Median of guzmania/vriesea/aechmea/neoregelia/tillandsia §4.1.
        assert preset["watering_interval_days"] == 7
        assert preset["watering_method"] is WateringMethod.TOP_WATER
        # "extreme Schwachzehrer" (botanical_families.yaml) — twice the ORCHID interval.
        assert preset["fertilizing_interval_days"] == 28
        assert (
            preset["fertilizing_interval_days"] > CARE_STYLE_PRESETS[CareStyleType.ORCHID]["fertilizing_interval_days"]
        )
        # All five docs demand lime-free water.
        assert "Lime-free" in preset["water_quality_hint"]
        assert preset["humidity_check_enabled"] is True

    def test_aquatic_is_a_pond_level_check_not_a_watering(self):
        preset = CARE_STYLE_PRESETS[CareStyleType.AQUATIC]
        # nymphaea_alba.md §4.1: "ca. 2-5 cm/Woche im Sommer".
        assert preset["watering_interval_days"] == 7
        # Winter watering is "none (aquatisch, steht im Wasser)".
        assert preset["winter_watering_multiplier"] == 4.0
        # "28-42 (alle 4-6 Wochen, Depot-Tabletten)", active April to August.
        assert preset["fertilizing_interval_days"] == 30
        assert preset["fertilizing_active_months"] == [4, 5, 6, 7, 8]
        # "36-60 (alle 3-5 Jahre Pflanzkorb erneuern und Rhizom teilen)".
        assert preset["repotting_interval_months"] == 48
        # "false (aquatisch)".
        assert preset["humidity_check_enabled"] is False

    def test_both_presets_produce_a_valid_profile(self):
        for style in (CareStyleType.BROMELIAD, CareStyleType.AQUATIC):
            profile = CareReminderEngine().auto_generate_profile(
                botanical_family={
                    CareStyleType.BROMELIAD: "Bromeliaceae",
                    CareStyleType.AQUATIC: "Nymphaeaceae",
                }[style],
                plant_key="p1",
            )
            assert profile.care_style is style
            assert profile.auto_generated is True
