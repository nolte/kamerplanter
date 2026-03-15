from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import InvitationStatus, InvitationType, TenantRole

if TYPE_CHECKING:
    from datetime import datetime


class Invitation(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    invited_by_user_key: str
    invitation_type: InvitationType = InvitationType.EMAIL
    email: EmailStr | None = None
    role: TenantRole = TenantRole.VIEWER
    token_hash: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    accepted_by_user_key: str | None = None
    accepted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class InvitationLink(BaseModel):
    invitation_key: str
    token: str
    expires_at: datetime
