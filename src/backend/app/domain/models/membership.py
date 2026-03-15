
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import TenantRole

if TYPE_CHECKING:
    from datetime import datetime


class Membership(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    tenant_key: str
    role: TenantRole = TenantRole.VIEWER
    is_active: bool = True
    joined_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class MemberInfo(BaseModel):
    key: str
    user_key: str
    display_name: str
    email: str
    role: TenantRole
    is_active: bool
    joined_at: datetime | None
