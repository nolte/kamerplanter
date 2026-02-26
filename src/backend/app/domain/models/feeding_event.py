from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ApplicationMethod


class FeedingEventFertilizer(BaseModel):
    fertilizer_key: str
    ml_applied: float = Field(gt=0)


class FeedingEvent(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    plant_key: str
    timestamp: datetime | None = None
    application_method: ApplicationMethod = ApplicationMethod.FERTIGATION
    is_supplemental: bool = False
    tank_fill_event_key: str | None = None
    volume_applied_liters: float = Field(gt=0)
    fertilizers_used: list[FeedingEventFertilizer] = Field(default_factory=list)
    measured_ec_before: float | None = Field(default=None, ge=0)
    measured_ec_after: float | None = Field(default=None, ge=0)
    measured_ph_before: float | None = Field(default=None, ge=0, le=14)
    measured_ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
