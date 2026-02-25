from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import CycleType, PhotoperiodType, StressTolerance


class GrowthPhase(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    display_name: str = ""
    lifecycle_key: str = ""
    typical_duration_days: int = Field(ge=1)
    sequence_order: int = Field(ge=0)
    is_terminal: bool = False
    allows_harvest: bool = False
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class LifecycleConfig(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    species_key: str = ""
    cycle_type: CycleType = CycleType.ANNUAL
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = Field(default=None, ge=1)
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = Field(default=None, ge=0, le=24)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_biennial_vernalization(self) -> "LifecycleConfig":
        if self.cycle_type == CycleType.BIENNIAL and not self.vernalization_required:
            raise ValueError("Biennial plants must have vernalization_required=True")
        return self
