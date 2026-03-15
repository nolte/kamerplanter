from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr, Field

if TYPE_CHECKING:
    from datetime import datetime


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
