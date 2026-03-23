from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── WateringSchedule schema ─────────────────────────────────────────


class WateringScheduleSchema(BaseModel):
    schedule_mode: str
    weekday_schedule: list[int] = Field(default_factory=list)
    interval_days: int | None = Field(default=None, ge=1, le=90)
    preferred_time: str | None = None
    application_method: str = "drench"
    reminder_hours_before: int = Field(default=2, ge=0, le=24)
    times_per_day: int = Field(default=1, ge=1, le=6)


# ── Method-specific parameter schemas ───────────────────────────────


class FertigationParamsSchema(BaseModel):
    method: Literal["fertigation"] = "fertigation"
    runs_per_day: int = Field(default=1, ge=1, le=24)
    duration_seconds: int = Field(default=300, ge=1, le=7200)
    flow_rate_ml_min: float | None = Field(default=None, gt=0)


class DrenchParamsSchema(BaseModel):
    method: Literal["drench"] = "drench"
    volume_per_feeding_liters: float = Field(default=1.0, gt=0, le=100)


class FoliarParamsSchema(BaseModel):
    method: Literal["foliar"] = "foliar"
    volume_per_spray_liters: float = Field(default=0.5, gt=0, le=10)


class TopDressParamsSchema(BaseModel):
    method: Literal["top_dress"] = "top_dress"
    grams_per_plant: float | None = Field(default=None, gt=0)
    grams_per_m2: float | None = Field(default=None, gt=0)


# ── DeliveryChannel schema ──────────────────────────────────────────


class DeliveryChannelSchema(BaseModel):
    channel_id: str = Field(min_length=1, max_length=50)
    label: str = Field(default="", max_length=200)
    application_method: str
    enabled: bool = True
    notes: str | None = None
    schedule: WateringScheduleSchema | None = None
    target_ec_ms: float | None = Field(default=None, ge=0, le=10)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    fertilizer_dosages: list[FertilizerDosageSchema] = Field(default_factory=list)
    method_params: FertigationParamsSchema | DrenchParamsSchema | FoliarParamsSchema | TopDressParamsSchema | None = (
        None
    )


class ChannelFertilizerAssignRequest(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False
    mixing_order: int = Field(default=0, ge=0)


# ── NutrientPlan schemas ────────────────────────────────────────────


class NutrientPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    recommended_substrate_type: str | None = None
    reference_substrate_type: str | None = None
    author: str = ""
    is_template: bool = False
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)
    watering_schedule: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = Field(default=None, ge=0, le=100)
    cycle_restart_from_sequence: int | None = Field(default=None, ge=1)


class NutrientPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    recommended_substrate_type: str | None = None
    reference_substrate_type: str | None = None
    author: str | None = None
    is_template: bool | None = None
    version: str | None = None
    tags: list[str] | None = None
    watering_schedule: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = Field(default=None, ge=0, le=100)
    cycle_restart_from_sequence: int | None = Field(default=None, ge=1)


class NutrientPlanResponse(BaseModel):
    key: str
    name: str
    description: str
    recommended_substrate_type: str | None
    reference_substrate_type: str = "soil"
    author: str
    is_template: bool
    version: str
    tags: list[str]
    cloned_from_key: str | None
    watering_schedule: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = None
    cycle_restart_from_sequence: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── PhaseEntry schemas ──────────────────────────────────────────────


