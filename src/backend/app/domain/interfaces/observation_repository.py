from abc import ABC, abstractmethod
from collections.abc import Generator
from datetime import datetime

from app.domain.models.observation import AggregatedReading, ArchivedReading, SensorReading


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
    def delete_by_tenant(self, tenant_key: str) -> int:
        """Delete every raw reading of the tenant (tenant deletion, #1769); returns the count removed."""

    @abstractmethod
    def iter_tenant_readings(self, tenant_key: str, *, page_size: int) -> Generator[list[ArchivedReading]]:
        """Every reading of the tenant still kept — raw rows, then hourly, then daily buckets — page by page.

        The tenant export's read (REQ-056 §8.3, #2138). Bound to the tenant by the query itself:
        only rows whose ``tenant_key`` is *tenant_key* — never a caller-supplied list of series, and
        never the pre-#2076 rows without a tenant key. An empty *tenant_key* raises ``ValueError``
        (on the first ``next``). The caller must exhaust or ``close()`` the generator: it holds a
        database connection while open.
        """

    @abstractmethod
    def is_available(self) -> bool: ...
