from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.common.validators import DisplayName

# REQ-023 v1.10: ``service`` accounts are M2M identities (Home Assistant,
# Grafana, CI/CD). They have no password, can never log in via the
# web UI, and authenticate exclusively via API keys with optional IP
# allowlists and per-account rate limits.
AccountType = Literal["user", "service"]

#: Domain of the address a soft-deleted account is parked under (REQ-025 Szenario 3).
#:
#: RFC 2606's documentation domain: guaranteed undeliverable, and — unlike
#: ``.local``/``.invalid``/``.test`` — accepted by ``EmailStr``'s validator, which
#: refuses every special-use/reserved name. The previous ``@deleted.local`` made the
#: repository's model re-validation (#968) raise, so the soft-delete persisted nothing
#: at all (#1525).
DELETED_EMAIL_DOMAIN = "deleted.example.com"


def tombstone_email(user_key: str) -> str:
    """The address ``UserService.delete_account`` parks a soft-deleted account under."""
    return f"deleted_{user_key}@{DELETED_EMAIL_DOMAIN}"


def is_tombstone_email(email: str) -> bool:
    """Whether ``email`` lives in the reserved soft-delete domain.

    ``users.email`` is uniquely indexed, so an address in this domain that somebody
    *registered* would make the eventual soft-delete of the account it impersonates
    collide: the Art. 17 path would answer 409 and the account could not be deleted at
    all. Registration and the email-change flow therefore refuse the domain outright
    (#1525 SCR-014). The rule is on the address alone, never on whether an account
    exists, so it adds no enumeration oracle (SEC-H-009).
    """
    return email.strip().lower().endswith(f"@{DELETED_EMAIL_DOMAIN}")


class User(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    email: EmailStr
    display_name: DisplayName
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
    display_name: DisplayName | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None
