from collections.abc import Generator
from datetime import datetime

from app.domain.interfaces.observation_repository import IObservationRepository
from app.domain.models.observation import AggregatedReading, ArchivedReading, SensorReading


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

    def delete_by_tenant(self, tenant_key: str) -> int:
        return 0

    def iter_tenant_readings(self, tenant_key: str, *, page_size: int) -> Generator[list[ArchivedReading]]:
        """A deployment without TimescaleDB stores no reading, so a tenant has none to export."""
        if not tenant_key:
            msg = "iter_tenant_readings needs a tenant key"
            raise ValueError(msg)
        yield from ()

    def is_available(self) -> bool:
        return False
