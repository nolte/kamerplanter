"""Regression guard for the adventskalender harvest-attribute pass-through (#453).

WP-10 A1 backfilled ``harvest_pattern`` / ``harvested_part`` for the three
harvestable vegetables whose canonical entries live in ``adventskalender.yaml``
(leek, beetroot, Brussels sprouts). The adventskalender seeder builds
``Species`` models from an explicit field whitelist in ``_build_species`` — if
``harvest_pattern`` / ``harvested_part`` are missing from that whitelist the
YAML values are silently dropped on import (the same "inert data" class of bug
as the toxicity B2/B7 finding). These tests construct the models without a
database and assert the attributes survive the whitelist.
"""

from app.common.enums import HarvestedPart, HarvestPattern
from app.migrations.seed_adventskalender import _build_species

# Minimal entry mirroring the "Allium porrum" shape in adventskalender.yaml.
LEEK_ENTRY = {
    "scientific_name": "Allium porrum",
    "common_names": ["Porree", "Leek"],
    "genus": "Allium",
    "growth_habit": "herb",
    "root_type": "fibrous",
    "allows_harvest": True,
    "harvest_pattern": "single",
    "harvested_part": "stem",
}


class TestAdventskalenderHarvestPassthrough:
    def test_harvest_fields_survive_the_whitelist(self):
        species = _build_species({"new_species": [LEEK_ENTRY]})

        assert len(species) == 1
        leek = species[0]
        assert leek.harvest_pattern is HarvestPattern.SINGLE
        assert leek.harvested_part is HarvestedPart.STEM

    def test_absent_harvest_fields_default_to_none(self):
        entry = {k: v for k, v in LEEK_ENTRY.items() if not k.startswith("harvest")}

        species = _build_species({"new_species": [entry]})

        assert species[0].harvest_pattern is None
        assert species[0].harvested_part is None

    def test_real_adventskalender_vegetables_are_backfilled(self):
        """The three genuinely harvestable adventskalender vegetables carry both
        lifetime-harvest attributes after loading the real YAML."""
        from app.migrations.seed_adventskalender import _load_data

        by_name = {s.scientific_name: s for s in _build_species(_load_data())}

        expected = {
            "Allium porrum": (HarvestPattern.SINGLE, HarvestedPart.STEM),
            "Beta vulgaris subsp. vulgaris": (HarvestPattern.SINGLE, HarvestedPart.ROOT),
            "Brassica oleracea var. gemmifera": (
                HarvestPattern.CONTINUOUS,
                HarvestedPart.LEAF,
            ),
        }
        for name, (pattern, part) in expected.items():
            assert by_name[name].harvest_pattern is pattern, name
            assert by_name[name].harvested_part is part, name
