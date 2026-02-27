from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import ApplicationMethod, PhaseName, ScheduleMode, SubstrateType


class FertilizerDosage(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False


class NutrientPlanPhaseEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plan_key: str
    phase_name: PhaseName
    sequence_order: int = Field(ge=1)
    week_start: int = Field(ge=1)
    week_end: int = Field(ge=1)
    npk_ratio: tuple[float, float, float] = (0.0, 0.0, 0.0)
    target_ec_ms: float = Field(default=1.0, ge=0, le=10)
    target_ph: float = Field(default=6.0, ge=0, le=14)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    feeding_frequency_per_week: int = Field(default=1, ge=1, le=14)
    volume_per_feeding_liters: float | None = Field(default=None, gt=0)
    notes: str | None = None
    fertilizer_dosages: list[FertilizerDosage] = Field(default_factory=list)
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


class WateringSchedule(BaseModel):
    schedule_mode: ScheduleMode
    weekday_schedule: list[int] = Field(default_factory=list)  # 0=Mo..6=Su
    interval_days: int | None = Field(default=None, ge=1, le=90)
    preferred_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    reminder_hours_before: int = Field(default=2, ge=0, le=24)

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
        if self.application_method == ApplicationMethod.FERTIGATION:
            raise ValueError("FERTIGATION not allowed for watering schedule")
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

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        return [tag.lower().strip() for tag in v]
