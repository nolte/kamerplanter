from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import TenantRole, TenantType


class Tenant(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    tenant_type: TenantType = TenantType.PERSONAL
    description: str | None = None
    owner_user_key: str
    is_active: bool = True
    is_platform: bool = False
    max_members: int = Field(default=1, ge=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    tenant_type: TenantType = TenantType.ORGANIZATION
    description: str | None = None
    max_members: int = Field(default=50, ge=1)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)


class TenantWithRole(BaseModel):
    key: str
    name: str
    slug: str
    tenant_type: TenantType
    description: str | None
    role: TenantRole
    is_active: bool
