from abc import ABC, abstractmethod

from app.common.types import LocationKey, SlotKey, WateringEventKey
from app.domain.models.watering_event import WateringEvent


class IWateringRepository(ABC):
    # ── Create & Read ──────────────────────────────────────────────────

    @abstractmethod
    def create(self, event: WateringEvent) -> WateringEvent:
        ...

    @abstractmethod
    def get_by_key(self, key: WateringEventKey) -> WateringEvent | None:
        ...

    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[WateringEvent], int]:
        ...

    # ── Queries ────────────────────────────────────────────────────────

    @abstractmethod
    def get_by_slot(
        self, slot_key: SlotKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        ...

    @abstractmethod
    def get_by_location(
        self, location_key: LocationKey, offset: int = 0, limit: int = 50,
    ) -> list[WateringEvent]:
        ...

    @abstractmethod
    def get_stats_by_location(self, location_key: LocationKey) -> dict:
        ...
