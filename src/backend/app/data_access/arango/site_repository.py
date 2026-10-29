from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.common.types import LocationKey, PlantInstanceKey, SiteKey, SlotKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.graph_edges import edges_touching, remove_edges
from app.data_access.arango.irrigation_zone_repository import ZONE_EDGES
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.garden_plan import PlanAuditRecord
from app.domain.models.site import Location, Site, Slot

_SITE_EDGES = edges_touching(col.SITES)
_LOCATION_EDGES = edges_touching(col.LOCATIONS)
_SLOT_EDGES = edges_touching(col.SLOTS)
_OBJECT_EDGES = edges_touching(col.GARDEN_OBJECTS)

#: The rows that exist only for one site and go with it (REQ-046/047/037): selected by ``site_key``, never across
#: tenants. Care events and the plan's change log are history and stay (REQ-053 GP-FR-101, §20.13 SR-011, #2513).
_SITE_DEPENDENTS: tuple[str, ...] = (
    col.SEASON_STATES,
    col.WEATHER_FORECASTS,
    col.CLIMATE_NORMALS,
    col.WEATHER_SOURCE_CONFIGS,
    col.IRRIGATION_DEMANDS,
)
#: Every edge a removed dependent row may carry (``has_*`` from the site, ``demand_for_run`` on a demand).
_DEPENDENT_EDGES = tuple(pair for name in _SITE_DEPENDENTS for pair in edges_touching(name))

#: What :meth:`ArangoSiteRepository._remove_locations` writes: the locations, their slots, every edge on either.
_LOCATION_REMOVAL_WRITE: tuple[str, ...] = tuple(
    dict.fromkeys((col.LOCATIONS, col.SLOTS, *(edge for edge, _ in (*_LOCATION_EDGES, *_SLOT_EDGES))))
)

#: What the site delete writes, deduplicated: the structure rows, the dependents, the audit row and every edge a
#: removed vertex may carry — derived, so a relation registered later is cut without touching this module.
_SITE_DELETE_WRITE: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            col.SITES,
            *_LOCATION_REMOVAL_WRITE,
            col.GARDEN_OBJECTS,
            col.IRRIGATION_ZONES,
            *_SITE_DEPENDENTS,
            col.GARDEN_PLAN_AUDIT,
            *(edge for edge, _ in (*_SITE_EDGES, *_OBJECT_EDGES, *ZONE_EDGES, *_DEPENDENT_EDGES)),
        )
    )
)
#: Read only: the plants standing on the site (V-09 one level up, #2513 WP-3).
_SITE_DELETE_READ: tuple[str, ...] = (col.PLANT_INSTANCES,)

#: The site as the delete needs it: its tenant, name and plan revision (the audit row's revision is the next one).
_SITE_FOR_DELETE = """
FOR s IN @@sites
    FILTER s._key == @site_key
    RETURN {tenant_key: s.tenant_key, name: s.name, revision: s.plan.plan_revision || 0}
"""

#: The site's irrigation zones: by ``site_key`` **and** the site's own tenant (the zone carries one, E-01).
_ZONES_OF_SITE = """
FOR z IN @@zones
    FILTER z.site_key == @site_key AND z.tenant_key == @tenant_key
    RETURN z._id
"""

#: A dependent row of the site. A row stamped with another tenant is never taken, whatever its ``site_key`` says;
#: an unstamped one (``tenant_key`` defaults to ``""`` on these models) belongs to the site that names it.
_DEPENDENTS_OF_SITE = """
FOR d IN @@col
    FILTER d.site_key == @site_key
        AND (d.tenant_key == null OR d.tenant_key == "" OR d.tenant_key == @tenant_key)
    RETURN d._id
"""


@dataclass(frozen=True)
class _SiteDeleteScope:
    """Everything one site delete removes, collected before its first write.

    Holds full document ids. ``location_ids``/``slot_ids`` are also what a refusal on standing plants checks against
    (``location_key``/``slot_key`` of a plant), so that check needs no second read.
    """

    site_id: str
    tenant_key: str
    name: str
    revision: int
    location_ids: list[str]
    slot_ids: list[str]
    object_ids: list[str]
    zone_ids: list[str]
    dependent_ids: dict[str, list[str]]


