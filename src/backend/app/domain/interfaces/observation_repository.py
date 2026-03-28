from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.models.observation import AggregatedReading, SensorReading


class IObservationRepository(ABC):
    @abstractmethod
    def insert(self, reading: SensorReading) -> None: ...

    @abstractmethod
    def insert_batch(self, readings: list[SensorReading]) -> int: ...

    @abstractmethod
    def query_raw(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
        limit: int = 1000,
    ) -> list[SensorReading]: ...

    @abstractmethod
    def query_hourly(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
    ) -> list[AggregatedReading]: ...

    @abstractmethod
    def query_daily(
        self,
        sensor_key: str,
        start: datetime,
        end: datetime,
        tenant_key: str,
    ) -> list[AggregatedReading]: ...

    @abstractmethod
    def get_latest(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> SensorReading | None: ...

    @abstractmethod
    def delete_by_sensor(
        self,
        sensor_key: str,
        tenant_key: str,
    ) -> int: ...

    @abstractmethod
    def is_available(self) -> bool: ...
