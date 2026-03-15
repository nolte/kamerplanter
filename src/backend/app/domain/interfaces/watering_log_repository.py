from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from app.domain.models.watering_log import WateringLog


class IWateringLogRepository(ABC):

    @abstractmethod
    def create(self, log: WateringLog) -> WateringLog: ...

    @abstractmethod
    def get_by_key(self, key: str) -> WateringLog | None: ...

    @abstractmethod
    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[WateringLog], int]: ...

    @abstractmethod
    def update(self, key: str, log: WateringLog) -> WateringLog: ...

    @abstractmethod
    def update_fields(self, key: str, fields: dict) -> WateringLog: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def get_by_slot(self, slot_key: str, offset: int = 0, limit: int = 50) -> list[WateringLog]: ...

    @abstractmethod
    def get_by_location(self, location_key: str, offset: int = 0, limit: int = 50) -> list[WateringLog]: ...

    @abstractmethod
    def get_stats_by_location(self, location_key: str) -> dict: ...

    @abstractmethod
    def get_last_watering_date_for_run(self, run_key: str) -> date | None: ...

    @abstractmethod
    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> list[WateringLog]: ...

    @abstractmethod
    def get_latest_by_plant(self, plant_key: str) -> WateringLog | None: ...

    @abstractmethod
    def get_recent_runoff_logs(self, plant_key: str, limit: int = 5) -> list[WateringLog]: ...

    @abstractmethod
    def resolve_plant_names(self, plant_keys: list[str]) -> dict[str, str]: ...
