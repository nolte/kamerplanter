from abc import ABC, abstractmethod
from typing import Any

from app.common.types import CalendarFeedKey
from app.domain.models.calendar import CalendarFeed


class ICalendarFeedRepository(ABC):
    @abstractmethod
    def save(self, feed: CalendarFeed) -> CalendarFeed: ...

    @abstractmethod
    def get_by_key(self, key: CalendarFeedKey) -> CalendarFeed | None: ...

    @abstractmethod
    def get_or_raise(self, key: CalendarFeedKey) -> CalendarFeed: ...

    @abstractmethod
    def get_by_token_hash(self, token_hash: str) -> CalendarFeed | None: ...

    @abstractmethod
    def update(self, key: CalendarFeedKey, feed: CalendarFeed) -> CalendarFeed: ...

    @abstractmethod
    def update_fields(self, key: CalendarFeedKey, fields: dict[str, Any]) -> CalendarFeed:
        """Write only ``fields`` into the stored feed; every other attribute stays as stored.

        An object in ``fields`` (``filters``) replaces the stored one whole, it is
        not merged into it: a filter key the new value lacks is gone afterwards.
        """

    @abstractmethod
    def list_by_user(
        self,
        user_key: str,
        *,
        tenant_key: str,
    ) -> list[CalendarFeed]: ...

    @abstractmethod
    def list_by_tenant(self, *, tenant_key: str) -> list[CalendarFeed]:
        """Every feed of ``tenant_key``; an empty key lists nothing."""

    @abstractmethod
    def delete_by_user(self, user_key: str, *, tenant_key: str) -> int:
        """Delete every feed ``user_key`` owns in ``tenant_key``; empty keys delete nothing."""

    @abstractmethod
    def delete(self, key: CalendarFeedKey) -> bool: ...
