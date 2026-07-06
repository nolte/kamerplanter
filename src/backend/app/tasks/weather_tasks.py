"""REQ-046 §3.6 — Celery task that fetches daily weather per configured site.

Iterates every ``:WeatherSourceConfig`` (cross-tenant), loads the owning site,
resolves the prioritised source chain via :class:`WeatherSourceResolver` and
upserts the resulting :class:`WeatherForecast` records. ``source`` / ``data_kind``
carry the source that actually produced the data (public forecast or HA
observed). Guarded by the ``weather_enabled`` kill-switch.
"""

import structlog

from app.common.async_bridge import run_async
from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_weather_forecasts(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Fetch and store daily weather for every configured, enabled site."""
    if not settings.weather_enabled:
        return {"status": "skipped", "reason": "weather_disabled"}

    from app.common.dependencies import (
        _effective_weather_settings,
        get_encryption_engine,
        get_ha_client,
        get_site_repo,
        get_weather_forecast_repo,
        get_weather_source_config_repo,
    )
    from app.data_access.arango.collections import WEATHER_SOURCE_CONFIGS
    from app.domain.models.weather import WeatherSourceConfig
    from app.domain.services.weather_source_resolver import WeatherSourceResolver

    config_repo = get_weather_source_config_repo()
    forecast_repo = get_weather_forecast_repo()
    site_repo = get_site_repo()
    # Inject the DB-backed effective provider config so the fetch honours the
    # central admin overrides (base URL, timeout, enable flags, global OWM key).
    resolver = WeatherSourceResolver(
        get_encryption_engine(),
        get_ha_client,
        weather_settings_provider=_effective_weather_settings,
    )

    db = config_repo._db  # noqa: SLF001 — direct AQL for cross-tenant iteration
    cursor = db.aql.execute(
        "FOR c IN @@col FILTER c.enabled == true RETURN c",
        bind_vars={"@col": WEATHER_SOURCE_CONFIGS},
    )

    written = 0
    skipped = 0
    errors: list[dict] = []

    for doc in cursor:
        config = WeatherSourceConfig(**config_repo._from_doc(doc))  # noqa: SLF001
        site = site_repo.get_site_by_key(config.site_key)
        if site is None or site.gps_coordinates is None:
            skipped += 1
            continue
        # SEC-002: defense-in-depth — a config's tenant_key must match its site's.
        # The API save-path guarantees this, but never write forecasts under a
        # tenant the site does not belong to if some other path ever diverges.
        if site.tenant_key != config.tenant_key:
            logger.warning(
                "weather_fetch_tenant_mismatch",
                site_key=config.site_key,
                config_tenant=config.tenant_key,
                site_tenant=site.tenant_key,
            )
            skipped += 1
            continue
        try:
            forecasts = run_async(resolver.resolve_daily(site, config))
        except Exception as exc:  # noqa: BLE001 — one bad site must not abort the run
            logger.warning("weather_fetch_site_failed", site_key=config.site_key, error=str(exc))
            errors.append({"site_key": config.site_key, "error": str(exc)})
            continue

        for forecast in forecasts:
            record = forecast.model_copy(update={"site_key": config.site_key, "tenant_key": site.tenant_key})
            forecast_repo.upsert_daily(record)
            written += 1

    logger.info("weather_fetch_complete", written=written, skipped=skipped, errors=len(errors))
    return {"status": "ok", "written": written, "skipped": skipped, "errors": len(errors)}
