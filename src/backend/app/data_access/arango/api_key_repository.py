"""ArangoDB implementation of the API key repository."""

from arango.database import StandardDatabase

from app.common.types import ApiKeyKey, UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.api_key_repository import IApiKeyRepository
from app.domain.models.auth import ApiKey


class ArangoApiKeyRepository(IApiKeyRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.API_KEYS)

    def create(self, api_key: ApiKey) -> ApiKey:
        doc = BaseArangoRepository.create(self, api_key)
        created = ApiKey(**doc)
        # Create edge user -> api_key
        user_id = f"{col.USERS}/{api_key.user_key}"
        key_id = f"{col.API_KEYS}/{doc['_key']}"
        self.create_edge(col.HAS_API_KEY, user_id, key_id)
        return created

    def get_by_key(self, key: ApiKeyKey) -> ApiKey | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        if doc is None:
            return None
        return ApiKey(**doc)

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.key_hash == @hash AND doc.revoked == false
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.API_KEYS,
            "hash": key_hash,
        })
        docs = list(cursor)
        if not docs:
            return None
        return ApiKey(**self._from_doc(docs[0]))

    def list_by_user(self, user_key: UserKey) -> list[ApiKey]:
        query = """
        FOR doc IN @@collection
          FILTER doc.user_key == @user_key
          SORT doc.created_at DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={
            "@collection": col.API_KEYS,
            "user_key": user_key,
        })
        return [ApiKey(**self._from_doc(doc)) for doc in cursor]

    def update_last_used(self, key: ApiKeyKey) -> None:
        self._db.collection(col.API_KEYS).update(
            {"_key": key, "last_used_at": self._now()},
        )

    def revoke(self, key: ApiKeyKey) -> bool:
        try:
            self._db.collection(col.API_KEYS).update(
                {"_key": key, "revoked": True, "updated_at": self._now()},
            )
            return True
        except Exception:
            return False

    def delete(self, key: ApiKeyKey) -> bool:
        return BaseArangoRepository.delete(self, key)
