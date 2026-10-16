from typing import cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.common.types import GardenObjectKey, SiteKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.garden_object_repository import IGardenObjectRepository
from app.domain.models.garden_object import GardenObject

#: The object's site must exist and belong to the caller's tenant (E-01: the site is the owner).
_OWNED_BY_SITE = """
    LET site = DOCUMENT(CONCAT(@sites, o.site_key))
    FILTER site != null AND site.tenant_key == @tenant_key
"""


class ArangoGardenObjectRepository(BaseArangoRepository[GardenObject], IGardenObjectRepository):
    """``garden_objects`` (migration v0093, REQ-053 §20.14) and its ``has_garden_object`` edge.

    The collection carries no ``tenant_key`` (E-01, #2107), so every read joins the
    object's site and filters on *its* tenant — the predicate is in the query, as
    ``ArangoSiteRepository.get_location_tree`` does it, never on a field of the row.
    An empty tenant is no tenant (``_require_tenant_key``), so a caller cannot switch
    the predicate off by omission.

    Updates are **full replace** (:attr:`_update_is_full_replace`): ``parent_location_key
    = None`` means "lies directly on the site" and ``notes = None`` means "no note",
    and both must be able to *clear* the stored value — the #714 shape that made
    the location view full-replace. The service keeps ``created_by`` from the
    stored row on edit (WP 1.9); the base class strips ``created_at`` itself.
    """

    _model_cls = GardenObject
    _update_is_full_replace = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.GARDEN_OBJECTS)

    def get_garden_objects_by_site(self, site_key: SiteKey, *, tenant_key: str) -> list[GardenObject]:
        """Every object of a site of ``tenant_key``, in ``z_order`` (the v0093 ``(site_key, object_type)`` index)."""
        self._require_tenant_key(tenant_key, "get_garden_objects_by_site")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR o IN @@col
                FILTER o.site_key == @site_key
                {_OWNED_BY_SITE}
                SORT o.z_order ASC, o._key ASC
                RETURN o
            """,
                bind_vars={
                    "@col": self._collection_name,
                    "site_key": site_key,
                    "sites": f"{col.SITES}/",
                    "tenant_key": tenant_key,
                },
            ),
        )
        return [GardenObject(**self._from_doc(doc)) for doc in cursor]

    def get_garden_object_by_key(self, key: GardenObjectKey, *, tenant_key: str) -> GardenObject | None:
        """The object behind ``key`` when its site belongs to ``tenant_key``; absent and foreign both give ``None``."""
        self._require_tenant_key(tenant_key, "get_garden_object_by_key")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            LET o = DOCUMENT(CONCAT(@objects, @key))
            FILTER o != null
            {_OWNED_BY_SITE}
            RETURN o
            """,
                bind_vars={
                    "objects": f"{col.GARDEN_OBJECTS}/",
                    "key": key,
                    "sites": f"{col.SITES}/",
                    "tenant_key": tenant_key,
                },
            ),
        )
        doc = next(cursor, None)
        return GardenObject(**self._from_doc(doc)) if doc is not None else None

    def get_garden_object_or_raise(self, key: GardenObjectKey, *, tenant_key: str) -> GardenObject:
        garden_object = self.get_garden_object_by_key(key, tenant_key=tenant_key)
        if garden_object is None:
            raise NotFoundError("GardenObject", key)
        return garden_object

    def create_garden_object(self, garden_object: GardenObject) -> GardenObject:
        if not garden_object.site_key:
            # Without the site there is no edge and both scoped reads would never see the row.
            raise ValueError("A garden object needs a site_key (it is anchored on its site, E-01).")
        created = super().create(garden_object)
        self.create_edge(
            col.HAS_GARDEN_OBJECT,
            f"{col.SITES}/{garden_object.site_key}",
            f"{col.GARDEN_OBJECTS}/{created.key}",
        )
        return created

    def update_garden_object(self, key: GardenObjectKey, garden_object: GardenObject) -> GardenObject:
        return super().update(key, garden_object)

    def delete_garden_object(self, key: GardenObjectKey) -> bool:
        """Delete the object and every edge written on it, each cut on the end it hangs off.

        ``has_garden_object`` points *at* the object (site → object): inbound.
        ``has_task`` runs object → task (v0093 widened the definition): outbound.
        ``zone_supplied_by`` runs irrigation zone → object (a water source): inbound.
        """
        object_id = f"{col.GARDEN_OBJECTS}/{key}"
        self.delete_edges(col.HAS_GARDEN_OBJECT, vertex_id=object_id, direction="inbound")
        self.delete_edges(col.HAS_TASK, vertex_id=object_id, direction="outbound")
        self.delete_edges(col.ZONE_SUPPLIED_BY, vertex_id=object_id, direction="inbound")
        return super().delete(key)