def _keys(ids: Sequence[str]) -> list[str]:
    return [doc_id.split("/", 1)[1] for doc_id in ids]


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

    def get_all_sites(self, offset: int = 0, limit: int = 50, *, tenant_key: str) -> tuple[list[Site], int]:
        return super().get_all(offset, limit, tenant_key=tenant_key)

    def list_sites_window(self, offset: int = 0, limit: int = 50, *, tenant_key: str) -> list[Site]:
        """The page of :meth:`get_all_sites` without its count query (MT-035, #2131)."""
        self._require_tenant_key(tenant_key, "list_sites_window")
        return self.list_window(offset=offset, limit=limit, tenant_key=tenant_key)

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

    def delete_site(self, key: SiteKey, *, user_key: str) -> bool:
        """Remove the site and everything that exists only for it, in one stream transaction (#2513).

        Goes: the locations below the site (the ``contains`` tree **and** every location naming the site), their
        slots, the garden objects, the irrigation zones, and the site's season state, forecasts, climate normals,
        weather-source config and irrigation demands — plus every graph edge on any of those vertices, derived
        from the graph definitions. Stays: ``care_events`` and the earlier ``garden_plan_audit`` rows (history,
        REQ-053 GP-FR-101 / §20.13 SR-011); their edges to a removed vertex are cut. Fields of other requirements'
        rows that name a removed key are left as they are. One audit row (``op="delete"``, ``entity="site"``)
        records the delete in the same transaction.

        Args:
            key: The site's document key.
            user_key: The account that deletes; stored on the audit row (pseudonymised on account erasure).

        Returns:
            ``True`` — the site was removed.

        Raises:
            NotFoundError: The site does not exist (any more) when the transaction reads it.
        """
        with stream_transaction(self._db, write=_SITE_DELETE_WRITE, read=_SITE_DELETE_READ, entity="site") as txn:
            scope = self._collect_site_delete_scope(txn, key)
            # Everything above only reads; everything below writes. A refusal of the whole delete belongs here, so
            # it holds against the transaction's snapshot and nothing has been written when it fires.
            self._remove_site_scope(txn, scope)
            txn.check_budget()
            self._write_site_delete_audit(txn, key, scope, user_key)
            txn.collection(col.SITES).delete(key)
        return True

    def _collect_site_delete_scope(self, txn: StreamTransaction, key: SiteKey) -> _SiteDeleteScope:
        rows = list(txn.aql.execute(_SITE_FOR_DELETE, bind_vars={"@sites": col.SITES, "site_key": key}))
        if not rows:
            raise NotFoundError("Site", key)
        tenant_key = str(rows[0]["tenant_key"] or "")
        location_ids = self._location_ids_of_site(txn, key)
        zone_ids = list(
            txn.aql.execute(
                _ZONES_OF_SITE,
                bind_vars={"@zones": col.IRRIGATION_ZONES, "site_key": key, "tenant_key": tenant_key},
            )
        )
        dependent_ids = {
            name: [
                str(doc_id)
                for doc_id in txn.aql.execute(
                    _DEPENDENTS_OF_SITE, bind_vars={"@col": name, "site_key": key, "tenant_key": tenant_key}
                )
            ]
            for name in _SITE_DEPENDENTS
        }
        return _SiteDeleteScope(
            site_id=f"{col.SITES}/{key}",
            tenant_key=tenant_key,
            name=str(rows[0]["name"] or ""),
            revision=int(rows[0]["revision"] or 0),
            location_ids=location_ids,
            slot_ids=self._slot_ids_of_locations(txn, location_ids),
            object_ids=self._object_ids_of_site(txn, key),
            zone_ids=[str(zone_id) for zone_id in zone_ids],
            dependent_ids=dependent_ids,
        )

    @staticmethod
    def _location_ids_of_site(txn: StreamTransaction, key: SiteKey) -> list[str]:
        """The site's locations at every depth: the ``contains`` tree below the site ∪ every location naming it.

        A nested location hangs from its parent location (:meth:`create_location`) and is not guaranteed to carry
        ``site_key``, so neither source alone is complete. Walked level by level until no new location appears —
        no depth limit, and the seen set ends the walk on a cyclic edge too.
        """
        seen: dict[str, None] = dict.fromkeys(
            str(doc_id)
            for doc_id in txn.aql.execute(
                "FOR l IN @@locations FILTER l.site_key == @site_key RETURN l._id",
                bind_vars={"@locations": col.LOCATIONS, "site_key": key},
            )
        )
        frontier = [f"{col.SITES}/{key}", *seen]
        while frontier:
            children = [
                str(doc_id)
                for doc_id in txn.aql.execute(
                    """
                    FOR e IN @@contains
                        FILTER e._from IN @parents AND IS_SAME_COLLECTION(@locations, e._to)
                        RETURN DISTINCT e._to
                    """,
                    bind_vars={"@contains": col.CONTAINS, "parents": frontier, "locations": col.LOCATIONS},
                )
            ]
            frontier = [doc_id for doc_id in children if doc_id not in seen]
            seen.update(dict.fromkeys(frontier))
        return list(seen)

    @staticmethod
    def _slot_ids_of_locations(txn: StreamTransaction, location_ids: Sequence[str]) -> list[str]:
        """The slots of *location_ids*: by ``location_key`` ∪ by ``has_slot`` edge (either alone may be stale)."""
        if not location_ids:
            return []
        rows = txn.aql.execute(
            """
            RETURN UNION_DISTINCT(
                (FOR s IN @@slots FILTER s.location_key IN @keys RETURN s._id),
                (FOR e IN @@has_slot FILTER e._from IN @ids AND IS_SAME_COLLECTION(@slots_name, e._to) RETURN e._to)
            )
            """,
            bind_vars={
                "@slots": col.SLOTS,
                "@has_slot": col.HAS_SLOT,
                "slots_name": col.SLOTS,
                "keys": _keys(location_ids),
                "ids": list(location_ids),
            },
        )
        return sorted(str(doc_id) for doc_id in next(iter(rows)))

    @staticmethod
    def _object_ids_of_site(txn: StreamTransaction, key: SiteKey) -> list[str]:
        """The site's garden objects: by ``site_key`` ∪ by ``has_garden_object`` edge (objects carry no tenant)."""
        rows = txn.aql.execute(
            """
            RETURN UNION_DISTINCT(
                (FOR o IN @@objects FILTER o.site_key == @site_key RETURN o._id),
                (FOR e IN @@has_object FILTER e._from == @site_id AND IS_SAME_COLLECTION(@objects_name, e._to)
                    RETURN e._to)
            )
            """,
            bind_vars={
                "@objects": col.GARDEN_OBJECTS,
                "@has_object": col.HAS_GARDEN_OBJECT,
                "objects_name": col.GARDEN_OBJECTS,
                "site_key": key,
                "site_id": f"{col.SITES}/{key}",
            },
        )
        return sorted(str(doc_id) for doc_id in next(iter(rows)))

    def _remove_site_scope(self, txn: StreamTransaction, scope: _SiteDeleteScope) -> None:
        """Cut every derived edge on the scope's vertices, then remove the rows (the site itself excepted)."""
        self._remove_locations(txn, scope.location_ids)
        txn.check_budget()
        removals: tuple[tuple[str, list[str], tuple[tuple[str, str], ...]], ...] = (
            (col.GARDEN_OBJECTS, scope.object_ids, _OBJECT_EDGES),
            (col.IRRIGATION_ZONES, scope.zone_ids, ZONE_EDGES),
            *((name, scope.dependent_ids[name], edges_touching(name)) for name in _SITE_DEPENDENTS),
        )
        for collection, ids, edges in removals:
            if not ids:
                continue
            for edge, field_name in edges:
                remove_edges(txn, edge, field_name, ids)
            self._remove_rows(txn, collection, ids)
        for edge, field_name in _SITE_EDGES:
            remove_edges(txn, edge, field_name, [scope.site_id])

    def _remove_locations(self, txn: StreamTransaction, location_ids: Sequence[str]) -> None:
        """Remove *location_ids*, their slots and every graph edge on either, inside *txn* (#2513).

        The edge sets are derived (:func:`edges_touching`), so ``care_event_at``, ``run_at_location``,
        ``placed_in`` and every relation registered later are cut with the vertex; the care events themselves
        stay. *txn* must declare :data:`_LOCATION_REMOVAL_WRITE` for writing. Callers pass the complete set —
        descendants included — this helper does not walk the tree.

        Args:
            txn: The open stream transaction.
            location_ids: Full document ids (``"locations/<key>"``) of the locations to remove.
        """
        if not location_ids:
            return
        slot_ids = self._slot_ids_of_locations(txn, location_ids)
        if slot_ids:
            for edge, field_name in _SLOT_EDGES:
                remove_edges(txn, edge, field_name, slot_ids)
            self._remove_rows(txn, col.SLOTS, slot_ids)
        for edge, field_name in _LOCATION_EDGES:
            remove_edges(txn, edge, field_name, location_ids)
        self._remove_rows(txn, col.LOCATIONS, location_ids)

    @staticmethod
    def _remove_rows(txn: StreamTransaction, collection: str, ids: Sequence[str]) -> None:
        txn.aql.execute(
            "FOR d IN @@col FILTER d._id IN @ids REMOVE d IN @@col",
            bind_vars={"@col": collection, "ids": list(ids)},
        )

    @staticmethod
    def _write_site_delete_audit(txn: StreamTransaction, key: SiteKey, scope: _SiteDeleteScope, user_key: str) -> None:
        """The SR-011 row of the delete (REQ-053 §20.13): who removed which site, at the revision after the last."""
        record = PlanAuditRecord(
            tenant_key=scope.tenant_key,
            site_key=key,
            revision=scope.revision + 1,
            user_key=user_key,
            op="delete",
            entity="site",
            key=key,
            summary=scope.name[:200],
            at=datetime.now(UTC),
        )
        doc: dict[str, Any] = record.model_dump(mode="json")
        txn.collection(col.GARDEN_PLAN_AUDIT).insert(doc)

    # ── Location CRUD ─────────────────────────────────────────────────

    def get_locations_by_site(self, site_key: SiteKey) -> list[Location]:
        site_id = f"{col.SITES}/{site_key}"
        results = self.get_edges(col.CONTAINS, site_id, direction="outbound")
        return [Location(**self._from_doc(r["vertex"])) for r in results]

    def get_location_by_key(self, key: LocationKey) -> Location | None:
        return self._locations.get_by_key(key)

    def get_locations_by_keys(self, keys: list[LocationKey]) -> list[Location]:
        if not keys:
            return []
        cursor = self._db.aql.execute(
            "FOR l IN @@locations FILTER l._key IN @keys SORT l._key RETURN l",
            bind_vars={"@locations": col.LOCATIONS, "keys": list(keys)},
        )
        return [Location(**self._from_doc(doc)) for doc in cast("Cursor", cursor)]

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
        # REQ-053 WP 7.1: the bed leaves its irrigation zone (the field goes with the document).
        self.delete_edges(col.ZONE_COVERS, vertex_id=location_id, direction="inbound")
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
        """Rewrite a slot and keep its ``has_slot`` edge on ``slot.location_key`` (#1878).

        The field and the edge are two spellings of the same fact — the field is
        read by the ownership anchor (``resolve_owned_slot``), the edge by
        ``get_slots_by_location`` — and this method used to write only the field,
        so a re-parented slot was listed under its old location and owned through
        its new one. The edge is re-pointed whenever the stored one does not
        already hang off the new location; an unchanged location writes nothing.

        The edge is **never** moved across a tenant boundary. Internal callers
        (a planting run occupying a slot, a plant being placed) hand back the slot
        they read, whose field on a pre-#1871 row may point into another tenant;
        following it would re-parent the owner's slot into the stranger's location.
        Such a row is left as it is for the v0067 migration to count.
        """
        updated = self._slots.update(key, slot)
        if updated.location_key:
            self._point_has_slot_at(key, updated.location_key)
        return updated

    def _location_tenant(self, location_key: str) -> str | None:
        """The tenant of the site a location hangs off, ``None`` when the location or its site is missing."""
        rows = list(
            self._db.aql.execute(
                "LET l = DOCUMENT(CONCAT(@locations, @key)) "
                "LET s = (l == null OR l.site_key == null) ? null : DOCUMENT(CONCAT(@sites, l.site_key)) "
                "RETURN s == null ? null : (s.tenant_key == null ? '' : s.tenant_key)",
                bind_vars={"locations": f"{col.LOCATIONS}/", "sites": f"{col.SITES}/", "key": location_key},
            )
        )
        return rows[0] if rows else None

    def _point_has_slot_at(self, key: SlotKey, location_key: LocationKey) -> None:
        slot_id = f"{col.SLOTS}/{key}"
        location_id = f"{col.LOCATIONS}/{location_key}"
        current = list(
            self._db.aql.execute(
                "FOR e IN @@edges FILTER e._to == @slot_id RETURN e",
                bind_vars={"@edges": col.HAS_SLOT, "slot_id": slot_id},
            )
        )
        if len(current) == 1 and current[0]["_from"] == location_id:
            return
        if current:
            target_tenant = self._location_tenant(location_key)
            if target_tenant is None or any(
                self._location_tenant(edge["_from"].split("/", 1)[1]) != target_tenant for edge in current
            ):
                return
        # Ensure the target edge first, then drop the others: a concurrent reader
        # never finds the slot without a parent, and a lost race leaves a duplicate
        # the next update (or v0067's count) sees rather than an orphan.
        self._db.aql.execute(
            "UPSERT {_from: @loc, _to: @slot} INSERT {_from: @loc, _to: @slot, created_at: @now} UPDATE {} IN @@edges",
            bind_vars={"loc": location_id, "slot": slot_id, "now": self._now(), "@edges": col.HAS_SLOT},
        )
        self._db.aql.execute(
            "FOR e IN @@edges FILTER e._to == @slot AND e._from != @loc REMOVE e IN @@edges",
            bind_vars={"loc": location_id, "slot": slot_id, "@edges": col.HAS_SLOT},
        )

    def delete_slot(self, key: SlotKey) -> bool:
        return self._delete_slot_internal(key)

    def _delete_slot_internal(self, key: SlotKey) -> bool:
        slot_id = f"{col.SLOTS}/{key}"
        # Each edge is cut on the end it is actually written on — the three differ,
        # and getting one wrong leaves a dangling edge that nothing reports.
        #
        # `has_slot` points *at* the slot (location → slot), so the end to detach is
        # the inbound one — the repair #1525 made for `phase_history_edge`. It used to
        # be spelled `from_id=f"{col.LOCATIONS}/%", to_id=slot_id` (#1535):
        # `delete_edges` binds the vertex and compares it with `==`, never `LIKE`, so
        # the `%` was a literal character and `locations/%` is not an id any edge
        # carries. The call matched nothing, every time, so a slot deleted through
        # THIS path left its incoming edge behind. (Deletion via `delete_location`
        # was unaffected: it sweeps the location's outbound `has_slot` edges itself
        # afterwards, see `_delete_location_internal`.)
        self.delete_edges(col.HAS_SLOT, vertex_id=slot_id, direction="inbound")
        # `adjacent_to` is written in BOTH directions for one adjacency
        # (`GraphRepository.set_adjacent_slots`: "Adjacency is bidirectional — create
        # edges in both directions"), so cutting only the outbound half left
        # `neighbour → deleted slot` behind (#1573 review SCR-001).
        self.delete_edges(col.ADJACENT_TO, vertex_id=slot_id, direction="any")
        # `filled_with` is slot → batch, written by
        # `SubstrateRepository.assign_batch_to_slot`; outbound is the right end here.
        self.delete_edges(col.FILLED_WITH, vertex_id=slot_id, direction="outbound")
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
