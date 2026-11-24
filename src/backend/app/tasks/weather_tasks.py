"""REQ-046 §3.6 / §3.6a — Celery task that fetches daily weather per configured site.

Iterates every ``:WeatherSourceConfig`` (cross-tenant), loads the owning site,
resolves the prioritised source chain via :class:`WeatherSourceResolver` and
upserts the resulting :class:`WeatherForecast` records. ``source`` / ``data_kind``
carry the source that actually produced the data (public forecast or HA
observed). Guarded by the ``weather_enabled`` kill-switch.

Schedule (#2934): the beat starts the task **hourly**; a scheduled run returns early
unless ``fetch_interval_hours`` have passed since the newest successful run
(:meth:`WeatherFetchService.is_due`). A manual run (platform admin) skips that
check. Every run holds the running lock, records its result in the status document
and — only when it succeeded (:func:`is_successful_run`) — queues the frost
early-warning and the irrigation demand. A failed run is not retried by Celery: the next hourly tick is the retry.

Both follow-up tasks also keep a daily beat slot of their own as a safety net
(operator decision 2026-11-22): with a long interval or a provider outage, a frost
night that enters the forecast horizon between two fetches is still reported, and
the irrigation demand still has a value for the day. Three failed runs in a row log
``weather_fetch_outage`` at ``error`` level.

The run lock expires after ``RUN_LOCK_TTL_SECONDS``; the task's soft and hard time
limits sit below it, so the lock never lapses under a run that is still going. The
soft limit is handled: the run is recorded as failed and the lock released.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import structlog
from celery.exceptions import SoftTimeLimitExceeded

from app.common.async_bridge import run_async
from app.common.datetimes import now_utc
from app.common.enums import WeatherFetchTrigger
from app.common.log_privacy import log_tenant, loggable_error
from app.config.settings import settings
from app.domain.models.weather_fetch import (
    OUTAGE_ALERT_AFTER_FAILURES,
    SITE_FETCH_BUDGET_SECONDS,
    WeatherFetchRun,
    is_successful_run,
)
from app.domain.services.weather_fetch_service import RUN_SOFT_TIME_LIMIT_SECONDS, RUN_TIME_LIMIT_SECONDS
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@dataclass
class _FetchOutcome:
    sites: int = 0
    sites_written: int = 0
    skipped: int = 0
    written: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)


# No Celery retry (#2934): a failed run is retried by the next hourly due-check.
@celery_app.task(
    bind=True, max_retries=0, soft_time_limit=RUN_SOFT_TIME_LIMIT_SECONDS, time_limit=RUN_TIME_LIMIT_SECONDS
)
def fetch_weather_forecasts(self, trigger: str = WeatherFetchTrigger.SCHEDULED.value) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Fetch and store daily weather for every configured, enabled site when a fetch is due."""
    if not settings.weather_enabled:
        return {"status": "skipped", "reason": "weather_disabled"}

    from app.common.dependencies import get_weather_fetch_service

    run_trigger = WeatherFetchTrigger(trigger)
    fetch_service = get_weather_fetch_service()
    if run_trigger is WeatherFetchTrigger.SCHEDULED and not fetch_service.is_due():
        return {"status": "skipped", "reason": "not_due"}

    token = fetch_service.acquire_run_lock()
    if token is None:
        logger.info("weather_fetch_already_running", trigger=run_trigger.value)
        if run_trigger is WeatherFetchTrigger.MANUAL:
            # The admitted manual fetch did not run: give its cooldown back, so the
            # admin is not blocked for 10 minutes by a fetch that left no status.
            fetch_service.cancel_manual_fetch()
        return {"status": "skipped", "reason": "already_running"}
    if not token:
        # Valkey is down: fetch unlocked rather than leave every site without weather.
        logger.warning("weather_fetch_unlocked", trigger=run_trigger.value)

    started_at = now_utc()
    try:
        try:
            outcome = _fetch_all_sites()
        except Exception as exc:  # incl. SoftTimeLimitExceeded: recorded, lock released, re-raised
            failures = fetch_service.record_run(
                WeatherFetchRun(
                    trigger=run_trigger,
                    started_at=started_at,
                    finished_at=now_utc(),
                    success=False,
                    error_type=type(exc).__name__,
                )
            )
            logger.error("weather_fetch_aborted", trigger=run_trigger.value, error=loggable_error(exc))
            _report_outage(failures)
            raise
        success = is_successful_run(aborted=False, sites=outcome.sites, sites_written=outcome.sites_written)
        failures = fetch_service.record_run(
            WeatherFetchRun(
                trigger=run_trigger,
                started_at=started_at,
                finished_at=now_utc(),
                success=success,
                sites=outcome.sites,
                sites_written=outcome.sites_written,
                sites_failed=len(outcome.errors),
                sites_skipped=outcome.skipped,
                forecasts_written=outcome.written,
            )
        )
    finally:
        fetch_service.release_run_lock(token)

    if success:
        _dispatch_followups()
    else:
        _report_outage(failures)
    logger.info(
        "weather_fetch_complete",
        trigger=run_trigger.value,
        success=success,
        written=outcome.written,
        skipped=outcome.skipped,
        errors=len(outcome.errors),
    )
    return {
        "status": "ok" if success else "failed",
        "written": outcome.written,
        "skipped": outcome.skipped,
        "errors": len(outcome.errors),
    }


