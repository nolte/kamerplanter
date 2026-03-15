from typing import TYPE_CHECKING

from app.common.enums import TenantType
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.tenant import Tenant

if TYPE_CHECKING:
    from arango.database import StandardDatabase


class ArangoTenantRepository(ITenantRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.TENANTS)

    def get_by_key(self, key: str) -> Tenant | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Tenant(**doc) if doc else None

    def get_by_slug(self, slug: str) -> Tenant | None:
        query = "FOR doc IN @@collection FILTER doc.slug == @slug LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.TENANTS, "slug": slug})
        docs = list(cursor)
        if not docs:
            return None
        return Tenant(**self._from_doc(docs[0]))

    def create(self, tenant: Tenant) -> Tenant:
        doc = BaseArangoRepository.create(self, tenant)
        return Tenant(**doc)

    def update(self, key: str, data: dict) -> Tenant | None:
        existing = self.get_by_key(key)
        if not existing:
            return None
        update_data = existing.model_copy(update=data)
        doc = BaseArangoRepository.update(self, key, update_data)
        return Tenant(**doc)

    def delete(self, key: str) -> bool:
        return BaseArangoRepository.delete(self, key)

    def list_by_owner(self, owner_user_key: str) -> list[Tenant]:
        query = """
        FOR doc IN @@collection
          FILTER doc.owner_user_key == @owner
          SORT doc.created_at ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.TENANTS, "owner": owner_user_key},
        )
        return [Tenant(**self._from_doc(doc)) for doc in cursor]

    def count_organizations_by_owner(self, owner_user_key: str) -> int:
        query = """
        FOR doc IN @@collection
          FILTER doc.owner_user_key == @owner AND doc.tenant_type == @type
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.TENANTS,
                "owner": owner_user_key,
                "type": TenantType.ORGANIZATION.value,
            },
        )
        return next(cursor, 0)
