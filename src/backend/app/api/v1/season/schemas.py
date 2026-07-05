"""REQ-047 §4.4 — API response schemas for the season state."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.common.enums import SeasonPhase, SeasonTriggerTier


class SeasonStateResponse(BaseModel):
    """The current season state of one outdoor/greenhouse site."""

    site_key: str
    season_state_id: str = ""
    phase: SeasonPhase
    trigger_tier: SeasonTriggerTier
    trigger_reason_i18n_key: str
    season_year: int | None = None
    entered_phase_at: datetime | None = None
    last_min_temp_c: float | None = None
    forecast_first_frost_date: date | None = None
    estimated_first_frost_md: str | None = None
    estimated_last_frost_md: str | None = None
    evaluated_at: datetime | None = None


class SeasonOverviewResponse(BaseModel):
    """Aggregated season states across all outdoor/greenhouse sites of a tenant."""

    states: list[SeasonStateResponse]
