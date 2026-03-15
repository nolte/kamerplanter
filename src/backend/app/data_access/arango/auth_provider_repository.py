from arango.database import StandardDatabase

from app.common.enums import AuthProviderType
from app.common.types import AuthProviderKey, UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.models.auth import AuthProvider


class ArangoAuthProviderRepository(IAuthProviderRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.AUTH_PROVIDERS)

    def get_by_provider(self, provider: AuthProviderType, provider_user_id: str) -> AuthProvider | None:
        query = """
        FOR doc IN @@collection
          FILTER doc.provider == @provider AND doc.provider_user_id == @pid
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.AUTH_PROVIDERS,
                "provider": provider.value,
                "pid": provider_user_id,
            },
        )
        docs = list(cursor)
        if not docs:
            return None
        return AuthProvider(**self._from_doc(docs[0]))

    def create(self, auth_provider: AuthProvider) -> AuthProvider:
        doc = BaseArangoRepository.create(self, auth_provider)
        created = AuthProvider(**doc)
        # Create edge user -> auth_provider
        user_id = f"{col.USERS}/{auth_provider.user_key}"
        provider_id = f"{col.AUTH_PROVIDERS}/{doc['_key']}"
        self.create_edge(col.HAS_AUTH_PROVIDER, user_id, provider_id)
        return created

    def update(self, key: AuthProviderKey, auth_provider: AuthProvider) -> AuthProvider:
        doc = BaseArangoRepository.update(self, key, auth_provider)
        return AuthProvider(**doc)

    def delete(self, key: AuthProviderKey) -> bool:
        provider_id = f"{col.AUTH_PROVIDERS}/{key}"
        # Delete inbound edges
        query = f"FOR e IN {col.HAS_AUTH_PROVIDER} FILTER e._to == @pid REMOVE e IN {col.HAS_AUTH_PROVIDER}"
        self._db.aql.execute(query, bind_vars={"pid": provider_id})
        return BaseArangoRepository.delete(self, key)

    def list_by_user(self, user_key: UserKey) -> list[AuthProvider]:
        query = "FOR doc IN @@collection FILTER doc.user_key == @user_key RETURN doc"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.AUTH_PROVIDERS,
                "user_key": user_key,
            },
        )
        return [AuthProvider(**self._from_doc(doc)) for doc in cursor]
