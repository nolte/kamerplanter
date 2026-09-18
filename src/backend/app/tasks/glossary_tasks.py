"""REQ-035 §4.3 — Celery maintenance tasks for the KI terminology glossary.

Three tasks: a daily cleanup of expired ``glossary_term_cache`` rows (02:45 UTC),
a reingest-invalidation that drops the whole glossary cache, and the warm-up that
refills it for the curated catalogue.

The warm-up is what makes the invalidation survivable since #1460. Until then the
cache refilled itself from the **read** path: the first caller to ask for a term
after a reingest paid for the LLM call, and on the anonymous
``/public/glossary/term/{slug}`` route that caller did not even have an account.
Now no ``GET`` generates, so something else has to — a task, scheduled where the
invalidation already is, which is also where the cost belongs.

A cache miss still degrades to the curated editorial fallback text, so an empty
cache is never fatal and the warm-up is never on a request's critical path.
"""

from __future__ import annotations

import asyncio

import structlog

from app.common.dependencies import get_glossary_service
from app.config.settings import settings
from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.glossary_repository import ArangoGlossaryTermCacheRepository
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

#: Every (language, expertise) variant the read path can ask for. The warm-up
#: covers the full product because a variant it skips is a permanent editorial
#: fallback for that audience — nothing else generates any more.
_VARIANTS: tuple[tuple[str, str], ...] = tuple(
    (language, level) for language in ("de", "en") for level in ("beginner", "intermediate", "expert")
)


@celery_app.task(name="glossary.cleanup_expired_cache")
def cleanup_expired_cache() -> int:
    """Remove ``glossary_term_cache`` rows whose ``valid_until`` has passed (§4.3)."""
    db = ArangoConnection().db
    removed = ArangoGlossaryTermCacheRepository(db).delete_expired()
    logger.info("glossary_cleanup_cache", removed=removed)
    return removed


@celery_app.task(name="glossary.invalidate_after_reingest")
def invalidate_after_reingest() -> int:
    """Drop the entire glossary cache after a KB reingest (§4.3).

    Chained after ``ai.knowledge_service_ingest`` so answers regenerate with the
    new ``kb_version``, and it now *queues that regeneration itself*: since #1460
    the read path no longer refills the cache, so an invalidation without a
    warm-up would leave every term on its editorial fallback until somebody with
    a grower role happened to press "generate".

    The warm-up is queued rather than called: it is long-running (one LLM call per
    term and variant) and its failure must not roll back an invalidation that has
    already happened.
    """
    db = ArangoConnection().db
    removed = ArangoGlossaryTermCacheRepository(db).invalidate_all()
    logger.info("glossary_invalidate_after_reingest", removed=removed)
    warm_glossary_cache.delay()
    return removed


@celery_app.task(name="glossary.warm_cache")
def warm_glossary_cache() -> dict:
    """Regenerate the cached explanation of every curated term (§4.3, #1460).

    Runs the *generation* path — the one the anonymous ``GET`` used to run — for
    the whole catalogue, in the background, on a schedule the operator controls,
    with no user waiting on it. That is the trade #1460 asked for: the same LLM
    calls happen, but the installation decides when, instead of an unauthenticated
    caller deciding by asking for an unseen slug.

    Skipped entirely when ``ai_features_enabled`` is off: there is no RAG stack to
    ask, and the curated fallback already answers every read.

    One term is one failure. A Knowledge-Service outage part-way through leaves
    the terms already warmed in place and the rest on their editorial fallback,
    which is a degraded but correct state — so the loop records and continues
    rather than aborting, and the counts come back for the operator to read.
    """
    if not settings.ai_features_enabled:
        logger.info("glossary_warm_cache_skipped", reason="ai_features_disabled")
        return {"status": "skipped", "warmed": 0, "errors": 0}

    service = get_glossary_service()
    slugs = service.catalogue_slugs()
    warmed = 0
    errors = 0

    async def _warm() -> None:
        nonlocal warmed, errors
        for slug in slugs:
            for language, level in _VARIANTS:
                try:
                    await service.generate_term(slug, language=language, expertise_level=level)
                except Exception as exc:  # noqa: BLE001 — one term must not abort the run
                    errors += 1
                    logger.warning("glossary_warm_cache_term_failed", slug=slug, language=language, error=str(exc))
                else:
                    warmed += 1

    asyncio.run(_warm())
    logger.info("glossary_warm_cache_complete", terms=len(slugs), warmed=warmed, errors=errors)
    return {"status": "ok", "terms": len(slugs), "warmed": warmed, "errors": errors}
