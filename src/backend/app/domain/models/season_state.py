"""REQ-047 §2.1 — the per-site season state.

A :class:`SeasonState` is the persisted, 1:1-per-outdoor/greenhouse-site result
of the season state machine (REQ-047 §2.2). It records the current season phase,
which cascade tier produced it (live weather / climatological / calendar), the
hysteresis counter and the best-available frost dates so the dashboard and the
downstream materialisation / dormancy-care wiring can act on it.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import SeasonPhase, SeasonTriggerTier


class SeasonState(BaseModel):
    """REQ-047 §2.1 — season/winter state of a single outdoor/greenhouse site."""

    key: str | None = Field(default=None, alias="_key")

    season_state_id: str = ""
    site_key: str
    #: Tenant scoping (REQ-024) — inherited from the owning site.
    tenant_key: str = ""

    phase: SeasonPhase = SeasonPhase.GROWING
    #: Which cascade tier determined the current state (UI transparency).
    trigger_tier: SeasonTriggerTier = SeasonTriggerTier.CALENDAR
    #: Natural-language reason key, e.g. ``pages.season.trigger.frostForecast``.
    trigger_reason_i18n_key: str = "pages.season.trigger.unknown"

    entered_phase_at: datetime | None = None
    #: Reference year of the running overwintering season (winter 2026/27 → 2026);
    #: ``None`` while the site is in ``growing`` (season released). Blocks backward
    #: transitions within the same season (hysteresis, REQ-047 §3.3).
    season_year: int | None = None

    last_min_temp_c: float | None = None
    consecutive_signal_days: int = 0
    forecast_first_frost_date: date | None = None
    #: Climatological frost termini (tier 2/3), format ``MM-DD``.
    estimated_first_frost_md: str | None = None
    estimated_last_frost_md: str | None = None

    updated_at: datetime | None = None
    #: Timestamp of the last engine run (also set when no transition occurred).
    evaluated_at: datetime | None = None

    model_config = {"populate_by_name": True}
