from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ── Request schemas ────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class VerifyEmailRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)


class RefreshRequest(BaseModel):
    """Body-based refresh as fallback (primary is HttpOnly cookie)."""

    refresh_token: str | None = None


class ApiKeyCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    tenant_scope: str | None = None


class SetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


# ── Response schemas ───────────────────────────────────────────────


class UserProfileResponse(BaseModel):
    key: str
    email: str
    display_name: str
    email_verified: bool
    is_active: bool
    avatar_url: str | None
    locale: str
    timezone: str = "Europe/Berlin"
    last_login_at: datetime | None
    created_at: datetime | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthProviderResponse(BaseModel):
    key: str
    provider: str
    provider_email: str | None
    provider_display_name: str | None
    linked_at: datetime | None
    last_used_at: datetime | None = None


class SessionResponse(BaseModel):
    key: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool
    is_persistent: bool


class OAuthProviderListItem(BaseModel):
    slug: str
    display_name: str
    icon_url: str | None


class ApiKeyCreatedResponse(BaseModel):
    key: str
    label: str
    raw_key: str
    key_prefix: str
    tenant_scope: str | None
    created_at: datetime | None


class ApiKeySummaryResponse(BaseModel):
    key: str
    label: str
    key_prefix: str
    tenant_scope: str | None
    revoked: bool
    last_used_at: datetime | None
    created_at: datetime | None


class MessageResponse(BaseModel):
    message: str
