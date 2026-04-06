import structlog

from app.data_access.external.ha_client import HomeAssistantClient
from app.domain.interfaces.sensor_repository import ISensorRepository
from app.domain.models.sensor import Sensor

logger = structlog.get_logger(__name__)


class SensorService:
    def __init__(
        self,
        repo: ISensorRepository,
        ha_client: HomeAssistantClient | None,
    ) -> None:
        self._repo = repo
        self._ha_client = ha_client

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
