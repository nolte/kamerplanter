"""REQ-041 — on-demand fetch of a single site's climate normals (NASA POWER).

The monthly ``fetch_climate_normals`` Celery beat keeps every eligible site's
climate normals warm, but a user who just entered GPS coordinates and presses
"derive hardiness zone from GPS" cannot wait a month for that beat. This fetcher
performs the same per-site fetch+upsert on demand, honouring the same TTL so a
freshly-cached record is reused instead of re-hitting the API.

It is deliberately best-effort: it returns ``None`` (never raises) when climate
normals are disabled, the site has no GPS, the adapter is missing, or the remote
call yields nothing — the caller decides how to surface that (the hardiness
resolver falls back to its 422 "no usable normals yet").
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog

from app.common.async_bridge import run_async
from app.config.settings import settings
from app.domain.interfaces.climate_normal_repository import IClimateNormalRepository
from app.domain.models.site import Site
from app.domain.models.weather import ClimateNormal

logger = structlog.get_logger(__name__)

_SOURCE = "nasa-power"


class ClimateNormalFetcher:
    """Fetches and upserts one site's NASA-POWER climate normal on demand."""

    def __init__(self, normal_repo: IClimateNormalRepository) -> None:
        self._normal_repo = normal_repo

    def fetch_for_site(self, site: Site) -> ClimateNormal | None:
        """Return a fresh climate normal for ``site``, fetching+upserting if needed.

        Reuses an existing record still within ``nasa_power_climate_ttl_days``.
        Returns ``None`` when climate normals are disabled, the site lacks a key
        or GPS, the NASA-POWER adapter is unavailable, or the remote call yields
        no usable payload.
        """
        if not settings.weather_enabled or not settings.nasa_power_climate_enabled:
            return None
        if not site.key or site.gps_coordinates is None:
            return None

        from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

        adapter_cls = WeatherAdapterRegistry.get(_SOURCE)
        if adapter_cls is None:
            logger.warning("climate_normals_adapter_missing", source=_SOURCE)
            return None
        adapter = adapter_cls(timeout_s=float(settings.weather_fetch_timeout_s))

        now = datetime.now(UTC)
        ttl = timedelta(days=settings.nasa_power_climate_ttl_days)
        existing = self._normal_repo.find_one(site.key, site.tenant_key, adapter.source_name)
        if existing is not None and _is_fresh(existing.fetched_at, now, ttl):
            return existing

        try:
            latitude, longitude = site.gps_coordinates
            normal = run_async(adapter.fetch_climate_normals(latitude=latitude, longitude=longitude))
        except Exception as exc:  # noqa: BLE001 — best-effort: a remote failure yields None, never a 500
            logger.warning("climate_normals_ondemand_failed", site_key=site.key, error=str(exc))
            return None
        if normal is None:
            return None

        record = normal.model_copy(
            update={
                "site_key": site.key,
                "tenant_key": site.tenant_key,
                "climate_normal_id": f"{site.key}:{adapter.source_name}",
            }
        )
        return self._normal_repo.upsert(record)


def _is_fresh(fetched_at: datetime, now: datetime, ttl: timedelta) -> bool:
    """True when ``fetched_at`` is within ``ttl`` of ``now`` (tolerates naive UTC)."""
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)
    return (now - fetched_at) < ttl
