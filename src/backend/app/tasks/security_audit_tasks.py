"""MT-014 (#2111) - the retention sweep of the persistent security audit (NFR-011 R-38).

``security_audit_log`` rows are kept :data:`~app.domain.services.security_audit_service.SECURITY_AUDIT_RETENTION_DAYS`
days (two years) from ``created_at`` and then deleted. ArangoDB persistent indexes do not
auto-expire, so this task performs the sweep (the same shape as ``mcp.cleanup_expired_audit_log``).
"""

from __future__ import annotations

import structlog

from app.common.held_count import held_undated_count
from app.data_access.arango.connection import ArangoConnection
from app.data_access.arango.security_audit_repository import ArangoSecurityAuditRepository
from app.domain.services.security_audit_service import SECURITY_AUDIT_RETENTION_DAYS
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="security_audit.purge_expired")
def purge_expired_security_audit_log() -> int:
    """Remove ``security_audit_log`` rows older than the retention window (NFR-011 R-38)."""
    repo = ArangoSecurityAuditRepository(ArangoConnection().db)
    removed = repo.delete_expired(retention_days=SECURITY_AUDIT_RETENTION_DAYS)
    # #1806 GDPR-003: rows without a readable ``created_at`` are never selected.
    held_undated = held_undated_count(repo.count_undated, task="security_audit.purge_expired")
    logger.info("security_audit_purge", removed=removed, held_undated=held_undated)
    return removed
