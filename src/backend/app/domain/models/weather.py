"""REQ-046 — Weather data-source domain models (foundation).

This module is the SSOT for the shared weather-source infrastructure introduced
by REQ-046:

* :class:`WeatherForecast` — the result records produced by every weather
  adapter (public services or Home Assistant). Extends the REQ-005 base model
  with the additive provenance fields ``data_kind`` / ``is_current_conditions``.
* :class:`ClimateNormal` — a *minimal* foundation model; REQ-041 (NASA POWER)
  owns and extends the full climate-normal schema.
* The user-facing configuration models (:class:`WeatherSourceConfig` and its
  embedded entries) that let a grower choose, per site, whether weather data
  comes from a public service or from Home Assistant sensors (REQ-046 §2).
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

#: Provenance classification of a weather record (REQ-046 §2.3).
WeatherDataKind = Literal["forecast", "observed", "reanalysis"]

#: Coarse class of a weather source, used for UI switching / config
#: discrimination (REQ-046 §2.2).
WeatherSourceKind = Literal["public", "home_assistant"]

#: The two confirmed Home Assistant operating modes (REQ-046 §2.2).
HaWeatherMode = Literal["weather_entity", "sensor_mapping"]


class WeatherForecast(BaseModel):
    """Daily weather record produced by a :class:`WeatherAdapter`.

    Collection ``weather_forecasts`` (REQ-005 §2). All numeric weather fields
    are optional: Home Assistant sensor mapping leaves unmapped fields as
    ``None``, and ``unavailable``/``unknown`` HA states also collapse to
    ``None``.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    site_key: str
    forecast_date: date
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    wind_gust_kmh: float | None = None
    humidity_percent: float | None = None
    weather_code: str | None = None
    source: str
    fetched_at: datetime
    # ── REQ-046 additive provenance (defaults keep legacy records valid) ──
    data_kind: WeatherDataKind = "forecast"
    is_current_conditions: bool = False
    #: Populated by the REQ-041 (NASA POWER) adapter; declared here only as an
    #: additive field on the shared result model.
    solar_radiation_mj_m2: float | None = None

    model_config = {"populate_by_name": True}


class ClimateNormal(BaseModel):
    """Minimal foundation model; REQ-041 (NASA POWER) owns and extends the full
    :class:`ClimateNormal` schema.

    Only the fields required by the REQ-046 adapter contract
    (``fetch_climate_normals``) are defined here so downstream requirements can
    grow the schema without a second, competing model.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    site_key: str
    source: str
    fetched_at: datetime
    monthly_temp_min_c: list[float] = Field(default_factory=list)
    monthly_temp_max_c: list[float] = Field(default_factory=list)
    coldest_month_min_c: float | None = None

    model_config = {"populate_by_name": True}


class HaSensorMapping(BaseModel):
    """Mapping of individual Home Assistant ``sensor.*`` entities onto the
    :class:`WeatherForecast` fields (REQ-046 §2.2). All optional — unmapped
    fields stay ``None``.
    """

    temp_min_entity: str | None = None
    temp_max_entity: str | None = None
    temp_current_entity: str | None = None
    humidity_entity: str | None = None
    precipitation_entity: str | None = None
    wind_speed_entity: str | None = None
    wind_gust_entity: str | None = None
    pressure_entity: str | None = None


class WeatherSourceHaConfig(BaseModel):
    """Home-Assistant-specific configuration of a weather source (REQ-046 §2.2)."""

    mode: HaWeatherMode
    weather_entity_id: str | None = None
    sensor_mapping: HaSensorMapping | None = None


class WeatherSourcePublicConfig(BaseModel):
    """Public-service-specific configuration of a weather source (REQ-046 §2.2).

    ``api_key_ref`` references a Fernet-encrypted secret (REQ-023) — never the
    plaintext key. ``None`` for key-free services (DWD / Open-Meteo).
    """

    api_key_ref: str | None = None
    units_hint: str | None = None


class WeatherSourceEntry(BaseModel):
    """One prioritised weather source of a site (REQ-046 §2.2, embedded).

    The ``config`` union is discriminated at use-time by ``kind`` /
    ``source_name``; the two config models have disjoint fields, so Pydantic v2
    smart-union resolution is sufficient (no formal discriminator needed).
    """

    source_name: str
    kind: WeatherSourceKind
    enabled: bool = True
    config: WeatherSourcePublicConfig | WeatherSourceHaConfig | None = None


class WeatherSourceConfig(BaseModel):
    """Per-site user configuration of weather data sources (REQ-046 §2.1).

    Collection ``weather_source_configs`` (1:1 per site). Tenant-scoped: inherits
    ``tenant_key`` from the owning site (REQ-024). ``sources`` is an ordered
    priority list — index 0 has the highest priority.
    """

    key: str | None = Field(default=None, alias="_key")
    weather_source_config_id: str = ""
    site_key: str
    tenant_key: str = ""
    enabled: bool = True
    sources: list[WeatherSourceEntry] = Field(default_factory=list)
    updated_at: datetime | None = None
    updated_by: str = ""

    model_config = {"populate_by_name": True}
