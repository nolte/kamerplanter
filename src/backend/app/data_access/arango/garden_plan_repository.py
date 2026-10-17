"""The garden plan's read model and its transactional batch write (REQ-053 §21.1, §21.3, GP-NFR-013).

``locations``, ``slots`` and ``garden_objects`` carry no ``tenant_key`` (E-01, #2107):
the site is the owner, so every read here joins the site by key and filters on
*its* tenant inside the query — the predicate is in the statement, never in a
field of the row (§22.3 T-04).

The write is **one** stream transaction (``transactions.stream_transaction``):
inside it the site's ``plan_revision`` is read and compared before anything is
written, so the revision check and the writes cannot be separated by another
request. Everything the batch needs to *validate* was read before the transaction
opened (containment and overlap are CPU work, GP-NFR-013); only the check and the
writes run inside.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, DocumentUpdateError
from pydantic import BaseModel

from app.common.exceptions import NotFoundError, PlanError, PlanRevisionConflictError, WriteConflictError
from app.common.types import SiteKey
from app.data_access.arango import collections as col
from app.data_access.arango.conflicts import WRITE_WRITE_CONFLICT
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.transactions import StreamTransaction, TransactionCollection, stream_transaction
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository, PlanReadData
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    PlanAuditEntry,
    PlanAuditRecord,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlantShortInfo,
    TaskCounter,
)
from app.domain.models.site import DEFAULT_ADJACENCY_FACTOR, DEFAULT_GRID_M, Location, Slot

logger = structlog.get_logger()

#: The site exists and belongs to ``@tenant_key`` — the anchor of every read below.
_OWNED_BY_SITE = """
    LET site = DOCUMENT(CONCAT(@sites, @site_key))
    FILTER site != null AND site.tenant_key == @tenant_key
"""

#: The same anchor for a loop variable named ``l`` (a location): its site exists and is the tenant's.
_OWNED_BY_LOCATION_SITE = """
    LET site = DOCUMENT(CONCAT(@sites, l.site_key))
    FILTER site != null AND site.tenant_key == @tenant_key
"""

_OPEN_TASK_STATUSES = ("pending", "in_progress")


def _edges_touching(vertex_collection: str) -> tuple[tuple[str, str], ...]:
    """``(edge collection, "_from" | "_to")`` for every named-graph edge that can end at *vertex_collection*.

    Derived from ``GRAPH_EDGE_DEFINITIONS`` rather than listed by hand: a hand-written list is the one
    ``delete_location`` carries, and it misses every relation added since (run reservations, sensors,
    equipment, actuators, care events …), which then dangle on a document that is gone.
    """
    found: list[tuple[str, str]] = []
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        edge = str(definition["edge_collection"])
        if vertex_collection in definition["from_vertex_collections"]:
            found.append((edge, "_from"))
        if vertex_collection in definition["to_vertex_collections"]:
            found.append((edge, "_to"))
    return tuple(found)


_LOCATION_EDGES = _edges_touching(col.LOCATIONS)
_SLOT_EDGES = _edges_touching(col.SLOTS)
_OBJECT_EDGES = _edges_touching(col.GARDEN_OBJECTS)

#: Collections the batch transaction writes: the documents, the audit, and every edge a deleted vertex may carry.
_BATCH_WRITE = tuple(
    dict.fromkeys(
        (
            col.SITES,
            col.LOCATIONS,
            col.SLOTS,
            col.GARDEN_OBJECTS,
            col.GARDEN_PLAN_AUDIT,
            col.CONTAINS,
            col.HAS_GARDEN_OBJECT,
            *(edge for edge, _ in (*_LOCATION_EDGES, *_SLOT_EDGES, *_OBJECT_EDGES)),
        )
    )
)
_BATCH_READ = (col.USERS, col.PLANT_INSTANCES)


class _LostTheRace(Exception):  # noqa: N818 — a control-flow signal inside the module, never leaves it
    """Another writer saved the plan between this transaction's snapshot and its first write."""


