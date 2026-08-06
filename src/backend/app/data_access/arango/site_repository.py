from datetime import UTC, datetime

from arango.database import StandardDatabase
from arango.exceptions import DocumentUpdateError

from app.common.exceptions import NotFoundError
from app.common.types import LocationKey, PlantInstanceKey, SiteKey, SlotKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, Slot


class _LocationRepository(BaseArangoRepository[Location]):
    """Location view with a null-preserving update (Issue #714, P1).

    A stored ``Location.frost_exposed`` override (``true``/``false``) must be
    resettable to ``null`` ("inherit from the parent site") via an update. The
    base :meth:`BaseArangoRepository._update_doc` dumps with
    ``exclude_none=True`` and ArangoDB merges with ``keepNull=true``, so an
    explicit ``null`` is dropped from the patch and the stored value survives.

    This override dumps the *full* model (``exclude_none=False``) and passes
    ``keep_none=False`` so ArangoDB removes a null attribute from the document —
    the Pydantic default then reads back as ``None`` (= inherit). It mirrors
    :meth:`ArangoPlantInstanceRepository.update` and keeps the base
    ``DocumentUpdateError`` → :class:`NotFoundError` mapping (error code 1202).
    """

    _model_cls = Location

    def update(self, key: str, model: Location) -> Location:
        # exclude_none=False writes the full model so user-nullable fields
        # (frost_exposed, tank_key, orientation, …) sent as null are honoured;
        # keep_none=False tells ArangoDB to drop the null attribute instead of
        # merging it away (Full-Replace-PUT semantics).
        data = model.model_dump(by_alias=True, exclude_none=False, mode="json")
        data.pop("_key", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        try:
            result = self.collection.update({"_key": key, **data}, return_new=True, keep_none=False)
        except DocumentUpdateError as e:
            if e.error_code == 1202:  # document not found
                raise NotFoundError(self._collection_name, key) from e
            raise
        return Location(**self._from_doc(result["new"]))


class ArangoSiteRepository(BaseArangoRepository[Site], ISiteRepository):
    is_tenant_scoped = True
    _model_cls = Site

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SITES)
        self._locations = _LocationRepository(db, col.LOCATIONS)
        self._slots = BaseArangoRepository[Slot](db, col.SLOTS, Slot)

    # ── Site CRUD ─────────────────────────────────────────────────────

    def get_all_sites(self, offset: int = 0, limit: int = 50, tenant_key: str | None = None) -> tuple[list[Site], int]:
        return super().get_all(offset, limit, tenant_key=tenant_key)

    def find_site_docs_by_types(self, types: list[str]) -> list[dict]:
        """Return normalised site docs of the given ``type`` across all tenants.

        Yields already ``_from_doc``-normalised dicts (not ``Site`` models) so a
        cross-tenant batch consumer (e.g. the daily season task) can construct each
        model defensively — one schema-drift document must not abort the batch
        (REQ-047 AC-18). Keeps the AQL in the data-access layer (NFR-001).
        """
        cursor = self._db.aql.execute(
            "FOR s IN @@col FILTER s.type IN @types RETURN s",
            bind_vars={"@col": self._collection_name, "types": types},
        )
        return [self._from_doc(doc) for doc in cursor]

    def find_site_docs_by_keys(self, keys: list[str]) -> list[dict]:
        """Return normalised site docs for the given ``_key`` list across all tenants.

        Companion to :meth:`find_site_docs_by_types`: yields already
        ``_from_doc``-normalised dicts (not ``Site`` models) so the cross-tenant season
        task can union them with the type-based selection and construct each ``Site``
        defensively (one schema-drift document must not abort the batch, REQ-047 AC-18).
        An empty ``keys`` list short-circuits without a query.
        """
        if not keys:
            return []
        cursor = self._db.aql.execute(
            "FOR s IN @@col FILTER s._key IN @keys RETURN s",
            bind_vars={"@col": self._collection_name, "keys": keys},
        )
        return [self._from_doc(doc) for doc in cursor]

    def find_site_keys_with_frost_exposed_location(self) -> list[str]:
        """Return the distinct ``site_key``s that own ≥1 frost-exposed location.

        Selects only locations whose :attr:`Location.frost_exposed` override is
        explicitly ``true`` (Issue #706/#713) — never ``!= null`` — so a ``false``
        override on an indoor site does NOT pull that site into the season evaluation.
        Parametrised via ``bind_vars`` (no string interpolation); keeps the AQL in the
        data-access layer (NFR-001).
        """
        cursor = self._db.aql.execute(
            """
            FOR l IN @@col
                FILTER l.frost_exposed == true AND l.site_key != null AND l.site_key != ""
                RETURN DISTINCT l.site_key
            """,
            bind_vars={"@col": col.LOCATIONS},
        )
        return [key for key in cursor if key]

    def get_site_by_key(self, key: SiteKey) -> Site | None:
        return super().get_by_key(key)

    def get_site_or_raise(self, key: SiteKey) -> Site:
        return super().get_or_raise(key)

    def create_site(self, site: Site) -> Site:
        return super().create(site)

    def update_site(self, key: SiteKey, site: Site) -> Site:
        return super().update(key, site)

    def delete_site(self, key: SiteKey) -> bool:
        site_id = f"{col.SITES}/{key}"
        # Remove associated CONTAINS edges and cascade to locations
        results = self.get_edges(col.CONTAINS, site_id, direction="outbound")
        for result in results:
            location_doc = result["vertex"]
            location_key = location_doc.get("_key", location_doc.get("_id", "").split("/")[-1])
            self.delete_location(location_key)
        self.delete_edges(col.CONTAINS, from_id=site_id)
        return super().delete(key)

    # ── Location CRUD ─────────────────────────────────────────────────

    def get_locations_by_site(self, site_key: SiteKey) -> list[Location]:
        site_id = f"{col.SITES}/{site_key}"
        results = self.get_edges(col.CONTAINS, site_id, direction="outbound")
        return [Location(**self._from_doc(r["vertex"])) for r in results]

    def get_location_by_key(self, key: LocationKey) -> Location | None:
        return self._locations.get_by_key(key)

    def get_location_or_raise(self, key: LocationKey) -> Location:
        return self._locations.get_or_raise(key)

    def create_location(self, location: Location) -> Location:
        created = self._locations.create(location)
        location_id = f"{col.LOCATIONS}/{created.key}"
        if location.parent_location_key:
            parent_id = f"{col.LOCATIONS}/{location.parent_location_key}"
            self.create_edge(col.CONTAINS, parent_id, location_id)
        elif location.site_key:
            site_id = f"{col.SITES}/{location.site_key}"
            self.create_edge(col.CONTAINS, site_id, location_id)
        return created

    def update_location(self, key: LocationKey, location: Location) -> Location:
        return self._locations.update(key, location)

    def delete_location(self, key: LocationKey) -> bool:
        location_id = f"{col.LOCATIONS}/{key}"
        # Recursively delete child locations
        child_results = self.get_edges(col.CONTAINS, location_id, direction="outbound")
        for result in child_results:
            vertex = result["vertex"]
            if vertex["_id"].startswith(f"{col.LOCATIONS}/"):
                child_key = vertex.get("_key", vertex["_id"].split("/")[-1])
                self.delete_location(child_key)
        # Remove associated HAS_SLOT edges and cascade to slots
        slot_results = self.get_edges(col.HAS_SLOT, location_id, direction="outbound")
        for result in slot_results:
            slot_doc = result["vertex"]
            slot_key = slot_doc.get("_key", slot_doc.get("_id", "").split("/")[-1])
            self._delete_slot_internal(slot_key)
        self.delete_edges(col.HAS_SLOT, from_id=location_id)
        # Remove outbound CONTAINS edges (to children, already deleted)
        self.delete_edges(col.CONTAINS, from_id=location_id)
        # Remove inbound CONTAINS edge (from parent site or parent location)
        self.delete_edges(col.CONTAINS, location_id, direction="inbound")
        return self._locations.delete(key)

    def get_location_children(self, parent_key: LocationKey) -> list[Location]:
        parent_id = f"{col.LOCATIONS}/{parent_key}"
        results = self.get_edges(col.CONTAINS, parent_id, direction="outbound")
        return [
            Location(**self._from_doc(r["vertex"]))
            for r in results
            if r["vertex"]["_id"].startswith(f"{col.LOCATIONS}/")
        ]

    def get_location_tree(self, site_key: SiteKey, *, tenant_key: str) -> list[Location]:
        """A site's location hierarchy, **inside one tenant** (#927).

        Listed in #927 under "one line away": the endpoint resolves the site
        against the caller's tenant before asking, so a foreign ``site_key`` is
        already rejected today. The traversal itself named no tenant, though, so
        any new caller that skipped that check would walk another tenant's tree.
        """
        self._require_tenant_key(tenant_key, "get_location_tree")
        aql = """
        FOR v IN 1..10 OUTBOUND @start_id GRAPH @graph
            OPTIONS {edgeCollections: [@contains_col]}
            FILTER IS_SAME_COLLECTION(@locations_col, v)
            FILTER v.tenant_key == @tenant_key
            RETURN v
        """
        cursor = self._db.aql.execute(
            aql,
            bind_vars={
                "start_id": f"{col.SITES}/{site_key}",
                "graph": col.GRAPH_NAME,
                "contains_col": col.CONTAINS,
                "locations_col": col.LOCATIONS,
                "tenant_key": tenant_key,
            },
        )
        return [Location(**self._from_doc(doc)) for doc in cursor]

    # ── Slot CRUD ─────────────────────────────────────────────────────

    def get_slots_by_location(self, location_key: LocationKey) -> list[Slot]:
        location_id = f"{col.LOCATIONS}/{location_key}"
        results = self.get_edges(col.HAS_SLOT, location_id, direction="outbound")
        return [Slot(**self._from_doc(r["vertex"])) for r in results]

    def get_slot_by_key(self, key: SlotKey) -> Slot | None:
        return self._slots.get_by_key(key)

    def get_slot_or_raise(self, key: SlotKey) -> Slot:
        return self._slots.get_or_raise(key)

    def create_slot(self, slot: Slot) -> Slot:
        created = self._slots.create(slot)
        if slot.location_key:
            location_id = f"{col.LOCATIONS}/{slot.location_key}"
            slot_id = f"{col.SLOTS}/{created.key}"
            self.create_edge(col.HAS_SLOT, location_id, slot_id)
        return created

    def update_slot(self, key: SlotKey, slot: Slot) -> Slot:
        return self._slots.update(key, slot)

    def delete_slot(self, key: SlotKey) -> bool:
        return self._delete_slot_internal(key)

    def _delete_slot_internal(self, key: SlotKey) -> bool:
        slot_id = f"{col.SLOTS}/{key}"
        self.delete_edges(col.HAS_SLOT, from_id=f"{col.LOCATIONS}/%", to_id=slot_id)
        self.delete_edges(col.ADJACENT_TO, from_id=slot_id)
        self.delete_edges(col.FILLED_WITH, from_id=slot_id)
        return self._slots.delete(key)

    def get_slot_for_plant(self, plant_key: PlantInstanceKey, *, tenant_key: str) -> Slot | None:
        """The slot a plant is placed in, **inside one tenant** (#927).

        Listed in #927 under "one line away". The traversal starts at a
        caller-supplied plant key and named no tenant; both current callers sit in
        the watering service, which reaches this with a plant of the caller's own
        tenant. The predicate now belongs to the query instead of to that habit.
        """
        self._require_tenant_key(tenant_key, "get_slot_for_plant")
        query = """
        FOR e IN @@placed_in
          FILTER e._from == @plant_id
          LET slot = DOCUMENT(e._to)
          FILTER slot != null AND slot.tenant_key == @tenant_key
          RETURN slot
        """
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@placed_in": col.PLACED_IN,
                "plant_id": plant_id,
                "tenant_key": tenant_key,
            },
        )
        doc = next(cursor, None)
        if doc is None:
            return None
        return Slot(**self._from_doc(doc))
