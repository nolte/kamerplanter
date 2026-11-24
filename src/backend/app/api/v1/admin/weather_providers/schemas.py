"""Request / response schemas for the central weather-provider admin (REQ-046).

The response NEVER carries the global OpenWeatherMap key (neither plaintext nor
ciphertext) — only the presence flag ``openweathermap_global_api_key_set``.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.weather import WeatherForecast
from app.domain.models.weather_fetch import (
    MAX_FETCH_INTERVAL_HOURS,
    MAX_FETCH_TIMEOUT_S,
    MIN_FETCH_INTERVAL_HOURS,
    WeatherFetchRun,
)


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
    fetch_interval_hours: int
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
    fetch_timeout_s: int | None = Field(default=None, ge=1, le=MAX_FETCH_TIMEOUT_S)
    #: Hours between two successful fetches (REQ-046 §3.6a, #2934); below 6 → 422.
    fetch_interval_hours: int | None = Field(default=None, ge=MIN_FETCH_INTERVAL_HOURS, le=MAX_FETCH_INTERVAL_HOURS)
    default_public_source: Literal["open-meteo", "dwd", "openweathermap"] | None = None


class WeatherProviderTestResponse(BaseModel):
    """Result of the provider connection test (never a 500, no key leak)."""

    reachable: bool
    preview: list[WeatherForecast] = Field(default_factory=list)
    error: str | None = None


class WeatherFetchTriggerResponse(BaseModel):
    """202 answer of a queued manual fetch; the result appears in the fetch status."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "queued", "task_id": "9f1c2e4a-6b7d-4e3f-8a21-5c0d9e7b3f10"}]}
    )

    status: Literal["queued"] = "queued"
    task_id: str | None = None


class WeatherFetchStatusResponse(BaseModel):
    """Newest run, newest successful run and the next scheduled run (REQ-046 §3.6a).

    ``running`` and ``manual_fetch_available_in_s`` are ``None`` while the lock store
    cannot be reached; ``manual_fetch_available_in_s`` is ``0`` when a manual fetch
    may start now.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "interval_hours": 6,
                    "last_run": {
                        "trigger": "manual",
                        "started_at": "2026-11-22T09:17:02Z",
                        "finished_at": "2026-11-22T09:17:41Z",
                        "success": True,
                        "sites": 3,
                        "sites_written": 2,
                        "sites_failed": 1,
                        "sites_skipped": 0,
                        "forecasts_written": 14,
                        "error_type": None,
                    },
                    "last_success": {
                        "trigger": "manual",
                        "started_at": "2026-11-22T09:17:02Z",
                        "finished_at": "2026-11-22T09:17:41Z",
                        "success": True,
                        "sites": 3,
                        "sites_written": 2,
                        "sites_failed": 1,
                        "sites_skipped": 0,
                        "forecasts_written": 14,
                        "error_type": None,
                    },
                    "next_scheduled_at": "2026-11-22T16:00:00Z",
                    "running": False,
                    "manual_fetch_available_in_s": 0,
                }
            ]
        }
    )

    interval_hours: int
    last_run: WeatherFetchRun | None = None
    last_success: WeatherFetchRun | None = None
    #: ``None`` while the weather fetch is switched off (``WEATHER_ENABLED=false``).
    next_scheduled_at: datetime | None = None
    running: bool | None = None
    manual_fetch_available_in_s: int | None = None