def _report_outage(failures: int) -> None:
    """Log the outage at ``error`` level once ``OUTAGE_ALERT_AFTER_FAILURES`` runs failed in a row."""
    if isinstance(failures, int) and failures >= OUTAGE_ALERT_AFTER_FAILURES:
        logger.error("weather_fetch_outage", consecutive_failures=failures, threshold=OUTAGE_ALERT_AFTER_FAILURES)


def _dispatch_followups() -> None:
    """Queue the frost early-warning and the irrigation demand after a successful fetch (R4).

    Both are idempotent per site and day, so up to four fetches a day plus their daily
    safety-net beat duplicate nothing. Each task keeps its own kill-switch and
    ``ActiveTenants`` gate. ``tests/unit/guards/test_beats_skip_inactive_tenants.py``
    reads the task names this function passes to ``send_task`` and holds them to
    ``TENANT_WRITING_CHAINED_TASKS`` (and to registered tasks); the MT-051 guard sees
    the literal names as dispatches.

    ``send_task`` with a literal name on the typed ``celery_app`` rather than
    ``<task>.delay()``: the decorated task object carries no type the write-route call
    graph can follow, so every ``.delay`` is an unresolved receiver there (#2934).
    """
    celery_app.send_task("app.tasks.frost_forecast_tasks.evaluate_forecast_frost_warnings")
    if settings.irrigation_demand_enabled:
        celery_app.send_task("app.tasks.irrigation_tasks.compute_irrigation_demand")


def _fetch_all_sites() -> _FetchOutcome:
    """One pass over every enabled source config; one failing site never aborts the pass."""
    from app.common.dependencies import (
        _effective_weather_settings,
        get_encryption_engine,
        get_ha_client,
        get_ha_entity_grant_service,
        get_site_repo,
        get_tenant_repo,
        get_weather_forecast_repo,
        get_weather_source_config_repo,
    )
    from app.data_access.arango.collections import WEATHER_SOURCE_CONFIGS
    from app.domain.models.weather import WeatherSourceConfig
    from app.domain.services.weather_source_resolver import WeatherSourceResolver
    from app.tasks.tenant_gate import ActiveTenants

    config_repo = get_weather_source_config_repo()
    forecast_repo = get_weather_forecast_repo()
    site_repo = get_site_repo()
    # REQ-056 §5.2 — a tenant that is not ``active`` gets no weather: no provider call, no write.
    tenant_is_active = ActiveTenants(get_tenant_repo())
    # Inject the DB-backed effective provider config so the fetch honours the
    # central admin overrides (base URL, timeout, enable flags, global OWM key).
    resolver = WeatherSourceResolver(
        get_encryption_engine(),
        get_ha_client,
        weather_settings_provider=_effective_weather_settings,
        # MT-015 (#2112): one read of every tenant's grants for the whole run.
        ha_entity_gate=get_ha_entity_grant_service().snapshot(),
    )

    db = config_repo._db  # noqa: SLF001 — direct AQL for cross-tenant iteration
    cursor = db.aql.execute(
        "FOR c IN @@col FILTER c.enabled == true RETURN c",
        bind_vars={"@col": WEATHER_SOURCE_CONFIGS},
    )

    outcome = _FetchOutcome()
    for doc in cursor:
        config = WeatherSourceConfig(**config_repo._from_doc(doc))  # noqa: SLF001
        site = site_repo.get_site_by_key(config.site_key)
        if site is None or site.gps_coordinates is None:
            outcome.skipped += 1
            continue
        # SEC-002: defense-in-depth — a config's tenant_key must match its site's.
        # The API save-path guarantees this, but never write forecasts under a
        # tenant the site does not belong to if some other path ever diverges.
        if site.tenant_key != config.tenant_key:
            logger.warning(
                "weather_fetch_tenant_mismatch",
                site_key=config.site_key,
                config_tenant=log_tenant(config.tenant_key),
                site_tenant=log_tenant(site.tenant_key),
            )
            outcome.skipped += 1
            continue
        if not tenant_is_active(site.tenant_key):
            outcome.skipped += 1
            continue
        outcome.sites += 1
        try:
            # The per-site budget bounds the wait after a soft time limit (K2) and keeps one
            # site with a long chain of timing-out sources from eating the whole run.
            forecasts: list[Any] = run_async(
                asyncio.wait_for(resolver.resolve_daily(site, config), timeout=SITE_FETCH_BUDGET_SECONDS)
            )
        except SoftTimeLimitExceeded:
            raise  # the run's time is up: abort it, do not count it as one bad site
        except Exception as exc:  # noqa: BLE001 — one bad site must not abort the run
            logger.warning("weather_fetch_site_failed", site_key=config.site_key, error=loggable_error(exc))
            outcome.errors.append({"site_key": config.site_key, "error": type(exc).__name__})
            continue

        site_written = 0
        for forecast in forecasts:
            record = forecast.model_copy(update={"site_key": config.site_key, "tenant_key": site.tenant_key})
            forecast_repo.upsert_daily(record)
            site_written += 1
        if site_written:
            outcome.sites_written += 1
            outcome.written += site_written
    return outcome
