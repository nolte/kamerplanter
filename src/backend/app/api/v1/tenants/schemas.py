from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import (
    AdminScope,
    InvitationStatus,
    InvitationType,
    TenantRole,
    TenantType,
)
from app.domain.models.tenant_erasure import TenantDeletionConfirmation

# ── Tenant schemas ───────────────────────────────────────────────────


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    max_members: int = Field(default=50, ge=1)


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)


class TenantDeleteRequest(BaseModel):
    """The step-up a tenant deletion must carry (#1791, REQ-024 §1a.2).

    Both deletion routes — ``DELETE /tenants/{slug}`` and
    ``DELETE /admin/platform/tenants/{key}`` — take this body.
    """

    model_config = {"extra": "forbid"}

    confirm_slug: str = Field(
        min_length=1,
        max_length=200,
        description="The tenant's slug, typed back by the requester to confirm which tenant is erased.",
    )
    password: str | None = Field(
        default=None,
        max_length=1024,
        description=(
            "The requester's current password. Required when the account has a local password; "
            "an account that signs in only through a federated provider omits it."
        ),
    )

    def to_confirmation(self) -> TenantDeletionConfirmation:
        return TenantDeletionConfirmation(confirm_slug=self.confirm_slug, password=self.password)


class TenantResponse(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    owner_user_key: str
    is_active: bool
    max_members: int
    created_at: datetime | None
    updated_at: datetime | None


class TenantWithRoleResponse(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    role: TenantRole
    # REQ-049 axis 2 — what the caller may administer in this tenant. The UI
    # needs both axes to decide what to show; the rank alone no longer says.
    admin_scopes: list[AdminScope] = Field(default_factory=list)
    is_active: bool


# ── Member schemas ───────────────────────────────────────────────────


class MemberInfoResponse(BaseModel):
    key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    admin_scopes: list[AdminScope] = Field(default_factory=list)
    is_active: bool
    joined_at: datetime | None


class ChangeRoleRequest(BaseModel):
    role: TenantRole


class ChangeScopesRequest(BaseModel):
    admin_scopes: list[AdminScope] = Field(default_factory=list)


# ── Invitation schemas ───────────────────────────────────────────────


class EmailInvitationRequest(BaseModel):
    email: EmailStr
    role: TenantRole = TenantRole.VIEWER


class LinkInvitationRequest(BaseModel):
    role: TenantRole = TenantRole.VIEWER


class InvitationResponse(BaseModel):
    key: str
    tenant_key: str
    invitation_type: InvitationType
    email: str | None
    role: TenantRole
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime | None


class InvitationLinkResponse(BaseModel):
    invitation_key: str
    token: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    token: str


# ── Assignment schemas ───────────────────────────────────────────────


class AssignmentCreateRequest(BaseModel):
    membership_key: str
    location_key: str
    can_edit: bool = True
    notes: str | None = None


class AssignmentUpdateRequest(BaseModel):
    can_edit: bool | None = None
    notes: str | None = None


class AssignmentResponse(BaseModel):
    key: str
    membership_key: str
    location_key: str
    tenant_key: str
    can_edit: bool
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None


class MessageResponse(BaseModel):
    message: str
