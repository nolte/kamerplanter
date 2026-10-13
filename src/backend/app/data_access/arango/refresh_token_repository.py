from datetime import UTC, datetime
from typing import cast

from arango.cursor import Cursor
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

    def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        """The token with this hash whatever its state — revoked and rotated ones included (#2116).

        :meth:`get_by_hash` answers live tokens only. Replay detection needs the
        other half: a rotated token presented again is the signal, so it has to be
        found rather than reported "unknown".
        """
        docs = list(
            cast(
                Cursor,
                self._db.aql.execute(
                    "FOR doc IN @@collection FILTER doc.token_hash == @hash LIMIT 1 RETURN doc",
                    bind_vars={"@collection": col.REFRESH_TOKENS, "hash": token_hash},
                ),
            )
        )
        return RefreshToken(**self._from_doc(docs[0])) if docs else None

    def claim_rotation(self, key: str, family_key: str, rotated_at: datetime) -> bool:
        """Mark a live token as consumed by a rotation, atomically; ``False`` when another request got there first.

        One AQL statement, so of two refreshes presenting the same token exactly
        one wins; the loser re-reads the token and meets it rotated (the grace
        window or the replay path). ``family_key`` is written here as well, which
        is how a token minted before families existed joins one on its first
        rotation.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND doc.revoked == false AND doc.rotated_at == null
          UPDATE doc WITH { revoked: true, rotated_at: @rotated_at, family_key: @family, updated_at: @now }
            IN @@collection
          RETURN 1
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.REFRESH_TOKENS,
                    "key": key,
                    "family": family_key,
                    "rotated_at": rotated_at.isoformat(),
                    "now": self._now(),
                },
            ),
        )
        return any(True for _ in cursor)

    def set_successor(self, key: str, successor_key: str) -> None:
        """Record which token a rotation minted in place of ``key``."""
        self._db.collection(col.REFRESH_TOKENS).update(
            {"_key": key, "successor_key": successor_key, "updated_at": self._now()}
        )

    def family_is_live(self, user_key: UserKey, family_key: str) -> bool:
        """Whether the family still has a token that is neither revoked nor expired."""
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key AND doc.family_key == @family AND doc.revoked == false
            AND DATE_TIMESTAMP(doc.expires_at) > DATE_TIMESTAMP(@now)
          LIMIT 1
          RETURN 1
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.REFRESH_TOKENS,
                    "user_key": user_key,
                    "family": family_key,
                    "now": datetime.now(UTC).isoformat(),
                },
            ),
        )
        return any(True for _ in cursor)

    def revoke_family(self, user_key: UserKey, family_key: str) -> int:
        """Revoke every token of one family and end the account's access tokens (#2116).

        A family is one login on one device; this is "sign this device out". The
        token whose key *is* the family (a pre-family token that never rotated)
        is caught by the key match. Access tokens cannot be told apart by session
        without a read per request, so the account's ``access_token_generation``
        moves: every access token of the account stops resolving and the other
        sessions refresh once, silently.
        """
        query = """
        LET revoked = (
          FOR doc IN @@collection
            FILTER doc.user_key == @user_key AND (doc.family_key == @family OR doc._key == @family)
              AND doc.revoked == false
            UPDATE doc WITH { revoked: true, updated_at: @now } IN @@collection
            RETURN 1
        )
        LET bumped = (
          FOR u IN @@users
            FILTER u._key == @user_key
            UPDATE u WITH { access_token_generation: (u.access_token_generation || 0) + 1 } IN @@users
            RETURN 1
        )
        RETURN LENGTH(revoked)
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.REFRESH_TOKENS,
                    "@users": col.USERS,
                    "user_key": user_key,
                    "family": family_key,
                    "now": self._now(),
                },
            ),
        )
        return next(iter(cursor), 0)

    def revoke_all_for_user(self, user_key: UserKey) -> int:
        """Revoke every session of the account and move both of its session generations (#2116).

        One statement for both, so no caller can revoke the refresh tokens and
        forget the access tokens — the seven call sites (logout everywhere,
        password reset and change, the e-mail change and its revert, both Art. 17
        paths) all reach the access-token cut-off through this method.
        ``session_generation`` additionally refuses any refresh token of the
        account minted under the old generation, which closes the window where a
        rotation that read its token before this statement mints a successor
        after it.
        """
        query = """
        LET revoked = (
          FOR doc IN @@collection
            FILTER doc.user_key == @user_key AND doc.revoked == false
            UPDATE doc WITH { revoked: true, updated_at: @now } IN @@collection
            RETURN 1
        )
        LET bumped = (
          FOR u IN @@users
            FILTER u._key == @user_key
            UPDATE u WITH {
              session_generation: (u.session_generation || 0) + 1,
              access_token_generation: (u.access_token_generation || 0) + 1
            } IN @@users
            RETURN 1
        )
        RETURN LENGTH(revoked)
        """
        cursor = cast(
            Cursor,
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.REFRESH_TOKENS,
                    "@users": col.USERS,
                    "user_key": user_key,
                    "now": self._now(),
                },
            ),
        )
        return next(iter(cursor), 0)

    def cleanup_expired(self, *, now: datetime | None = None) -> int:
        """Remove revoked sessions and those past ``expires_at``, then the orphaned edges.

        A token a rotation consumed (``rotated_at`` set) is kept until its own
        ``expires_at`` (#2116): presenting it again is how a stolen token is
        detected, which needs it to be found. It carries no live credential — it
        is revoked — and its IP address is anonymised on the R-03 schedule like
        any session's.

        Compared as instants (see :mod:`app.data_access.arango.query_builder`).
        ``expires_at`` is required on :class:`RefreshToken`; a session whose
        expiry is missing or unreadable is removed, as the string comparison did
        for ``null`` — it can never be a valid session.
        """
        stamp = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER (doc.revoked == true AND doc.rotated_at == null)
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
          SORT DATE_TIMESTAMP(doc.created_at) DESC
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
        :mod:`app.data_access.arango.query_builder`). A session whose age cannot
        be read **is** selected: anonymising is the minimising action, so an IP of
        unknown age is anonymised rather than kept in full until the token expires
        (#1784 review GDPR-001). Destructive selectors go the other way.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.ip_address != null
            AND doc.ip_anonymized_at == null
            AND (
              DATE_TIMESTAMP(doc.created_at) == null
              OR DATE_TIMESTAMP(doc.created_at) < DATE_TIMESTAMP(@cutoff)
            )
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
