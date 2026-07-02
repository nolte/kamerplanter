"""Unit tests for the toxicity / allergen / seed_profile mapping in the seeders.

Covers the new canonical ``Toxicity`` and ``SeedProfile`` sub-models and the
model-construction helpers (_build_species, _build_enrichment) on both the base
and the extended seeder — without touching the database.

Regression guard for review finding B2/B7: before this change the structured
``toxicity`` object in the YAML data was silently dropped on import because the
``Species`` model did not consume it.
"""

import pytest

from app.common.enums import LightGermination, SeedPretreatment, ToxicitySeverity
from app.domain.models.species import AllergenInfo, SeedProfile, Toxicity
from app.migrations.seed_plant_info import _build_enrichment, _build_species
from app.migrations.seed_plant_info_extended import (
    _build_enrichment as _build_enrichment_extended,
)
from app.migrations.seed_plant_info_extended import (
    _build_species as _build_species_extended,
)

# ── Sample mirroring "Allium cepa" from plant_info_outdoor_1.yaml ────────────
ALLIUM_CEPA_ENTRY = {
    "scientific_name": "Allium cepa",
    "genus": "Allium",
    "growth_habit": "bulb_geophyte",
    "root_type": "bulbous",
    "toxicity": {
        "is_toxic_cats": True,
        "is_toxic_dogs": True,
        "is_toxic_children": False,
        "toxic_parts": ["bulb", "leaf"],
        "toxic_compounds": ["N-propyl disulfide", "Thiosulfate"],
        "severity": "moderate",
    },
    "allergen_info": {"contact_allergen": True, "pollen_allergen": False},
}


class TestToxicityModel:
    def test_defaults_are_safe(self):
        tox = Toxicity()
        assert tox.is_toxic_cats is False
        assert tox.is_toxic_dogs is False
        assert tox.is_toxic_children is False
        assert tox.toxic_parts == []
        assert tox.toxic_compounds == []
        assert tox.severity is None

    def test_severity_enum_coercion(self):
        tox = Toxicity(is_toxic_cats=True, severity="severe")
        assert tox.severity is ToxicitySeverity.SEVERE

    @pytest.mark.parametrize("value", ["none", "mild", "moderate", "severe"])
    def test_all_severity_values_accepted(self, value):
        assert Toxicity(severity=value).severity == value

    def test_invalid_severity_rejected(self):
        # "low"/"high" belong to the *flat* toxicity_severity scale, not this enum.
        with pytest.raises(ValueError):
            Toxicity(severity="high")


class TestAllergenInfoModel:
    def test_defaults(self):
        allergen = AllergenInfo()
        assert allergen.contact_allergen is False
        assert allergen.pollen_allergen is False


class TestSeedProfileModel:
    def test_all_fields_optional(self):
        profile = SeedProfile()
        assert profile.germination_temp_min_c is None
        assert profile.days_to_germination is None
        assert profile.light_germination is None
        assert profile.pretreatment == []

    def test_full_profile(self):
        profile = SeedProfile(
            germination_temp_min_c=15.0,
            germination_temp_max_c=25.0,
            sowing_depth_cm=1.5,
            days_to_germination=10,
            seed_viability_years=3,
            light_germination="dark",
            pretreatment=["cold_stratification", "presoak"],
            thousand_seed_weight_g=3.5,
            sowing_density_per_m2=120.0,
        )
        assert profile.light_germination is LightGermination.DARK
        assert profile.pretreatment == [
            SeedPretreatment.COLD_STRATIFICATION,
            SeedPretreatment.PRESOAK,
        ]

    def test_negative_depth_rejected(self):
        with pytest.raises(ValueError):
            SeedProfile(sowing_depth_cm=-1)


class TestBaseSeederToxicityRoundtrip:
    def test_toxicity_object_survives_import(self):
        species = _build_species({"new_species": [ALLIUM_CEPA_ENTRY]})[0]
        assert isinstance(species.toxicity, Toxicity)
        # The exact regression: this was lost before the model consumed it.
        assert species.toxicity.is_toxic_cats is True
        assert species.toxicity.is_toxic_dogs is True
        assert species.toxicity.is_toxic_children is False
        assert species.toxicity.toxic_parts == ["bulb", "leaf"]
        assert species.toxicity.severity is ToxicitySeverity.MODERATE

    def test_allergen_info_survives_import(self):
        species = _build_species({"new_species": [ALLIUM_CEPA_ENTRY]})[0]
        assert isinstance(species.allergen_info, AllergenInfo)
        assert species.allergen_info.contact_allergen is True
        assert species.allergen_info.pollen_allergen is False

    def test_missing_blocks_map_to_none(self):
        species = _build_species({"new_species": [{"scientific_name": "Genus species", "genus": "Genus"}]})[0]
        assert species.toxicity is None
        assert species.allergen_info is None
        assert species.seed_profile is None
        assert species.toxicity_severity is None

    def test_flat_toxicity_severity_passthrough_not_mapped(self):
        # The flat low/moderate/high scale must be preserved verbatim and NOT
        # coerced into toxicity.severity.
        entry = {"scientific_name": "Genus species", "genus": "Genus", "toxicity_severity": "low"}
        species = _build_species({"new_species": [entry]})[0]
        assert species.toxicity_severity == "low"
        assert species.toxicity is None

    def test_enrichment_converts_toxicity_dict_to_model(self):
        data = {
            "species_enrichment": {
                "Allium cepa": {
                    "scientific_name": "Allium cepa",
                    "toxicity": ALLIUM_CEPA_ENTRY["toxicity"],
                    "allergen_info": ALLIUM_CEPA_ENTRY["allergen_info"],
                    "seed_profile": {"days_to_germination": 10, "light_germination": "dark"},
                }
            }
        }
        converted = _build_enrichment(data)["Allium cepa"]
        assert isinstance(converted["toxicity"], Toxicity)
        assert converted["toxicity"].is_toxic_cats is True
        assert isinstance(converted["allergen_info"], AllergenInfo)
        assert isinstance(converted["seed_profile"], SeedProfile)
        assert converted["seed_profile"].light_germination is LightGermination.DARK


class TestExtendedSeederToxicityRoundtrip:
    def test_toxicity_object_survives_import(self):
        species = _build_species_extended({"new_species": [ALLIUM_CEPA_ENTRY]})[0]
        assert isinstance(species.toxicity, Toxicity)
        assert species.toxicity.is_toxic_cats is True
        assert species.toxicity.severity is ToxicitySeverity.MODERATE

    def test_seed_profile_empty_maps_to_none(self):
        species = _build_species_extended({"new_species": [ALLIUM_CEPA_ENTRY]})[0]
        # No seed_profile block in the data yet (finding B7 is not backfilled).
        assert species.seed_profile is None

    def test_enrichment_converts_objects(self):
        data = {
            "species_enrichment": {
                "Allium cepa": {
                    "scientific_name": "Allium cepa",
                    "toxicity": ALLIUM_CEPA_ENTRY["toxicity"],
                }
            }
        }
        converted = _build_enrichment_extended(data)["Allium cepa"]
        assert isinstance(converted["toxicity"], Toxicity)
        assert converted["toxicity"].toxic_compounds == ["N-propyl disulfide", "Thiosulfate"]
