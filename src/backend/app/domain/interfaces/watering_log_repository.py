from abc import ABC, abstractmethod
from datetime import date

from app.domain.models.watering_log import WateringLog


class IWateringLogRepository(ABC):
    @abstractmethod
    def list_window(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str | None = None,
        all_tenants: bool = False,
        after: str | None = None,
    ) -> list[WateringLog]:
        """One ``_key``-ordered page of the tenant's rows, without a count (MT-035, #2131)."""
        ...

    @abstractmethod
    def create(self, log: WateringLog) -> WateringLog: ...

    @abstractmethod
    def get_by_key(self, key: str) -> WateringLog | None: ...

    @abstractmethod
    def get_or_raise(self, key: str) -> WateringLog: ...

    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[WateringLog], int]: ...

    @abstractmethod
    def update(self, key: str, log: WateringLog) -> WateringLog: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict) -> WateringLog: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def get_by_slot(
        self,
        slot_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringLog]:
        """Return a slot's watering logs inside ``tenant_key`` (#927)."""
        ...

    @abstractmethod
    def get_by_location(
        self,
        location_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringLog]:
        """Return a location's watering logs inside ``tenant_key`` (#927)."""
        ...

    @abstractmethod
    def get_stats_by_location(self, location_key: str, *, tenant_key: str) -> dict: ...

    @abstractmethod
    def get_last_watering_date_for_run(self, run_key: str, *, tenant_key: str) -> date | None: ...

    @abstractmethod
    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
        *,
        all_tenants: bool = False,
    ) -> list[WateringLog]: ...

    @abstractmethod
    def resolve_plant_names(self, plant_keys: list[str], *, tenant_key: str) -> dict[str, str]:
        """Resolve plant keys to display names inside ``tenant_key`` (#952)."""
        ...
