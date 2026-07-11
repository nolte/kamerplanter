"""REQ-039 §3 — Celery task that refreshes site hardiness zones quarterly.

Hardiness zones derive from long-term climate normals, which change only very
slowly, so this runs on a *quarterly* beat. For every outdoor/greenhouse site
with GPS coordinates across all tenants it re-derives ``Site.hardiness_zone`` from
the site's REQ-041 climate normals. Sites whose zone was set manually
(``hardiness_zone_source == "manual"``) are skipped so a user override is never
clobbered.

The read/write path is tenant-scoped (each site is resolved with its own
``tenant_key``); one failing site never aborts the whole run. A site without
usable climate normals yet (``ValidationError``) is simply skipped and retried on
the next beat.
"""

import structlog

from app.common.exceptions import ValidationError
from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

#: Only outdoor growing surfaces have a meaningful hardiness zone (indoor sites
#: are climate-controlled).
_ZONE_SITE_TYPES = ("outdoor", "greenhouse")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_site_hardiness_zones(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Re-derive the hardiness zone for every eligible, non-manual site."""
    if not settings.hardiness_zone_refresh_enabled:
        return {"status": "skipped", "reason": "hardiness_zone_refresh_disabled"}

    from app.common.dependencies import get_db, get_hardiness_zone_service, get_site_repo
    from app.data_access.arango import collections as col
    from app.domain.models.site import Site

    service = get_hardiness_zone_service()
    site_repo = get_site_repo()
    db = get_db()

    cursor = db.aql.execute(
        "FOR s IN @@col FILTER s.type IN @types AND s.gps_coordinates != null "
        "AND s.hardiness_zone_source != 'manual' RETURN s",
        bind_vars={"@col": col.SITES, "types": list(_ZONE_SITE_TYPES)},
    )

    resolved = 0
    skipped = 0
    errors: list[dict] = []

    for doc in cursor:
        site = Site(**site_repo._from_doc(doc))  # noqa: SLF001 — cross-tenant iteration
        if not site.key:
            skipped += 1
            continue
        try:
            service.resolve_for_site(site.key, site.tenant_key)
            resolved += 1
        except ValidationError:
            # No usable climate normals yet — retried on the next beat.
            skipped += 1
        except Exception as exc:  # noqa: BLE001 — per-site isolation: one failure never aborts the run
            logger.warning("hardiness_zone_site_failed", site_key=site.key, error=str(exc))
            errors.append({"site_key": site.key, "error": str(exc)})
            continue

    logger.info("hardiness_zone_refresh_complete", resolved=resolved, skipped=skipped, errors=len(errors))
    return {"status": "ok", "resolved": resolved, "skipped": skipped, "errors": len(errors)}
