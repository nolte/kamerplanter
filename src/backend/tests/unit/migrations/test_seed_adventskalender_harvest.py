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

from app.common.enums import ClimactericClass, HarvestedPart, HarvestPattern
from app.domain.models.species import GrowingPeriod, Species
from app.migrations.seed_adventskalender import (
    _SPECIES_CARRY_BLACKLIST,
    _build_species,
    _species_carry_fields,
)

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


class TestAdventskalenderModelDrivenCarry:
    """Regression guard for the #453 / NCT-7 failure class (issue #679).

    The seeder must carry *every* Species attribute the model declares, driven by
    ``Species.model_fields`` — not a hand-maintained whitelist that silently drops
    unlisted attributes. ``climacteric`` is a resolver-driving Species field that
    was NOT part of the former ``optional_fields`` whitelist: under the old code
    it was dropped on import, under the model-driven carry it survives.
    """

    def test_field_absent_from_former_whitelist_now_survives(self):
        # ``climacteric`` drives post-harvest ripening logic and was never listed
        # in the retired ``optional_fields`` whitelist — the exact #453 regression.
        entry = {
            "scientific_name": "Malus domestica",
            "genus": "Malus",
            "climacteric": "climacteric",
        }

        species = _build_species({"new_species": [entry]})[0]

        assert species.climacteric is ClimactericClass.CLIMACTERIC

    def test_carry_fields_are_derived_from_the_model(self):
        # The carried set is exactly the model fields minus the blacklist — no
        # positive whitelist to fall out of sync with the model.
        assert _species_carry_fields() == frozenset(Species.model_fields) - _SPECIES_CARRY_BLACKLIST
        # Resolver-driving attributes that were never whitelisted are now carried.
        assert "climacteric" in _species_carry_fields()
        assert "plant_category" in _species_carry_fields()
        # Server-managed / relational fields are never carried from the seed data.
        assert "scientific_name_normalized" not in _species_carry_fields()
        assert "family_key" not in _species_carry_fields()
        assert "origin" not in _species_carry_fields()

    def test_blacklisted_fields_exist_on_the_model(self):
        # Guards against a stale blacklist entry after a model rename.
        assert _SPECIES_CARRY_BLACKLIST.issubset(frozenset(Species.model_fields))

    def test_none_values_fall_back_to_model_defaults(self):
        entry = {"scientific_name": "Genus species", "climacteric": None}

        species = _build_species({"new_species": [entry]})[0]

        assert species.climacteric is None
        assert species.allows_harvest is True  # model default preserved

    def test_growing_periods_coerced_from_raw_dicts(self):
        entry = {
            "scientific_name": "Allium porrum",
            "growing_periods": [
                {"label": "Sommerporree", "direct_sow_months": [2, 3], "harvest_months": [8, 9]},
            ],
        }

        species = _build_species({"new_species": [entry]})[0]

        assert species.growing_periods == [
            GrowingPeriod(label="Sommerporree", direct_sow_months=[2, 3], harvest_months=[8, 9]),
        ]

    def test_real_yaml_has_no_field_drift(self):
        """No ``new_species`` YAML entry may carry a key the model does not know."""
        from app.migrations.seed_adventskalender import _load_data

        known = set(Species.model_fields)
        for entry in _load_data().get("new_species", []):
            unknown = set(entry) - known
            assert not unknown, f"{entry.get('scientific_name')}: unknown keys {sorted(unknown)}"
