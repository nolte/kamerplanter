from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.calendar_feed_repository import ICalendarFeedRepository
from app.domain.models.calendar import CalendarFeed

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import CalendarFeedKey


class ArangoCalendarFeedRepository(BaseArangoRepository, ICalendarFeedRepository):
    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CALENDAR_FEEDS)

    def _to_model(self, doc: dict) -> CalendarFeed:
        return CalendarFeed(**doc)

    def save(self, feed: CalendarFeed) -> CalendarFeed:
        doc = self.create(feed)
        return self._to_model(doc)

    def get_by_key(self, key: CalendarFeedKey) -> CalendarFeed | None:
        doc = super().get_by_key(key)
        if doc is None:
            return None
        return self._to_model(doc)

    def get_by_token(self, token: str) -> CalendarFeed | None:
        results = self.find_by_field("token", token)
        if not results:
            return None
        return self._to_model(results[0])

    def update(self, key: CalendarFeedKey, feed: CalendarFeed) -> CalendarFeed:
        doc = super().update(key, feed)
        return self._to_model(doc)

    def list_by_user(
        self,
        user_key: str,
        tenant_key: str,
    ) -> list[CalendarFeed]:
        query = """
        FOR f IN @@col
          FILTER f.user_key == @user_key AND f.tenant_key == @tenant_key
          SORT f.created_at DESC
          RETURN f
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@col": self._collection_name,
                "user_key": user_key,
                "tenant_key": tenant_key,
            },
        )
        return [self._to_model(self._from_doc(doc)) for doc in cursor]

    def delete(self, key: CalendarFeedKey) -> bool:
        return super().delete(key)
