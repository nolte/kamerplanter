
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

# ── Snapshot ────────────────────────────────────────────────────────

class FertilizerSnapshotSchema(BaseModel):
    product_key: str | None = None
    product_name: str
    ml_per_liter: float = Field(gt=0)


# ── WateringEvent schemas ──────────────────────────────────────────

class WateringEventCreate(BaseModel):
    application_method: str = "drench"
    is_supplemental: bool = False
    volume_liters: float = Field(gt=0)
    plant_keys: list[str] = Field(min_length=1)
    tank_fill_event_key: str | None = None
    nutrient_plan_key: str | None = None
    fertilizers_used: list[FertilizerSnapshotSchema] = Field(default_factory=list)
    target_ec: float | None = Field(default=None, ge=0)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    water_source: str | None = None
    performed_by: str | None = None
    notes: str | None = None


class WateringEventResponse(BaseModel):
    key: str
    watered_at: datetime | None
    application_method: str
    is_supplemental: bool
    volume_liters: float
    plant_keys: list[str]
    tank_fill_event_key: str | None
    nutrient_plan_key: str | None
    fertilizers_used: list[FertilizerSnapshotSchema]
    target_ec: float | None
    target_ph: float | None
    measured_ec: float | None
    measured_ph: float | None
    runoff_ec: float | None
    runoff_ph: float | None
    water_source: str | None
    performed_by: str | None
    notes: str | None
    created_at: datetime | None = None


class WateringEventWithWarnings(BaseModel):
    event: WateringEventResponse
    warnings: list[dict]


class MethodStats(BaseModel):
    method: str
    count: int
    total_volume: float


class WateringStatsResponse(BaseModel):
    total_events: int
    total_volume: float
    by_method: list[MethodStats]


# ── Confirm schemas ──────────────────────────────────────────────────

class WateringConfirmRequest(BaseModel):
    run_key: str
    task_key: str
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    volume_liters: float | None = Field(default=None, gt=0)
    overrides: dict | None = None


class WateringQuickConfirmRequest(BaseModel):
    run_key: str
    task_key: str


class WateringConfirmResponse(BaseModel):
    watering_event_key: str
    feeding_events_created: int
    task_completed: bool
    warnings: list[dict] = Field(default_factory=list)


# ── Volume suggestion schemas ─────────────────────────────────────

class VolumeSuggestionRequest(BaseModel):
    plant_key: str
    reference_date: str | None = Field(
        default=None,
        description="ISO date for seasonal adjustment (defaults to today)",
    )
    hemisphere: str = Field(default="north", pattern="^(north|south)$")


class VolumeSuggestionResponse(BaseModel):
    volume_ml: int = Field(description="Recommended volume in milliliters")
    volume_ml_min: int = Field(description="Lower bound of recommended range")
    volume_ml_max: int = Field(description="Upper bound of recommended range")
    source: str = Field(description="Which data source determined the volume")
    adjustments: list[str] = Field(default_factory=list, description="Applied adjustments")
