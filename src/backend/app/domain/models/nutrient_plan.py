from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Discriminator, Field, field_validator, model_validator

from app.common.enums import ApplicationMethod, PhaseName, ScheduleMode, SubstrateType


class FertilizerDosage(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False


# ── Method-specific parameters for DeliveryChannel ───────────────────


class FertigationParams(BaseModel):
    method: Literal["fertigation"] = "fertigation"
    runs_per_day: int = Field(default=1, ge=1, le=24)
    duration_seconds: int = Field(default=300, ge=1, le=7200)
    flow_rate_ml_min: float | None = Field(default=None, gt=0)
    tank_key: str | None = None


class DrenchParams(BaseModel):
    method: Literal["drench"] = "drench"
    volume_per_feeding_liters: float = Field(default=1.0, gt=0, le=100)


class FoliarParams(BaseModel):
    method: Literal["foliar"] = "foliar"
    volume_per_spray_liters: float = Field(default=0.5, gt=0, le=10)


class TopDressParams(BaseModel):
    method: Literal["top_dress"] = "top_dress"
    grams_per_plant: float | None = Field(default=None, gt=0)
    grams_per_m2: float | None = Field(default=None, gt=0)


MethodParams = Annotated[
    FertigationParams | DrenchParams | FoliarParams | TopDressParams,
    Discriminator("method"),
]


# ── WateringSchedule ─────────────────────────────────────────────────


class WateringSchedule(BaseModel):
    schedule_mode: ScheduleMode
    weekday_schedule: list[int] = Field(default_factory=list)  # 0=Mo..6=Su
    interval_days: int | None = Field(default=None, ge=1, le=90)
    preferred_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    reminder_hours_before: int = Field(default=2, ge=0, le=24)
    times_per_day: int = Field(default=1, ge=1, le=6)

    @model_validator(mode="after")
    def validate_schedule_mode(self) -> WateringSchedule:
        if self.schedule_mode == ScheduleMode.WEEKDAYS:
            if not self.weekday_schedule:
                raise ValueError("weekday_schedule required for WEEKDAYS mode")
            if any(d < 0 or d > 6 for d in self.weekday_schedule):
                raise ValueError("weekday_schedule values must be 0-6")
        if self.schedule_mode == ScheduleMode.INTERVAL:
            if self.interval_days is None:
                raise ValueError("interval_days required for INTERVAL mode")
        return self


# ── DeliveryChannel ──────────────────────────────────────────────────


class DeliveryChannel(BaseModel):
    channel_id: str = Field(min_length=1, max_length=50)
    label: str = Field(default="", max_length=200)
    application_method: ApplicationMethod
    enabled: bool = True
    notes: str | None = None
    schedule: WateringSchedule | None = None
    target_ec_ms: float | None = Field(default=None, ge=0, le=10)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    fertilizer_dosages: list[FertilizerDosage] = Field(default_factory=list)
    method_params: MethodParams | None = None


# ── NutrientPlanPhaseEntry ───────────────────────────────────────────


class NutrientPlanPhaseEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plan_key: str
    phase_name: PhaseName
    sequence_order: int = Field(ge=1)
    week_start: int = Field(ge=1)
    week_end: int = Field(ge=1)
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    notes: str | None = None
    delivery_channels: list[DeliveryChannel] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("npk_ratio")
    @classmethod
    def validate_npk(cls, v: tuple[float, float, float]) -> tuple[float, float, float]:
        for val in v:
            if val < 0:
                raise ValueError("NPK values must be non-negative")
        return v

    @field_validator("week_end")
    @classmethod
    def validate_week_end(cls, v: int, info) -> int:
        if "week_start" in info.data and v <= info.data["week_start"]:
            raise ValueError("week_end must be greater than week_start")
        return v

    @model_validator(mode="after")
    def validate_unique_channel_ids(self) -> NutrientPlanPhaseEntry:
        if not self.delivery_channels:
            return self
        ids = [ch.channel_id for ch in self.delivery_channels]
        if len(ids) != len(set(ids)):
            raise ValueError("delivery_channels must have unique channel_id values")
        return self


class NutrientPlan(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    recommended_substrate_type: SubstrateType | None = None
    author: str = ""
    is_template: bool = False
    version: str = "1.0"
    tags: list[str] = Field(default_factory=list)
    cloned_from_key: str | None = None
    watering_schedule: WateringSchedule | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_plan_schedule(self) -> NutrientPlan:
        if (
            self.watering_schedule is not None
            and self.watering_schedule.application_method == ApplicationMethod.FERTIGATION
        ):
            raise ValueError(
                "FERTIGATION not allowed for plan-level watering schedule; "
                "use delivery channels with fertigation instead"
            )
        return self

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        return [tag.lower().strip() for tag in v]
