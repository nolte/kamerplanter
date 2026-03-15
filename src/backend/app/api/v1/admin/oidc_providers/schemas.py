from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class OidcProviderCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=200)
    provider_type: str = "oidc"
    issuer_url: str
    client_id: str
    client_secret: str
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    authorization_url: str | None = None
    token_url: str | None = None
    userinfo_url: str | None = None
    auto_discover: bool = True
    enabled: bool = False
    icon_url: str | None = None
    default_tenant_key: str | None = None


class OidcProviderUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    provider_type: str | None = None
    issuer_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] | None = None
    authorization_url: str | None = None
    token_url: str | None = None
    userinfo_url: str | None = None
    auto_discover: bool | None = None
    enabled: bool | None = None
    icon_url: str | None = None
    default_tenant_key: str | None = None


class OidcProviderResponse(BaseModel):
    key: str
    slug: str
    display_name: str
    provider_type: str = "oidc"
    issuer_url: str
    client_id: str
    scopes: list[str]
    enabled: bool
    icon_url: str | None
    auto_discover: bool = True
    discovery_refreshed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
