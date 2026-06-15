from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.common.enums import (
    ClimactericClass,
    DtmReference,
    FrostTolerance,
    GrowthHabit,
    HarvestedPart,
    HarvestPattern,
    NutrientDemandLevel,
    PlantCategory,
    PlantTrait,
    PropagationDifficulty,
    PropagationMethod,
    RootType,
    Suitability,
    WateringMethod,
    WoodStage,
)
from app.domain.models.botanical_family import PhRange

# ── Environmental-physiology literals (REQ-001 v4.2) ─────────────────
type PhotosynthesisType = Literal["c3", "c4", "cam"]
type ShadeTolerance = Literal["deep_shade", "shade", "partial_shade", "full_sun"]
type WaterloggingTolerance = Literal["sensitive", "moderate", "tolerant"]
type SaltToleranceClass = Literal[
    "sensitive",
    "moderately_sensitive",
    "moderately_tolerant",
    "tolerant",
]

# ── WateringGuide (embedded on Species/Cultivar) ─────────────────────


class SeasonalWateringAdjustment(BaseModel):
    """Seasonal adjustment to watering defaults."""

    months: list[int] = Field(default_factory=list)
    interval_days: int = Field(ge=0, le=90)
    volume_ml_min: int = Field(default=0, ge=0)
    volume_ml_max: int = Field(default=0, ge=0)
    label: str = ""

    @field_validator("months")
    @classmethod
    def validate_months(cls, v: list[int]) -> list[int]:
        for m in v:
            if m < 1 or m > 12:
                raise ValueError(f"Month must be between 1 and 12, got {m}")
        return v


class WateringGuide(BaseModel):
    """Structured watering defaults for a species or cultivar."""

    interval_days: int = Field(default=7, ge=1, le=90)
    volume_ml_min: int = Field(default=100, ge=0)
    volume_ml_max: int = Field(default=500, ge=0)
    watering_method: WateringMethod = WateringMethod.TOP_WATER
    water_quality_hint: str | None = None
    practical_tip: str | None = None
    seasonal_adjustments: list[SeasonalWateringAdjustment] = Field(default_factory=list)


