from datetime import datetime

import structlog

from app.common.exceptions import NotFoundError
from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.interfaces.sensor_repository import ISensorRepository
from app.domain.models.observation import AggregatedReading, SensorReading

logger = structlog.get_logger(__name__)


class ObservationService:
    def __init__(
        self,
        observation_repo: IObservationRepository,
        sensor_repo: ISensorRepository,
    ) -> None:
        self._obs_repo = observation_repo
        self._sensor_repo = sensor_repo

    def record_reading(self, reading: SensorReading) -> None:
        sensor = self._sensor_repo.get(reading.sensor_key)
        if sensor is None:
            raise NotFoundError("Sensor", reading.sensor_key)
        self._obs_repo.insert(reading)

    def record_readings_batch(self, readings: list[SensorReading]) -> int:
        return self._obs_repo.insert_batch(readings)

    def get_readings(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
        resolution: str = "raw",
    ) -> list[SensorReading] | list[AggregatedReading]:
        if resolution == "hourly":
            return self._obs_repo.query_hourly(sensor_key, start, end, tenant_key)
        if resolution == "daily":
            return self._obs_repo.query_daily(sensor_key, start, end, tenant_key)
        return self._obs_repo.query_raw(sensor_key, start, end, tenant_key)

    def get_latest_reading(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> SensorReading | None:
        return self._obs_repo.get_latest(sensor_key, tenant_key)

    def delete_readings_for_sensor(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> int:
        return self._obs_repo.delete_by_sensor(sensor_key, tenant_key)

    def is_available(self) -> bool:
        return self._obs_repo.is_available()
