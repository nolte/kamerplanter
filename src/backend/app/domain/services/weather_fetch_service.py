"""REQ-046 §3.6a (#2934) — when the weather is fetched, and who may start a fetch.

The fetch cadence is an interval in hours (``fetch_interval_hours``, platform-admin
setting, DB over env, minimum 6). An hourly beat runs ``fetch_weather_forecasts``,
which asks :meth:`WeatherFetchService.is_due` first and returns early when the
interval since the newest *successful* run has not passed — so a changed interval
applies on the next tick, without a restart, and a failed run is retried on the
next tick.

A manual fetch (platform admin) is a regular run that skips the due-check: it is
refused while any run holds the running lock (409) and within the cooldown after
the previous manual fetch (429 + ``Retry-After``).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

import structlog
from pydantic import BaseModel

from app.common.datetimes import now_utc
from app.common.exceptions import (
    WeatherFetchCooldownError,
    WeatherFetchDisabledError,
    WeatherFetchRunningError,
    WeatherFetchUnavailableError,
)
from app.domain.interfaces.weather_fetch import (
    IWeatherFetchGate,
    IWeatherFetchStatusRepository,
    WeatherFetchGateUnavailableError,
)
from app.domain.models.weather_fetch import MANUAL_FETCH_COOLDOWN_SECONDS, WeatherFetchRun, WeatherFetchStatus

logger = structlog.get_logger(__name__)

#: The beat ticks hourly at minute 0, a run starts a few seconds after it. Without a
#: tolerance a run started at 06:00:05 would not be due at the 12:00:01 tick and the
#: cadence would slip by one hour per interval.
DUE_TOLERANCE = timedelta(minutes=5)

#: How long a run may hold the running lock. A run normally ends within minutes; the
#: expiry only matters for a worker that died mid-run, and stays below the next tick.
RUN_LOCK_TTL_SECONDS = 55 * 60
#: Celery time limits of the fetch task, both below the lock TTL so the lock never
#: expires under a run that is still going (security review S1, 2026-11-22). The soft
#: limit raises ``SoftTimeLimitExceeded`` in the task, which records the run as failed
#: and releases the lock; the hard limit kills a run that ignores it — the lock then
#: expires on its own, still before another run could start next to a live one.
RUN_SOFT_TIME_LIMIT_SECONDS = 45 * 60
RUN_TIME_LIMIT_SECONDS = 50 * 60

#: Sentinel of :meth:`WeatherFetchService.acquire_run_lock` — the lock store is down.
LOCK_UNAVAILABLE = ""


class WeatherFetchOverview(BaseModel):
    """What the admin status shows (acceptance-4/-6)."""

    interval_hours: int
    last_run: WeatherFetchRun | None = None
    last_success: WeatherFetchRun | None = None
    #: ``None`` while the weather fetch is switched off — nothing is scheduled.
    next_scheduled_at: datetime | None = None
    #: ``None`` when the lock store cannot be reached.
    running: bool | None = None
    #: Seconds until a manual fetch is allowed again; ``None`` when unknown.
    manual_fetch_available_in_s: int | None = None


def _ceil_to_hour(moment: datetime) -> datetime:
    floored = moment.replace(minute=0, second=0, microsecond=0)
    return floored if floored == moment else floored + timedelta(hours=1)


class WeatherFetchService:
    """Due-check, running lock, manual-fetch admission and status of the weather fetch."""

    def __init__(
        self,
        status_repo: IWeatherFetchStatusRepository,
        gate: IWeatherFetchGate,
        interval_hours: Callable[[], int],
        *,
        weather_enabled: Callable[[], bool],
        clock: Callable[[], datetime] = now_utc,
    ) -> None:
        self._status_repo = status_repo
        self._gate = gate
        self._interval_hours = interval_hours
        self._weather_enabled = weather_enabled
        self._clock = clock

    # ── Schedule ──────────────────────────────────────────────────────

    def _due_at(self, status: WeatherFetchStatus, interval: timedelta) -> datetime | None:
        """When the next run is due, ``None`` when no run ever succeeded (due now)."""
        if status.last_success is None:
            return None
        return status.last_success.started_at + interval - DUE_TOLERANCE

    def is_due(self) -> bool:
        """True when the interval since the newest successful run has passed (or none ever ran)."""
        status = self._status_repo.get_status()
        due_at = self._due_at(status, timedelta(hours=self._interval_hours()))
        return due_at is None or self._clock() >= due_at

    def next_scheduled_at(self, status: WeatherFetchStatus, interval_hours: int) -> datetime:
        """The hourly tick that will start the next scheduled run."""
        now = self._clock()
        due_at = self._due_at(status, timedelta(hours=interval_hours))
        return _ceil_to_hour(now if due_at is None or due_at < now else due_at)

    # ── Run (fetch task) ──────────────────────────────────────────────

    def acquire_run_lock(self) -> str | None:
        """Take the running lock: a token, ``None`` when held, :data:`LOCK_UNAVAILABLE` when unknown."""
        try:
            return self._gate.acquire_run_lock(RUN_LOCK_TTL_SECONDS)
        except WeatherFetchGateUnavailableError:
            return LOCK_UNAVAILABLE

    def release_run_lock(self, token: str) -> None:
        if token != LOCK_UNAVAILABLE:
            self._gate.release_run_lock(token)

    def record_run(self, run: WeatherFetchRun) -> int:
        """Store the run; returns the failed runs in a row after it."""
        return self._status_repo.record_run(run)

    # ── Manual fetch (API) ────────────────────────────────────────────

    def reserve_manual_fetch(self) -> None:
        """Admit one manual fetch or refuse it.

        Raises:
            WeatherFetchDisabledError: the weather fetch is switched off (409); no cooldown is taken.
            WeatherFetchRunningError: a run holds the lock (409).
            WeatherFetchCooldownError: the cooldown after the previous manual fetch runs (429).
            WeatherFetchUnavailableError: the lock store cannot be reached (503).
        """
        if not self._weather_enabled():
            raise WeatherFetchDisabledError
        try:
            if self._gate.is_running():
                raise WeatherFetchRunningError
            retry_after = self._gate.claim_manual_cooldown(MANUAL_FETCH_COOLDOWN_SECONDS)
        except WeatherFetchGateUnavailableError as exc:
            raise WeatherFetchUnavailableError from exc
        if retry_after > 0:
            raise WeatherFetchCooldownError(retry_after)

    def cancel_manual_fetch(self) -> None:
        """Give the cooldown back — the admitted fetch could not be queued."""
        self._gate.release_manual_cooldown()

    # ── Status ────────────────────────────────────────────────────────

    def get_overview(self) -> WeatherFetchOverview:
        status = self._status_repo.get_status()
        interval_hours = self._interval_hours()
        running: bool | None
        available_in: int | None
        try:
            running = self._gate.is_running()
            available_in = self._gate.manual_cooldown_remaining()
        except WeatherFetchGateUnavailableError:
            running, available_in = None, None
        return WeatherFetchOverview(
            interval_hours=interval_hours,
            last_run=status.last_run,
            last_success=status.last_success,
            next_scheduled_at=self.next_scheduled_at(status, interval_hours) if self._weather_enabled() else None,
            running=running,
            manual_fetch_available_in_s=available_in,
        )
