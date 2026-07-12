"""REQ-035 §4.3 — Celery maintenance tasks for the KI terminology glossary.

Two tasks: a daily cleanup of expired ``glossary_term_cache`` rows (02:45 UTC)
and a reingest-invalidation that drops the whole glossary cache so subsequent
requests regenerate against the fresh knowledge-base index. Cache misses degrade
gracefully to the editorial fallback text, so an empty cache is never fatal.
"""

from __future__ import annotations

import structlog

from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.glossary_repository import ArangoGlossaryTermCacheRepository
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


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
    new ``kb_version``.
    """
    db = ArangoConnection().db
    removed = ArangoGlossaryTermCacheRepository(db).invalidate_all()
    logger.info("glossary_invalidate_after_reingest", removed=removed)
    return removed
