from datetime import datetime

from pydantic import BaseModel, Field


class OidcProviderCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=200)
    issuer_url: str
    client_id: str
    client_secret: str
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    enabled: bool = False
    icon_url: str | None = None


class OidcProviderUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    issuer_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] | None = None
    enabled: bool | None = None
    icon_url: str | None = None


class OidcProviderResponse(BaseModel):
    key: str
    slug: str
    display_name: str
    issuer_url: str
    client_id: str
    scopes: list[str]
    enabled: bool
    icon_url: str | None
    discovery_refreshed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
