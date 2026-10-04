"""Writes the persistent security-audit log (MT-014, #2111).

The one write path: every service function that changes a tenant membership, its
role or its scopes hands the change here (``TenantService._audit_membership``),
and ``tests/unit/guards/test_membership_mutations_write_the_security_audit.py``
holds that for the class. The row keeps the opaque account keys (NFR-011 R-38,
pseudonymised on an account erasure); the log line beside it carries only the
salted references (``log_subject`` / ``log_tenant``, #1781).

A write that fails **raises**: a role change whose record could not be written
must not stand silently, and the callers write the record after the change so a
failure surfaces as a 500 the operator sees rather than a gap nobody notices.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from app.common.enums import SecurityAuditAction, SecurityAuditVia
from app.common.log_privacy import log_subject, log_tenant
from app.domain.interfaces.security_audit_repository import ISecurityAuditRepository
from app.domain.models.security_audit import SecurityAuditEntry

logger = structlog.get_logger()

#: How long a row is kept, counted from ``created_at`` (NFR-011 R-38): two years - long enough to
#: reconstruct who was given or lost access to a tenant across a normal incident-review and
#: complaint horizon, short enough that it never becomes a standing profile of a person
#: (the erasure audit R-06 keeps its proof three years, the tenant-erasure record five).
SECURITY_AUDIT_RETENTION_DAYS = 730

#: The most rows one read returns (the admin read route and ``list_recent``).
MAX_READ_LIMIT = 200


class SecurityAuditService:
    def __init__(self, repo: ISecurityAuditRepository) -> None:
        self._repo = repo

    def record_membership_change(
        self,
        *,
        action: SecurityAuditAction,
        via: SecurityAuditVia,
        actor_user_key: str,
        target_user_key: str,
        tenant_key: str,
        membership_key: str | None = None,
        old_role: str | None = None,
        new_role: str | None = None,
        old_scopes: list[str] | None = None,
        new_scopes: list[str] | None = None,
    ) -> SecurityAuditEntry:
        """Append one row and write the structlog line beside it."""
        entry = SecurityAuditEntry(
            action=action,
            via=via,
            actor_user_key=actor_user_key,
            target_user_key=target_user_key,
            tenant_key=tenant_key,
            membership_key=membership_key,
            old_role=old_role,
            new_role=new_role,
            old_scopes=old_scopes,
            new_scopes=new_scopes,
            request_id=_current_request_id(),
            created_at=datetime.now(UTC),
        )
        entry.key = self._repo.record(entry)
        logger.warning(
            "security_audit_recorded",
            action=action.value,
            via=via.value,
            actor=log_subject(actor_user_key),
            target=log_subject(target_user_key),
            tenant=log_tenant(tenant_key),
            old_role=old_role,
            new_role=new_role,
        )
        return entry

    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        return self._repo.list_recent(tenant_key=tenant_key, limit=max(1, min(limit, MAX_READ_LIMIT)))


def _current_request_id() -> str | None:
    value = structlog.contextvars.get_contextvars().get("request_id")
    return str(value) if value else None
