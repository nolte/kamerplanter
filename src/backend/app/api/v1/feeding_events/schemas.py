
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

# ── FeedingEvent schemas ────────────────────────────────────────────

class FeedingFertilizerSchema(BaseModel):
    fertilizer_key: str
    ml_applied: float = Field(gt=0)


class FeedingEventCreate(BaseModel):
    plant_key: str
    application_method: str = "fertigation"
    is_supplemental: bool = False
    tank_fill_event_key: str | None = None
    volume_applied_liters: float = Field(gt=0)
    fertilizers_used: list[FeedingFertilizerSchema] = Field(default_factory=list)
    measured_ec_before: float | None = Field(default=None, ge=0)
    measured_ec_after: float | None = Field(default=None, ge=0)
    measured_ph_before: float | None = Field(default=None, ge=0, le=14)
    measured_ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    notes: str | None = None


class FeedingEventUpdate(BaseModel):
    application_method: str | None = None
    is_supplemental: bool | None = None
    volume_applied_liters: float | None = Field(default=None, gt=0)
    measured_ec_before: float | None = Field(default=None, ge=0)
    measured_ec_after: float | None = Field(default=None, ge=0)
    measured_ph_before: float | None = Field(default=None, ge=0, le=14)
    measured_ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    notes: str | None = None


class FeedingEventResponse(BaseModel):
    key: str
    plant_key: str
    timestamp: datetime | None
    application_method: str
    is_supplemental: bool
    tank_fill_event_key: str | None
    volume_applied_liters: float
    fertilizers_used: list[FeedingFertilizerSchema]
    measured_ec_before: float | None
    measured_ec_after: float | None
    measured_ph_before: float | None
    measured_ph_after: float | None
    runoff_ec: float | None
    runoff_ph: float | None
    runoff_volume_liters: float | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
