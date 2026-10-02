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

    def list_by_provider(self, provider: AuthProviderType, provider_user_id: str) -> list[AuthProvider]:
        query = """
        FOR doc IN @@collection
          FILTER doc.provider == @provider AND doc.provider_user_id == @pid
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
        return [AuthProvider(**self._from_doc(doc)) for doc in cursor]

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

    def delete_by_config_slug(self, oidc_config_slug: str) -> int:
        """One by one through :meth:`delete`, so the ``has_auth_provider`` edge goes with each link."""
        if not oidc_config_slug:
            return 0
        deleted = 0
        for link in self.find_by_field("oidc_config_slug", oidc_config_slug):
            if link.key and self.delete(link.key):
                deleted += 1
        return deleted
