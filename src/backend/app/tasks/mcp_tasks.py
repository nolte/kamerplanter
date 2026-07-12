"""REQ-033 §4.6 — Celery retention tasks for the MCP server.

Keeps the two adapter-layer collections within their retention windows:

* ``mcp_audit_log`` — deleted after 90 days (NFR-011, AC-S4);
* ``mcp_idempotency_record`` — deleted once past its 24h TTL (AC-22).

ArangoDB persistent indexes on ``created_at``/``expires_at`` do not auto-expire,
so these tasks perform the sweep.
"""

from __future__ import annotations

import structlog

from app.config.settings import settings
from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.mcp_repository import (
    ArangoMcpAuditRepository,
    ArangoMcpIdempotencyRepository,
)
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="mcp.cleanup_expired_audit_log")
def cleanup_expired_audit_log() -> int:
    """Remove ``mcp_audit_log`` entries older than the retention window (AC-S4)."""
    db = ArangoConnection().db
    removed = ArangoMcpAuditRepository(db).delete_expired(
        retention_days=settings.mcp_audit_retention_days,
    )
    logger.info("mcp_cleanup_audit_log", removed=removed)
    return removed


@celery_app.task(name="mcp.cleanup_expired_idempotency")
def cleanup_expired_idempotency() -> int:
    """Remove ``mcp_idempotency_record`` entries past their TTL (AC-22)."""
    db = ArangoConnection().db
    removed = ArangoMcpIdempotencyRepository(db).delete_expired()
    logger.info("mcp_cleanup_idempotency", removed=removed)
    return removed
