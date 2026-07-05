"""REQ-046 §3.3 — ``DwdWeatherAdapter`` (public, key-free, DACH).

DWD Open Data is consumed pragmatically through the free Brightsky JSON facade
(``api.brightsky.dev``) which exposes the DWD raw data as clean JSON (WMO-style
``icon``/``condition`` present), avoiding the MOSMIX KMZ parsing. Attribution
remains DWD (GeoNutzV): ``Datenbasis: Deutscher Wetterdienst``.

Brightsky returns *hourly* records; this adapter aggregates them into daily
:class:`WeatherForecast` values (min/max temperature, precipitation sum,
max wind/gust, mean humidity, representative weather code).
"""

from datetime import UTC, date, datetime, timedelta

import httpx
import structlog

from app.config.settings import settings
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

logger = structlog.get_logger(__name__)

_HEALTH_LAT = 52.52
_HEALTH_LON = 13.40
_FORECAST_DAYS = 7

#: Brightsky ``icon`` -> WMO weather code (string). Robust superset; unknown
#: icons collapse to ``None``.
_ICON_TO_WMO: dict[str, str] = {
    "clear-day": "0",
    "clear-night": "0",
    "partly-cloudy-day": "2",
    "partly-cloudy-night": "2",
    "cloudy": "3",
    "fog": "45",
    "wind": "1",
    "rain": "61",
    "sleet": "66",
    "snow": "71",
    "hail": "96",
    "thunderstorm": "95",
}

#: Brightsky ``condition`` -> WMO weather code (fallback when ``icon`` missing).
_CONDITION_TO_WMO: dict[str, str] = {
    "dry": "0",
    "fog": "45",
    "rain": "61",
    "sleet": "66",
    "snow": "71",
    "hail": "96",
    "thunderstorm": "95",
}


def _condition_to_wmo(icon: str | None, condition: str | None) -> str | None:
    if icon and icon in _ICON_TO_WMO:
        return _ICON_TO_WMO[icon]
    if condition and condition in _CONDITION_TO_WMO:
        return _CONDITION_TO_WMO[condition]
    return None


class _DayAccumulator:
    """Aggregates hourly Brightsky records for a single calendar day."""

    def __init__(self) -> None:
        self.temps: list[float] = []
        self.precip: float = 0.0
        self.wind_max: float | None = None
        self.gust_max: float | None = None
        self.humidities: list[float] = []
        self.icon: str | None = None
        self.condition: str | None = None

    def add(self, record: dict) -> None:
        temp = record.get("temperature")
        if temp is not None:
            self.temps.append(float(temp))
        precip = record.get("precipitation")
        if precip is not None:
            self.precip += float(precip)
        wind = record.get("wind_speed")
        if wind is not None:
            self.wind_max = float(wind) if self.wind_max is None else max(self.wind_max, float(wind))
        gust = record.get("wind_gust_speed")
        if gust is not None:
            self.gust_max = float(gust) if self.gust_max is None else max(self.gust_max, float(gust))
        humidity = record.get("relative_humidity")
        if humidity is not None:
            self.humidities.append(float(humidity))
        # Keep a representative daytime code (first non-empty wins).
        if self.icon is None and record.get("icon"):
            self.icon = record.get("icon")
        if self.condition is None and record.get("condition"):
            self.condition = record.get("condition")


@WeatherAdapterRegistry.register
class DwdWeatherAdapter(WeatherAdapter):
    """DWD via the Brightsky JSON facade — free, no API key, DACH (REQ-046 §3.3)."""

    source_name = "dwd"
    kind = "public"
    requires_api_key = False

    def __init__(self, *, base_url: str | None = None, timeout_s: float | None = None) -> None:
        self._base_url = (base_url or settings.dwd_base_url).rstrip("/")
        self._timeout = timeout_s if timeout_s is not None else float(settings.weather_fetch_timeout_s)

    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        start = date.today()
        last = start + timedelta(days=_FORECAST_DAYS - 1)
        params = {
            "lat": latitude,
            "lon": longitude,
            "date": start.isoformat(),
            "last_date": last.isoformat(),
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/weather", params=params)
            resp.raise_for_status()
            return self._map(resp.json())

    def _map(self, payload: dict) -> list[WeatherForecast]:
        hourly: list[dict] = payload.get("weather") or []
        by_day: dict[date, _DayAccumulator] = {}
        for record in hourly:
            timestamp = record.get("timestamp")
            if not timestamp:
                continue
            try:
                day = datetime.fromisoformat(timestamp).date()
            except ValueError:
                continue
            by_day.setdefault(day, _DayAccumulator()).add(record)

        fetched_at = datetime.now(tz=UTC)
        out: list[WeatherForecast] = []
        for day in sorted(by_day):
            acc = by_day[day]
            out.append(
                WeatherForecast(
                    site_key="",
                    forecast_date=day,
                    temp_min_c=min(acc.temps) if acc.temps else None,
                    temp_max_c=max(acc.temps) if acc.temps else None,
                    precipitation_mm=round(acc.precip, 2) if acc.precip else 0.0 if acc.temps else None,
                    wind_speed_kmh=acc.wind_max,
                    wind_gust_kmh=acc.gust_max,
                    humidity_percent=(sum(acc.humidities) / len(acc.humidities)) if acc.humidities else None,
                    weather_code=_condition_to_wmo(acc.icon, acc.condition),
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
            logger.warning("dwd_health_check_failed", error=str(exc))
            return False
        return bool(records)
