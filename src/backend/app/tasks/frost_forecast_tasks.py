"""Issue #392 — Celery task that emits proactive frost early-warnings.

Reads the daily :class:`WeatherForecast` records persisted by the REQ-046
``fetch_weather_forecasts`` task, evaluates the in-horizon frost risk per site
with the pure :func:`evaluate_forecast_frost_warning` engine and, when a frost
night is predicted, emits **one** N-003 notification per tenant member —
idempotent per ``(site_key, expected frost date)`` (R9).

Iterates every enabled ``:WeatherSourceConfig`` cross-tenant (mirroring the
fetch task); the read/notification path is tenant-scoped (R10). The reactive
frost path and the REQ-046 fetch task are left untouched.
"""

import asyncio
from datetime import UTC, datetime

import structlog

from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def evaluate_forecast_frost_warnings(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Evaluate persisted forecasts and notify on in-horizon frost per site."""
    if not settings.weather_enabled:
        return {"status": "skipped", "reason": "weather_disabled"}

    from app.common.dependencies import (
        get_membership_repo,
        get_notification_service,
        get_site_repo,
        get_weather_forecast_repo,
        get_weather_source_config_repo,
    )
    from app.data_access.arango.collections import WEATHER_SOURCE_CONFIGS
    from app.domain.engines.frost_warning_engine import evaluate_forecast_frost_warning
    from app.domain.models.weather import WeatherSourceConfig

    config_repo = get_weather_source_config_repo()
    forecast_repo = get_weather_forecast_repo()
    site_repo = get_site_repo()
    membership_repo = get_membership_repo()
    notification_service = get_notification_service()

    db = config_repo._db  # noqa: SLF001 — direct AQL for cross-tenant iteration
    cursor = db.aql.execute(
        "FOR c IN @@col FILTER c.enabled == true RETURN c",
        bind_vars={"@col": WEATHER_SOURCE_CONFIGS},
    )

    today = datetime.now(UTC).date()
    notified = 0
    skipped = 0
    errors: list[dict] = []

    for doc in cursor:
        config = WeatherSourceConfig(**config_repo._from_doc(doc))  # noqa: SLF001
        try:
            site = site_repo.get_site_by_key(config.site_key)
            if site is None or site.gps_coordinates is None:
                skipped += 1
                continue
            # R10 / SEC-002 — a config's tenant_key must match its site's; never
            # read forecasts or notify under a tenant the site does not belong to.
            if site.tenant_key != config.tenant_key:
                logger.warning(
                    "frost_forecast_tenant_mismatch",
                    site_key=config.site_key,
                    config_tenant=config.tenant_key,
                    site_tenant=site.tenant_key,
                )
                skipped += 1
                continue

            forecasts = forecast_repo.find_by_site(config.site_key, site.tenant_key)
            result = evaluate_forecast_frost_warning(
                forecasts,
                threshold_celsius=settings.frost_forecast_threshold_celsius,
                horizon_days=settings.frost_forecast_horizon_days,
                today=today,
            )
            if result["predicted"] is not True:
                skipped += 1
                continue

            # Recipients: the tenant's active members (preferences are honoured by
            # the underlying send path, so no channel logic is duplicated here).
            members = membership_repo.list_by_tenant(site.tenant_key)
            user_keys = [m.user_key for m in members if m.is_active and m.user_key]

            emit = asyncio.run(
                notification_service.send_frost_forecast_notifications(
                    site.tenant_key,
                    user_keys,
                    site_key=config.site_key,
                    site_name=site.name,
                    expected_date=result["expected_date"],
                    min_temp=result["min_temp"],
                    source=result["source"],
                )
            )
            if emit.get("status") == "complete":
                notified += emit.get("users_notified", 0)
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001 — one bad site must not abort the run
            logger.warning("frost_forecast_site_failed", site_key=config.site_key, error=str(exc))
            errors.append({"site_key": config.site_key, "error": str(exc)})
            continue

    logger.info("frost_forecast_evaluate_complete", notified=notified, skipped=skipped, errors=len(errors))
    return {"status": "ok", "notified": notified, "skipped": skipped, "errors": len(errors)}
