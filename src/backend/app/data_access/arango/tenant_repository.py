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

    def update_fields(self, key: str, fields: dict) -> Tenant | None:
        """Merge ``fields`` into the stored tenant and rewrite it (#968 §2).

        **Renamed from ``update``.** The old name shadowed
        :meth:`BaseArangoRepository.update`, whose signature takes a full
        *model*, with one that takes an arbitrary ``dict``. That reads like
        the checked full-model path while accepting whatever keys it is
        handed, so a caller who forwarded request data would have performed
        mass assignment under a reassuring name. The name now says what the
        payload is, and the inherited full-model :meth:`update` is reachable
        again on this repository instead of being shadowed.

        **Caller obligation.** ``fields`` is applied key-by-key, so it must be
        built from named fields or a validated schema's ``model_dump()`` —
        never from a raw request body. ``model_copy(update=...)`` does not
        validate, so an unknown or ill-typed key survives this step; what
        catches an ill-typed *declared* field is the re-validation the
        inherited :meth:`update` performs on the merged model (#968).

        **Not the base class's merge.** This deliberately keeps its
        read-modify-write shape rather than delegating to
        :meth:`BaseArangoRepository.update_fields`: that method writes the
        dict straight through and is documented as unchecked, whereas this
        one materialises a full Tenant and therefore gets validated. The
        price is the base method's lost-update commutativity — two concurrent
        calls touching *disjoint* fields can clobber each other here. Swapping
        that trade is a decision of its own, not a side effect of a rename.

        Returns ``None`` when no tenant carries ``key``.
        """
        existing = self.get_by_key(key)
        if not existing:
            return None
        merged = existing.model_copy(update=fields)
        return super().update(key, merged)

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
