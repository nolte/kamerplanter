"""REQ-041 §3 — ``NasaPowerWeatherAdapter`` (public, key-free, global reanalysis).

NASA POWER (power.larc.nasa.gov) is a keyless, globally available source of
satellite/model **reanalysis** data. Unlike the forecast adapters it does not
predict the future — it serves quality-controlled *past* daily values (with a
publication latency of a few days) and long-term monthly **climate normals**.
Both feed the outdoor requirements built on top of REQ-041:

* ``fetch_daily`` returns recent daily values (``data_kind="reanalysis"``) with a
  populated ``solar_radiation_mj_m2`` — the measured-radiation input the REQ-037
  Penman-Monteith path needs.
* ``fetch_climate_normals`` returns the twelve monthly averages used by the
  REQ-039 hardiness-zone resolver.

Because the records are reanalysis, they are deliberately excluded from the
proactive frost early-warning (see ``frost_warning_engine`` /
``frost_forecast_tasks``): only genuine ``"forecast"`` records may raise a
warning.

Attribution: ``Klima- und Strahlungsdaten: NASA POWER (power.larc.nasa.gov)``
(CC-BY-4.0 / US public domain — citation requested).
"""

from datetime import UTC, date, datetime, timedelta

import httpx
import structlog

from app.config.settings import settings
from app.domain.interfaces.weather_adapter import WeatherAdapter
from app.domain.models.weather import ClimateNormal, WeatherForecast
from app.domain.services.weather_adapter_registry import WeatherAdapterRegistry

logger = structlog.get_logger(__name__)

#: Reference point (Berlin) used by the lightweight health probe.
_HEALTH_LAT = 52.52
_HEALTH_LON = 13.40

#: POWER's universal "no value" fill; collapsed to ``None`` everywhere.
_MISSING_SENTINEL = -999.0

#: Daily parameters requested from ``/daily/point`` (community ``AG``).
_DAILY_PARAMETERS = "T2M_MIN,T2M_MAX,PRECTOTCORR,WS2M,RH2M,ALLSKY_SFC_SW_DWN"

#: Climatology parameters requested from ``/climatology/point``.
_CLIMATOLOGY_PARAMETERS = "T2M,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN"

#: The twelve POWER climatology month keys, in calendar order. POWER also emits an
#: ``ANN`` (annual) key which is read separately.
_MONTH_KEYS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

#: Days per calendar month (non-leap reference) used to turn POWER's mm/day
#: climatology precipitation into a monthly total in mm.
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

#: m/s → km/h (POWER wind ``WS2M`` is metres per second).
_MS_TO_KMH = 3.6


def _clean(value: float | int | None) -> float | None:
    """Return ``None`` for missing / POWER-sentinel values, else a float."""
    if value is None:
        return None
    number = float(value)
    if number == _MISSING_SENTINEL:
        return None
    return number


