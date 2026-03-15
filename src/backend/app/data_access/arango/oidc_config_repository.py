
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.oidc_config_repository import IOidcConfigRepository
from app.domain.models.oidc_config import OidcProviderConfig

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.common.types import OidcProviderConfigKey


class ArangoOidcConfigRepository(IOidcConfigRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.OIDC_PROVIDER_CONFIGS)

    def get_by_key(self, key: OidcProviderConfigKey) -> OidcProviderConfig | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return OidcProviderConfig(**doc) if doc else None

    def get_by_slug(self, slug: str) -> OidcProviderConfig | None:
        query = "FOR doc IN @@collection FILTER doc.slug == @slug LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.OIDC_PROVIDER_CONFIGS, "slug": slug})
        docs = list(cursor)
        if not docs:
            return None
        return OidcProviderConfig(**self._from_doc(docs[0]))

    def create(self, config: OidcProviderConfig) -> OidcProviderConfig:
        doc = BaseArangoRepository.create(self, config)
        return OidcProviderConfig(**doc)

    def update(self, key: OidcProviderConfigKey, config: OidcProviderConfig) -> OidcProviderConfig:
        doc = BaseArangoRepository.update(self, key, config)
        return OidcProviderConfig(**doc)

    def delete(self, key: OidcProviderConfigKey) -> bool:
        return BaseArangoRepository.delete(self, key)

    def list_all(self) -> list[OidcProviderConfig]:
        query = "FOR doc IN @@collection SORT doc.slug RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.OIDC_PROVIDER_CONFIGS})
        return [OidcProviderConfig(**self._from_doc(doc)) for doc in cursor]

    def list_enabled(self) -> list[OidcProviderConfig]:
        query = "FOR doc IN @@collection FILTER doc.enabled == true SORT doc.slug RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.OIDC_PROVIDER_CONFIGS})
        return [OidcProviderConfig(**self._from_doc(doc)) for doc in cursor]
