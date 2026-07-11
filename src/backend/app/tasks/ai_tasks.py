"""REQ-031 §4.6 — Celery retention tasks for the KI-Assistent.

Cleanups keep KI data within its NFR-011 retention windows. The reingest task
triggers the Knowledge-Service ``/ingest`` so master-data snapshots stay fresh.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog

from app.data_access.arango.ai_repository import (
    ArangoAiAuditRepository,
    ArangoAiConversationRepository,
)
from app.data_access.arango.connection import ArangoConnection
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

#: Audit-log retention (§7.4, min 14 days, default 30).
_AUDIT_RETENTION_DAYS = 30


@celery_app.task(name="ai.cleanup_expired_conversations")
def cleanup_expired_conversations() -> int:
    """Remove ``ai_conversations`` whose ``expires_at`` has passed (§4.6)."""
    db = ArangoConnection().db
    removed = ArangoAiConversationRepository(db).delete_expired()
    logger.info("ai_cleanup_conversations", removed=removed)
    return removed


@celery_app.task(name="ai.cleanup_expired_audit_log")
def cleanup_expired_audit_log() -> int:
    """Remove ``ai_audit_log`` entries older than the retention window (§4.6)."""
    db = ArangoConnection().db
    cutoff = datetime.now(UTC) - timedelta(days=_AUDIT_RETENTION_DAYS)
    removed = ArangoAiAuditRepository(db).delete_older_than(cutoff)
    logger.info("ai_cleanup_audit_log", removed=removed, cutoff=cutoff.isoformat())
    return removed


@celery_app.task(
    bind=True,
    name="ai.knowledge_service_ingest",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError),
    default_retry_delay=300,
)
def knowledge_service_ingest(self) -> dict:  # noqa: ANN001 - Celery bound task
    """Trigger a Knowledge-Service reingest of master-data snapshots (§4.6).

    Best-effort — a Knowledge-Service outage must not crash the beat worker; the
    autoretry policy handles transient connectivity issues.
    """
    import httpx

    from app.config.settings import settings

    if not settings.knowledge_service_enabled:
        return {"status": "skipped", "reason": "knowledge_service_disabled"}

    headers = {}
    if settings.internal_service_token:
        headers["Authorization"] = f"Bearer {settings.internal_service_token}"
    url = settings.knowledge_service_url.rstrip("/") + "/ingest"
    response = httpx.post(url, headers=headers, timeout=120.0)
    response.raise_for_status()
    result = response.json()
    logger.info("ai_knowledge_service_ingest", status=result.get("status"))
    return result
