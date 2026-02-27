from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import AuthProviderType


class AuthProvider(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    provider: AuthProviderType
    provider_user_id: str
    provider_email: str | None = None
    provider_display_name: str | None = None
    avatar_url: str | None = None
    linked_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class AuthProviderInfo(BaseModel):
    key: str
    provider: AuthProviderType
    provider_email: str | None
    provider_display_name: str | None
    linked_at: datetime | None


class RefreshToken(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    token_hash: str
    user_agent: str | None = None
    ip_address: str | None = None
    expires_at: datetime
    revoked: bool = False
    created_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TokenPayload(BaseModel):
    sub: str  # user_key
    email: str
    display_name: str
    tenant_roles: dict[str, str] = Field(default_factory=dict)
    exp: int
    iat: int
    jti: str


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class OAuthRedirect(BaseModel):
    authorization_url: str
    state: str


class OAuthUserInfo(BaseModel):
    provider: AuthProviderType
    provider_user_id: str
    email: str
    display_name: str
    avatar_url: str | None = None


class SessionInfo(BaseModel):
    key: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool = False
