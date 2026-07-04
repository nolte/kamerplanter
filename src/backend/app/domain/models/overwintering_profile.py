from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    HardinessRating,
    SpringAction,
    TuberStatus,
    WinterAction,
    WinterQuarterLight,
    WinterWatering,
)


class OverwinteringProfile(BaseModel):
    """REQ-022 §OverwinteringProfile (G-002) — overwintering configuration for a
    single plant instance or planting run (dual-support, REQ-013 v2.0).

    Exactly one of ``plant_key`` / ``planting_run_key`` identifies the subject.
    """

    key: str | None = Field(default=None, alias="_key")

    # Subject (dual-support: run primary, standalone plant fallback).
    plant_key: str | None = None
    planting_run_key: str | None = None

    # Hardiness assessment.
    hardiness_zone_min: str | None = None
    hardiness_rating: HardinessRating

    # Winter action (path A in-situ protection or path B relocation).
    winter_action: WinterAction
    winter_action_month: int = Field(ge=1, le=12)

    # Spring reactivation.
    spring_action: SpringAction | None = None
    spring_action_month: int | None = Field(default=None, ge=1, le=12)

    # Winter quarter conditions (path B).
    winter_quarter_key: str | None = None
    winter_quarter_temp_min: float | None = None
    winter_quarter_temp_max: float | None = None
    winter_quarter_light: WinterQuarterLight | None = None
    winter_watering: WinterWatering | None = None

    # Tuber/bulb storage cycle (hardiness_rating == dig_and_store).
    storage_medium: str | None = None
    storage_check_interval_days: int | None = Field(default=None, ge=1, le=365)
    tuber_status: TuberStatus | None = None

    notes: str | None = None
    auto_generated: bool = False
    tenant_key: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _validate_tuber_status(self) -> OverwinteringProfile:
        """``tuber_status`` is only meaningful for the dig-and-store rating."""
        if self.tuber_status is not None and self.hardiness_rating != HardinessRating.DIG_AND_STORE:
            raise ValueError("tuber_status is only valid when hardiness_rating is 'dig_and_store'.")
        return self


class WinterHardinessOverviewEntry(BaseModel):
    """One red (must-relocate) plant in the dashboard hardiness overview."""

    profile_key: str
    plant_key: str | None = None
    planting_run_key: str | None = None
    hardiness_rating: HardinessRating
    winter_action: WinterAction


class WinterHardinessOverview(BaseModel):
    """REQ-022 §Dashboard-Widget "Winterschutz-Übersicht" — aggregate counts per
    traffic-light colour plus the actionable red-plant list."""

    green: int = 0
    yellow: int = 0
    red: int = 0
    total: int = 0
    red_plants: list[WinterHardinessOverviewEntry] = Field(default_factory=list)
