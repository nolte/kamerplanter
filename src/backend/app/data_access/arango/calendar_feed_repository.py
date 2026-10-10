from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.calendar_feed_repository import ICalendarFeedRepository
from app.domain.models.calendar import CalendarFeed


class ArangoCalendarFeedRepository(BaseArangoRepository[CalendarFeed], ICalendarFeedRepository):
    _model_cls = CalendarFeed
    #: Every row belongs to exactly one tenant; a base list read without a
    #: ``tenant_key`` (or an explicit ``all_tenants=True``) raises (MT-023, #2119).
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CALENDAR_FEEDS)

    def save(self, feed: CalendarFeed) -> CalendarFeed:
        return super().create(feed)

    def get_by_token_hash(self, token_hash: str) -> CalendarFeed | None:
        """The feed whose stored token digest is ``token_hash``; ``None`` for an empty digest (#2171)."""
        if not token_hash:
            return None
        return self.find_one_by_field("token_hash", token_hash)

    def list_by_user(
        self,
        user_key: str,
        *,
        tenant_key: str,
    ) -> list[CalendarFeed]:
        query = """
        FOR f IN @@col
          FILTER f.user_key == @user_key AND f.tenant_key == @tenant_key
          SORT DATE_TIMESTAMP(f.created_at) DESC
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

    def list_by_tenant(self, *, tenant_key: str) -> list[CalendarFeed]:
        """Every feed of ``tenant_key``, newest first - the lead's overview (#2226 review SEC-001)."""
        if not tenant_key:
            return []
        query = """
        FOR f IN @@col
          FILTER f.tenant_key == @tenant_key
          SORT DATE_TIMESTAMP(f.created_at) DESC
          RETURN f
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(query, bind_vars={"@col": self._collection_name, "tenant_key": tenant_key}),
        )
        return [CalendarFeed(**self._from_doc(doc)) for doc in cursor]

    def delete_by_user(self, user_key: str, *, tenant_key: str) -> int:
        """Delete the feeds ``user_key`` owns in ``tenant_key``; the number deleted (#2226 review SEC-001).

        Both keys are required: an empty one would match every legacy feed whose
        owner or tenant was never stamped.
        """
        if not user_key or not tenant_key:
            return 0
        query = """
        FOR f IN @@col
          FILTER f.user_key == @user_key AND f.tenant_key == @tenant_key
          REMOVE f IN @@col
          RETURN 1
        """
        bind_vars: dict[str, Any] = {"@col": self._collection_name, "user_key": user_key, "tenant_key": tenant_key}
        return len(list(cast(Cursor, self._db.aql.execute(query, bind_vars=bind_vars))))
