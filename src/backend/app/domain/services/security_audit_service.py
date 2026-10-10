"""Writes the persistent security-audit log (MT-014, #2111).

The one write path: every service function that changes a tenant membership, its
role or its scopes hands the change here (``TenantService._audit_membership``),
and ``tests/unit/guards/test_membership_mutations_write_the_security_audit.py``
holds that for the class. A platform admin's change of an account's trust flags
(``UserService._audit_account``) and every change of a tenant's lifecycle - a
suspension, a reactivation, an accepted or withdrawn deletion
(``TenantService._audit_tenant``) - come here too;
``tests/unit/guards/test_account_and_tenant_mutations_write_the_security_audit.py``
holds that class. The row keeps the opaque account keys (NFR-011 R-38,
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
        entry = self.membership_entry(
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
        )
        return self._write(entry)

    @staticmethod
    def membership_entry(
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
        """The row of one membership change, **not yet written** (#2118).

        Split from the write so a founder's row can be written inside the transaction that creates the
        tenant it names (``ITenantRepository.create_with_lead_membership``): a tenant that exists without its
        audit row, or the reverse, is what the transaction rules out.
        """
        return SecurityAuditEntry(
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

    @staticmethod
    def announce(entry: SecurityAuditEntry) -> None:
        """The structlog line of a written row (pseudonymised: no account or tenant key)."""
        logger.warning(
            "security_audit_recorded",
            action=SecurityAuditAction(entry.action).value,
            via=SecurityAuditVia(entry.via).value,
            actor=log_subject(entry.actor_user_key),
            target=log_subject(entry.target_user_key),
            tenant=log_tenant(entry.tenant_key),
            old_role=entry.old_role,
            new_role=entry.new_role,
        )

    def record_account_change(
        self,
        *,
        action: SecurityAuditAction,
        via: SecurityAuditVia,
        actor_user_key: str,
        target_user_key: str,
    ) -> SecurityAuditEntry:
        """Append the row of one change of an account's trust flag (#2111); it names no tenant.

        The action says the before and after (``account_deactivated`` = active -> inactive), so the row
        carries no value of the account - no address, no name.
        """
        return self._write(
            SecurityAuditEntry(
                action=action,
                via=via,
                actor_user_key=actor_user_key,
                target_user_key=target_user_key,
                request_id=_current_request_id(),
                created_at=datetime.now(UTC),
            )
        )

    def record_tenant_change(
        self,
        *,
        action: SecurityAuditAction,
        via: SecurityAuditVia,
        actor_user_key: str,
        tenant_key: str,
    ) -> SecurityAuditEntry:
        """Append the row of one change of a whole tenant's lifecycle (#2111); it names no target account."""
        return self._write(
            SecurityAuditEntry(
                action=action,
                via=via,
                actor_user_key=actor_user_key,
                tenant_key=tenant_key,
                request_id=_current_request_id(),
                created_at=datetime.now(UTC),
            )
        )

    def _write(self, entry: SecurityAuditEntry) -> SecurityAuditEntry:
        entry.key = self._repo.record(entry)
        self.announce(entry)
        return entry

    def list_recent(self, *, tenant_key: str | None = None, limit: int = 100) -> list[SecurityAuditEntry]:
        return self._repo.list_recent(tenant_key=tenant_key, limit=max(1, min(limit, MAX_READ_LIMIT)))


def _current_request_id() -> str | None:
    value = structlog.contextvars.get_contextvars().get("request_id")
    return str(value) if value else None
