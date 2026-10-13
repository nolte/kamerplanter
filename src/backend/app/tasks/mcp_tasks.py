"""REQ-033 §4.6 — Celery retention tasks for the MCP server.

Keeps the two adapter-layer collections within their retention windows:

* ``mcp_audit_log`` — deleted after 90 days (NFR-011, AC-S4);
* ``mcp_idempotency_record`` — deleted once past its 24h TTL (AC-22).

ArangoDB persistent indexes on ``created_at``/``expires_at`` do not auto-expire,
so these tasks perform the sweep.
"""

from __future__ import annotations

import structlog

from app.common.dependencies import get_db
from app.common.held_count import held_undated_count
from app.config.settings import settings
from app.data_access.arango.mcp_repository import (
    ArangoMcpAuditRepository,
    ArangoMcpIdempotencyRepository,
)
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="mcp.cleanup_expired_audit_log")
def cleanup_expired_audit_log() -> int:
    """Remove ``mcp_audit_log`` entries older than the retention window (AC-S4)."""
    db = get_db()
    repo = ArangoMcpAuditRepository(db)
    removed = repo.delete_expired(retention_days=settings.mcp_audit_retention_days)
    # #1806 GDPR-003: entries without a readable ``created_at`` are never selected.
    held_undated = held_undated_count(repo.count_undated, task="mcp.cleanup_expired_audit_log")
    logger.info("mcp_cleanup_audit_log", removed=removed, held_undated=held_undated)
    return removed


@celery_app.task(name="mcp.cleanup_expired_idempotency")
def cleanup_expired_idempotency() -> int:
    """Remove ``mcp_idempotency_record`` entries past their TTL (AC-22)."""
    db = get_db()
    removed = ArangoMcpIdempotencyRepository(db).delete_expired()
    logger.info("mcp_cleanup_idempotency", removed=removed)
    return removed
