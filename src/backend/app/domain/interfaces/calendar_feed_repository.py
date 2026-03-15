from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.common.types import CalendarFeedKey
    from app.domain.models.calendar import CalendarFeed


class ICalendarFeedRepository(ABC):
    @abstractmethod
    def save(self, feed: CalendarFeed) -> CalendarFeed: ...

    @abstractmethod
    def get_by_key(self, key: CalendarFeedKey) -> CalendarFeed | None: ...

    @abstractmethod
    def get_by_token(self, token: str) -> CalendarFeed | None: ...

    @abstractmethod
    def update(self, key: CalendarFeedKey, feed: CalendarFeed) -> CalendarFeed: ...

    @abstractmethod
    def list_by_user(
        self,
        user_key: str,
        tenant_key: str,
    ) -> list[CalendarFeed]: ...

    @abstractmethod
    def delete(self, key: CalendarFeedKey) -> bool: ...
