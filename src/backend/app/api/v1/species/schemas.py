from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import FrostTolerance, GrowthHabit, PlantCategory, RootType, Suitability
from app.domain.models.species import GrowingPeriod, WateringGuide


class SpeciesCreate(BaseModel):
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family_key: str | None = None
    genus: str = ""
    hardiness_zones: list[str] = Field(default_factory=list)
    native_habitat: str = ""
    growth_habit: GrowthHabit = GrowthHabit.HERB
    root_type: RootType = RootType.FIBROUS
    allelopathy_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    base_temp: float = 10.0
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    description: str = ""
    sowing_indoor_weeks_before_last_frost: int | None = None
    sowing_outdoor_after_last_frost_days: int | None = None
    direct_sow_months: list[int] = Field(default_factory=list)
    harvest_months: list[int] = Field(default_factory=list)
    bloom_months: list[int] = Field(default_factory=list)
    harvest_from_year: int | None = None
    bloom_from_year: int | None = None
    frost_sensitivity: FrostTolerance | None = None
    plant_category: PlantCategory | None = None
    allows_harvest: bool = True
    growing_periods: list[GrowingPeriod] = Field(default_factory=list)
    container_suitable: Suitability | None = None
    recommended_container_volume_l: str | None = None
    min_container_depth_cm: int | None = None
    mature_height_cm: str | None = None
    mature_width_cm: str | None = None
    spacing_cm: str | None = None
    indoor_suitable: Suitability | None = None
    balcony_suitable: Suitability | None = None
    greenhouse_recommended: bool = False
    support_required: bool = False
    watering_guide: WateringGuide | None = None
    default_nutrient_plan_key: str | None = None


class SpeciesResponse(BaseModel):
    key: str
    scientific_name: str
    common_names: list[str]
    family_key: str | None
    family_name: str | None = None
    genus: str
    hardiness_zones: list[str]
    native_habitat: str
    growth_habit: GrowthHabit
    root_type: RootType
    allelopathy_score: float
    base_temp: float
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    description: str = ""
    sowing_indoor_weeks_before_last_frost: int | None = None
    sowing_outdoor_after_last_frost_days: int | None = None
    direct_sow_months: list[int] = Field(default_factory=list)
    harvest_months: list[int] = Field(default_factory=list)
    bloom_months: list[int] = Field(default_factory=list)
    harvest_from_year: int | None = None
    bloom_from_year: int | None = None
    frost_sensitivity: FrostTolerance | None = None
    plant_category: PlantCategory | None = None
    allows_harvest: bool = True
    growing_periods: list[GrowingPeriod] = Field(default_factory=list)
    container_suitable: Suitability | None = None
    recommended_container_volume_l: str | None = None
    min_container_depth_cm: int | None = None
    mature_height_cm: str | None = None
    mature_width_cm: str | None = None
    spacing_cm: str | None = None
    indoor_suitable: Suitability | None = None
    balcony_suitable: Suitability | None = None
    greenhouse_recommended: bool = False
    support_required: bool = False
    watering_guide: WateringGuide | None = None
    default_nutrient_plan_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SpeciesListResponse(BaseModel):
    items: list[SpeciesResponse]
    total: int
    offset: int
    limit: int