@WeatherAdapterRegistry.register
class NasaPowerWeatherAdapter(WeatherAdapter):
    """NASA POWER — free, keyless, global reanalysis + climate normals (REQ-041)."""

    source_name = "nasa-power"
    kind = "public"
    requires_api_key = False

    def __init__(self, *, base_url: str | None = None, timeout_s: float | None = None) -> None:
        self._base_url = (base_url or settings.nasa_power_base_url).rstrip("/")
        self._timeout = timeout_s if timeout_s is not None else float(settings.weather_fetch_timeout_s)

    # ── Daily reanalysis values ───────────────────────────────────────────────

    def _daily_window(self, today: date | None = None) -> tuple[date, date]:
        """Return the inclusive ``(start, end)`` look-back window.

        POWER publishes daily values with a few days' latency, so the window ends
        ``latency`` days before today and spans ``days_back`` days. ``today`` is
        injectable to keep the mapping deterministic under test.
        """
        anchor = today or datetime.now(tz=UTC).date()
        end = anchor - timedelta(days=settings.nasa_power_data_latency_days)
        start = end - timedelta(days=max(settings.nasa_power_daily_days_back - 1, 0))
        return start, end

    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        start, end = self._daily_window()
        params = {
            "parameters": _DAILY_PARAMETERS,
            "community": "AG",
            "latitude": latitude,
            "longitude": longitude,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/daily/point", params=params)
            resp.raise_for_status()
            return self._map_daily(resp.json())

    def _map_daily(self, payload: dict) -> list[WeatherForecast]:
        parameter = (((payload or {}).get("properties") or {}).get("parameter")) or {}
        temp_min = parameter.get("T2M_MIN") or {}
        temp_max = parameter.get("T2M_MAX") or {}
        precip = parameter.get("PRECTOTCORR") or {}
        wind = parameter.get("WS2M") or {}
        humidity = parameter.get("RH2M") or {}
        solar = parameter.get("ALLSKY_SFC_SW_DWN") or {}
        fetched_at = datetime.now(tz=UTC)

        # POWER keys every parameter by the same ``YYYYMMDD`` day strings; union them
        # so a day missing from one parameter still produces a record.
        day_keys = sorted({key for series in (temp_min, temp_max, precip, wind, humidity, solar) for key in series})

        out: list[WeatherForecast] = []
        for day_key in day_keys:
            forecast_date = datetime.strptime(day_key, "%Y%m%d").date()
            wind_ms = _clean(wind.get(day_key))
            out.append(
                WeatherForecast(
                    site_key="",
                    forecast_date=forecast_date,
                    temp_min_c=_clean(temp_min.get(day_key)),
                    temp_max_c=_clean(temp_max.get(day_key)),
                    precipitation_mm=_clean(precip.get(day_key)),
                    wind_speed_kmh=round(wind_ms * _MS_TO_KMH, 2) if wind_ms is not None else None,
                    wind_gust_kmh=None,
                    humidity_percent=_clean(humidity.get(day_key)),
                    weather_code=None,
                    solar_radiation_mj_m2=_clean(solar.get(day_key)),
                    source=self.source_name,
                    fetched_at=fetched_at,
                    data_kind="reanalysis",
                    is_current_conditions=False,
                )
            )
        return out

    # ── Climate normals ───────────────────────────────────────────────────────

    async def fetch_climate_normals(self, *, latitude: float, longitude: float) -> ClimateNormal | None:
        params = {
            "parameters": _CLIMATOLOGY_PARAMETERS,
            "community": "AG",
            "latitude": latitude,
            "longitude": longitude,
            "format": "JSON",
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/climatology/point", params=params)
            resp.raise_for_status()
            return self._map_climate_normals(resp.json())

    def _map_climate_normals(self, payload: dict) -> ClimateNormal | None:
        payload = payload or {}
        parameter = ((payload.get("properties") or {}).get("parameter")) or {}
        if not parameter:
            return None

        monthly_temp_avg = self._months(parameter.get("T2M"))
        monthly_temp_min = self._months(parameter.get("T2M_MIN"))
        monthly_solar = self._months(parameter.get("ALLSKY_SFC_SW_DWN"))
        # POWER climatology precipitation is a mean **mm/day** per month; convert to
        # a monthly total in mm so ``monthly_precip_mm`` is a meaningful sum.
        monthly_precip_per_day = self._months(parameter.get("PRECTOTCORR"))
        monthly_precip = [round(value * _DAYS_IN_MONTH[idx], 2) for idx, value in enumerate(monthly_precip_per_day)]

        coldest = min(monthly_temp_min) if monthly_temp_min else None
        annual_temp = self._annual(parameter.get("T2M"))
        annual_precip = sum(monthly_precip) if monthly_precip else None
        start_year, end_year = self._period(payload)

        return ClimateNormal(
            site_key="",
            source=self.source_name,
            fetched_at=datetime.now(tz=UTC),
            monthly_temp_min_c=monthly_temp_min,
            monthly_temp_max_c=[],  # POWER climatology exposes no monthly Tmax
            coldest_month_min_c=coldest,
            period_start_year=start_year,
            period_end_year=end_year,
            monthly_temp_avg_c=monthly_temp_avg,
            monthly_precip_mm=monthly_precip,
            monthly_solar_mj_m2=monthly_solar,
            annual_temp_avg_c=annual_temp,
            annual_precip_mm=round(annual_precip, 2) if annual_precip is not None else None,
        )

    @staticmethod
    def _months(series: dict | None) -> list[float]:
        """Project a POWER climatology parameter onto twelve ordered month values.

        Returns ``[]`` when the series is absent or any month is missing/sentinel,
        so a partial payload never yields a half-length list that the UI would
        mis-align.
        """
        if not series:
            return []
        values: list[float] = []
        for month_key in _MONTH_KEYS:
            cleaned = _clean(series.get(month_key))
            if cleaned is None:
                return []
            values.append(cleaned)
        return values

    @staticmethod
    def _annual(series: dict | None) -> float | None:
        if not series:
            return None
        return _clean(series.get("ANN"))

    @staticmethod
    def _period(payload: dict) -> tuple[int | None, int | None]:
        """Extract the averaging period (start/end year) from the POWER header."""
        header = payload.get("header") or {}
        start = header.get("start")
        end = header.get("end")

        def _year(value: object) -> int | None:
            try:
                # POWER reports the period as full years (``2001``) or, in some
                # payloads, ``YYYYMMDD``; keep only the leading four digits.
                return int(str(value)[:4]) if value is not None else None
            # NB: the ``as exc`` binding is deliberate — a bare tuple-except without
            # it is miscompiled by ``ruff format`` into invalid ``except A, B:``.
            except (TypeError, ValueError) as exc:  # noqa: F841
                return None

        return _year(start), _year(end)

    # ── Health probe ───────────────────────────────────────────────────────────

    async def health_check(self, *, config: object | None = None) -> bool:
        try:
            records = await self.fetch_daily(latitude=_HEALTH_LAT, longitude=_HEALTH_LON)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("nasa_power_health_check_failed", error=str(exc))
            return False
        return bool(records)
