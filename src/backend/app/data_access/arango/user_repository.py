from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User


class ArangoUserRepository(BaseArangoRepository[User], IUserRepository):
    _model_cls = User

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.USERS)

    def update_fields(self, key: UserKey, fields: dict) -> User | None:
        """Merge ``fields`` into the stored user and rewrite it (#1018, mirrors #968 §2).

        Read-modify-write, exactly like :meth:`ArangoTenantRepository.update_fields`:
        the stored ``User`` is loaded, ``fields`` is applied through
        ``model_copy(update=...)`` and the merged model is written via the
        inherited full-model :meth:`update`, which re-validates it in ``_to_doc``
        (#982/#996), strips ArangoDB system attributes and maps a 1202 onto
        :class:`NotFoundError`. That is the set of guards the platform-admin
        router bypassed by writing ``collection.update`` itself (#1018).

        **Caller obligation.** ``fields`` is applied key-by-key, so it must be
        built from named fields or a validated schema's ``model_dump()`` — never
        from a raw request body.

        Deliberately not the base class's dict-merge :meth:`update_fields`, which
        writes the dict straight through unchecked; materialising a full ``User``
        here is what gets the payload validated. The price is that method's
        lost-update commutativity for disjoint concurrent fields.

        Returns ``None`` when no user carries ``key``.
        """
        existing = self.get_by_key(key)
        if not existing:
            return None
        merged = existing.model_copy(update=fields)
        return super().update(key, merged)

    def get_by_email(self, email: str) -> User | None:
        query = "FOR doc IN @@collection FILTER LOWER(doc.email) == LOWER(@email) LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "email": email})
        docs = list(cursor)
        if not docs:
            return None
        return User(**self._from_doc(docs[0]))

    def delete(self, key: UserKey) -> bool:
        user_id = f"{col.USERS}/{key}"
        # Delete auth provider edges + docs
        self.delete_edges(col.HAS_AUTH_PROVIDER, user_id)
        query = f"FOR doc IN {col.AUTH_PROVIDERS} FILTER doc.user_key == @key REMOVE doc IN {col.AUTH_PROVIDERS}"
        self._db.aql.execute(query, bind_vars={"key": key})
        # Delete refresh tokens
        query = f"FOR doc IN {col.REFRESH_TOKENS} FILTER doc.user_key == @key REMOVE doc IN {col.REFRESH_TOKENS}"
        self._db.aql.execute(query, bind_vars={"key": key})
        # Delete session edges
        self.delete_edges(col.HAS_SESSION, user_id)
        return super().delete(key)

    def get_unverified_before(self, cutoff_iso: str) -> list[User]:
        query = """
        FOR doc IN @@collection
          FILTER doc.email_verified == false AND doc.created_at < @cutoff
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "cutoff": cutoff_iso})
        return [User(**self._from_doc(doc)) for doc in cursor]
