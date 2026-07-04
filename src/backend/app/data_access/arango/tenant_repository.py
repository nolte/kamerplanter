from arango.database import StandardDatabase

from app.common.enums import TenantType
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.tenant import Tenant


class ArangoTenantRepository(BaseArangoRepository[Tenant], ITenantRepository):
    _model_cls = Tenant

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.TENANTS)

    def get_by_slug(self, slug: str) -> Tenant | None:
        return self.find_one_by_field("slug", slug)

    def update(self, key: str, data: dict) -> Tenant | None:
        existing = self.get_by_key(key)
        if not existing:
            return None
        update_data = existing.model_copy(update=data)
        return super().update(key, update_data)

    def list_by_owner(self, owner_user_key: str) -> list[Tenant]:
        return self.find_by_field("owner_user_key", owner_user_key, sort="created_at")

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
