from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import CycleType, PhotoperiodType


class LifecycleCreate(BaseModel):
    species_key: str
    cycle_type: CycleType = CycleType.ANNUAL
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = Field(default=None, ge=1)
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = Field(default=None, ge=0, le=24)


class LifecycleResponse(BaseModel):
    key: str
    species_key: str
    cycle_type: CycleType
    typical_lifespan_years: int | None
    dormancy_required: bool
    vernalization_required: bool
    vernalization_min_days: int | None
    photoperiod_type: PhotoperiodType
    critical_day_length_hours: float | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
