"""The persistent security-audit record (MT-014, #2111).

One row says *who changed what access, of whom or of which tenant, when* - a
membership, its role or scopes, a trust flag of an account (``is_active``,
``email_verified``) or the lifecycle of a whole tenant (suspended, reactivated,
deletion accepted or withdrawn) - nothing about the person beyond the opaque
account keys. The row is kept as proof (NFR-011 R-38) and therefore outlives the
tenant; on an account erasure the account keys become tombstone hashes
(``ErasureEngine.PSEUDONYMIZE_AUDIT_COLLECTIONS``), so a retained row stays
linkable without naming anybody.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import SecurityAuditAction, SecurityAuditVia
from app.domain.models.plan import PlanLimitChange


class SecurityAuditEntry(BaseModel):
    """One change of tenant membership, role or scopes, of an account's trust flags or of a tenant's lifecycle."""

    key: str | None = Field(default=None, alias="_key")
    action: SecurityAuditAction
    #: The door the change came through (platform-admin panel, the tenant's own
    #: member administration, an accepted invitation, leaving, registration).
    via: SecurityAuditVia
    #: The account that made the change; for an invitation, the one that accepted it.
    actor_user_key: str
    #: The account whose membership or trust flag changed; ``None`` for a change of a whole tenant (#2111).
    target_user_key: str | None = None
    #: The tenant the change concerns; ``None`` for a change of an account's trust flags (#2111).
    tenant_key: str | None = None
    membership_key: str | None = None
    old_role: str | None = None
    new_role: str | None = None
    old_scopes: list[str] | None = None
    new_scopes: list[str] | None = None
    #: REQ-056 §7.6 (#2142) — the plan a ``tenant_plan_changed`` row moved the tenant to, or the plan a
    #: ``plan_created`` / ``plan_changed`` / ``plan_deleted`` row is about.
    plan_key: str | None = None
    #: The plan a ``tenant_plan_changed`` row moved the tenant away from.
    old_plan_key: str | None = None
    #: The fields a ``plan_changed`` row changed (``name``, ``limits.storage_mb``, ``is_default`` ...), no values.
    changed_fields: list[str] | None = None
    #: SEC-005 — of a ``plan_changed`` row: each changed limit with its old and new value, flagged when the
    #: change lifts the limit (to ``0`` = unlimited, or to ``null`` = the instance setting).
    limit_changes: list[PlanLimitChange] | None = None
    #: The ``X-Request-ID`` of the request (structlog context), when there is one.
    request_id: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True, "use_enum_values": True}
