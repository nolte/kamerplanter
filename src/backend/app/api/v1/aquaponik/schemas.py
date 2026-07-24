"""REQ-026 Aquaponics API request/response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    AquaponicSupplementType,
    AquaponicSystemType,
    BiofilterType,
    ClarifierType,
    CyclingStatus,
    FishFeedCategory,
    FishFeedingResponse,
    FishFeedType,
    TemperatureZone,
    WaterTestSource,
)

# ── AquaponicSystem ─────────────────────────────────────────────────────


class AquaponicSystemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    system_type: AquaponicSystemType
    total_volume_liters: float = Field(gt=0)
    grow_area_m2: float = Field(gt=0)
    biofilter_type: BiofilterType | None = None
    biofilter_volume_liters: float | None = Field(default=None, gt=0)
    biofilter_media_ssa_m2_per_m3: float | None = None
    has_clarifier: bool = False
    clarifier_type: ClarifierType | None = None
    has_mineralization: bool = False
    has_vermicompost: bool = False
    daily_feed_target_g: float = Field(default=0, ge=0)
    turnover_rate_per_hour: float | None = None
    outdoor: bool = False
    backup_power: bool = False
    ph_target_min: float = Field(default=6.8, ge=5.0, le=9.0)
    ph_target_max: float = Field(default=7.2, ge=5.0, le=9.0)
    notes: str | None = None


class AquaponicSystemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    system_type: AquaponicSystemType | None = None
    total_volume_liters: float | None = Field(default=None, gt=0)
    grow_area_m2: float | None = Field(default=None, gt=0)
    biofilter_type: BiofilterType | None = None
    biofilter_volume_liters: float | None = Field(default=None, gt=0)
    has_clarifier: bool | None = None
    clarifier_type: ClarifierType | None = None
    has_mineralization: bool | None = None
    has_vermicompost: bool | None = None
    daily_feed_target_g: float | None = Field(default=None, ge=0)
    turnover_rate_per_hour: float | None = None
    outdoor: bool | None = None
    backup_power: bool | None = None
    ph_target_min: float | None = Field(default=None, ge=5.0, le=9.0)
    ph_target_max: float | None = Field(default=None, ge=5.0, le=9.0)
    notes: str | None = None


class AquaponicSystemResponse(BaseModel):
    key: str
    name: str
    system_type: AquaponicSystemType
    total_volume_liters: float
    grow_area_m2: float
    cycling_status: CyclingStatus
    cycling_start_date: date | None = None
    cycled_since: date | None = None
    biofilter_type: BiofilterType | None = None
    biofilter_volume_liters: float | None = None
    has_clarifier: bool = False
    clarifier_type: ClarifierType | None = None
    has_mineralization: bool = False
    has_vermicompost: bool = False
    daily_feed_target_g: float = 0
    turnover_rate_per_hour: float | None = None
    outdoor: bool = False
    backup_power: bool = False
    ph_target_min: float = 6.8
    ph_target_max: float = 7.2
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CyclingStatusUpdate(BaseModel):
    cycling_status: CyclingStatus


# ── FishStock ───────────────────────────────────────────────────────────


class FishStockCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    species_key: str
    count: int = Field(gt=0)
    avg_weight_g: float = Field(gt=0)
    stocking_date: date
    notes: str | None = None


class FishStockUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    count: int | None = Field(default=None, ge=0)
    avg_weight_g: float | None = Field(default=None, gt=0)
    last_weighed_at: date | None = None
    notes: str | None = None


class FishStockResponse(BaseModel):
    key: str
    system_key: str
    name: str
    species_key: str
    count: int
    initial_count: int
    avg_weight_g: float
    total_biomass_kg: float
    stocking_date: date
    mortality_count: int
    last_weighed_at: date | None = None
    notes: str | None = None


class MortalityCreate(BaseModel):
    deaths: int = Field(gt=0)


# ── WaterTest ───────────────────────────────────────────────────────────


class WaterTestCreate(BaseModel):
    ph: float = Field(ge=0, le=14)
    ammonia_tan_mgl: float = Field(ge=0)
    nitrite_mgl: float = Field(ge=0)
    nitrate_mgl: float = Field(ge=0)
    temperature_c: float = Field(ge=0, le=45)
    dissolved_oxygen_mgl: float | None = Field(default=None, ge=0)
    kh_dh: float | None = Field(default=None, ge=0)
    gh_dh: float | None = Field(default=None, ge=0)
    iron_ppm: float | None = Field(default=None, ge=0)
    potassium_ppm: float | None = Field(default=None, ge=0)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    phosphate_ppm: float | None = Field(default=None, ge=0)
    source: WaterTestSource = WaterTestSource.MANUAL
    notes: str | None = None


class WaterTestResponse(BaseModel):
    key: str
    system_key: str
    tested_at: datetime | None = None
    ph: float
    ammonia_tan_mgl: float
    nitrite_mgl: float
    nitrate_mgl: float
    temperature_c: float
    dissolved_oxygen_mgl: float | None = None
    kh_dh: float | None = None
    gh_dh: float | None = None
    iron_ppm: float | None = None
    potassium_ppm: float | None = None
    calcium_ppm: float | None = None
    magnesium_ppm: float | None = None
    phosphate_ppm: float | None = None
    free_ammonia_mgl: float
    source: WaterTestSource
    notes: str | None = None


# ── Feeding ─────────────────────────────────────────────────────────────


class FishFeedingEventCreate(BaseModel):
    feed_brand: str | None = None
    feed_type: FishFeedType = FishFeedType.PELLET
    protein_percent: float | None = Field(default=None, ge=0, le=100)
    amount_g: float = Field(gt=0)
    water_temp_c: float = Field(ge=0, le=45)
    fish_response: FishFeedingResponse = FishFeedingResponse.NORMAL
    notes: str | None = None


class FishFeedingEventResponse(BaseModel):
    key: str
    system_key: str
    stock_key: str
    fed_at: datetime | None = None
    feed_brand: str | None = None
    feed_type: FishFeedType
    protein_percent: float | None = None
    amount_g: float
    water_temp_c: float
    fish_response: FishFeedingResponse
    notes: str | None = None


# ── Supplementation ─────────────────────────────────────────────────────


class SupplementationEventCreate(BaseModel):
    supplement_type: AquaponicSupplementType
    amount_ml: float | None = Field(default=None, gt=0)
    amount_g: float | None = Field(default=None, gt=0)
    target_parameter: str
    measured_before: float | None = None
    measured_after: float | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_amount(self) -> SupplementationEventCreate:
        if self.amount_ml is None and self.amount_g is None:
            raise ValueError("Entweder amount_ml oder amount_g muss angegeben werden.")
        return self


class SupplementationEventResponse(BaseModel):
    key: str
    system_key: str
    applied_at: datetime | None = None
    supplement_type: AquaponicSupplementType
    amount_ml: float | None = None
    amount_g: float | None = None
    target_parameter: str
    measured_before: float | None = None
    measured_after: float | None = None
    notes: str | None = None


# ── FishSpecies (global) ────────────────────────────────────────────────


class RegulatoryNoteResponse(BaseModel):
    country: str
    regulation: str
    requirement: str
    hobby_exempt: bool


class FishSpeciesResponse(BaseModel):
    key: str
    scientific_name: str
    common_name_de: str
    common_name_en: str
    temperature_zone: TemperatureZone
    temperature_min_c: float
    temperature_max_c: float
    temperature_optimal_min_c: float
    temperature_optimal_max_c: float
    temperature_lethal_low_c: float
    temperature_lethal_high_c: float
    ph_min: float
    ph_max: float
    do_minimum_mgl: float
    do_optimal_mgl: float
    do_stress_mgl: float
    max_tan_mgl: float
    max_nitrite_mgl: float
    max_nitrate_mgl: float
    fcr_hobby: float | None = None
    fcr_professional: float | None = None
    feed_type: FishFeedCategory
    max_stocking_density_kg_per_1000l: float
    max_stocking_density_professional_kg_per_1000l: float | None = None
    growth_rate_g_per_day: float | None = None
    market_weight_g: float | None = None
    time_to_market_days: int | None = None
    schooling: bool
    min_group_size: int
    regulatory_notes: list[RegulatoryNoteResponse] = Field(default_factory=list)
    notes_de: str | None = None
    notes_en: str | None = None


# ── Analysis response models ────────────────────────────────────────────


class WaterQualityEvaluationResponse(BaseModel):
    parameter: str
    value: float
    limit: float
    severity: str
    message_de: str
    message_en: str


class CyclingProgressResponse(BaseModel):
    status: CyclingStatus
    progress_percent: float
    stable_days: int
    days_required: int
    estimated_completion: date | None = None
    phase_description_de: str
    phase_description_en: str


class FeedingRecommendationResponse(BaseModel):
    recommended_g: float
    base_rate_percent: float
    temperature_factor: float
    cycling_factor: float
    species_name: str
    biomass_kg: float
    water_temp_c: float
    notes: list[str]


class DeficiencyFindingResponse(BaseModel):
    nutrient: str
    value_ppm: float | None
    target_min_ppm: float
    target_max_ppm: float
    status: str
    recommended_supplement: str
    message_de: str


class DeficiencyReportResponse(BaseModel):
    findings: list[DeficiencyFindingResponse]
    grow_bed_ec_status: str
    grow_bed_ec_message: str


class HealthAlertResponse(BaseModel):
    alert_type: str
    severity: str
    message_de: str
    message_en: str
    recommended_action: str


class CompatiblePlantEntry(BaseModel):
    species_key: str | None = None
    common_name: str | None = None
    scientific_name: str | None = None
    temperature_match: float | None = None
    nutrient_match: float | None = None
    reason: str | None = None
    notes: str | None = None


class CompatiblePlantsResponse(BaseModel):
    fish_species_key: str
    fish_common_name_de: str
    temperature_zone: str
    compatible: list[CompatiblePlantEntry]
    incompatible: list[CompatiblePlantEntry]


class BiomassHistoryResponse(BaseModel):
    """Current biomass snapshot for a fish stock."""

    stock_key: str | None = None
    current_biomass_kg: float
    count: int
    avg_weight_g: float
    last_weighed_at: date | None = None


class MortalityRateResponse(BaseModel):
    """Cumulative mortality figures for a fish stock."""

    stock_key: str | None = None
    mortality_count: int
    initial_count: int
    mortality_rate: float
    mortality_rate_percent: float


class NitrogenCyclePoint(BaseModel):
    """One water-test measurement in the nitrogen-cycle chart series."""

    tested_at: datetime | None = None
    ammonia_tan_mgl: float
    free_ammonia_mgl: float
    nitrite_mgl: float
    nitrate_mgl: float
    ph: float
    temperature_c: float


class FcrAnalysisResponse(BaseModel):
    """Feed-conversion-ratio analysis for an aquaponic system."""

    total_feed_kg: float
    biomass_gain_kg: float
    fcr: float | None = None
    feeding_count: int


class SafetyStatusResponse(BaseModel):
    """Aggregated safety status: water quality plus stocking validation."""

    system_key: str | None = None
    cycling_status: str
    water_quality: list[dict]
    stocking: dict | None = None
