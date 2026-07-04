from arango.database import StandardDatabase

from app.common.enums import AuthProviderType
from app.common.types import AuthProviderKey, UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.models.auth import AuthProvider


class ArangoAuthProviderRepository(BaseArangoRepository[AuthProvider], IAuthProviderRepository):
    _model_cls = AuthProvider

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.AUTH_PROVIDERS)

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
        created = super().create(auth_provider)
        # Create edge user -> auth_provider
        user_id = f"{col.USERS}/{auth_provider.user_key}"
        provider_id = f"{col.AUTH_PROVIDERS}/{created.key}"
        self.create_edge(col.HAS_AUTH_PROVIDER, user_id, provider_id)
        return created

    def delete(self, key: AuthProviderKey) -> bool:
        provider_id = f"{col.AUTH_PROVIDERS}/{key}"
        self.delete_edges(col.HAS_AUTH_PROVIDER, provider_id, direction="inbound")
        return super().delete(key)

    def list_by_user(self, user_key: UserKey) -> list[AuthProvider]:
        return self.find_by_field("user_key", user_key)
