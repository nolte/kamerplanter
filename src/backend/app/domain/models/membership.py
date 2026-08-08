from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import AdminScope, TenantRole


def _normalize_scopes(value: list[AdminScope]) -> list[AdminScope]:
    """Deduplicate while imposing the declaration order of :class:`AdminScope`.

    REQ-049 INV-2: ``admin_scopes`` is duplicate-free and holds only defined
    values. Pydantic already rejects undefined values; ordering is normalised
    here so two memberships conveying the same rights compare and serialise
    identically, instead of differing by the order someone happened to tick the
    boxes in.
    """
    return [scope for scope in AdminScope if scope in value]


class Membership(BaseModel):
    """Links a user to a tenant (REQ-024) and carries both permission axes (REQ-049 §2).

    The axes are independent by design: ``role`` ranks what the member may do
    with the tenant's domain data, ``admin_scopes`` says what they may
    administer. All six combinations are valid (INV-3) — a viewer holding
    ``MANAGEMENT`` is the club secretary who keeps the member list and changes
    nothing in the garden.
    """

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    tenant_key: str

    # Axis 1 — exactly one domain role.
    role: TenantRole = TenantRole.VIEWER

    # Axis 2 — none, one or both administrative scopes.
    admin_scopes: list[AdminScope] = Field(default_factory=list)

    is_active: bool = True
    joined_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("admin_scopes")
    @classmethod
    def _dedupe_scopes(cls, value: list[AdminScope]) -> list[AdminScope]:
        return _normalize_scopes(value)

    @property
    def has_management(self) -> bool:
        """Whether this membership administers members, invitations and settings."""
        return AdminScope.MANAGEMENT in self.admin_scopes

    @property
    def has_technical(self) -> bool:
        """Whether this membership configures the tenant's own integrations."""
        return AdminScope.TECHNICAL in self.admin_scopes


class MemberInfo(BaseModel):
    key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    admin_scopes: list[AdminScope] = Field(default_factory=list)
    is_active: bool
    joined_at: datetime | None

    @field_validator("admin_scopes")
    @classmethod
    def _dedupe_scopes(cls, value: list[AdminScope]) -> list[AdminScope]:
        return _normalize_scopes(value)


class UserMembershipInfo(BaseModel):
    """One of a user's memberships, enriched with its tenant's name and slug.

    The user-perspective twin of :class:`MemberInfo` (which enriches a tenant's
    membership with the *member's* name/email). Both are read projections built
    by a single repository join, so the platform-admin panel no longer hand-rolls
    the same ``FOR m … LET t = DOCUMENT(tenants/…)`` AQL in three separate router
    handlers (``list_user_memberships``, ``list_all_users`` and the ``update_user``
    roles block — #1019).
    """

    membership_key: str
    tenant_key: str
    tenant_name: str
    tenant_slug: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None
