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
    method_params: (
        FertigationParamsSchema | DrenchParamsSchema | FoliarParamsSchema | TopDressParamsSchema | None
    ) = None


class ChannelFertilizerAssignRequest(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False


# ── NutrientPlan schemas ────────────────────────────────────────────

class NutrientPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    recommended_substrate_type: str | None = None
    author: str = ""
    is_template: bool = False
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)
    watering_schedule: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = Field(default=None, ge=0, le=100)


class NutrientPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    recommended_substrate_type: str | None = None
    author: str | None = None
    is_template: bool | None = None
    version: str | None = None
    tags: list[str] | None = None
    watering_schedule: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = Field(default=None, ge=0, le=100)


class NutrientPlanResponse(BaseModel):
    key: str
    name: str
    description: str
    recommended_substrate_type: str | None
    author: str
    is_template: bool
    version: str
    tags: list[str]
    cloned_from_key: str | None
    watering_schedule: WateringScheduleSchema | None = None
    water_mix_ratio_ro_percent: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── PhaseEntry schemas ──────────────────────────────────────────────

class FertilizerDosageSchema(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False


class PhaseEntryCreate(BaseModel):
    phase_name: str
    sequence_order: int = Field(ge=1)
    week_start: int = Field(ge=1)
    week_end: int = Field(ge=1)
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    notes: str | None = None
    delivery_channels: list[DeliveryChannelSchema] = Field(default_factory=list)


class PhaseEntryUpdate(BaseModel):
    phase_name: str | None = None
    sequence_order: int | None = Field(default=None, ge=1)
    week_start: int | None = Field(default=None, ge=1)
    week_end: int | None = Field(default=None, ge=1)
    npk_ratio: tuple[float, float, float] | None = None
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    notes: str | None = None
    delivery_channels: list[DeliveryChannelSchema] | None = None


class PhaseEntryResponse(BaseModel):
    key: str
    plan_key: str
    phase_name: str
    sequence_order: int
    week_start: int
    week_end: int
    npk_ratio: tuple[float, float, float]
    calcium_ppm: float | None
    magnesium_ppm: float | None
    notes: str | None
    delivery_channels: list[DeliveryChannelSchema] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Clone / Assign schemas ──────────────────────────────────────────

class CloneRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=200)
    author: str = ""


class AssignPlanRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""


