from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# REQ-023 v1.10: ``service`` accounts are M2M identities (Home Assistant,
# Grafana, CI/CD). They have no password, can never log in via the
# web UI, and authenticate exclusively via API keys with optional IP
# allowlists and per-account rate limits.
AccountType = Literal["user", "service"]


class User(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=200)
    password_hash: str | None = None
    email_verified: bool = False
    email_verification_token: str | None = None
    email_verification_expires: datetime | None = None
    password_reset_token: str | None = None
    password_reset_expires: datetime | None = None
    is_active: bool = True
    # REQ-023 v1.10 service accounts (M2M).
    account_type: AccountType = "user"
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    avatar_url: str | None = None
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class UserProfile(BaseModel):
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


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
