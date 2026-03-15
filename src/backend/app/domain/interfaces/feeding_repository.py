from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import FeedingEventKey
    from app.domain.models.feeding_event import FeedingEvent


class IFeedingRepository(ABC):
    # ── CRUD ─────────────────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self, offset: int = 0, limit: int = 50,
    ) -> tuple[list[FeedingEvent], int]:
        ...

    @abstractmethod
    def get_by_key(self, key: FeedingEventKey) -> FeedingEvent | None:
        ...

    @abstractmethod
    def create(self, event: FeedingEvent) -> FeedingEvent:
        ...

    @abstractmethod
    def update(self, key: FeedingEventKey, event: FeedingEvent) -> FeedingEvent:
        ...

    @abstractmethod
    def delete(self, key: FeedingEventKey) -> bool:
        ...

    # ── Queries ──────────────────────────────────────────────────────

    @abstractmethod
    def get_by_plant(self, plant_key: str, offset: int = 0, limit: int = 50) -> list[FeedingEvent]:
        ...

    @abstractmethod
    def get_latest_by_plant(self, plant_key: str) -> FeedingEvent | None:
        ...

    @abstractmethod
    def get_recent_runoff_events(self, plant_key: str, limit: int = 5) -> list[FeedingEvent]:
        """Return last N FeedingEvents with non-null runoff_ec, ordered by timestamp desc."""
        ...
