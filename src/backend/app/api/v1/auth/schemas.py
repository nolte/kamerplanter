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


# ── Response schemas ───────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    key: str
    email: str
    display_name: str
    email_verified: bool
    is_active: bool
    avatar_url: str | None
    locale: str
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


class SessionResponse(BaseModel):
    key: str
    user_agent: str | None
    ip_address: str | None
    created_at: datetime | None
    expires_at: datetime
    is_current: bool


class OAuthProviderListItem(BaseModel):
    slug: str
    display_name: str
    icon_url: str | None


class MessageResponse(BaseModel):
    message: str
