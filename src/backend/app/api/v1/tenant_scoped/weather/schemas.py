"""REQ-046 §4.3 — request/response schemas for the weather-source API.

Three model families are deliberately kept apart (D1, AC-8):

* **Request** schemas carry the OpenWeatherMap key as **plaintext** input
  (:class:`WeatherSourcePublicConfigRequest.api_key`). They are FastAPI body
  models, so malformed payloads produce ``422`` (never a raw
  ``pydantic.ValidationError`` bubbling up as ``500``).
* The **storage** model is :class:`app.domain.models.weather.WeatherSourceConfig`
  (holds the Fernet **ciphertext** in ``api_key_ref``); never exposed here.
* **Response** schemas are **masked** — a public source only reports
  ``api_key_set: bool`` and never the plaintext or the ciphertext.
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.domain.models.weather import HaWeatherMode, WeatherSourceKind

# SEC-003/SEC-004: HA entity ids are interpolated into the HA REST path, so bound
# them to the intended domain + a strict slug (empty string = unmapped) and cap
# their length. Defense-in-depth alongside the adapter-level guard.
SensorEntityId = Annotated[str | None, Field(default=None, max_length=255, pattern=r"^(sensor\.[a-z0-9_]+)?$")]
WeatherEntityId = Annotated[str | None, Field(default=None, max_length=255, pattern=r"^(weather\.[a-z0-9_]+)?$")]

# ── Request schemas (plaintext in) ────────────────────────────────────────


class HaSensorMappingRequest(BaseModel):
    """HA ``sensor.*`` field mapping (all optional, unmapped stays ``None``)."""

    temp_min_entity: SensorEntityId = None
    temp_max_entity: SensorEntityId = None
    temp_current_entity: SensorEntityId = None
    humidity_entity: SensorEntityId = None
    precipitation_entity: SensorEntityId = None
    wind_speed_entity: SensorEntityId = None
    wind_gust_entity: SensorEntityId = None
    pressure_entity: SensorEntityId = None


class WeatherSourceHaConfigRequest(BaseModel):
    """Home-Assistant source configuration (mode A / mode B)."""

    mode: HaWeatherMode
    weather_entity_id: WeatherEntityId = None
    sensor_mapping: HaSensorMappingRequest | None = None


class WeatherSourcePublicConfigRequest(BaseModel):
    """Public-service source configuration.

    ``api_key`` is the **plaintext** OpenWeatherMap key as typed by the user. An
    empty / ``None`` / masked value means "unchanged" — the service keeps the
    previously stored ciphertext (see :meth:`WeatherSourceService.save_config`).
    """

    api_key: str | None = None
    units_hint: str | None = None


class WeatherSourceEntryRequest(BaseModel):
    """One prioritised source entry in the request body.

    ``public_config`` / ``ha_config`` are explicit (rather than a discriminated
    union) so the frontend can populate exactly the branch matching ``kind``.
    """

    source_name: str
    kind: WeatherSourceKind
    enabled: bool = True
    public_config: WeatherSourcePublicConfigRequest | None = None
    ha_config: WeatherSourceHaConfigRequest | None = None


class WeatherSourceConfigRequest(BaseModel):
    """PUT body — the full prioritised source list for a site."""

    enabled: bool = True
    # SEC-004: cap the priority list (well above the number of registered sources).
    sources: list[WeatherSourceEntryRequest] = Field(default_factory=list, max_length=16)


# ── Response schemas (masked out) ─────────────────────────────────────────


class HaSensorMappingResponse(BaseModel):
    temp_min_entity: str | None = None
    temp_max_entity: str | None = None
    temp_current_entity: str | None = None
    humidity_entity: str | None = None
    precipitation_entity: str | None = None
    wind_speed_entity: str | None = None
    wind_gust_entity: str | None = None
    pressure_entity: str | None = None


class WeatherSourceHaConfigResponse(BaseModel):
    mode: HaWeatherMode
    weather_entity_id: str | None = None
    sensor_mapping: HaSensorMappingResponse | None = None


class WeatherSourcePublicConfigResponse(BaseModel):
    """Masked public config — ``api_key_set`` replaces the secret (AC-8)."""

    api_key_set: bool = False
    units_hint: str | None = None


class WeatherSourceEntryResponse(BaseModel):
    source_name: str
    kind: WeatherSourceKind
    enabled: bool = True
    public_config: WeatherSourcePublicConfigResponse | None = None
    ha_config: WeatherSourceHaConfigResponse | None = None


class WeatherSourceConfigResponse(BaseModel):
    site_key: str
    enabled: bool = True
    sources: list[WeatherSourceEntryResponse] = Field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: str = ""


# ── Available sources ─────────────────────────────────────────────────────


class AvailableSourceItem(BaseModel):
    source_name: str
    kind: str
    requires_api_key: bool = False


class AvailableSourcesResponse(BaseModel):
    sources: list[AvailableSourceItem] = Field(default_factory=list)
    ha_token_set: bool = False


# ── Connection test ───────────────────────────────────────────────────────


class WeatherTestPreviewItem(BaseModel):
    forecast_date: date
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    humidity_percent: float | None = None
    source: str
    data_kind: str
    is_current_conditions: bool = False


class WeatherTestResponse(BaseModel):
    reachable: bool
    preview: list[WeatherTestPreviewItem] = Field(default_factory=list)
    error: str | None = None


# ── Forecast read (Issue #392 — dashboard WeatherForecastWidget) ───────────


class SiteWeatherForecastDay(BaseModel):
    """One in-horizon daily forecast row for the per-site forecast widget.

    Carries the REQ-046 provenance (``source`` / ``data_kind``) so the frontend
    can render the ``WeatherProvenanceBadge``.
    """

    forecast_date: date
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    humidity_percent: float | None = None
    weather_code: str | None = None
    source: str
    data_kind: str = "forecast"


class SiteWeatherForecastResponse(BaseModel):
    """Per-site weather forecast plus the proactive frost early-warning summary.

    Graceful: when no forecast source is available (no coordinates,
    ``weather_enabled`` off, or no persisted record) ``forecasts`` is empty and
    every ``forecast_*`` summary field is ``None`` — never a 500.
    """

    site_key: str
    forecasts: list[SiteWeatherForecastDay] = Field(default_factory=list)
    forecast_frost_warning: bool | None = None
    forecast_min_temperature: float | None = None
    forecast_expected_date: date | None = None
    forecast_source: str | None = None


# ── HA entity pickers ─────────────────────────────────────────────────────


class HaEntityItem(BaseModel):
    entity_id: str
    friendly_name: str
    state: str | None = None
    unit_of_measurement: str | None = None
    device_class: str | None = None
