from pydantic import BaseModel, Field

from app.common.enums import AdminScope, TenantRole


class TenantContext(BaseModel):
    """The acting user's standing inside one tenant, on both REQ-049 axes."""

    tenant_key: str
    tenant_slug: str
    user_key: str

    # Axis 1 — the ranked domain role.
    role: TenantRole

    # Axis 2 — administrative scopes, independent of the rank above.
    admin_scopes: list[AdminScope] = Field(default_factory=list)

    @property
    def can_delete(self) -> bool:
        """Whether the member may destroy domain records.

        The grower/lead boundary runs along irreversibility (REQ-049 §2.3): a
        grower fixes a mistake by overwriting a value, a lead can erase history.
        """
        return self.role == TenantRole.LEAD

    @property
    def can_edit(self) -> bool:
        """Whether the member may create and change domain records."""
        return self.role in (TenantRole.LEAD, TenantRole.GROWER)

    @property
    def has_management(self) -> bool:
        """Whether the member administers members, invitations and tenant settings."""
        return AdminScope.MANAGEMENT in self.admin_scopes

    @property
    def has_technical(self) -> bool:
        """Whether the member configures this tenant's own integrations and sensors."""
        return AdminScope.TECHNICAL in self.admin_scopes
