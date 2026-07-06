"""Request / response schemas for the central weather-provider admin (REQ-046).

The response NEVER carries the global OpenWeatherMap key (neither plaintext nor
ciphertext) — only the presence flag ``openweathermap_global_api_key_set``.
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.domain.models.weather import WeatherForecast


class WeatherProviderInfo(BaseModel):
    """Effective config of a single public provider for the admin UI."""

    source_name: str
    enabled: bool
    base_url: str
    attribution: str


class WeatherProvidersResponse(BaseModel):
    """Masked effective weather-provider settings (no secret, no ciphertext)."""

    providers: list[WeatherProviderInfo]
    openweathermap_global_api_key_set: bool
    fetch_timeout_s: int
    default_public_source: str


class WeatherProvidersUpdate(BaseModel):
    """Update payload for the central weather-provider config.

    A ``None`` field is left unchanged (env fallback preserved). The global
    OpenWeatherMap key follows the "unchanged on empty/masked" rule: a new
    plaintext value is Fernet-encrypted, an empty / masked value keeps the stored
    ciphertext.

    ``extra="forbid"`` rejects unmodelled keys with a hard 422 instead of
    silently dropping them.
    """

    model_config = {"extra": "forbid"}

    open_meteo_enabled: bool | None = None
    open_meteo_base_url: str | None = Field(default=None, max_length=2048)
    dwd_enabled: bool | None = None
    dwd_base_url: str | None = Field(default=None, max_length=2048)
    openweathermap_enabled: bool | None = None
    openweathermap_base_url: str | None = Field(default=None, max_length=2048)
    openweathermap_global_api_key: str | None = Field(default=None, max_length=512)
    fetch_timeout_s: int | None = Field(default=None, ge=1, le=120)
    default_public_source: Literal["open-meteo", "dwd", "openweathermap"] | None = None


class WeatherProviderTestResponse(BaseModel):
    """Result of the provider connection test (never a 500, no key leak)."""

    reachable: bool
    preview: list[WeatherForecast] = Field(default_factory=list)
    error: str | None = None
