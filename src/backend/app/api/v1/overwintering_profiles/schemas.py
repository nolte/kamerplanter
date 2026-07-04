from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    FrostTolerance,
    HardinessRating,
    SpringAction,
    TuberStatus,
    WinterAction,
    WinterQuarterLight,
    WinterWatering,
)


class OverwinteringProfileCreate(BaseModel):
    plant_key: str | None = None
    planting_run_key: str | None = None
    hardiness_zone_min: str | None = Field(default=None, max_length=10)
    hardiness_rating: HardinessRating
    winter_action: WinterAction
    winter_action_month: int = Field(ge=1, le=12)
    spring_action: SpringAction | None = None
    spring_action_month: int | None = Field(default=None, ge=1, le=12)
    winter_quarter_key: str | None = None
    winter_quarter_temp_min: float | None = None
    winter_quarter_temp_max: float | None = None
    winter_quarter_light: WinterQuarterLight | None = None
    winter_watering: WinterWatering | None = None
    storage_medium: str | None = Field(default=None, max_length=200)
    storage_check_interval_days: int | None = Field(default=None, ge=1, le=365)
    tuber_status: TuberStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_tuber_status(self) -> OverwinteringProfileCreate:
        """Mirror the domain rule: ``tuber_status`` only for the dig-and-store
        rating. Enforcing it on the request schema turns an invalid combination
        into a 422 (``RequestValidationError``) instead of a 500 raised by the
        domain model constructor downstream (B2)."""
        if self.tuber_status is not None and self.hardiness_rating != HardinessRating.DIG_AND_STORE:
            raise ValueError("tuber_status is only valid when hardiness_rating is 'dig_and_store'.")
        return self


class OverwinteringProfileUpdate(BaseModel):
    hardiness_zone_min: str | None = Field(default=None, max_length=10)
    hardiness_rating: HardinessRating | None = None
    winter_action: WinterAction | None = None
    winter_action_month: int | None = Field(default=None, ge=1, le=12)
    spring_action: SpringAction | None = None
    spring_action_month: int | None = Field(default=None, ge=1, le=12)
    winter_quarter_key: str | None = None
    winter_quarter_temp_min: float | None = None
    winter_quarter_temp_max: float | None = None
    winter_quarter_light: WinterQuarterLight | None = None
    winter_watering: WinterWatering | None = None
    storage_medium: str | None = Field(default=None, max_length=200)
    storage_check_interval_days: int | None = Field(default=None, ge=1, le=365)
    tuber_status: TuberStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)


class OverwinteringProfileAutoGenerate(BaseModel):
    plant_key: str | None = None
    planting_run_key: str | None = None
    species_key: str | None = None
    site_key: str | None = None
    frost_sensitivity: FrostTolerance | None = None
    species_zone: str | None = Field(default=None, max_length=10)
    site_zone: str | None = Field(default=None, max_length=10)
    winter_action_month: int = Field(default=10, ge=1, le=12)
    spring_action_month: int = Field(default=3, ge=1, le=12)
    winter_quarter_key: str | None = None


class OverwinteringProfileResponse(BaseModel):
    key: str
    plant_key: str | None = None
    planting_run_key: str | None = None
    hardiness_zone_min: str | None = None
    hardiness_rating: HardinessRating
    winter_action: WinterAction
    winter_action_month: int
    spring_action: SpringAction | None = None
    spring_action_month: int | None = None
    winter_quarter_key: str | None = None
    winter_quarter_temp_min: float | None = None
    winter_quarter_temp_max: float | None = None
    winter_quarter_light: WinterQuarterLight | None = None
    winter_watering: WinterWatering | None = None
    storage_medium: str | None = None
    storage_check_interval_days: int | None = None
    tuber_status: TuberStatus | None = None
    notes: str | None = None
    auto_generated: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WinterHardinessOverviewEntryResponse(BaseModel):
    profile_key: str
    plant_key: str | None = None
    planting_run_key: str | None = None
    hardiness_rating: HardinessRating
    winter_action: WinterAction


class WinterHardinessOverviewResponse(BaseModel):
    green: int
    yellow: int
    red: int
    total: int
    red_plants: list[WinterHardinessOverviewEntryResponse]
