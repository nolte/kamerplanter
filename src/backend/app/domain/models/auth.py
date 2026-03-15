from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.common.enums import AuthProviderType


class AuthProvider(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    provider: AuthProviderType
    provider_user_id: str
    provider_email: str | None = None
    provider_display_name: str | None = None
    avatar_url: str | None = None
    access_token_encrypted: str | None = None
    refresh_token_encrypted: str | None = None
    token_expires_at: datetime | None = None
    last_used_at: datetime | None = None
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
    last_used_at: datetime | None = None


class RefreshToken(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    token_hash: str
    user_agent: str | None = None
    ip_address: str | None = None
    ip_anonymized_at: datetime | None = None
    expires_at: datetime
    is_persistent: bool = False
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
    nonce: str = ""
    code_verifier: str = ""


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
    is_persistent: bool = False


class ApiKey(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    label: str = Field(min_length=1, max_length=100)
    key_hash: str
    key_prefix: str  # First 8 chars for identification
    tenant_scope: str | None = None  # If set, key only works for this tenant
    revoked: bool = False
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ApiKeyCreated(BaseModel):
    key: str
    label: str
    raw_key: str  # Only shown once at creation
    key_prefix: str
    tenant_scope: str | None
    created_at: datetime | None


class ApiKeySummary(BaseModel):
    key: str
    label: str
    key_prefix: str
    tenant_scope: str | None
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime | None
