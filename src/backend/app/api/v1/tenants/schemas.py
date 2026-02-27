from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import (
    InvitationStatus,
    InvitationType,
    TenantRole,
    TenantType,
)

# ── Tenant schemas ───────────────────────────────────────────────────


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    max_members: int = Field(default=50, ge=1)


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)


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
    is_active: bool


# ── Member schemas ───────────────────────────────────────────────────


class MemberInfoResponse(BaseModel):
    key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None


class ChangeRoleRequest(BaseModel):
    role: TenantRole


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
