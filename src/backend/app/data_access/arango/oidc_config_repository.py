from datetime import UTC, datetime
from typing import Any

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

    def update_discovery(
        self,
        key: str,
        *,
        issuer_url: str,
        discovery_document: dict[str, Any],
        refreshed_at: datetime,
    ) -> bool:
        """One conditional AQL update: the issuer check and the write cannot be interleaved."""
        query = (
            "FOR doc IN @@collection FILTER doc._key == @key AND doc.issuer_url == @issuer "
            "UPDATE doc WITH {discovery_document: @discovery, discovery_refreshed_at: @refreshed, updated_at: @now} "
            "IN @@collection OPTIONS {keepNull: true, mergeObjects: false} RETURN NEW._key"
        )
        now = datetime.now(UTC).isoformat()
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.OIDC_PROVIDER_CONFIGS,
                "key": key,
                "issuer": issuer_url,
                "discovery": discovery_document,
                "refreshed": refreshed_at.isoformat(),
                "now": now,
            },
        )
        return any(True for _ in cursor)

    def list_enabled(self) -> list[OidcProviderConfig]:
        return self.find_by_field("enabled", True, sort="slug")
