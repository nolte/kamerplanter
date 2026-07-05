"""REQ-046 §3.4 — ``HomeAssistantWeatherAdapter`` (the core value-add).

Turns an existing Home Assistant installation into a weather source through the
shared :class:`HomeAssistantClient` (REST). Two confirmed modes:

* **Mode A (``weather_entity``):** reads a native HA ``weather.*`` entity; its
  ``attributes.forecast[]`` yields daily :class:`WeatherForecast` records
  (``data_kind="forecast"``).
* **Mode B (``sensor_mapping``):** reads individually mapped ``sensor.*``
  entities and produces exactly one *current-conditions* record for today
  (``is_current_conditions=True``, ``data_kind="observed"``). Unmapped fields and
  ``unavailable`` / ``unknown`` states collapse to ``None``.

Requires a valid HA token (REQ-005). When HA is missing / off the resolver skips
this source and falls back to the next prioritised one (degradation, never a
hard error).
"""

import re
from datetime import UTC, date, datetime

import structlog

from app.data_access.external.ha_client import HomeAssistantClient
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import HaSensorMapping, WeatherForecast, WeatherSourceHaConfig
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

logger = structlog.get_logger(__name__)

#: SEC-003 — a HA entity_id is interpolated into the REST path; only allow the
#: two intended domains with a strict slug so a crafted id cannot reach other
#: routes of the shared HA instance (path injection on the deployment-wide host).
_ENTITY_ID_RE = re.compile(r"^(weather|sensor)\.[a-z0-9_]+$")


def _valid_entity(entity_id: str | None, domain: str) -> bool:
    return bool(entity_id) and entity_id.startswith(f"{domain}.") and bool(_ENTITY_ID_RE.match(entity_id))


#: HA ``weather.*`` ``condition`` -> WMO weather code (string). Unknown -> None.
_HA_CONDITION_TO_WMO: dict[str, str] = {
    "sunny": "0",
    "clear-night": "0",
    "partlycloudy": "2",
    "cloudy": "3",
    "fog": "45",
    "hail": "96",
    "lightning": "95",
    "lightning-rainy": "95",
    "pouring": "65",
    "rainy": "61",
    "snowy": "71",
    "snowy-rainy": "66",
    "windy": "1",
    "windy-variant": "1",
    # "exceptional" intentionally unmapped -> None via dict.get
}


def _condition_to_wmo(condition: str | None) -> str | None:
    if not condition:
        return None
    return _HA_CONDITION_TO_WMO.get(condition)


@WeatherAdapterRegistry.register
class HomeAssistantWeatherAdapter(WeatherAdapter):
    """Weather source from a Home Assistant installation (REQ-046 §3.4)."""

    source_name = "ha_weather"
    kind = "home_assistant"
    requires_api_key = False  # reuses the existing HA token, no own secret

    def __init__(self, ha_client: HomeAssistantClient) -> None:
        self._ha = ha_client

    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        if not isinstance(config, WeatherSourceHaConfig):
            return []
        if config.mode == "weather_entity":
            if not _valid_entity(config.weather_entity_id, "weather"):
                if config.weather_entity_id:
                    logger.warning("ha_weather_invalid_entity_id", entity_id=config.weather_entity_id)
                return []
            return self._from_weather_entity(config.weather_entity_id)
        if config.sensor_mapping is None:
            return []
        return self._from_sensor_mapping(config.sensor_mapping)

    def _from_weather_entity(self, entity_id: str) -> list[WeatherForecast]:
        attrs = self._ha.get_state_attributes(entity_id)
        if not attrs:
            return []
        fetched_at = datetime.now(tz=UTC)
        out: list[WeatherForecast] = []
        for forecast in attrs.get("forecast", []) or []:
            raw_dt = forecast.get("datetime")
            if not raw_dt:
                continue
            try:
                forecast_date = datetime.fromisoformat(raw_dt).date()
            except ValueError:
                continue
            out.append(
                WeatherForecast(
                    site_key="",
                    forecast_date=forecast_date,
                    temp_max_c=_as_float(forecast.get("temperature")),
                    temp_min_c=_as_float(forecast.get("templow")),
                    precipitation_mm=_as_float(forecast.get("precipitation")),
                    wind_speed_kmh=_as_float(forecast.get("wind_speed")),
                    humidity_percent=_as_float(forecast.get("humidity")),
                    weather_code=_condition_to_wmo(forecast.get("condition")),
                    source=self.source_name,
                    fetched_at=fetched_at,
                    data_kind="forecast",
                    is_current_conditions=False,
                )
            )
        return out

    def _from_sensor_mapping(self, mapping: HaSensorMapping) -> list[WeatherForecast]:
        def read(entity_id: str | None) -> float | None:
            if not _valid_entity(entity_id, "sensor"):
                if entity_id:
                    logger.warning("ha_weather_invalid_sensor_id", entity_id=entity_id)
                return None
            state = self._ha.get_state(entity_id)
            if state is None:
                return None
            return state.get("value")

        return [
            WeatherForecast(
                site_key="",
                forecast_date=date.today(),
                temp_min_c=read(mapping.temp_min_entity),
                temp_max_c=read(mapping.temp_max_entity) or read(mapping.temp_current_entity),
                precipitation_mm=read(mapping.precipitation_entity),
                wind_speed_kmh=read(mapping.wind_speed_entity),
                wind_gust_kmh=read(mapping.wind_gust_entity),
                humidity_percent=read(mapping.humidity_entity),
                weather_code=None,
                source=self.source_name,
                fetched_at=datetime.now(tz=UTC),
                data_kind="observed",
                is_current_conditions=True,
            )
        ]

    async def health_check(self, *, config: object | None = None) -> bool:
        try:
            records = await self.fetch_daily(latitude=0.0, longitude=0.0, config=config)
        except Exception as exc:  # noqa: BLE001 — probe must never raise outward
            logger.warning("ha_weather_health_check_failed", error=str(exc))
            return False
        return bool(records)


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):  # fmt: skip
        return None
