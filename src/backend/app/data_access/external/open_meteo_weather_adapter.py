"""REQ-046 §3.3 — ``OpenMeteoWeatherAdapter`` (public, key-free, global).

Open-Meteo is the default public source: free, no API key, global coverage. It
returns daily aggregated values directly, so ``_map`` is a straight per-day
projection with no client-side aggregation.

Attribution: ``Weather data by Open-Meteo.com`` (CC BY 4.0).
"""

from datetime import UTC, date, datetime

import httpx
import structlog

from app.config.settings import settings
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

logger = structlog.get_logger(__name__)

#: Reference point (Berlin) used by the lightweight health probe.
_HEALTH_LAT = 52.52
_HEALTH_LON = 13.40

#: Sentinel some providers use for "no value"; collapsed to ``None``.
_MISSING_SENTINEL = -999.0

_DAILY_FIELDS = (
    "temperature_2m_min,temperature_2m_max,precipitation_sum,"
    "wind_speed_10m_max,wind_gusts_10m_max,relative_humidity_2m_mean,weather_code"
)


def _clean(value: float | int | None) -> float | None:
    """Return ``None`` for missing / sentinel values, else a float."""
    if value is None:
        return None
    number = float(value)
    if number == _MISSING_SENTINEL:
        return None
    return number


@WeatherAdapterRegistry.register
class OpenMeteoWeatherAdapter(WeatherAdapter):
    """Open-Meteo — free, no API key, global. Default public source (REQ-046 §3.3)."""

    source_name = "open-meteo"
    kind = "public"
    requires_api_key = False

    def __init__(self, *, base_url: str | None = None, timeout_s: float | None = None) -> None:
        self._base_url = base_url or settings.open_meteo_base_url
        self._timeout = timeout_s if timeout_s is not None else float(settings.weather_fetch_timeout_s)

    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": _DAILY_FIELDS,
            "wind_speed_unit": "kmh",
            "timezone": "auto",
            "forecast_days": 7,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(self._base_url, params=params)
            resp.raise_for_status()
            return self._map(resp.json())

    def _map(self, payload: dict) -> list[WeatherForecast]:
        daily = payload.get("daily") or {}
        days: list[str] = daily.get("time") or []
        temp_min = daily.get("temperature_2m_min") or []
        temp_max = daily.get("temperature_2m_max") or []
        precip = daily.get("precipitation_sum") or []
        wind = daily.get("wind_speed_10m_max") or []
        gust = daily.get("wind_gusts_10m_max") or []
        humidity = daily.get("relative_humidity_2m_mean") or []
        codes = daily.get("weather_code") or []
        fetched_at = datetime.now(tz=UTC)

        def at(seq: list, idx: int) -> float | None:
            return _clean(seq[idx]) if idx < len(seq) else None

        out: list[WeatherForecast] = []
        for idx, day in enumerate(days):
            code = codes[idx] if idx < len(codes) and codes[idx] is not None else None
            out.append(
                WeatherForecast(
                    site_key="",
                    forecast_date=date.fromisoformat(day),
                    temp_min_c=at(temp_min, idx),
                    temp_max_c=at(temp_max, idx),
                    precipitation_mm=at(precip, idx),
                    wind_speed_kmh=at(wind, idx),
                    wind_gust_kmh=at(gust, idx),
                    humidity_percent=at(humidity, idx),
                    weather_code=str(code) if code is not None else None,
                    source=self.source_name,
                    fetched_at=fetched_at,
                    data_kind="forecast",
                    is_current_conditions=False,
                )
            )
        return out

    async def health_check(self, *, config: object | None = None) -> bool:
        try:
            records = await self.fetch_daily(latitude=_HEALTH_LAT, longitude=_HEALTH_LON)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("open_meteo_health_check_failed", error=str(exc))
            return False
        return bool(records)