class FertilizerDosageSchema(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False
    mixing_order: int = Field(default=0, ge=0)


class PhaseEntryCreate(BaseModel):
    phase_name: str
    sequence_order: int = Field(ge=1)
    week_start: int = Field(ge=1)
    week_end: int = Field(ge=1)
    is_recurring: bool = False
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    target_ec_ms: float | None = Field(default=None, ge=0, le=10)
    reference_ec_ms: float | None = Field(default=None, ge=0, le=10)
    target_calcium_ppm: float | None = Field(default=None, ge=0)
    target_magnesium_ppm: float | None = Field(default=None, ge=0)
    reference_base_ec: float = Field(default=0.0, ge=0, le=5)
    notes: str | None = None
    delivery_channels: list[DeliveryChannelSchema] = Field(default_factory=list)
    watering_schedule_override: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = Field(default=None, ge=0, le=100)


class PhaseEntryUpdate(BaseModel):
    phase_name: str | None = None
    sequence_order: int | None = Field(default=None, ge=1)
    week_start: int | None = Field(default=None, ge=1)
    week_end: int | None = Field(default=None, ge=1)
    is_recurring: bool | None = None
    npk_ratio: tuple[float, float, float] | None = None
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    target_ec_ms: float | None = Field(default=None, ge=0, le=10)
    reference_ec_ms: float | None = Field(default=None, ge=0, le=10)
    target_calcium_ppm: float | None = Field(default=None, ge=0)
    target_magnesium_ppm: float | None = Field(default=None, ge=0)
    reference_base_ec: float | None = Field(default=None, ge=0, le=5)
    notes: str | None = None
    delivery_channels: list[DeliveryChannelSchema] | None = None
    watering_schedule_override: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = Field(default=None, ge=0, le=100)


class PhaseEntryResponse(BaseModel):
    key: str
    plan_key: str
    phase_name: str
    sequence_order: int
    week_start: int
    week_end: int
    is_recurring: bool = False
    npk_ratio: tuple[float, float, float]
    calcium_ppm: float | None
    magnesium_ppm: float | None
    target_ec_ms: float | None = None
    reference_ec_ms: float | None = None
    target_calcium_ppm: float | None = None
    target_magnesium_ppm: float | None = None
    reference_base_ec: float = 0.0
    notes: str | None
    delivery_channels: list[DeliveryChannelSchema] = Field(default_factory=list)
    watering_schedule_override: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Clone / Assign schemas ──────────────────────────────────────────


class CloneRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=200)
    author: str = ""


class AssignPlanRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""


# ── Water Mix Recommendation schemas ─────────────────────────────────


class CalMagCorrectionResponse(BaseModel):
    calcium_deficit_ppm: float
    magnesium_deficit_ppm: float
    ca_mg_ratio: float | None = None
    ca_mg_ratio_warning: str | None = None
    needs_correction: bool


class MixAlternativeResponse(BaseModel):
    ro_percent: int
    ec_headroom: float
    trade_off: str


class WaterMixRecommendationDetail(BaseModel):
    recommended_ro_percent: int
    ec_headroom: float
    effective_ec_ms: float
    available_ec_for_nutrients: float
    target_ec_ms: float
    substrate_type: str
    min_headroom_ratio: float
    reasoning: str
    alternatives: list[MixAlternativeResponse]
    calmag_correction: CalMagCorrectionResponse | None = None


class WaterMixRecommendationResponse(BaseModel):
    recommendation: WaterMixRecommendationDetail
    plan_name: str
    plan_key: str
    phase_name: str
    sequence_order: int
    site_name: str
    site_key: str


class WaterMixBatchRecommendationResponse(BaseModel):
    recommendations: list[WaterMixRecommendationResponse]
    site_name: str
    site_key: str
    plan_name: str
    plan_key: str


# ── Dosage Calculation schemas (REQ-004 §4b) ─────────────────────────


class CalculateDosagesRequest(BaseModel):
    site_key: str
    phase_sequence_order: int = Field(ge=1)
    channel_id: str | None = None
    volume_liters: float = Field(default=10.0, gt=0, le=10000)
    ro_percent_override: int | None = Field(default=None, ge=0, le=100)


class DosageEntryResponse(BaseModel):
    product_name: str
    fertilizer_key: str | None = None
    ml_per_liter: float
    total_ml: float
    ec_contribution: float
    source: str
    mixing_order: int = 0


class EffectiveWaterResponse(BaseModel):
    ec_ms: float
    ph: float
    alkalinity_ppm: float
    calcium_ppm: float
    magnesium_ppm: float
    chlorine_ppm: float
    chloramine_ppm: float


class CalMagCorrectionDetailResponse(BaseModel):
    calcium_deficit_ppm: float
    magnesium_deficit_ppm: float
    ca_mg_ratio: float | None = None
    ca_mg_ratio_warning: str | None = None
    needs_correction: bool


class EcBudgetSummaryResponse(BaseModel):
    ec_base_water: float
    ec_calmag: float
    ec_ph_reserve: float
    ec_fertilizers: float
    ec_final: float


class CalculateDosagesResponse(BaseModel):
    phase_name: str
    channel_id: str
    target_ec_ms: float
    effective_water: EffectiveWaterResponse | None = None
    ro_percent_used: int
    calmag_correction: CalMagCorrectionDetailResponse | None = None
    calmag_dosage: DosageEntryResponse | None = None
    ec_budget: EcBudgetSummaryResponse
    scaling_factor: float
    dosages: list[DosageEntryResponse]
    mixing_instructions: list[str]
    warnings: list[str]
    reference_ec_ms: float | None = None
    substrate_correction_applied: bool = False