#: The site's tenant, its plan and the display name of the account that last changed it.
_SITE_REVISION_QUERY = """
FOR s IN @@sites
    FILTER s._key == @site_key
    RETURN {
        tenant_key: s.tenant_key,
        plan: s.plan,
        changed_by: s.plan.plan_updated_by == null
            ? null
            : DOCUMENT(CONCAT(@users, s.plan.plan_updated_by)).display_name
    }
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def _revalidated(model: Location | GardenObject) -> Location | GardenObject:
    """The model run through its own validation again: a service may have mutated it after construction (#968)."""
    if isinstance(model, Location):
        return Location(**_dump(model, by_alias=True))
    return GardenObject(**_dump(model, by_alias=True))


def _insert_doc(model: Location | GardenObject) -> dict[str, Any]:
    """A model as the document to insert, re-validated on the way (the #968 rule for hand-written writers)."""
    data = _dump(_revalidated(model), by_alias=True, exclude_none=True, mode="json")
    data.pop("_key", None)
    return data


class ArangoGardenPlanRepository(IGardenPlanRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db
        self._objects = ArangoGardenObjectRepository(db)

    # ── Reads ─────────────────────────────────────────────────────────

    def _locations(self, site_key: SiteKey, tenant_key: str) -> list[Location]:
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR l IN @@col
                FILTER l.site_key == @site_key
                {_OWNED_BY_SITE}
                SORT l.depth ASC, l.z_order ASC, l._key ASC
                RETURN l
            """,
                bind_vars={
                    "@col": col.LOCATIONS,
                    "site_key": site_key,
                    "sites": f"{col.SITES}/",
                    "tenant_key": tenant_key,
                },
            ),
        )
        return [Location(**doc) for doc in cursor]

    def load_structure(self, site_key: SiteKey, *, tenant_key: str) -> tuple[list[Location], list[GardenObject]]:
        if not tenant_key:
            raise ValueError("load_structure needs a tenant_key (an empty tenant is no tenant, #2107).")
        return (
            self._locations(site_key, tenant_key),
            self._objects.get_garden_objects_by_site(site_key, tenant_key=tenant_key),
        )

    def load_read_model(
        self, site_key: SiteKey, *, tenant_key: str, include_plants: bool, include_tasks: bool
    ) -> PlanReadData:
        locations, objects = self.load_structure(site_key, tenant_key=tenant_key)
        location_keys = [loc.key for loc in locations if loc.key]
        data = PlanReadData(locations=locations, garden_objects=objects)
        data.plan_updated_by_name = self._editor_name(site_key, tenant_key)
        if location_keys:
            # The keys come from the owned locations above, so the slot query needs no tenant of its own.
            slots_cursor = cast(
                "Cursor",
                self._db.aql.execute(
                    """
                FOR s IN @@col
                    FILTER s.location_key IN @location_keys AND s.archived_at == null
                    SORT s.location_key ASC, s.sequence ASC, s._key ASC
                    RETURN s
                """,
                    bind_vars={"@col": col.SLOTS, "location_keys": location_keys},
                ),
            )
            data.slots = [Slot(**doc) for doc in slots_cursor]
        if include_plants and location_keys:
            data.plants = self._plants(location_keys, tenant_key)
        if include_tasks and location_keys:
            data.task_counters = self._task_counters(location_keys, tenant_key)
        return data

    def _editor_name(self, site_key: SiteKey, tenant_key: str) -> str | None:
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            LET site = DOCUMENT(CONCAT(@sites, @site_key))
            FILTER site != null AND site.tenant_key == @tenant_key
            LET by = site.plan.plan_updated_by
            RETURN by == null ? null : DOCUMENT(CONCAT(@users, by)).display_name
            """,
                bind_vars={
                    "sites": f"{col.SITES}/",
                    "users": f"{col.USERS}/",
                    "site_key": site_key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        return next(cursor, None)

    def _plants(self, location_keys: list[str], tenant_key: str) -> list[PlantShortInfo]:
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@col
                FILTER p.tenant_key == @tenant_key AND p.location_key IN @location_keys AND p.removed_on == null
                SORT p.location_key ASC, p._key ASC
                RETURN {
                    key: p._key,
                    instance_id: p.instance_id,
                    species_key: p.species_key,
                    phase_key: p.current_phase_key,
                    slot_key: p.slot_key,
                    location_key: p.location_key
                }
            """,
                bind_vars={"@col": col.PLANT_INSTANCES, "tenant_key": tenant_key, "location_keys": location_keys},
            ),
        )
        return [PlantShortInfo(**row) for row in cursor]

    def _task_counters(self, location_keys: list[str], tenant_key: str) -> dict[str, TaskCounter]:
        """Open tasks per location: tasks on the location itself plus those on plants standing in it.

        Suggestions (``suggested = true``) are proposals, not work, and are not counted. The
        ``!= true`` form is null-safe for rows imported before migration v0095.
        """
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR t IN @@tasks
                FILTER t.tenant_key == @tenant_key
                    AND t.status IN @open
                    AND t.suggested != true
                    AND t.entity_type IN ["location", "plant_instance"]
                LET loc = t.entity_type == "location"
                    ? t.entity_key
                    : DOCUMENT(CONCAT(@plants, t.entity_key)).location_key
                FILTER loc IN @location_keys
                COLLECT location = loc AGGREGATE open_count = COUNT(1),
                    overdue = SUM(t.due_date != null AND DATE_TIMESTAMP(t.due_date) < DATE_TIMESTAMP(@now) ? 1 : 0)
                RETURN {location, open_count, overdue}
            """,
                bind_vars={
                    "@tasks": col.TASKS,
                    "tenant_key": tenant_key,
                    "open": list(_OPEN_TASK_STATUSES),
                    "plants": f"{col.PLANT_INSTANCES}/",
                    "location_keys": location_keys,
                    "now": _now(),
                },
            ),
        )
        return {
            row["location"]: TaskCounter(open_task_count=row["open_count"], overdue_task_count=int(row["overdue"] or 0))
            for row in cursor
        }

    def load_active_slots(self, site_key: SiteKey, location_keys: list[str], *, tenant_key: str) -> list[Slot]:
        if not tenant_key:
            raise ValueError("load_active_slots needs a tenant_key (an empty tenant is no tenant, #2107).")
        if not location_keys:
            return []
        # A location counts only when it hangs off *this* site of *this* tenant — the keys are the caller's.
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR l IN @@locations
                FILTER l._key IN @location_keys AND l.site_key == @site_key
                {_OWNED_BY_LOCATION_SITE}
                FOR s IN @@slots
                    FILTER s.location_key == l._key AND s.archived_at == null
                    RETURN s
            """,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "@slots": col.SLOTS,
                    "location_keys": location_keys,
                    "site_key": site_key,
                    "sites": f"{col.SITES}/",
                    "tenant_key": tenant_key,
                },
            ),
        )
        return [Slot(**doc) for doc in cursor]

    def bed_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        if not location_type_keys:
            return {}
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                "FOR t IN @@col FILTER t._key IN @keys RETURN {key: t._key, is_bed: t.is_bed == true}",
                bind_vars={"@col": col.LOCATION_TYPES, "keys": sorted(set(location_type_keys))},
            ),
        )
        return {row["key"]: row["is_bed"] for row in cursor}

    def count_active_plants(self, location_keys: list[str], *, tenant_key: str) -> int:
        if not tenant_key:
            raise ValueError("count_active_plants needs a tenant_key (an empty tenant is no tenant, #2107).")
        if not location_keys:
            return 0
        # The keys come from the site's owned structure, and a plant standing in one blocks the delete whatever
        # its own ``tenant_key`` says: a stamp that is missing or wrong must not let a plant be orphaned (V-09).
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            RETURN LENGTH(
                FOR p IN @@col
                    FILTER p.location_key IN @location_keys AND p.removed_on == null
                    RETURN 1
            )
            """,
                bind_vars={"@col": col.PLANT_INSTANCES, "location_keys": location_keys},
            ),
        )
        return int(next(cursor, 0))

    def list_audit(self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int) -> list[PlanAuditEntry]:
        if not tenant_key:
            raise ValueError("list_audit needs a tenant_key (an empty tenant is no tenant, #2107).")
        bind_vars: dict[str, Any] = {
            "@col": col.GARDEN_PLAN_AUDIT,
            "site_key": site_key,
            "tenant_key": tenant_key,
            "users": f"{col.USERS}/",
            "offset": offset,
            "limit": limit,
        }
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR a IN @@col
                FILTER a.site_key == @site_key AND a.tenant_key == @tenant_key
                SORT a.revision DESC, DATE_TIMESTAMP(a.at) DESC, a._key DESC
                LIMIT @offset, @limit
                RETURN {
                    revision: a.revision, op: a.op, entity: a.entity, key: a.key,
                    summary: a.summary, at: a.at,
                    changed_by_name: a.user_key == null ? null : DOCUMENT(CONCAT(@users, a.user_key)).display_name
                }
            """,
                bind_vars=bind_vars,
            ),
        )
        return [PlanAuditEntry(**row) for row in cursor]

    # ── The batch ─────────────────────────────────────────────────────

    def apply_plan_batch(self, write: PlanBatchWrite) -> PlanBatchOutcome:
        try:
            with stream_transaction(
                self._db,
                write=_BATCH_WRITE,
                read=_BATCH_READ,
                entity="garden_plan",
                time_budget_seconds=write.time_budget_seconds,
            ) as txn:
                stored_plan, revision = self._check_revision(txn, write)
                now = _now()
                new_revision = revision + 1
                key_map: dict[str, str] = {}

                self._delete_locations(txn, write)
                txn.check_budget()
                self._delete_objects(txn, write.object_deletes)
                self._insert_locations(txn, write, key_map, now)
                self._update_locations(txn, write, now)
                self._insert_objects(txn, write, key_map, now)
                self._update_objects(txn, write, now)
                txn.check_budget()
                self._write_site(txn, write, stored_plan, new_revision, now)
                self._write_audit(txn, write, new_revision, now)
        except _LostTheRace:
            # The transaction is aborted; the winner's revision is what the loser is told about.
            raise self._conflict_after_race(write) from None
        return PlanBatchOutcome(plan_revision=new_revision, key_map=key_map)

    def _conflict_after_race(self, write: PlanBatchWrite) -> PlanRevisionConflictError:
        """The 409 for a writer that lost the race for the site document (V-14), read after its abort."""
        rows = list(
            cast("Cursor", self._db.aql.execute(_SITE_REVISION_QUERY, bind_vars=self._site_revision_binds(write)))
        )
        if not rows or rows[0]["tenant_key"] != write.tenant_key:
            raise NotFoundError("Site", write.site_key)
        plan = rows[0]["plan"] or {}
        committed = int(plan.get("plan_revision") or 0)
        if committed <= write.expected_revision:
            # The winner holds the site document and has not committed yet, so the committed state is still the
            # one this writer read. It was overtaken: the revision to reload is at least the next one, and who
            # saved it is not known yet.
            return PlanRevisionConflictError(
                current_revision=write.expected_revision + 1, changed_by=None, changed_at=None
            )
        return PlanRevisionConflictError(
            current_revision=committed, changed_by=rows[0]["changed_by"], changed_at=plan.get("plan_updated_at")
        )

    @staticmethod
    def _site_revision_binds(write: PlanBatchWrite) -> dict[str, Any]:
        return {"@sites": col.SITES, "users": f"{col.USERS}/", "site_key": write.site_key}

    def _check_revision(self, txn: StreamTransaction, write: PlanBatchWrite) -> tuple[dict[str, Any] | None, int]:
        rows = list(txn.aql.execute(_SITE_REVISION_QUERY, bind_vars=self._site_revision_binds(write)))
        if not rows or not write.tenant_key or rows[0]["tenant_key"] != write.tenant_key:
            raise NotFoundError("Site", write.site_key)
        plan = rows[0]["plan"]
        revision = int((plan or {}).get("plan_revision") or 0)
        if revision != write.expected_revision or revision != write.basis_revision:
            raise PlanRevisionConflictError(
                current_revision=revision,
                changed_by=rows[0]["changed_by"],
                changed_at=(plan or {}).get("plan_updated_at"),
            )
        self._take_revision(txn, write, revision)
        return plan, revision

    def _take_revision(self, txn: StreamTransaction, write: PlanBatchWrite, revision: int) -> None:
        """Compare-and-swap the revision first, so two writers at the same revision cannot both get past it.

        Reading ``plan_revision`` alone is not enough: both transactions read ``N`` from their snapshot and pass,
        and the loser would fail at the *end* on the site document's write-write conflict (``conflict.write``) —
        a correct abort with the wrong answer. Updating the document here, as the first write, makes the loser
        fail at this statement, where the conflict is read as what it is: someone else saved first (V-14).
        """
        try:
            taken = list(
                txn.aql.execute(
                    """
                FOR s IN @@sites
                    FILTER s._key == @site_key AND s.tenant_key == @tenant_key
                        AND (s.plan.plan_revision || 0) == @revision
                    UPDATE s WITH { plan: { plan_revision: @next } } IN @@sites
                    RETURN 1
                """,
                    bind_vars={
                        "@sites": col.SITES,
                        "site_key": write.site_key,
                        "tenant_key": write.tenant_key,
                        "revision": revision,
                        "next": revision + 1,
                    },
                )
            )
        except AQLQueryExecuteError as exc:
            if exc.error_code == WRITE_WRITE_CONFLICT:
                raise _LostTheRace from exc
            raise
        if not taken:
            raise _LostTheRace

    def _delete_locations(self, txn: StreamTransaction, write: PlanBatchWrite) -> None:
        keys = write.location_deletes
        if not keys:
            return
        # Re-checked inside the transaction: a plant placed between the service's read and this
        # statement must not be orphaned (V-09).
        active = list(
            txn.aql.execute(
                """
            RETURN LENGTH(
                FOR p IN @@plants
                    FILTER p.location_key IN @keys AND p.removed_on == null
                    RETURN 1
            )
            """,
                bind_vars={"@plants": col.PLANT_INSTANCES, "keys": keys},
            )
        )[0]
        if active:
            raise PlanError(
                "location.has_active_plants",
                "A location with active plants cannot be deleted.",
                status_code=409,
                active_plant_count=int(active),
            )
        # A child created through a path outside the plan revision after the service read the tree would be
        # orphaned by the edge cascade below: refuse, the client reloads and deletes again.
        orphaned = list(
            txn.aql.execute(
                "FOR l IN @@col FILTER l.parent_location_key IN @keys AND l._key NOT IN @keys LIMIT 1 RETURN 1",
                bind_vars={"@col": col.LOCATIONS, "keys": keys},
            )
        )
        if orphaned:
            raise WriteConflictError("garden_plan", "a location below the deleted one was created concurrently")
        location_ids = [f"{col.LOCATIONS}/{key}" for key in keys]
        slot_ids = list(
            txn.aql.execute(
                "FOR s IN @@slots FILTER s.location_key IN @keys RETURN s._id",
                bind_vars={"@slots": col.SLOTS, "keys": keys},
            )
        )
        if slot_ids:
            for edge, field in _SLOT_EDGES:
                self._remove_edges(txn, edge, field, slot_ids)
            txn.aql.execute(
                "FOR s IN @@slots FILTER s.location_key IN @keys REMOVE s IN @@slots",
                bind_vars={"@slots": col.SLOTS, "keys": keys},
            )
        for edge, field in _LOCATION_EDGES:
            self._remove_edges(txn, edge, field, location_ids)
        txn.aql.execute(
            "FOR l IN @@col FILTER l._key IN @keys REMOVE l IN @@col",
            bind_vars={"@col": col.LOCATIONS, "keys": keys},
        )

    @staticmethod
    def _remove_edges(txn: StreamTransaction, edge_collection: str, field: str, ids: list[str]) -> None:
        # ``field`` is one of two literals chosen above — never a request value — so it is
        # interpolated; the collection and the ids are bound.
        txn.aql.execute(
            f"FOR e IN @@edges FILTER e.{aql_field(field)} IN @ids REMOVE e IN @@edges",
            bind_vars={"@edges": edge_collection, "ids": ids},
        )

    def _delete_objects(self, txn: StreamTransaction, keys: list[str]) -> None:
        if not keys:
            return
        ids = [f"{col.GARDEN_OBJECTS}/{key}" for key in keys]
        for edge, field in _OBJECT_EDGES:
            self._remove_edges(txn, edge, field, ids)
        txn.aql.execute(
            "FOR o IN @@col FILTER o._key IN @keys REMOVE o IN @@col",
            bind_vars={"@col": col.GARDEN_OBJECTS, "keys": keys},
        )

    def _insert_locations(
        self, txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str
    ) -> None:
        collection = txn.collection(col.LOCATIONS)
        contains = txn.collection(col.CONTAINS)
        for temp_key, location in write.location_inserts:
            doc = _insert_doc(location)
            parent = doc.get("parent_location_key")
            if parent in key_map:
                parent = doc["parent_location_key"] = key_map[parent]
            doc["site_key"] = write.site_key
            doc["created_at"] = doc["updated_at"] = now
            created = collection.insert(doc, return_new=True)
            key = created["_key"]
            key_map[temp_key] = key
            origin = f"{col.LOCATIONS}/{parent}" if parent else f"{col.SITES}/{write.site_key}"
            contains.insert({"_from": origin, "_to": f"{col.LOCATIONS}/{key}", "created_at": now})
            txn.check_budget()

    def _update_locations(self, txn: StreamTransaction, write: PlanBatchWrite, now: str) -> None:
        collection = txn.collection(col.LOCATIONS)
        for key, fields in write.location_updates:
            self._replace_fields(collection, key, fields, now)

    def _insert_objects(self, txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str) -> None:
        collection = txn.collection(col.GARDEN_OBJECTS)
        edges = txn.collection(col.HAS_GARDEN_OBJECT)
        for temp_key, garden_object in write.object_inserts:
            doc = _insert_doc(garden_object)
            parent = doc.get("parent_location_key")
            if parent in key_map:
                doc["parent_location_key"] = key_map[parent]
            doc["site_key"] = write.site_key
            doc["created_by"] = write.editor_key
            doc["created_at"] = doc["updated_at"] = now
            created = collection.insert(doc, return_new=True)
            key_map[temp_key] = created["_key"]
            edges.insert(
                {
                    "_from": f"{col.SITES}/{write.site_key}",
                    "_to": f"{col.GARDEN_OBJECTS}/{created['_key']}",
                    "created_at": now,
                }
            )
            txn.check_budget()

    def _update_objects(self, txn: StreamTransaction, write: PlanBatchWrite, now: str) -> None:
        collection = txn.collection(col.GARDEN_OBJECTS)
        for key, fields in write.object_updates:
            self._replace_fields(collection, key, fields, now)

    @staticmethod
    def _replace_fields(collection: TransactionCollection, key: str, fields: dict[str, Any], now: str) -> None:
        """Write *only* the fields the batch changed (the service computed the diff against what it read).

        Writing the whole model back would overwrite, with the value read before the transaction, every
        field another path changed in the meantime without raising the plan revision (``PUT /locations``,
        status, soil, slot routes — §21.2 "outside the revision"). ``merge=False`` replaces a changed object
        whole (a geometry that changes kind must not keep the old kind's keys); ``keep_none=False`` removes a
        field the batch cleared.
        """
        try:
            collection.update({"_key": key, **fields, "updated_at": now}, merge=False, keep_none=False)
        except DocumentUpdateError as exc:
            if exc.error_code == 1202:  # the document is gone: another writer removed it after our read
                raise WriteConflictError("garden_plan", "a document of the plan was removed concurrently") from exc
            raise

    def _write_site(
        self,
        txn: StreamTransaction,
        write: PlanBatchWrite,
        stored_plan: dict[str, Any] | None,
        new_revision: int,
        now: str,
    ) -> None:
        plan: dict[str, Any] = (
            dict(stored_plan)
            if stored_plan
            else {
                "north_angle_deg": 0.0,
                "default_grid_m": DEFAULT_GRID_M,
                "adjacency_factor": DEFAULT_ADJACENCY_FACTOR,
            }
        )
        if write.boundary is not None:
            plan["boundary"] = write.boundary.model_dump(mode="json")
        if write.north_angle_deg is not None:
            plan["north_angle_deg"] = write.north_angle_deg
        if write.default_grid_m is not None:
            plan["default_grid_m"] = write.default_grid_m
        if write.adjacency_factor is not None:
            plan["adjacency_factor"] = write.adjacency_factor
        plan["plan_revision"] = new_revision
        plan["plan_updated_at"] = now
        plan["plan_updated_by"] = write.editor_key
        site_update: dict[str, Any] = {"_key": write.site_key, "plan": plan, "updated_at": now}
        if write.total_area_m2 is not None:
            site_update["total_area_m2"] = write.total_area_m2
        # ``merge=False`` replaces the nested ``plan`` object whole: the dict above is the complete plan.
        txn.collection(col.SITES).update(site_update, merge=False)

    def _write_audit(self, txn: StreamTransaction, write: PlanBatchWrite, revision: int, now: str) -> None:
        if not write.audit:
            return
        audit = txn.collection(col.GARDEN_PLAN_AUDIT)
        entry: dict[str, str]
        for entry in write.audit:
            record = PlanAuditRecord(
                tenant_key=write.tenant_key,
                site_key=write.site_key,
                revision=revision,
                user_key=write.editor_key,
                op=entry["op"],
                entity=entry["entity"],
                key=entry["key"],
                summary=entry.get("summary", ""),
                at=datetime.fromisoformat(now),
            )
            audit.insert(_dump(record, mode="json"))