class Cultivar(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    species_key: str
    breeder: str | None = None
    breeding_year: int | None = None
    traits: list[PlantTrait] = Field(default_factory=list)
    patent_status: str = ""
    seed_type: str = ""
    days_to_maturity: int | None = Field(default=None, ge=1, le=1095)
    # ── Ernte-Bezug (REQ-007, Plan WP-6) ──
    dtm_reference: DtmReference | None = Field(
        default=None,
        description="Reference point for days_to_maturity (direct_seed vs. transplant) — "
        "disambiguates the value, as the seed-industry convention differs.",
    )
    bearing_start_year_min: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Earliest standing year with a usable yield (perennial harvest pattern); a corridor.",
    )
    bearing_start_year_max: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="Year of full yield (perennial harvest pattern) — rootstock/planting-stock dependent.",
    )
    disease_resistances: list[str] = Field(default_factory=list)
    watering_guide_override: WateringGuide | None = None
    phase_watering_overrides: dict[str, int] | None = Field(
        default=None,
        description="Per-phase watering interval overrides (phase_name → interval_days)",
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class GrowingPeriod(BaseModel):
    """A self-contained growing period from sowing through harvest/bloom."""

    label: str = ""
    sowing_indoor_weeks_before_last_frost: int | None = Field(default=None, ge=1, le=26)
    sowing_outdoor_after_last_frost_days: int | None = Field(default=None, ge=-60, le=90)
    direct_sow_months: list[int] = Field(default_factory=list)
    growth_months: list[int] = Field(default_factory=list)
    harvest_months: list[int] = Field(default_factory=list)
    bloom_months: list[int] = Field(default_factory=list)
    harvest_from_year: int | None = Field(default=None, ge=1, le=10)
    bloom_from_year: int | None = Field(default=None, ge=1, le=10)

    @field_validator("direct_sow_months", "growth_months", "harvest_months", "bloom_months")
    @classmethod
    def validate_month_lists(cls, v: list[int]) -> list[int]:
        for m in v:
            if m < 1 or m > 12:
                raise ValueError(f"Month must be between 1 and 12, got {m}")
        return v


class PropagationConfig(BaseModel):
    """A single propagation method with its method-specific parameters (REQ-017).

    Replaces the former flat ``propagation_methods``/``propagation_months``/
    ``propagation_notes`` fields: a species may support several methods, and each
    method carries its own timing window, maturity stage and notes (e.g. softwood
    cuttings May–July vs. division in autumn on the same species).
    """

    method: PropagationMethod
    months: list[int] = Field(
        default_factory=list,
        description="Recommended months (1–12) for this method — independent of other methods.",
    )
    wood_stage: WoodStage | None = Field(
        default=None,
        description="Cutting maturity stage; only meaningful for cutting-type methods.",
    )
    difficulty: PropagationDifficulty | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("months")
    @classmethod
    def validate_months(cls, v: list[int]) -> list[int]:
        for m in v:
            if m < 1 or m > 12:
                raise ValueError(f"Month must be between 1 and 12, got {m}")
        return sorted(set(v))


class Species(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family_key: str | None = None
    genus: str = ""
    hardiness_zones: list[str] = Field(default_factory=list)
    native_habitat: str = ""
    growth_habit: GrowthHabit = GrowthHabit.HERB
    root_type: RootType = RootType.FIBROUS
    allelopathy_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    base_temp: float = Field(default=10.0, description="Base temperature for GDD calculation (Celsius)")
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    description: str = ""
    # ── Growing periods (REQ-015-A) — preferred for multi-period species ──
    growing_periods: list[GrowingPeriod] = Field(default_factory=list)
    # ── Legacy flat sowing / harvest fields (REQ-015 §3.8) ──
    # Used when growing_periods is empty — auto-converted to single period by engine.
    sowing_indoor_weeks_before_last_frost: int | None = Field(default=None, ge=1, le=26)
    sowing_outdoor_after_last_frost_days: int | None = Field(default=None, ge=-60, le=90)
    direct_sow_months: list[int] = Field(default_factory=list)
    harvest_months: list[int] = Field(default_factory=list)
    bloom_months: list[int] = Field(default_factory=list)
    harvest_from_year: int | None = Field(default=None, ge=1, le=10)
    bloom_from_year: int | None = Field(default=None, ge=1, le=10)
    frost_sensitivity: FrostTolerance | None = None
    plant_category: PlantCategory | None = None
    nutrient_demand_level: NutrientDemandLevel | None = None
    green_manure_suitable: bool = False
    pruning_months: list[int] = Field(default_factory=list)
    pruning_type: str | None = None
    traits: list[str] = Field(default_factory=list)
    # ── Vermehrung (REQ-017) — structured per-method configs ──
    # Replaces the former flat propagation_methods/months/notes/difficulty fields
    # so that timing and notes attach to the method, not to the whole species.
    propagation_configs: list[PropagationConfig] = Field(default_factory=list)
    allows_harvest: bool = True
    # ── Ernteverhalten (REQ-007, Plan WP-6) — orthogonal axes ──
    harvest_pattern: HarvestPattern | None = Field(
        default=None,
        description="Lifetime harvest pattern (single/continuous/perennial). Distinct from the "
        "per-event HarvestType; orthogonal to harvested_part.",
    )
    harvested_part: HarvestedPart | None = Field(
        default=None,
        description="The plant part that is harvested. Orthogonal to harvest_pattern.",
    )
    climacteric: ClimactericClass | None = Field(
        default=None,
        description="Post-harvest ripening behaviour of fruit (climacteric/non/atypical) — drives "
        "ripen-after-harvest and storage logic.",
    )
    # ── Anbaubedingungen (cultivation conditions) ──
    container_suitable: Suitability | None = None
    recommended_container_volume_l: str | None = None
    min_container_depth_cm: int | None = Field(default=None, ge=0, le=200)
    mature_height_cm: str | None = None
    mature_width_cm: str | None = None
    spacing_cm: str | None = None
    indoor_suitable: Suitability | None = None
    balcony_suitable: Suitability | None = None
    greenhouse_recommended: bool = False
    support_required: bool = False
    watering_guide: WateringGuide | None = None
    default_nutrient_plan_key: str | None = Field(
        default=None,
        description="Default NutrientPlan for this species — used as fallback when no plant-specific plan is assigned",
    )
    # ── Umgebungs-Physiologie (REQ-001 v4.2) ──
    # Light compensation point (LCP) drives the site-suitability check; modelled as a
    # range because LCP is acclimation-plastic (shade- vs. sun-adapted).
    photosynthesis_type: PhotosynthesisType | None = Field(
        default=None,
        description="Photosynthesis pathway as a WUE/transpiration modifier for VPD/irrigation logic "
        "('cam' = inverted nocturnal stomata logic). Not a standalone drought predictor.",
    )
    light_compensation_point_ppfd_min: int | None = Field(
        default=None,
        ge=0,
        description="Lower LCP bound in µmol/m²/s (shade-adapted) — drives 'too dark' site warning.",
    )
    light_compensation_point_ppfd_max: int | None = Field(
        default=None,
        ge=0,
        description="Upper LCP bound in µmol/m²/s (sun-adapted).",
    )
    shade_tolerance: ShadeTolerance | None = Field(
        default=None,
        description="Qualitative shade/sun exposure for placement — complements LCP.",
    )
    effective_root_depth_cm: int | None = Field(
        default=None,
        ge=0,
        le=500,
        description="Typical effective rooting depth for irrigation depth / crop steering (plastic guideline).",
    )
    waterlogging_tolerance: WaterloggingTolerance | None = Field(
        default=None,
        description="Root-zone waterlogging/anoxia tolerance — drives drainage recommendation and watering cap.",
    )
    salt_tolerance_class: SaltToleranceClass | None = Field(
        default=None,
        description="Qualitative Maas-Hoffman salt tolerance class (S/MS/MT/T).",
    )
    salt_tolerance_ece_threshold_ds_m: float | None = Field(
        default=None,
        ge=0,
        description="Maas-Hoffman threshold ECe in dS/m (= mS/cm) above which yield declines (parameter 'a').",
    )
    salt_tolerance_slope_pct: float | None = Field(
        default=None,
        ge=0,
        description="Maas-Hoffman yield-loss slope in %/dS/m above threshold (parameter 'b').",
    )
    soil_ph_preference: PhRange | None = Field(
        default=None,
        description="Species-specific pH preference (min_ph, max_ph) — optional override of the "
        "BotanicalFamily default; gates pH-dependent micronutrient availability (REQ-004).",
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator(
        "direct_sow_months",
        "harvest_months",
        "bloom_months",
        "pruning_months",
    )
    @classmethod
    def validate_month_lists(cls, v: list[int]) -> list[int]:
        for m in v:
            if m < 1 or m > 12:
                raise ValueError(f"Month must be between 1 and 12, got {m}")
        return sorted(set(v))

    @field_validator("scientific_name")
    @classmethod
    def validate_binomial(cls, v: str) -> str:
        parts = v.strip().split()
        if len(parts) < 2:
            raise ValueError("Scientific name must follow binomial nomenclature (e.g., 'Genus species')")
        return v.strip()

    @field_validator("hardiness_zones")
    @classmethod
    def validate_hardiness_zones(cls, v: list[str]) -> list[str]:
        import re

        for zone in v:
            if not re.match(r"^\d{1,2}[ab]?$", zone):
                raise ValueError(f"Invalid USDA hardiness zone format: '{zone}'")
        return v
