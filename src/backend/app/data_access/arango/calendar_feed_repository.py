from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.calendar_feed_repository import ICalendarFeedRepository
from app.domain.models.calendar import CalendarFeed


class ArangoCalendarFeedRepository(BaseArangoRepository[CalendarFeed], ICalendarFeedRepository):
    _model_cls = CalendarFeed

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CALENDAR_FEEDS)

    def save(self, feed: CalendarFeed) -> CalendarFeed:
        return super().create(feed)

    def get_by_token(self, token: str) -> CalendarFeed | None:
        return self.find_one_by_field("token", token)

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
        return [CalendarFeed(**self._from_doc(doc)) for doc in cursor]
