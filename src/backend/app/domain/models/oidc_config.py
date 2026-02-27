from datetime import datetime

from pydantic import BaseModel, Field


class OidcProviderConfig(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=200)
    issuer_url: str
    client_id: str
    client_secret_encrypted: str = ""
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    enabled: bool = False
    icon_url: str | None = None
    discovery_document: dict | None = None
    discovery_refreshed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class OidcProviderConfigCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=200)
    issuer_url: str
    client_id: str
    client_secret: str
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    enabled: bool = False
    icon_url: str | None = None


class OidcProviderConfigUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    issuer_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] | None = None
    enabled: bool | None = None
    icon_url: str | None = None
