"""The persistent security-audit record (MT-014, #2111).

One row says *who changed whose membership, role or scopes, in which tenant, when*
- nothing about the person beyond the opaque account keys. The row is kept as proof
(NFR-011 R-38) and therefore outlives the tenant; on an account erasure the two
account keys become tombstone hashes (``ErasureEngine.PSEUDONYMIZE_AUDIT_COLLECTIONS``),
so a retained row stays linkable without naming anybody.

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import SecurityAuditAction, SecurityAuditVia


class SecurityAuditEntry(BaseModel):
    """One change of tenant membership, role or scopes."""

    key: str | None = Field(default=None, alias="_key")
    action: SecurityAuditAction
    #: The door the change came through (platform-admin panel, the tenant's own
    #: member administration, an accepted invitation, leaving, registration).
    via: SecurityAuditVia
    #: The account that made the change; for an invitation, the one that accepted it.
    actor_user_key: str
    #: The account whose membership changed.
    target_user_key: str
    tenant_key: str
    membership_key: str | None = None
    old_role: str | None = None
    new_role: str | None = None
    old_scopes: list[str] | None = None
    new_scopes: list[str] | None = None
    #: The ``X-Request-ID`` of the request (structlog context), when there is one.
    request_id: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True, "use_enum_values": True}
