from datetime import datetime

from pydantic import BaseModel, Field

# ── WateringSchedule schema ─────────────────────────────────────────

class WateringScheduleSchema(BaseModel):
    schedule_mode: str
    weekday_schedule: list[int] = Field(default_factory=list)
    interval_days: int | None = Field(default=None, ge=1, le=90)
    preferred_time: str | None = None
    application_method: str = "drench"
    reminder_hours_before: int = Field(default=2, ge=0, le=24)


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


class NutrientPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    recommended_substrate_type: str | None = None
    author: str | None = None
    is_template: bool | None = None
    version: str | None = None
    tags: list[str] | None = None
    watering_schedule: WateringScheduleSchema | None = None


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
    target_ec_ms: float = Field(default=1.0, ge=0, le=10)
    target_ph: float = Field(default=6.0, ge=0, le=14)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    feeding_frequency_per_week: int = Field(default=1, ge=1, le=14)
    volume_per_feeding_liters: float | None = Field(default=None, gt=0)
    notes: str | None = None
    fertilizer_dosages: list[FertilizerDosageSchema] = Field(default_factory=list)


class PhaseEntryUpdate(BaseModel):
    phase_name: str | None = None
    sequence_order: int | None = Field(default=None, ge=1)
    week_start: int | None = Field(default=None, ge=1)
    week_end: int | None = Field(default=None, ge=1)
    npk_ratio: tuple[float, float, float] | None = None
    target_ec_ms: float | None = Field(default=None, ge=0, le=10)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    calcium_ppm: float | None = Field(default=None, ge=0)
    magnesium_ppm: float | None = Field(default=None, ge=0)
    feeding_frequency_per_week: int | None = Field(default=None, ge=1, le=14)
    volume_per_feeding_liters: float | None = Field(default=None, gt=0)
    notes: str | None = None
    fertilizer_dosages: list[FertilizerDosageSchema] | None = None


class PhaseEntryResponse(BaseModel):
    key: str
    plan_key: str
    phase_name: str
    sequence_order: int
    week_start: int
    week_end: int
    npk_ratio: tuple[float, float, float]
    target_ec_ms: float
    target_ph: float
    calcium_ppm: float | None
    magnesium_ppm: float | None
    feeding_frequency_per_week: int
    volume_per_feeding_liters: float | None
    notes: str | None
    fertilizer_dosages: list[FertilizerDosageSchema]
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Clone / Assign schemas ──────────────────────────────────────────

class CloneRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=200)
    author: str = ""


class AssignPlanRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""


class FertilizerAssignRequest(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0, le=50)
    optional: bool = False
