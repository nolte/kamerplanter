import pytest
from pydantic import ValidationError

from app.common.enums import (
    ClimactericClass,
    DtmReference,
    GrowthHabit,
    HarvestedPart,
    HarvestPattern,
    PropagationDifficulty,
    PropagationMethod,
    RootType,
    Suitability,
    WoodStage,
)
from app.domain.models.species import Cultivar, PropagationConfig, Species


class TestSpeciesValidation:
    def test_valid_species(self):
        s = Species(scientific_name="Solanum lycopersicum", genus="Solanum")
        assert s.scientific_name == "Solanum lycopersicum"

    def test_binomial_validation_fails(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Tomato", genus="Solanum")

    def test_allelopathy_range(self):
        s = Species(scientific_name="Genus species", allelopathy_score=0.5)
        assert s.allelopathy_score == 0.5

    def test_allelopathy_too_high(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", allelopathy_score=1.5)

    def test_allelopathy_too_low(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", allelopathy_score=-1.5)

    def test_valid_hardiness_zones(self):
        s = Species(scientific_name="Genus species", hardiness_zones=["7a", "7b", "8a"])
        assert len(s.hardiness_zones) == 3

    def test_invalid_hardiness_zone(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", hardiness_zones=["invalid"])


class TestSuitabilityEnum:
    def test_enum_values(self):
        assert Suitability.YES == "yes"
        assert Suitability.LIMITED == "limited"
        assert Suitability.NO == "no"
        assert len(Suitability) == 3


class TestCultivationConditionFields:
    def test_defaults_are_none_or_false(self):
        s = Species(scientific_name="Genus species")
        assert s.container_suitable is None
        assert s.recommended_container_volume_l is None
        assert s.min_container_depth_cm is None
        assert s.mature_height_cm is None
        assert s.mature_width_cm is None
        assert s.spacing_cm is None
        assert s.indoor_suitable is None
        assert s.balcony_suitable is None
        assert s.greenhouse_recommended is False
        assert s.support_required is False

    def test_min_container_depth_valid(self):
        s = Species(scientific_name="Genus species", min_container_depth_cm=25)
        assert s.min_container_depth_cm == 25

    def test_min_container_depth_too_low(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", min_container_depth_cm=-1)

    def test_min_container_depth_too_high(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", min_container_depth_cm=201)

    def test_string_range_fields(self):
        s = Species(
            scientific_name="Genus species",
            recommended_container_volume_l="10--20",
            mature_height_cm="100--300",
            mature_width_cm="80--150",
            spacing_cm="50--80",
        )
        assert s.recommended_container_volume_l == "10--20"
        assert s.mature_height_cm == "100--300"

    def test_suitability_fields(self):
        s = Species(
            scientific_name="Genus species",
            container_suitable=Suitability.YES,
            indoor_suitable=Suitability.LIMITED,
            balcony_suitable=Suitability.NO,
        )
        assert s.container_suitable == Suitability.YES
        assert s.indoor_suitable == Suitability.LIMITED
        assert s.balcony_suitable == Suitability.NO

    def test_boolean_cultivation_fields(self):
        s = Species(
            scientific_name="Genus species",
            greenhouse_recommended=True,
            support_required=True,
        )
        assert s.greenhouse_recommended is True
        assert s.support_required is True


class TestCultivarValidation:
    def test_valid_cultivar(self):
        c = Cultivar(name="San Marzano", species_key="sp1")
        assert c.name == "San Marzano"

    def test_days_to_maturity_range(self):
        c = Cultivar(name="Test", species_key="sp1", days_to_maturity=90)
        assert c.days_to_maturity == 90

    def test_days_to_maturity_too_high(self):
        with pytest.raises(ValidationError):
            Cultivar(name="Test", species_key="sp1", days_to_maturity=1096)

    def test_days_to_maturity_too_low(self):
        with pytest.raises(ValidationError):
            Cultivar(name="Test", species_key="sp1", days_to_maturity=0)

    def test_seed_type_default(self):
        c = Cultivar(name="Test", species_key="sp1")
        assert c.seed_type == ""

    def test_seed_type_set(self):
        c = Cultivar(name="Test", species_key="sp1", seed_type="f1_hybrid")
        assert c.seed_type == "f1_hybrid"


class TestRootTypeCorm:
    def test_corm_value(self):
        assert RootType.CORM == "corm"

    def test_species_with_corm(self):
        s = Species(scientific_name="Tigridia pavonia", root_type=RootType.CORM)
        assert s.root_type == RootType.CORM


class TestPropagationMethodEnum:
    def test_enum_has_seventeen_values(self):
        assert len(PropagationMethod) == 17

    def test_enum_values(self):
        assert PropagationMethod.SEED == "seed"
        assert PropagationMethod.CUTTING == "cutting"
        assert PropagationMethod.RHIZOME_DIVISION == "rhizome_division"
        assert PropagationMethod.LEAF_CUTTING == "leaf_cutting"
        assert PropagationMethod.SELF_SEEDING == "self_seeding"

    def test_reconciled_values_present(self):
        # Drift fix: REQ-017 methods now realised in the enum.
        assert PropagationMethod.AIR_LAYERING == "air_layering"
        assert PropagationMethod.TISSUE_CULTURE == "tissue_culture"
        assert PropagationMethod.BULBIL == "bulbil"
        assert PropagationMethod.WATER_PROPAGATION == "water_propagation"


class TestPropagationConfig:
    def test_minimal_config_defaults(self):
        c = PropagationConfig(method=PropagationMethod.CUTTING)
        assert c.method == PropagationMethod.CUTTING
        assert c.months == []
        assert c.wood_stage is None
        assert c.difficulty is None
        assert c.notes is None

    def test_full_config_dedupes_and_sorts_months(self):
        c = PropagationConfig(
            method="cutting",
            months=[7, 6, 5, 6],
            wood_stage=WoodStage.SOFTWOOD,
            difficulty=PropagationDifficulty.MODERATE,
            notes="Bewurzelungshormon empfohlen.",
        )
        assert c.method == PropagationMethod.CUTTING
        assert c.months == [5, 6, 7]
        assert c.wood_stage == WoodStage.SOFTWOOD
        assert c.difficulty == PropagationDifficulty.MODERATE

    def test_invalid_method_rejected(self):
        with pytest.raises(ValidationError):
            PropagationConfig(method="teleportation")

    def test_invalid_month_rejected(self):
        with pytest.raises(ValidationError):
            PropagationConfig(method="seed", months=[13])


class TestSpeciesPropagationConfigs:
    def test_default_is_empty_list(self):
        s = Species(scientific_name="Genus species")
        assert s.propagation_configs == []

    def test_accepts_config_objects(self):
        s = Species(
            scientific_name="Genus species",
            propagation_configs=[
                PropagationConfig(method=PropagationMethod.SEED, months=[3]),
                PropagationConfig(method=PropagationMethod.DIVISION, months=[9, 10]),
            ],
        )
        assert [c.method for c in s.propagation_configs] == [
            PropagationMethod.SEED,
            PropagationMethod.DIVISION,
        ]

    def test_model_validate_from_dicts(self):
        raw = {
            "scientific_name": "Mentha spicata",
            "genus": "Mentha",
            "propagation_configs": [
                {"method": "cutting", "months": [5, 6], "wood_stage": "softwood"},
                {"method": "division", "months": [3, 4]},
            ],
        }
        s = Species.model_validate(raw)
        assert s.propagation_configs[0].method == PropagationMethod.CUTTING
        assert s.propagation_configs[0].wood_stage == WoodStage.SOFTWOOD
        assert s.propagation_configs[1].method == PropagationMethod.DIVISION

    def test_invalid_method_rejected(self):
        with pytest.raises(ValidationError):
            Species(
                scientific_name="Genus species",
                propagation_configs=[{"method": "teleportation"}],
            )


class TestEnvironmentalPhysiologyFields:
    """REQ-001 v4.2 — environmental-physiology fields on Species."""

    def test_defaults_are_none(self):
        s = Species(scientific_name="Genus species")
        assert s.photosynthesis_type is None
        assert s.light_compensation_point_ppfd_min is None
        assert s.light_compensation_point_ppfd_max is None
        assert s.shade_tolerance is None
        assert s.effective_root_depth_cm is None
        assert s.waterlogging_tolerance is None
        assert s.salt_tolerance_class is None
        assert s.salt_tolerance_ece_threshold_ds_m is None
        assert s.salt_tolerance_slope_pct is None
        assert s.soil_ph_preference is None

    def test_valid_photosynthesis_type(self):
        s = Species(scientific_name="Genus species", photosynthesis_type="cam")
        assert s.photosynthesis_type == "cam"

    def test_invalid_photosynthesis_type(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", photosynthesis_type="c5")

    def test_valid_shade_tolerance(self):
        s = Species(scientific_name="Genus species", shade_tolerance="partial_shade")
        assert s.shade_tolerance == "partial_shade"

    def test_invalid_shade_tolerance(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", shade_tolerance="bright")

    def test_valid_waterlogging_tolerance(self):
        s = Species(scientific_name="Genus species", waterlogging_tolerance="sensitive")
        assert s.waterlogging_tolerance == "sensitive"

    def test_invalid_waterlogging_tolerance(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", waterlogging_tolerance="very_tolerant")

    def test_valid_salt_tolerance_class(self):
        s = Species(scientific_name="Genus species", salt_tolerance_class="moderately_sensitive")
        assert s.salt_tolerance_class == "moderately_sensitive"

    def test_invalid_salt_tolerance_class(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", salt_tolerance_class="extreme")


class TestGrowthHabitEnum:
    """Plan WP-1 — growth_habit enum expanded to cover the real botanical range."""

    def test_expanded_values_present(self):
        for value in (
            GrowthHabit.SUBSHRUB,
            GrowthHabit.GRASS,
            GrowthHabit.SUCCULENT,
            GrowthHabit.BULB_GEOPHYTE,
            GrowthHabit.FERN,
            GrowthHabit.AQUATIC,
            GrowthHabit.EPIPHYTE,
        ):
            assert value in GrowthHabit

    def test_species_accepts_new_value(self):
        s = Species(scientific_name="Echinocactus grusonii", growth_habit="succulent")
        assert s.growth_habit == GrowthHabit.SUCCULENT

    def test_invalid_growth_habit_rejected(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", growth_habit="liana")


class TestSpeciesHarvestBehaviour:
    """Plan WP-6 — harvest_pattern / harvested_part / climacteric on Species."""

    def test_defaults_are_none(self):
        s = Species(scientific_name="Genus species")
        assert s.harvest_pattern is None
        assert s.harvested_part is None
        assert s.climacteric is None

    def test_pattern_and_part_are_orthogonal(self):
        # Same harvested part, different patterns (head lettuce vs. cut-and-come-again).
        single = Species(scientific_name="Lactuca sativa", harvested_part="leaf", harvest_pattern="single")
        cont = Species(scientific_name="Lactuca crispa", harvested_part="leaf", harvest_pattern="continuous")
        assert single.harvest_pattern == HarvestPattern.SINGLE
        assert cont.harvest_pattern == HarvestPattern.CONTINUOUS
        assert single.harvested_part == cont.harvested_part == HarvestedPart.LEAF

    def test_climacteric_accepts_atypical(self):
        s = Species(scientific_name="Cucumis melo", climacteric="atypical")
        assert s.climacteric == ClimactericClass.ATYPICAL

    def test_invalid_values_rejected(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", harvest_pattern="sometimes")
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", harvested_part="essence")


class TestCultivarHarvestFields:
    """Plan WP-6 — dtm_reference + bearing-year corridor on Cultivar."""

    def test_defaults_are_none(self):
        c = Cultivar(name="Test", species_key="sp1")
        assert c.dtm_reference is None
        assert c.bearing_start_year_min is None
        assert c.bearing_start_year_max is None

    def test_dtm_reference_set(self):
        c = Cultivar(name="Test", species_key="sp1", days_to_maturity=70, dtm_reference="transplant")
        assert c.dtm_reference == DtmReference.TRANSPLANT

    def test_bearing_year_corridor(self):
        c = Cultivar(name="Apple M9", species_key="sp1", bearing_start_year_min=2, bearing_start_year_max=4)
        assert c.bearing_start_year_min == 2
        assert c.bearing_start_year_max == 4

    def test_bearing_year_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            Cultivar(name="Test", species_key="sp1", bearing_start_year_max=25)

    def test_lcp_range_valid(self):
        s = Species(
            scientific_name="Ficus benjamina",
            light_compensation_point_ppfd_min=6,
            light_compensation_point_ppfd_max=17,
        )
        assert s.light_compensation_point_ppfd_min == 6
        assert s.light_compensation_point_ppfd_max == 17

    def test_lcp_min_negative_rejected(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", light_compensation_point_ppfd_min=-1)

    def test_effective_root_depth_bounds(self):
        s = Species(scientific_name="Genus species", effective_root_depth_cm=60)
        assert s.effective_root_depth_cm == 60

    def test_effective_root_depth_too_low(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", effective_root_depth_cm=-1)

    def test_effective_root_depth_too_high(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", effective_root_depth_cm=501)

    def test_salt_tolerance_ece_threshold_negative_rejected(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", salt_tolerance_ece_threshold_ds_m=-0.5)

    def test_salt_tolerance_slope_negative_rejected(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", salt_tolerance_slope_pct=-1.0)

    def test_salt_tolerance_maas_hoffman_values(self):
        s = Species(
            scientific_name="Genus species",
            salt_tolerance_class="moderately_tolerant",
            salt_tolerance_ece_threshold_ds_m=2.5,
            salt_tolerance_slope_pct=9.9,
        )
        assert s.salt_tolerance_ece_threshold_ds_m == 2.5
        assert s.salt_tolerance_slope_pct == 9.9

    def test_soil_ph_preference_override(self):
        s = Species(
            scientific_name="Vaccinium corymbosum",
            soil_ph_preference={"min_ph": 4.5, "max_ph": 5.5},
        )
        assert s.soil_ph_preference is not None
        assert s.soil_ph_preference.min_ph == 4.5
        assert s.soil_ph_preference.max_ph == 5.5

    def test_soil_ph_preference_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            Species(
                scientific_name="Genus species",
                soil_ph_preference={"min_ph": 1.0, "max_ph": 5.5},
            )

    def test_model_validate_from_seed_dict(self):
        """Seed-import path: model_validate must adopt all new fields from a plain dict."""
        raw = {
            "scientific_name": "Echeveria elegans",
            "genus": "Echeveria",
            "photosynthesis_type": "cam",
            "light_compensation_point_ppfd_min": 10,
            "light_compensation_point_ppfd_max": 15,
            "shade_tolerance": "full_sun",
            "effective_root_depth_cm": 20,
            "waterlogging_tolerance": "sensitive",
            "salt_tolerance_class": "sensitive",
            "salt_tolerance_ece_threshold_ds_m": 1.5,
            "salt_tolerance_slope_pct": 12.0,
            "soil_ph_preference": {"min_ph": 5.5, "max_ph": 6.5},
        }
        s = Species.model_validate(raw)
        assert s.photosynthesis_type == "cam"
        assert s.light_compensation_point_ppfd_min == 10
        assert s.shade_tolerance == "full_sun"
        assert s.effective_root_depth_cm == 20
        assert s.waterlogging_tolerance == "sensitive"
        assert s.salt_tolerance_class == "sensitive"
        assert s.salt_tolerance_ece_threshold_ds_m == 1.5
        assert s.salt_tolerance_slope_pct == 12.0
        assert s.soil_ph_preference is not None
        assert s.soil_ph_preference.min_ph == 5.5
