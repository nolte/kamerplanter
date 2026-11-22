"""REQ-046 §3.6a (#2934) — the weather fetch's run record and status.

The fetch task writes one :class:`WeatherFetchRun` per run into a dedicated status
document (not the ``SystemSettings`` singleton, which admin PUTs rewrite whole). The
document keeps the newest run and the newest *successful* run: the interval counts
from the latter, the admin status shows both.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import WeatherFetchTrigger

#: The smallest and default fetch interval in hours (operator decision 2026-11-17).
MIN_FETCH_INTERVAL_HOURS = 6
#: The largest interval an admin may set — one week; a longer gap leaves frost
#: warnings and irrigation demand on stale forecasts.
MAX_FETCH_INTERVAL_HOURS = 168
#: How long a manual fetch blocks the next one (R6).
MANUAL_FETCH_COOLDOWN_SECONDS = 600


class WeatherFetchRun(BaseModel):
    """One finished fetch run, scheduled or manual.

    ``sites`` counts the sites the run was meant to fetch (enabled config, site with
    GPS, owning tenant active); ``sites_written`` those that stored at least one
    forecast, ``sites_failed`` those whose source chain raised. ``error_type`` names
    the class of a runtime error that aborted the whole run — never its message.
    """

    trigger: WeatherFetchTrigger
    started_at: datetime
    finished_at: datetime
    success: bool
    sites: int = Field(default=0, ge=0)
    sites_written: int = Field(default=0, ge=0)
    sites_failed: int = Field(default=0, ge=0)
    sites_skipped: int = Field(default=0, ge=0)
    forecasts_written: int = Field(default=0, ge=0)
    error_type: str | None = None


class WeatherFetchStatus(BaseModel):
    """The stored status document: newest run and newest successful run."""

    last_run: WeatherFetchRun | None = None
    last_success: WeatherFetchRun | None = None


def is_successful_run(*, aborted: bool, sites: int, sites_written: int) -> bool:
    """The success rule of acceptance-3 (operator decision 2026-11-17).

    A run succeeds when it ended without a runtime error and wrote at least one
    site — or had no site to fetch at all (nothing configured is not a failure).
    """
    if aborted:
        return False
    return sites == 0 or sites_written >= 1
