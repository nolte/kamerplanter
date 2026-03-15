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

    def get_live_state(self, tank_key: str) -> dict:
        """Read-through live query for a tank — NO persistence."""
        sensors = self._repo.find_by_tank(tank_key)
        return self.get_live_state_for_sensors(sensors)
