from abc import ABC, abstractmethod

from app.common.types import FeedingEventKey
from app.domain.models.feeding_event import FeedingEvent


class IFeedingRepository(ABC):
    # ── CRUD ─────────────────────────────────────────────────────────

    @abstractmethod
    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[FeedingEvent], int]: ...

    @abstractmethod
    def get_by_key(self, key: FeedingEventKey) -> FeedingEvent | None: ...

    @abstractmethod
    def get_or_raise(self, key: FeedingEventKey) -> FeedingEvent: ...

    @abstractmethod
    def create(self, event: FeedingEvent) -> FeedingEvent: ...

    @abstractmethod
    def update(self, key: FeedingEventKey, event: FeedingEvent) -> FeedingEvent: ...

    @abstractmethod
    def delete(self, key: FeedingEventKey) -> bool: ...

    # ── Queries ──────────────────────────────────────────────────────

    @abstractmethod
    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[FeedingEvent]:
        """Return a plant's feeding events inside ``tenant_key`` (#927).

        ``tenant_key`` is required and keyword-only: ``plant_key`` alone selects
        across every tenant, and it arrives from the URL.
        """
        ...

    @abstractmethod
    def get_latest_by_plant(self, plant_key: str, *, tenant_key: str) -> FeedingEvent | None: ...

    @abstractmethod
    def get_recent_runoff_events(self, plant_key: str, limit: int = 5, *, tenant_key: str) -> list[FeedingEvent]:
        """Return last N FeedingEvents with non-null runoff_ec, ordered by timestamp desc."""
        ...
