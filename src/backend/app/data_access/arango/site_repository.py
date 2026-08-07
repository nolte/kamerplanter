from arango.database import StandardDatabase

from app.common.types import LocationKey, PlantInstanceKey, SiteKey, SlotKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location, Site, Slot


class _LocationRepository(BaseArangoRepository[Location]):
    """Location view with a null-clearing update (Issue #714, P1).

    A stored ``Location.frost_exposed`` override (``true``/``false``) must be
    resettable to ``null`` ("inherit from the parent site") via an update. A
    *merging* update dumps with ``exclude_none=True`` and ArangoDB keeps nulls,
    so the explicit ``null`` never reaches the document and the stored value
    survives — the #714 defect.

    This view therefore selects the base class's full-replace mode: the model is
    dumped with ``exclude_none=False`` and ArangoDB is told ``keep_none=False``,
    so a null attribute is removed from the document and the Pydantic default
    reads back as ``None`` (= inherit).

    It used to hand-roll that write, which meant a ``Location`` — the entity
    every plant is placed in — reached ArangoDB without the base class's
    re-validation (#968 §2). Nothing is hand-rolled here any more: the semantics
    are a class attribute and the write is the inherited one, including the
    ``DocumentUpdateError`` → :class:`NotFoundError` mapping (error code 1202)
    and the ``created_at`` strip that stops a model without one erasing it.
    """

    _model_cls = Location
    _update_is_full_replace = True


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

        **The predicate is on the site, not on the location — deliberately.** The
        obvious ``FILTER v.tenant_key == @tenant_key`` is wrong here and would not
        block foreign rows but *all* rows: ``Location.tenant_key`` defaults to
        ``""`` and no write path ever fills it. ``LocationCreate`` does not carry
        the field, ``create_location`` builds ``Location(**body.model_dump())``
        without it, and ``PUT /locations/{key}`` replaces the whole document — so
        it also wipes whatever the one-off ``v0004_backfill_tenant_key`` migration
        had put there. That is the documented design (see
        ``PlantInstanceService``: "Location documents are persisted with an empty
        tenant_key and are tenant-verified through their parent site"), and Issue
        #706 already lost a guard to the same assumption.

        Anchoring on the traversal's start vertex instead is correct *and*
        cheaper: sites are stamped on every write path (both site routers, the
        onboarding service, the MCP ``CreateSite`` tool), and a location belongs
        to whatever tenant owns the site it hangs under — which is exactly how
        ``_verify_location_tenant`` in the locations router decides ownership.
        Same shape as ``ArangoTaskRepository.get_comments_for_task``, which takes
        a comment's tenant from its parent task.
        """
        self._require_tenant_key(tenant_key, "get_location_tree")
        # The ``LET`` is loop-invariant, so the optimiser hoists it out
        # (``move-calculations-up``) and the site document is read once; the
        # ``FILTER`` has to sit inside the ``FOR`` because AQL has no top-level one.
        aql = """
        FOR v IN 1..10 OUTBOUND @start_id GRAPH @graph
            OPTIONS {edgeCollections: [@contains_col]}
            FILTER IS_SAME_COLLECTION(@locations_col, v)
            LET site = DOCUMENT(@start_id)
            FILTER site != null AND site.tenant_key == @tenant_key
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

        **The predicate is on the plant, not on the slot — deliberately.**
        ``Slot.tenant_key`` has the same problem as ``Location.tenant_key``: it
        defaults to ``""``, ``SlotCreate`` does not carry it, ``create_slot``
        builds ``Slot(**body.model_dump())`` without it and ``PUT /slots/{key}``
        replaces the whole document. ``FILTER slot.tenant_key == @tenant_key``
        would therefore answer ``None`` for *every* slot rather than only for
        foreign ones — and both callers swallow a ``None`` silently:
        ``WateringService.create_event`` would lose the irrigation-dependent
        warnings of ``WateringEngine.validate_and_warn``, and
        ``_latest_soil_moisture_percent`` would never fire the REQ-005 sensor
        override on the volume recommendation again. A slot is tenant-resolved
        through its location's site, exactly as ``_verify_slot_tenant`` in the
        slots router resolves it.

        The plant is the anchor the application does maintain: the plant router's
        create, the onboarding service and the pup spawn in
        ``PlantInstanceService`` all stamp ``PlantInstance.tenant_key``, and the
        plant is where the caller's request starts anyway.

        One write path used not to stamp it: ``PlantingRunService.create_plants``
        built its batch ``PlantInstance``s without a ``tenant_key`` although
        ``run.tenant_key`` was right there. That was noted here as a pre-existing
        defect of the same family and is fixed under #951, with migration
        ``v0034`` binding the instances already written to their run's tenant.
        The predicate never depended on it — such a plant was already invisible to
        ``list_plants``/``get_plant`` and every other tenant-scoped read, so
        anchoring on it was no stricter than the rest of the application.
        """
        self._require_tenant_key(tenant_key, "get_slot_for_plant")
        query = """
        FOR e IN @@placed_in
          FILTER e._from == @plant_id
          LET plant = DOCUMENT(@plant_id)
          FILTER plant != null AND plant.tenant_key == @tenant_key
          LET slot = DOCUMENT(e._to)
          FILTER slot != null
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
