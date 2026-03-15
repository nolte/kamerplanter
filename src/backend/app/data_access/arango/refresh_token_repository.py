from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.models.auth import RefreshToken

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import UserKey


class ArangoRefreshTokenRepository(IRefreshTokenRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.REFRESH_TOKENS)

    def create(self, token: RefreshToken) -> RefreshToken:
        doc = BaseArangoRepository.create(self, token)
        created = RefreshToken(**doc)
        # Create edge user -> session
        user_id = f"{col.USERS}/{token.user_key}"
        token_id = f"{col.REFRESH_TOKENS}/{doc['_key']}"
        self.create_edge(col.HAS_SESSION, user_id, token_id)
        return created

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.token_hash == @hash AND doc.revoked == false
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.REFRESH_TOKENS,
            "hash": token_hash,
        })
        docs = list(cursor)
        if not docs:
            return None
        return RefreshToken(**self._from_doc(docs[0]))

    def revoke(self, key: str) -> bool:
        try:
            self._db.collection(col.REFRESH_TOKENS).update(
                {"_key": key, "revoked": True, "updated_at": self._now()},
            )
            return True
        except Exception:
            return False

    def revoke_all_for_user(self, user_key: UserKey) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.revoked == false
          UPDATE doc WITH { revoked: true, updated_at: @now } IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.REFRESH_TOKENS,
            "user_key": user_key,
            "now": self._now(),
        })
        return sum(1 for _ in cursor)

    def cleanup_expired(self) -> int:
        now = datetime.now(UTC).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.expires_at < @now OR doc.revoked == true
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.REFRESH_TOKENS,
            "now": now,
        })
        count = sum(1 for _ in cursor)
        # Also clean up orphaned edges
        query2 = f"""
        FOR e IN {col.HAS_SESSION}
          LET target = DOCUMENT(e._to)
          FILTER target == null
          REMOVE e IN {col.HAS_SESSION}
        """
        self._db.aql.execute(query2)
        return count

    def list_active_for_user(self, user_key: UserKey) -> list[RefreshToken]:
        now = datetime.now(UTC).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.revoked == false AND doc.expires_at > @now
          SORT doc.created_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.REFRESH_TOKENS,
            "user_key": user_key,
            "now": now,
        })
        return [RefreshToken(**self._from_doc(doc)) for doc in cursor]
