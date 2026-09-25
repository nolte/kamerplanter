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
from typing import get_args

import structlog
from celery.exceptions import SoftTimeLimitExceeded

from app.common.dependencies import get_glossary_service
from app.common.log_privacy import loggable_error
from app.config.settings import settings
from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.glossary_repository import ArangoGlossaryTermCacheRepository
from app.domain.models.glossary_term import ExpertiseLevel, Language
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

#: Every (language, expertise) variant the read path can ask for. The warm-up
#: covers the full product because a variant it skips is a permanent editorial
#: fallback for that audience — nothing else generates any more.
#:
#: Derived from the published ``Language``/``ExpertiseLevel`` literals rather than
#: retyped (review SCR-005): this was a third copy of a vocabulary that already
#: exists on the model and in the service, and the way that drifts is silent —
#: adding a language would leave the warm-up covering the old set while every read
#: in the new one answered a curated fallback forever.
_VARIANTS: tuple[tuple[str, str], ...] = tuple(
    (language, level) for language in get_args(Language) for level in get_args(ExpertiseLevel)
)


#: The run may take a while — 192 sequential LLM calls against a local Ollama is
#: minutes, not seconds — but not forever. Soft limit first so the loop can report
#: what it warmed; hard limit a minute later as the backstop.
_SOFT_TIME_LIMIT_SECONDS = 30 * 60
_HARD_TIME_LIMIT_SECONDS = _SOFT_TIME_LIMIT_SECONDS + 60

#: Consecutive failures that mean "the Knowledge Service is down", not "this term
#: is bad". Six is one full variant set: every variant of one term failing in a row
#: is already not a property of the term.
_MAX_CONSECUTIVE_FAILURES = 6

#: The mutex. Held for the hard limit so a worker killed mid-run cannot keep the
#: lock forever.
_RUN_LOCK_KEY = "glossary:warm_cache:running"


def _acquire_run_lock() -> tuple[object | None, bool]:
    """Take the single-run lock, or report that another run holds it.

    Returns ``(client, acquired)``. A missing or broken Redis yields
    ``(None, True)``: the lock is an optimisation against paying for the catalogue
    twice, and refusing to warm the cache because the accelerator is down would be
    the worse failure of the two.
    """
    try:
        from app.common.dependencies import _get_redis_client

        client = _get_redis_client()
    except Exception:  # noqa: BLE001 — Redis is an optional accelerator here.
        logger.debug("glossary_warm_cache_lock_unavailable")
        return None, True

    try:
        acquired = bool(client.set(_RUN_LOCK_KEY, "1", nx=True, ex=_HARD_TIME_LIMIT_SECONDS))
    except Exception:  # noqa: BLE001 — see above.
        logger.debug("glossary_warm_cache_lock_failed")
        return None, True
    return client, acquired


def _release_run_lock(client: object | None) -> None:
    if client is None:
        return
    try:
        client.delete(_RUN_LOCK_KEY)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 — the TTL releases it anyway.
        logger.debug("glossary_warm_cache_unlock_failed")


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


@celery_app.task(
    name="glossary.warm_cache",
    # Bounded on purpose (review SCR-008). The work is
    # ``catalogue x languages x levels`` sequential LLM calls; measured against the
    # seeded catalogue that is 32 x 6 = 192. Unbounded, a Knowledge Service that
    # answers slowly rather than failing would hold a worker for hours and the
    # only symptom would be a queue that stops draining. The soft limit raises
    # ``SoftTimeLimitExceeded`` inside the loop, so the run reports what it warmed
    # before giving up; the hard limit is the backstop for a call that ignores it.
    soft_time_limit=_SOFT_TIME_LIMIT_SECONDS,
    time_limit=_HARD_TIME_LIMIT_SECONDS,
)
def warm_glossary_cache() -> dict:
    """Regenerate the cached explanation of every curated term (§4.3, #1460).

    Runs the *generation* path — the one the anonymous ``GET`` used to run — for
    the whole catalogue, in the background, on a schedule the operator controls,
    with no user waiting on it. That is the trade #1460 asked for: the same LLM
    calls happen, but the installation decides when, instead of an unauthenticated
    caller deciding by asking for an unseen slug.

    Skipped entirely when ``ai_features_enabled`` is off: there is no RAG stack to
    ask, and the curated fallback already answers every read.

    **One term is one failure, but a broken Knowledge Service is not 192 of them**
    (review SCR-008). A single failing term leaves the rest warmable, so the loop
    records it and continues. A *run* of consecutive failures means the service is
    down, and continuing then spends the full time budget producing the same error
    once per variant — so after :data:`_MAX_CONSECUTIVE_FAILURES` in a row the run
    stops and reports ``status="aborted"``. The counter resets on any success, so
    a few scattered bad terms never trip it.

    **At most one run at a time.** Two reingests close together would otherwise
    pay for the catalogue twice, concurrently, against the same cache. A Redis key
    held for the hard time limit is the mutex; a second run exits immediately with
    ``status="locked"``. Redis being unavailable does not block the warm-up — it
    degrades to the previous unlocked behaviour and says so in the log, because
    refusing to warm the cache over a missing accelerator would be the worse
    failure.
    """
    if not settings.ai_features_enabled:
        logger.info("glossary_warm_cache_skipped", reason="ai_features_disabled")
        return {"status": "skipped", "warmed": 0, "errors": 0}

    redis_client, locked = _acquire_run_lock()
    if not locked:
        logger.info("glossary_warm_cache_skipped", reason="already_running")
        return {"status": "locked", "warmed": 0, "errors": 0}

    service = get_glossary_service()
    slugs = service.catalogue_slugs()
    warmed = 0
    errors = 0
    consecutive = 0
    status = "ok"

    async def _warm() -> str:
        nonlocal warmed, errors, consecutive
        for slug in slugs:
            for language, level in _VARIANTS:
                try:
                    await service.generate_term(slug, language=language, expertise_level=level)
                except SoftTimeLimitExceeded:
                    # The budget, not a failure of this term. Re-raised would lose
                    # the counts; reported instead so the operator sees how far it got.
                    logger.warning("glossary_warm_cache_timed_out", slug=slug, warmed=warmed, errors=errors)
                    return "timed_out"
                except Exception as exc:  # noqa: BLE001 — one term must not abort the run
                    errors += 1
                    consecutive += 1
                    logger.warning(
                        "glossary_warm_cache_term_failed", slug=slug, language=language, error=loggable_error(exc)
                    )
                    if consecutive >= _MAX_CONSECUTIVE_FAILURES:
                        logger.warning(
                            "glossary_warm_cache_aborted",
                            reason="consecutive_failures",
                            consecutive=consecutive,
                            warmed=warmed,
                            errors=errors,
                        )
                        return "aborted"
                else:
                    warmed += 1
                    consecutive = 0
        return "ok"

    try:
        status = asyncio.run(_warm())
    finally:
        _release_run_lock(redis_client)

    logger.info("glossary_warm_cache_complete", status=status, terms=len(slugs), warmed=warmed, errors=errors)
    return {"status": status, "terms": len(slugs), "warmed": warmed, "errors": errors}
