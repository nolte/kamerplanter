"""REQ-046 §3.3 — ``OpenWeatherMapWeatherAdapter`` (public, API-key, global).

Uses the OpenWeatherMap 5-day / 3-hour ``/forecast`` endpoint (``units=metric``)
and aggregates the 3-hourly slices into daily :class:`WeatherForecast` values.

The adapter receives the **decrypted plaintext** API key as a constructor
parameter — the Fernet decryption of ``config.api_key_ref`` is done by the
resolver (which owns the :class:`EncryptionEngine`), never by the adapter. If no
key is available, :meth:`fetch_daily` returns ``[]`` (no exception), so a missing
key degrades gracefully to the next prioritised source.
"""

from datetime import UTC, date, datetime

import httpx
import structlog

from app.config.settings import settings
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

logger = structlog.get_logger(__name__)

_HEALTH_LAT = 52.52
_HEALTH_LON = 13.40
_MS_TO_KMH = 3.6


#: OpenWeatherMap condition-id group -> WMO weather code (string). Mapped by the
#: leading digit / range of the OWM ``weather[0].id``.
def _owm_id_to_wmo(owm_id: int | None) -> str | None:
    if owm_id is None:
        return None
    if 200 <= owm_id < 300:
        return "95"  # thunderstorm
    if 300 <= owm_id < 400:
        return "51"  # drizzle
    if 500 <= owm_id < 600:
        return "61"  # rain
    if 600 <= owm_id < 700:
        return "71"  # snow
    if 700 <= owm_id < 800:
        return "45"  # atmosphere (fog/mist/haze)
    if owm_id == 800:
        return "0"  # clear
    if 801 <= owm_id < 900:
        return "3"  # clouds
    return None


class _DayAccumulator:
    """Aggregates 3-hourly OpenWeatherMap slices for a single calendar day."""

    def __init__(self) -> None:
        self.temp_min: float | None = None
        self.temp_max: float | None = None
        self.precip: float = 0.0
        self.wind_max: float | None = None
        self.gust_max: float | None = None
        self.humidities: list[float] = []
        self.owm_id: int | None = None

    def add(self, slice_: dict) -> None:
        main = slice_.get("main") or {}
        t_min = main.get("temp_min")
        if t_min is not None:
            self.temp_min = float(t_min) if self.temp_min is None else min(self.temp_min, float(t_min))
        t_max = main.get("temp_max")
        if t_max is not None:
            self.temp_max = float(t_max) if self.temp_max is None else max(self.temp_max, float(t_max))
        humidity = main.get("humidity")
        if humidity is not None:
            self.humidities.append(float(humidity))

        rain = slice_.get("rain") or {}
        self.precip += float(rain.get("3h", 0.0) or 0.0)

        wind = slice_.get("wind") or {}
        speed = wind.get("speed")
        if speed is not None:
            kmh = float(speed) * _MS_TO_KMH
            self.wind_max = kmh if self.wind_max is None else max(self.wind_max, kmh)
        gust = wind.get("gust")
        if gust is not None:
            gkmh = float(gust) * _MS_TO_KMH
            self.gust_max = gkmh if self.gust_max is None else max(self.gust_max, gkmh)

        weather = slice_.get("weather") or []
        if self.owm_id is None and weather:
            self.owm_id = weather[0].get("id")


@WeatherAdapterRegistry.register
class OpenWeatherMapWeatherAdapter(WeatherAdapter):
    """OpenWeatherMap — global, requires an API key (REQ-046 §3.3)."""

    source_name = "openweathermap"
    kind = "public"
    requires_api_key = True

    def __init__(
        self, api_key: str | None = None, *, base_url: str | None = None, timeout_s: float | None = None
    ) -> None:
        self._api_key = api_key
        self._base_url = (base_url or settings.openweathermap_base_url).rstrip("/")
        self._timeout = timeout_s if timeout_s is not None else float(settings.weather_fetch_timeout_s)

    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        if not self._api_key:
            logger.info("openweathermap_no_api_key", detail="skipping — missing key")
            return []
        params = {
            "lat": latitude,
            "lon": longitude,
            "units": "metric",
            "appid": self._api_key,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(f"{self._base_url}/forecast", params=params)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                # SEC-001: httpx error strings echo the full request URL including
                # the ``appid`` query param. Never let the plaintext key reach a log
                # or an API response — re-raise with the key redacted, keeping the
                # base ``httpx.HTTPError`` type so the resolver still treats it as a
                # fetchable failure and falls back to the next source.
                raise httpx.HTTPError(self._redact(str(exc))) from None
            return self._map(resp.json())

    def _redact(self, message: str) -> str:
        """Strip the plaintext API key from an error/log string (SEC-001)."""
        return message.replace(self._api_key, "***") if self._api_key else message

    def _map(self, payload: dict) -> list[WeatherForecast]:
        slices: list[dict] = payload.get("list") or []
        by_day: dict[date, _DayAccumulator] = {}
        for slice_ in slices:
            dt = slice_.get("dt")
            if dt is None:
                continue
            day = datetime.fromtimestamp(dt, tz=UTC).date()
            by_day.setdefault(day, _DayAccumulator()).add(slice_)

        fetched_at = datetime.now(tz=UTC)
        out: list[WeatherForecast] = []
        for day in sorted(by_day):
            acc = by_day[day]
            out.append(
                WeatherForecast(
                    site_key="",
                    forecast_date=day,
                    temp_min_c=acc.temp_min,
                    temp_max_c=acc.temp_max,
                    precipitation_mm=round(acc.precip, 2),
                    wind_speed_kmh=round(acc.wind_max, 2) if acc.wind_max is not None else None,
                    wind_gust_kmh=round(acc.gust_max, 2) if acc.gust_max is not None else None,
                    humidity_percent=(sum(acc.humidities) / len(acc.humidities)) if acc.humidities else None,
                    weather_code=_owm_id_to_wmo(acc.owm_id),
                    source=self.source_name,
                    fetched_at=fetched_at,
                    data_kind="forecast",
                    is_current_conditions=False,
                )
            )
        return out

    async def health_check(self, *, config: object | None = None) -> bool:
        if not self._api_key:
            return False
        try:
            records = await self.fetch_daily(latitude=_HEALTH_LAT, longitude=_HEALTH_LON)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("openweathermap_health_check_failed", error=str(exc))
            return False
        return bool(records)
