from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import TenantRole, TenantType


class AdminTenantResponse(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    owner_user_key: str
    is_active: bool
    is_platform: bool
    max_members: int
    member_count: int
    created_at: datetime | None
    updated_at: datetime | None


class AdminUserTenantRole(BaseModel):
    tenant_key: str
    tenant_name: str
    tenant_slug: str
    role: TenantRole


class AdminUserResponse(BaseModel):
    key: str
    email: str
    display_name: str
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime | None
    tenant_count: int
    roles: list[AdminUserTenantRole]


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_tenants: int
    active_tenants: int
    total_memberships: int


class AdminTenantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class AdminUserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    email_verified: bool | None = None


class AdminTenantMemberResponse(BaseModel):
    membership_key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None


class AdminAddMemberRequest(BaseModel):
    user_key: str
    role: TenantRole = TenantRole.VIEWER


class AdminUpdateMemberRoleRequest(BaseModel):
    role: TenantRole


class AdminUserMembershipResponse(BaseModel):
    membership_key: str
    tenant_key: str
    tenant_name: str
    tenant_slug: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None


class AdminAddUserToTenantRequest(BaseModel):
    tenant_key: str
    role: TenantRole = TenantRole.VIEWER
