from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import (
    FrostTolerance,
    GrowthHabit,
    NutrientDemandLevel,
    PlantCategory,
    PlantTrait,
    RootType,
    Suitability,
    WateringMethod,
)

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
    propagation_methods: list[str] = Field(default_factory=list)
    propagation_difficulty: str | None = None
    allows_harvest: bool = True
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("direct_sow_months", "harvest_months", "bloom_months", "pruning_months")
    @classmethod
    def validate_month_lists(cls, v: list[int]) -> list[int]:
        for m in v:
            if m < 1 or m > 12:
                raise ValueError(f"Month must be between 1 and 12, got {m}")
        return v

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
