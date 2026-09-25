from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.models.auth import RefreshToken


class ArangoRefreshTokenRepository(BaseArangoRepository[RefreshToken], IRefreshTokenRepository):
    _model_cls = RefreshToken

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.REFRESH_TOKENS)

    def create(self, token: RefreshToken) -> RefreshToken:
        created = super().create(token)
        # Create edge user -> session
        user_id = f"{col.USERS}/{token.user_key}"
        token_id = f"{col.REFRESH_TOKENS}/{created.key}"
        self.create_edge(col.HAS_SESSION, user_id, token_id)
        return created

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.token_hash == @hash AND doc.revoked == false
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.REFRESH_TOKENS,
                "hash": token_hash,
            },
        )
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
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.REFRESH_TOKENS,
                "user_key": user_key,
                "now": self._now(),
            },
        )
        return sum(1 for _ in cursor)

    def cleanup_expired(self, *, now: datetime | None = None) -> int:
        """Remove revoked sessions and those past ``expires_at``, then the orphaned edges.

        Compared as instants (see :mod:`app.data_access.arango.query_builder`).
        ``expires_at`` is required on :class:`RefreshToken`; a session whose
        expiry is missing or unreadable is removed, as the string comparison did
        for ``null`` — it can never be a valid session.
        """
        stamp = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.revoked == true
            OR DATE_TIMESTAMP(doc.expires_at) == null
            OR DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now)
          REMOVE doc IN @@collection
          RETURN 1
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.REFRESH_TOKENS,
                "now": stamp,
            },
        )
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

    def list_active_for_user(self, user_key: UserKey, *, now: datetime | None = None) -> list[RefreshToken]:
        stamp = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
            AND doc.revoked == false
            AND DATE_TIMESTAMP(doc.expires_at) > DATE_TIMESTAMP(@now)
          SORT doc.created_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.REFRESH_TOKENS,
                "user_key": user_key,
                "now": stamp,
            },
        )
        return [RefreshToken(**self._from_doc(doc)) for doc in cursor]

    def list_unanonymized_ips_before(self, cutoff_iso: str) -> list[tuple[str, str]]:
        """``(key, ip_address)`` of every session created before the cutoff whose IP is still plain (SEC-K-002).

        Returns pairs rather than :class:`RefreshToken` models on purpose: the
        anonymisation must reach a document even when some other field of it no
        longer validates, and it needs nothing but the key and the address.
        ``created_at`` is compared as an instant (see
        :mod:`app.data_access.arango.query_builder`); a session whose age cannot
        be read is not selected.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.ip_address != null
            AND doc.ip_anonymized_at == null
            AND DATE_TIMESTAMP(doc.created_at) != null
            AND DATE_TIMESTAMP(doc.created_at) < DATE_TIMESTAMP(@cutoff)
          RETURN { _key: doc._key, ip_address: doc.ip_address }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.REFRESH_TOKENS,
                "cutoff": cutoff_iso,
            },
        )
        return [(row["_key"], row["ip_address"]) for row in cursor]

    def mark_ip_anonymized(self, key: str, anonymized_ip: str, anonymized_at_iso: str) -> None:
        """Replace a session's IP with its anonymised form and stamp when that happened."""
        self._db.collection(col.REFRESH_TOKENS).update(
            {
                "_key": key,
                "ip_address": anonymized_ip,
                "ip_anonymized_at": anonymized_at_iso,
            }
        )
