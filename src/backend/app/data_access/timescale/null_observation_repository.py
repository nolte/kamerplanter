from datetime import datetime

from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.models.observation import AggregatedReading, SensorReading


class NullObservationRepository(IObservationRepository):
    """No-op repository used when TimescaleDB is disabled."""

    def insert(self, reading: SensorReading) -> None:
        pass

    def insert_batch(self, readings: list[SensorReading]) -> int:
        return 0

    def query_raw(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
        limit: int = 1000,
    ) -> list[SensorReading]:
        return []

    def query_hourly(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
    ) -> list[AggregatedReading]:
        return []

    def query_daily(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
    ) -> list[AggregatedReading]:
        return []

    def get_latest(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> SensorReading | None:
        return None

    def delete_by_sensor(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> int:
        return 0

    def is_available(self) -> bool:
        return False
