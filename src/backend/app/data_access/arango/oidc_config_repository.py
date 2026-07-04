from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.oidc_config_repository import IOidcConfigRepository
from app.domain.models.oidc_config import OidcProviderConfig


class ArangoOidcConfigRepository(BaseArangoRepository[OidcProviderConfig], IOidcConfigRepository):
    _model_cls = OidcProviderConfig

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.OIDC_PROVIDER_CONFIGS)

    def get_by_slug(self, slug: str) -> OidcProviderConfig | None:
        return self.find_one_by_field("slug", slug)

    def list_all(self) -> list[OidcProviderConfig]:
        query = "FOR doc IN @@collection SORT doc.slug RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.OIDC_PROVIDER_CONFIGS})
        return [OidcProviderConfig(**self._from_doc(doc)) for doc in cursor]

    def list_enabled(self) -> list[OidcProviderConfig]:
        return self.find_by_field("enabled", True, sort="slug")
