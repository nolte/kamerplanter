from datetime import UTC, datetime, timedelta

import structlog

from app.config.settings import settings
from app.data_access.external.ha_client import HomeAssistantClient
from app.domain.engines.frost_warning_engine import (
    evaluate_forecast_frost_warning,
    evaluate_frost_warning,
    pick_air_temperature,
)
from app.domain.interfaces.sensor_repository import ISensorRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
from app.domain.models.sensor import Sensor
from app.domain.models.weather import WeatherForecast

logger = structlog.get_logger(__name__)


class SensorService:
    def __init__(
        self,
        repo: ISensorRepository,
        ha_client: HomeAssistantClient | None,
        weather_forecast_repo: IWeatherForecastRepository | None = None,
        site_repo: ISiteRepository | None = None,
    ) -> None:
        self._repo = repo
        self._ha_client = ha_client
        # Optional (Issue #392): the proactive forecast path degrades gracefully
        # when either is absent — the reactive path never depends on them.
        self._weather_forecast_repo = weather_forecast_repo
        self._site_repo = site_repo

    def create_sensor(self, sensor: Sensor) -> Sensor:
        return self._repo.create(sensor)

    def get_sensors_for_tank(self, tank_key: str) -> list[Sensor]:
        return self._repo.find_by_tank(tank_key)

    def get_sensors_for_site(self, site_key: str) -> list[Sensor]:
        return self._repo.find_by_site(site_key)

    def get_sensors_for_location(self, location_key: str) -> list[Sensor]:
        return self._repo.find_by_location(location_key)

    def get_sensor(self, key: str) -> Sensor | None:
        return self._repo.get(key)

    def update_sensor(self, key: str, sensor: Sensor) -> Sensor:
        return self._repo.update(key, sensor)

    def delete_sensor(self, key: str) -> bool:
        return self._repo.delete(key)

    def get_live_state_for_sensors(self, sensors: list[Sensor]) -> dict:
        """Read-through live query for a list of sensors — NO persistence."""
        if not self._ha_client:
            return {
                "values": {},
                "errors": [],
                "source": "unavailable",
                "message": "Home Assistant not configured",
            }

        values: dict = {}
        errors: list[dict] = []
        for sensor in sensors:
            if not sensor.ha_entity_id:
                continue
            try:
                result = self._ha_client.get_state(sensor.ha_entity_id)
                if result and result["value"] is not None:
                    values[sensor.metric_type] = {
                        "value": result["value"],
                        "last_changed": result["last_changed"],
                        "entity_id": sensor.ha_entity_id,
                        "unit": result["unit"],
                    }
            except Exception as exc:
                logger.warning(
                    "ha_live_query_failed",
                    entity_id=sensor.ha_entity_id,
                    error=str(exc),
                )
                errors.append(
                    {
                        "entity_id": sensor.ha_entity_id,
                        "error": str(exc),
                    }
                )

        return {"values": values, "errors": errors, "source": "ha_live"}

    def get_ha_entities(self) -> list[dict]:
        """Return HA sensor entities with inferred metric_type and suggested name."""
        if not self._ha_client:
            return []

        device_class_map = {
            "ph": "ph",
            "ec": "ec_ms",
            "electrical_conductivity": "ec_ms",
            "temperature": "water_temp_celsius",
            "humidity": "humidity_percent",
            "carbon_dioxide": "co2_ppm",
            "volatile_organic_compounds": "co2_ppm",
        }
        unit_map = {
            "mS/cm": "ec_ms",
            "µS/cm": "ec_ms",
            "mS": "ec_ms",
            "°C": "water_temp_celsius",
            "°F": "water_temp_celsius",
            "%": "fill_level_percent",
            "ppm": "tds_ppm",
            "pH": "ph",
        }

        entities = self._ha_client.list_sensor_entities()
        result = []
        for e in entities:
            if e["entity_id"].startswith("sensor.kp_"):
                continue
            device_class = (e.get("device_class") or "").lower()
            unit = e.get("unit_of_measurement") or ""
            friendly = e.get("friendly_name") or e["entity_id"]

            suggested_metric = device_class_map.get(device_class) or unit_map.get(unit)

            result.append(
                {
                    "entity_id": e["entity_id"],
                    "friendly_name": friendly,
                    "unit_of_measurement": e.get("unit_of_measurement"),
                    "device_class": e.get("device_class"),
                    "state": e.get("state"),
                    "suggested_metric_type": suggested_metric,
                    "suggested_name": friendly,
                }
            )

        result.sort(key=lambda x: (x["suggested_metric_type"] is None, x["friendly_name"].lower()))
        return result

    def get_live_state(self, tank_key: str) -> dict:
        """Read-through live query for a tank — NO persistence."""
        sensors = self._repo.find_by_tank(tank_key)
        return self.get_live_state_for_sensors(sensors)

    def get_location_frost_warning(
        self,
        location_key: str,
        threshold_celsius: float | None = None,
        site_key: str | None = None,
        *,
        tenant_key: str,
    ) -> dict:
        """Compute the frost-warning state for a location — NO persistence.

        Backs the Home Assistant ``binary_sensor.kp_{location}_frost_warning``
        entity. The reactive ``frost_warning`` is derived from the location's most
        recent ambient temperature reading (read-through via Home Assistant) and
        the configured threshold; when no reading is available it is ``None``
        (Home Assistant reports ``unknown``) rather than a fabricated ``False``.

        Issue #392 adds the *additive* proactive forecast fields
        (``forecast_frost_warning`` etc.) derived from the persisted daily
        forecasts for the location's site (``site_key`` / ``tenant_key`` supplied
        by the router). The forecast path degrades gracefully: no forecast repo,
        ``weather_enabled`` off, no ``site_key``, no site coordinates, or no
        usable in-horizon record all leave the forecast fields ``None`` and the
        reactive field untouched — never a 500.
        """
        threshold = threshold_celsius if threshold_celsius is not None else settings.frost_warning_threshold_celsius

        sensors = self._repo.find_by_location(location_key)
        live = self.get_live_state_for_sensors(sensors)
        temperature, entity_id = pick_air_temperature(live["values"])
        frost_warning = evaluate_frost_warning(temperature, threshold)

        if live["source"] == "unavailable":
            source = "unavailable"
        elif temperature is None:
            source = "no_temperature"
        else:
            source = "ha_live"

        forecast = self._forecast_frost_summary(site_key, tenant_key)

        return {
            "location_key": location_key,
            "frost_warning": frost_warning,
            "temperature_celsius": temperature,
            "threshold_celsius": threshold,
            "source": source,
            "entity_id": entity_id,
            "forecast_frost_warning": forecast["predicted"],
            "forecast_min_temperature": forecast["min_temp"],
            "forecast_expected_date": forecast["expected_date"],
            "forecast_source": forecast["source"],
        }

    def get_site_weather_forecast(self, site_key: str, tenant_key: str) -> dict:
        """Return the in-horizon daily forecast for a site plus the frost summary.

        Backs the dashboard/per-site ``WeatherForecastWidget`` (Issue #392, R7):
        the in-horizon daily forecast rows (with ``source`` / ``data_kind``
        provenance) and the proactive frost early-warning summary. Graceful: no
        forecast repo, ``weather_enabled`` off, unknown/foreign site, no
        coordinates, or no forecast records all yield an empty ``forecasts`` list
        with ``None`` summary fields — never a 500.
        """
        empty: dict = {
            "site_key": site_key,
            "forecasts": [],
            "forecast_frost_warning": None,
            "forecast_min_temperature": None,
            "forecast_expected_date": None,
            "forecast_source": None,
        }
        try:
            forecasts = self._load_site_forecasts(site_key, tenant_key)
            if forecasts is None:
                return empty

            today = datetime.now(UTC).date()
            horizon_days = settings.frost_forecast_horizon_days
            horizon_end = today + timedelta(days=horizon_days - 1)
            in_horizon = sorted(
                (record for record in forecasts if today <= record.forecast_date <= horizon_end),
                key=lambda record: record.forecast_date,
            )
            summary = evaluate_forecast_frost_warning(
                forecasts,
                settings.frost_forecast_threshold_celsius,
                horizon_days,
                today,
            )
            return {
                "site_key": site_key,
                "forecasts": [self._forecast_day_dict(record) for record in in_horizon],
                "forecast_frost_warning": summary["predicted"],
                "forecast_min_temperature": summary["min_temp"],
                "forecast_expected_date": summary["expected_date"],
                "forecast_source": summary["source"],
            }
        except Exception as exc:
            logger.warning("site_weather_forecast_failed", site_key=site_key, error=str(exc))
            return empty

    @staticmethod
    def _forecast_day_dict(record: WeatherForecast) -> dict:
        return {
            "forecast_date": record.forecast_date,
            "temp_min_c": record.temp_min_c,
            "temp_max_c": record.temp_max_c,
            "precipitation_mm": record.precipitation_mm,
            "wind_speed_kmh": record.wind_speed_kmh,
            "humidity_percent": record.humidity_percent,
            "weather_code": record.weather_code,
            "source": record.source,
            "data_kind": record.data_kind,
        }

    def _forecast_frost_summary(self, site_key: str | None, tenant_key: str) -> dict:
        """Compute the proactive frost summary for a site, never raising.

        Returns the ``evaluate_forecast_frost_warning`` mapping, or the all-``None``
        "unknown" mapping when no usable forecast source is available (R5).
        """
        unknown: dict = {"predicted": None, "min_temp": None, "expected_date": None, "source": None}
        try:
            forecasts = self._load_site_forecasts(site_key, tenant_key)
            if forecasts is None:
                return unknown
            return evaluate_forecast_frost_warning(
                forecasts,
                settings.frost_forecast_threshold_celsius,
                settings.frost_forecast_horizon_days,
                datetime.now(UTC).date(),
            )
        except Exception as exc:
            logger.warning("forecast_frost_warning_failed", site_key=site_key, error=str(exc))
            return unknown

    def _load_site_forecasts(self, site_key: str | None, tenant_key: str) -> list[WeatherForecast] | None:
        """Load the persisted daily forecasts for a site, or ``None`` when the
        proactive path is unavailable (repo missing, weather disabled, no
        ``site_key``, unknown/foreign site, or a site without coordinates).

        Tenant isolation (R10): the forecast read is scoped by ``tenant_key``, and
        when the site repo is available the site's own ``tenant_key`` is verified
        fail-closed so a foreign site key cannot probe the proactive path. The
        comparison is unconditional: an empty ``tenant_key`` (light mode) only
        matches a site whose ``tenant_key`` is likewise empty — never a bypass.
        """
        if self._weather_forecast_repo is None or not settings.weather_enabled or not site_key:
            return None
        if self._site_repo is not None:
            site = self._site_repo.get_site_by_key(site_key)
            if site is None or site.gps_coordinates is None:
                return None
            if site.tenant_key != tenant_key:
                return None
        return self._weather_forecast_repo.find_by_site(site_key, tenant_key)
