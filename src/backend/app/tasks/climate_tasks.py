"""REQ-041 §3.5 — Celery task that fetches NASA POWER climate normals per site.

Long-term monthly climate normals are near-static, so this runs on a *monthly*
beat (plus on-demand when an outdoor/greenhouse site with GPS is created). For
every such site across all tenants it pulls the twelve monthly averages from NASA
POWER and upserts one :class:`ClimateNormal` record (idempotent on
``(site_key, source)``). A record fetched within
``settings.nasa_power_climate_ttl_days`` is left untouched, so a re-run inside the
TTL is a cheap no-op that never re-hits the API.

The read/write path is tenant-scoped (the record inherits the site's
``tenant_key``); one failing site never aborts the whole run. *Any* per-site
error — an HTTP 429/5xx, a timeout, a mapping error, or an upsert failure (e.g. a
unique-index race between the monthly beat and an on-demand trigger) — is caught,
recorded and skipped, so sites of other tenants are still processed and the
failed site is retried on the next beat.
"""

from datetime import UTC, datetime, timedelta

import structlog

from app.common.async_bridge import run_async
from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

#: Site types for which climate normals are materialised (REQ-041 — outdoor
#: growing surfaces; indoor/climate-controlled sites have no use for them).
_CLIMATE_SITE_TYPES = ("outdoor", "greenhouse")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_climate_normals(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Fetch and upsert NASA POWER climate normals for every eligible site."""
    if not settings.weather_enabled or not settings.nasa_power_climate_enabled:
        return {"status": "skipped", "reason": "climate_normals_disabled"}

    from app.common.dependencies import get_climate_normal_repo, get_db, get_site_repo
    from app.data_access.arango import collections as col
    from app.domain.models.site import Site
    from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

    adapter_cls = WeatherAdapterRegistry.get("nasa-power")
    if adapter_cls is None:
        logger.warning("climate_normals_adapter_missing", source="nasa-power")
        return {"status": "skipped", "reason": "adapter_unavailable"}
    adapter = adapter_cls(timeout_s=float(settings.weather_fetch_timeout_s))

    normal_repo = get_climate_normal_repo()
    site_repo = get_site_repo()
    db = get_db()

    cursor = db.aql.execute(
        "FOR s IN @@col FILTER s.type IN @types AND s.gps_coordinates != null RETURN s",
        bind_vars={"@col": col.SITES, "types": list(_CLIMATE_SITE_TYPES)},
    )

    ttl = timedelta(days=settings.nasa_power_climate_ttl_days)
    now = datetime.now(UTC)
    written = 0
    skipped = 0
    errors: list[dict] = []

    for doc in cursor:
        site = Site(**site_repo._from_doc(doc))  # noqa: SLF001 — cross-tenant iteration
        if not site.key or site.gps_coordinates is None:
            skipped += 1
            continue

        # Per-site isolation across ALL error classes (fetch, mapping, DB upsert):
        # a single failing site must never abort the cross-tenant run.
        try:
            existing = normal_repo.find_one(site.key, site.tenant_key, adapter.source_name)
            if existing is not None and _is_fresh(existing.fetched_at, now, ttl):
                skipped += 1
                continue

            latitude, longitude = site.gps_coordinates
            normal = run_async(adapter.fetch_climate_normals(latitude=latitude, longitude=longitude))
            if normal is None:
                skipped += 1
                continue

            record = normal.model_copy(
                update={
                    "site_key": site.key,
                    "tenant_key": site.tenant_key,
                    "climate_normal_id": f"{site.key}:{adapter.source_name}",
                }
            )
            normal_repo.upsert(record)
            written += 1
        except Exception as exc:  # noqa: BLE001 — per-site isolation: one failure never aborts the run
            logger.warning("climate_normals_site_failed", site_key=site.key, error=str(exc))
            errors.append({"site_key": site.key, "error": str(exc)})
            continue

    logger.info("climate_normals_complete", written=written, skipped=skipped, errors=len(errors))
    return {"status": "ok", "written": written, "skipped": skipped, "errors": len(errors)}


def _is_fresh(fetched_at: datetime, now: datetime, ttl: timedelta) -> bool:
    """True when ``fetched_at`` is within ``ttl`` of ``now`` (TTL not yet expired).

    Tolerates a naive stored timestamp by assuming UTC, so a legacy record never
    crashes the comparison with a "can't subtract offset-naive and offset-aware"
    ``TypeError``.
    """
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)
    return (now - fetched_at) < ttl
