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

from app.common.exceptions import (
    NotFoundError,
    PlanError,
    PlanRevisionConflictError,
    PlanValidationError,
    WriteConflictError,
)
from app.common.types import SiteKey
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import CARE_EVENT_WRITE_COLLECTIONS, write_care_event
from app.data_access.arango.conflicts import WRITE_WRITE_CONFLICT
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.irrigation_zone_repository import ZONE_EDGES
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.transactions import StreamTransaction, TransactionCollection, stream_transaction
from app.data_access.arango.watering_queries import last_waterings
from app.domain.calculators.overdue_calculator import start_of_utc_day
from app.domain.engines.garden_plan_engine import ERROR_REFERENCE_NOT_FOUND
from app.domain.engines.slot_reservation_engine import LIVE_RUN_STATUSES
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository, PlanReadData
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    BedCounters,
    PlanAuditEntry,
    PlanAuditRecord,
    PlanBatchOutcome,
    PlanBatchWrite,
    PlanSnapshotEntry,
    PlantShortInfo,
    SlotBatchOutcome,
    SlotBatchWrite,
    SlotSpeciesHint,
    TaskCounter,
)
from app.domain.models.site import DEFAULT_ADJACENCY_FACTOR, DEFAULT_GRID_M, Location, SiteUnderlay, Slot

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
            # A deleted water source is unlinked from its zones (``water_source_key``), REQ-053 WP 7.1.
            col.IRRIGATION_ZONES,
            # The import (WP 7.2) creates and replaces zones: the zone, its site edge and every edge on it.
            *(edge for edge, _ in ZONE_EDGES),
            *CARE_EVENT_WRITE_COLLECTIONS,
            col.CONTAINS,
            col.HAS_GARDEN_OBJECT,
            *(edge for edge, _ in (*_LOCATION_EDGES, *_SLOT_EDGES, *_OBJECT_EDGES)),
        )
    )
)
_BATCH_READ = (col.USERS, col.PLANT_INSTANCES)

#: Collections a slot batch writes: the slots, their ``has_slot`` edge and every other edge a deleted slot may carry.
_SLOT_BATCH_WRITE = tuple(dict.fromkeys((col.LOCATIONS, col.SLOTS, col.HAS_SLOT, *(edge for edge, _ in _SLOT_EDGES))))
#: ``run_planned_at`` is read for the reservation re-check; it is declared for writing already when a slot edge.
_SLOT_BATCH_READ = tuple(c for c in (col.RUN_PLANNED_AT,) if c not in _SLOT_BATCH_WRITE)


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
            data.last_watered = {
                key: found.at
                for key, found in last_waterings(
                    self._db, location_keys, tenant_key=tenant_key, now=datetime.now(UTC)
                ).items()
            }
        object_keys = [obj.key for obj in objects if obj.key]
        if include_tasks and object_keys:
            data.object_task_counters = self._object_task_counters(object_keys, tenant_key)
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
                COLLECT location = loc AGGREGATE open_count = COUNT(1), next_due = MIN(t.due_date),
                    overdue = SUM(t.due_date != null AND DATE_TIMESTAMP(t.due_date) < DATE_TIMESTAMP(@today_start)
                        ? 1 : 0)
                RETURN {location, open_count, overdue, next_due}
            """,
                bind_vars={
                    "@tasks": col.TASKS,
                    "tenant_key": tenant_key,
                    "open": list(_OPEN_TASK_STATUSES),
                    "plants": f"{col.PLANT_INSTANCES}/",
                    "location_keys": location_keys,
                    "today_start": start_of_utc_day(datetime.now(UTC)).isoformat(),
                },
            ),
        )
        return {
            row["location"]: TaskCounter(
                open_task_count=row["open_count"],
                overdue_task_count=int(row["overdue"] or 0),
                next_due_at=row["next_due"],
            )
            for row in cursor
        }

    def _object_task_counters(self, object_keys: list[str], tenant_key: str) -> dict[str, TaskCounter]:
        """Open tasks per garden object (compost, water source, storage — REQ-053 R-7.2), suggestions not counted."""
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR t IN @@tasks
                FILTER t.tenant_key == @tenant_key
                    AND t.status IN @open
                    AND t.suggested != true
                    AND t.entity_type == "garden_object"
                    AND t.entity_key IN @object_keys
                COLLECT object = t.entity_key AGGREGATE open_count = COUNT(1), next_due = MIN(t.due_date),
                    overdue = SUM(t.due_date != null AND DATE_TIMESTAMP(t.due_date) < DATE_TIMESTAMP(@today_start)
                        ? 1 : 0)
                RETURN {object, open_count, overdue, next_due}
            """,
                bind_vars={
                    "@tasks": col.TASKS,
                    "tenant_key": tenant_key,
                    "open": list(_OPEN_TASK_STATUSES),
                    "object_keys": object_keys,
                    "today_start": start_of_utc_day(datetime.now(UTC)).isoformat(),
                },
            ),
        )
        return {
            row["object"]: TaskCounter(
                open_task_count=row["open_count"],
                overdue_task_count=int(row["overdue"] or 0),
                next_due_at=row["next_due"],
            )
            for row in cursor
        }

    def load_slot_species_hints(self, location_key: str, *, tenant_key: str) -> list[SlotSpeciesHint]:
        if not tenant_key:
            raise ValueError("load_slot_species_hints needs a tenant_key (an empty tenant is no tenant, #2107).")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            LET l = DOCUMENT(CONCAT(@locations, @location_key))
            FILTER l != null
            LET site = DOCUMENT(CONCAT(@sites, l.site_key))
            FILTER site != null AND site.tenant_key == @tenant_key
            LET bed_slots = (
                FOR s IN @@slots FILTER s.location_key == @location_key AND s.archived_at == null RETURN s._key
            )
            LET slot_ids = (FOR k IN bed_slots RETURN CONCAT(@slots, k))
            LET from_plants = (
                FOR p IN @@plants
                    FILTER p.tenant_key == @tenant_key AND p.slot_key IN bed_slots AND p.removed_on == null
                    RETURN {slot_key: p.slot_key, species_key: p.species_key}
            )
            LET from_runs = (
                FOR e IN @@planned
                    FILTER e._to IN slot_ids AND e.planned_species_key != null
                        AND DOCUMENT(e._from).status IN @live_statuses
                    RETURN {slot_key: PARSE_IDENTIFIER(e._to).key, species_key: e.planned_species_key}
            )
            FOR r IN APPEND(from_plants, from_runs)
                LET sp = DOCUMENT(CONCAT(@species, r.species_key))
                FILTER sp != null
                RETURN {
                    slot_key: r.slot_key,
                    species_key: r.species_key,
                    spacing_cm: sp.spacing_cm,
                    row_spacing_cm: sp.row_spacing_cm,
                    mature_width_cm: sp.mature_width_cm,
                    growth_habit: sp.growth_habit
                }
            """,
                bind_vars={
                    "locations": f"{col.LOCATIONS}/",
                    "sites": f"{col.SITES}/",
                    "slots": f"{col.SLOTS}/",
                    "species": f"{col.SPECIES}/",
                    "@slots": col.SLOTS,
                    "@plants": col.PLANT_INSTANCES,
                    "@planned": col.RUN_PLANNED_AT,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                    "live_statuses": sorted(LIVE_RUN_STATUSES),
                },
            ),
        )
        return [SlotSpeciesHint(**row) for row in cursor]

    def load_active_slots(
        self, site_key: SiteKey, location_keys: list[str], *, tenant_key: str, include_archived: bool = False
    ) -> list[Slot]:
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
                    FILTER s.location_key == l._key AND (@include_archived OR s.archived_at == null)
                    RETURN s
            """,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "@slots": col.SLOTS,
                    "location_keys": location_keys,
                    "site_key": site_key,
                    "sites": f"{col.SITES}/",
                    "tenant_key": tenant_key,
                    "include_archived": include_archived,
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

    def locations_with_active_plants(self, location_keys: list[str], *, tenant_key: str) -> set[str]:
        if not tenant_key:
            raise ValueError("locations_with_active_plants needs a tenant_key (an empty tenant is no tenant, #2107).")
        if not location_keys:
            return set()
        # No ``tenant_key`` filter, like ``count_active_plants``: the keys come from the site's owned structure and a
        # plant whose own stamp is missing or wrong must still keep its bed from being deleted (V-09).
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@col
                FILTER p.removed_on == null AND p.location_key IN @location_keys
                RETURN DISTINCT p.location_key
            """,
                bind_vars={"@col": col.PLANT_INSTANCES, "location_keys": location_keys},
            ),
        )
        return set(cursor)

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

    def list_import_snapshots(
        self, site_key: SiteKey, *, tenant_key: str, offset: int, limit: int
    ) -> list[PlanSnapshotEntry]:
        if not tenant_key:
            raise ValueError("list_import_snapshots needs a tenant_key (an empty tenant is no tenant, #2107).")
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
                FILTER a.site_key == @site_key AND a.tenant_key == @tenant_key AND a.op == "import_snapshot"
                    AND a.snapshot != null
                SORT a.revision DESC, DATE_TIMESTAMP(a.at) DESC, a._key DESC
                LIMIT @offset, @limit
                RETURN {
                    audit_key: a._key, revision: a.revision, summary: a.summary, at: a.at,
                    changed_by_name: a.user_key == null ? null : DOCUMENT(CONCAT(@users, a.user_key)).display_name,
                    locations: LENGTH(a.snapshot.locations || []),
                    garden_objects: LENGTH(a.snapshot.garden_objects || []),
                    slots: LENGTH(a.snapshot.slots || []),
                    zones: LENGTH(a.snapshot.zones || [])
                }
            """,
                bind_vars=bind_vars,
            ),
        )
        return [PlanSnapshotEntry(**row) for row in cursor]

    def load_import_snapshot(self, site_key: SiteKey, audit_key: str, *, tenant_key: str) -> dict[str, Any] | None:
        if not tenant_key:
            raise ValueError("load_import_snapshot needs a tenant_key (an empty tenant is no tenant, #2107).")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR a IN @@col
                FILTER a._key == @audit_key AND a.site_key == @site_key AND a.tenant_key == @tenant_key
                    AND a.op == "import_snapshot" AND a.snapshot != null
                LIMIT 1
                RETURN a.snapshot
            """,
                bind_vars={
                    "@col": col.GARDEN_PLAN_AUDIT,
                    "audit_key": audit_key,
                    "site_key": site_key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        rows = list(cursor)
        return rows[0] if rows else None

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

                # A bed that is retired holds no plant either (V-09); re-checked here for the same reason as below.
                self._refuse_changed_status(txn, write.status_from)
                self._refuse_active_plants(
                    txn, [key for key, fields in write.location_updates if fields.get("bed_status") == "retired"]
                )
                self._delete_locations(txn, write)
                txn.check_budget()
                self._delete_objects(txn, write)
                self._delete_zones(txn, write)
                self._insert_zones(txn, write, key_map, now)
                self._insert_locations(txn, write, key_map, now)
                self._insert_slots(txn, write, key_map, now)
                self._update_locations(txn, write, now)
                self._insert_objects(txn, write, key_map, now)
                self._link_zone_water_sources(txn, write, key_map, now)
                self._update_objects(txn, write, now)
                txn.check_budget()
                self._write_site(txn, write, stored_plan, new_revision, now)
                self._write_audit(txn, write, new_revision, now)
                self._write_care_events(txn, write, now)
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
        self._refuse_active_plants(txn, keys)
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
    def _refuse_changed_status(txn: StreamTransaction, status_from: dict[str, str]) -> None:
        """V-10 inside the transaction: the bed still has the status the transition was validated from."""
        if not status_from:
            return
        rows = list(
            txn.aql.execute(
                'FOR l IN @@col FILTER l._key IN @keys RETURN {key: l._key, status: l.bed_status || "active"}',
                bind_vars={"@col": col.LOCATIONS, "keys": sorted(status_from)},
            )
        )
        stored = {row["key"]: row["status"] for row in rows}
        for key, expected in status_from.items():
            if key not in stored:
                raise NotFoundError("Location", key)
            if stored[key] != expected:
                raise PlanError(
                    "bed_status.changed",
                    "The bed status was changed by someone else; reload and try again.",
                    status_code=409,
                    field="bed_status",
                    current=stored[key],
                )

    @staticmethod
    def _refuse_active_plants(txn: StreamTransaction, keys: list[str]) -> None:
        """V-09 inside the transaction: a plant placed after the service's read must not be orphaned."""
        if not keys:
            return
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
                "A location with active plants cannot be deleted or retired.",
                status_code=409,
                active_plant_count=int(active),
            )

    @staticmethod
    def _remove_edges(txn: StreamTransaction, edge_collection: str, field: str, ids: list[str]) -> None:
        # ``field`` is one of two literals chosen above — never a request value — so it is
        # interpolated; the collection and the ids are bound.
        txn.aql.execute(
            f"FOR e IN @@edges FILTER e.{aql_field(field)} IN @ids REMOVE e IN @@edges",
            bind_vars={"@edges": edge_collection, "ids": ids},
        )

    def _delete_objects(self, txn: StreamTransaction, write: PlanBatchWrite) -> None:
        keys = write.object_deletes
        if not keys:
            return
        ids = [f"{col.GARDEN_OBJECTS}/{key}" for key in keys]
        for edge, field in _OBJECT_EDGES:
            self._remove_edges(txn, edge, field, ids)
        # The edge cascade above cut ``zone_supplied_by``; the zone's own ``water_source_key`` goes with it, so a
        # zone never names a water source that is gone (REQ-053 §20.11, WP 7.1).
        txn.aql.execute(
            """
            FOR z IN @@zones
                FILTER z.tenant_key == @tenant_key AND z.site_key == @site_key AND z.water_source_key IN @keys
                UPDATE z WITH { water_source_key: null, updated_at: @now } IN @@zones OPTIONS { keepNull: false }
            """,
            bind_vars={
                "@zones": col.IRRIGATION_ZONES,
                "tenant_key": write.tenant_key,
                "site_key": write.site_key,
                "keys": keys,
                "now": _now(),
            },
        )
        txn.aql.execute(
            "FOR o IN @@col FILTER o._key IN @keys REMOVE o IN @@col",
            bind_vars={"@col": col.GARDEN_OBJECTS, "keys": keys},
        )

    @staticmethod
    def _delete_zones(txn: StreamTransaction, write: PlanBatchWrite) -> None:
        """The zones a ``replace`` import removes (WP 7.2): the document and every edge on it.

        Under the write's tenant and site only. The service chose zones that cover no bed that stays; a bed that
        stays and was assigned to one meanwhile (``zone_covers`` survives the location delete above) makes this
        a conflict instead of a bed that names a zone that is gone.
        """
        keys = write.zone_deletes
        if not keys:
            return
        ids = [f"{col.IRRIGATION_ZONES}/{key}" for key in keys]
        still_covering = list(
            txn.aql.execute(
                "FOR e IN @@covers FILTER e._from IN @ids LIMIT 1 RETURN 1",
                bind_vars={"@covers": col.ZONE_COVERS, "ids": ids},
            )
        )
        if still_covering:
            raise WriteConflictError("garden_plan", "a bed was assigned to a zone of the replaced plan concurrently")
        for edge, field in ZONE_EDGES:
            ArangoGardenPlanRepository._remove_edges(txn, edge, field, ids)
        txn.aql.execute(
            """
            FOR z IN @@zones
                FILTER z._key IN @keys AND z.tenant_key == @tenant_key AND z.site_key == @site_key
                REMOVE z IN @@zones
            """,
            bind_vars={
                "@zones": col.IRRIGATION_ZONES,
                "keys": keys,
                "tenant_key": write.tenant_key,
                "site_key": write.site_key,
            },
        )

    @staticmethod
    def _insert_zones(txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str) -> None:
        """The zones of an import, under the write's tenant and site, with their ``has_irrigation_zone`` edge.

        The water source is linked after the objects exist (:meth:`_link_zone_water_sources`); the technical
        coupling is never part of an import (GP-FR-141), so the stored coupling fields keep their defaults.
        """
        if not write.zone_inserts:
            return
        zones = txn.collection(col.IRRIGATION_ZONES)
        has_zone = txn.collection(col.HAS_IRRIGATION_ZONE)
        for temp_key, zone in write.zone_inserts:
            doc = _dump(zone, by_alias=True, exclude_none=True, mode="json")
            for name in ("_key", "water_source_key", "actuator_key", "flow_rate_ha_entity_id"):
                doc.pop(name, None)
            doc["flow_rate_source"] = "manual"
            doc["tenant_key"] = write.tenant_key
            doc["site_key"] = write.site_key
            doc["created_at"] = doc["updated_at"] = now
            key = zones.insert(doc, return_new=False)["_key"]
            key_map[temp_key] = key
            has_zone.insert(
                {"_from": f"{col.SITES}/{write.site_key}", "_to": f"{col.IRRIGATION_ZONES}/{key}", "created_at": now}
            )
            txn.check_budget()

    @staticmethod
    def _link_zone_water_sources(
        txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str
    ) -> None:
        """Point each imported zone at the water source it names in the file (a temp key of this write)."""
        for temp_key, zone in write.zone_inserts:
            source = key_map.get(zone.water_source_key or "")
            if source is None:
                continue
            zone_key = key_map[temp_key]
            txn.aql.execute(
                "UPDATE @key WITH { water_source_key: @source } IN @@zones",
                bind_vars={"@zones": col.IRRIGATION_ZONES, "key": zone_key, "source": source},
            )
            txn.collection(col.ZONE_SUPPLIED_BY).insert(
                {
                    "_from": f"{col.IRRIGATION_ZONES}/{zone_key}",
                    "_to": f"{col.GARDEN_OBJECTS}/{source}",
                    "created_at": now,
                }
            )

    def _insert_locations(
        self, txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str
    ) -> None:
        collection = txn.collection(col.LOCATIONS)
        contains = txn.collection(col.CONTAINS)
        self._take_import_zones(txn, write, key_map, now)
        for temp_key, location in write.location_inserts:
            doc = _insert_doc(location)
            parent = doc.get("parent_location_key")
            if parent in key_map:
                parent = doc["parent_location_key"] = key_map[parent]
            doc["site_key"] = write.site_key
            if doc.get("irrigation_zone_key") in key_map:  # a zone of this write: its temp key becomes the real one
                doc["irrigation_zone_key"] = key_map[doc["irrigation_zone_key"]]
            doc["created_at"] = doc["updated_at"] = now
            created = collection.insert(doc, return_new=True)
            key = created["_key"]
            key_map[temp_key] = key
            origin = f"{col.LOCATIONS}/{parent}" if parent else f"{col.SITES}/{write.site_key}"
            contains.insert({"_from": origin, "_to": f"{col.LOCATIONS}/{key}", "created_at": now})
            zone_key = doc.get("irrigation_zone_key")
            if zone_key:
                # The import keeps a zone of this site, taken above in this transaction; the edge follows the field.
                txn.collection(col.ZONE_COVERS).insert(
                    {"_from": f"{col.IRRIGATION_ZONES}/{zone_key}", "_to": f"{col.LOCATIONS}/{key}", "created_at": now}
                )
            txn.check_budget()

    @staticmethod
    def _take_import_zones(txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str) -> None:
        """Take every zone the inserted beds name, inside the transaction and under the write's tenant and site.

        The import service resolved the zones before the transaction (GP-NFR-058); a zone deleted since then — or a
        delete running right now, which holds the zone's document — must not leave a bed naming it and an edge on a
        zone that is gone. The ``UPDATE`` makes a concurrent ``delete_zone`` conflict; a zone that vanished is a 409.
        """
        zone_keys = sorted(
            {
                str(location.irrigation_zone_key)
                for _, location in write.location_inserts
                if location.irrigation_zone_key and location.irrigation_zone_key not in key_map
            }
        )
        if not zone_keys:
            return
        taken = list(
            txn.aql.execute(
                """
            FOR z IN @@zones
                FILTER z._key IN @keys AND z.tenant_key == @tenant_key AND z.site_key == @site_key
                UPDATE z WITH { updated_at: @now } IN @@zones
                RETURN NEW._key
            """,
                bind_vars={
                    "@zones": col.IRRIGATION_ZONES,
                    "keys": zone_keys,
                    "tenant_key": write.tenant_key,
                    "site_key": write.site_key,
                    "now": now,
                },
            )
        )
        if len(taken) != len(zone_keys):
            raise WriteConflictError("garden_plan", "an irrigation zone of the imported plan was removed concurrently")

    @staticmethod
    def _insert_slots(txn: StreamTransaction, write: PlanBatchWrite, key_map: dict[str, str], now: str) -> None:
        """Slots of the locations this write inserted (the plan import): two bulk inserts, not 8 000 round trips."""
        if not write.slot_inserts:
            return
        docs: list[dict[str, Any]] = []
        for location_key, slot in write.slot_inserts:
            doc = _dump(slot, by_alias=True, exclude_none=True, mode="json")
            doc.pop("_key", None)
            doc["location_key"] = key_map[location_key]
            doc["created_at"] = doc["updated_at"] = now
            docs.append(doc)
        created = txn.collection(col.SLOTS).insert_many(docs, return_new=False)
        txn.check_budget()
        txn.collection(col.HAS_SLOT).insert_many(
            [
                {
                    "_from": f"{col.LOCATIONS}/{doc['location_key']}",
                    "_to": f"{col.SLOTS}/{meta['_key']}",
                    "created_at": now,
                }
                for doc, meta in zip(docs, created, strict=True)
            ]
        )
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

    @staticmethod
    def _write_care_events(txn: StreamTransaction, write: PlanBatchWrite, now: str) -> None:
        """The care events of the write (a bed-status change), each with its ``care_event_at`` edge to the bed."""
        if not write.care_events:
            return
        for event in write.care_events:
            write_care_event(txn, event, now)

    def _write_audit(self, txn: StreamTransaction, write: PlanBatchWrite, revision: int, now: str) -> None:
        audit = txn.collection(col.GARDEN_PLAN_AUDIT)
        if write.snapshot is not None:
            snapshot = PlanAuditRecord(
                tenant_key=write.tenant_key,
                site_key=write.site_key,
                revision=revision,
                user_key=write.editor_key,
                op="import_snapshot",
                entity="site",
                key=write.site_key,
                summary=write.snapshot_summary,
                at=datetime.fromisoformat(now),
                snapshot=write.snapshot,
            )
            audit.insert(_dump(snapshot, mode="json"))
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

    def purge_audit_before(self, cutoff: datetime, *, batch: int) -> int:
        """Hard-delete up to ``batch`` audit rows with ``at`` before ``cutoff`` (NFR-011 R-26, REQ-053 GP-NFR-055).

        A row whose ``at`` cannot be read as an instant is never selected (``DATE_TIMESTAMP`` of it is ``null``,
        which would order below every cutoff).
        """
        bind_vars: dict[str, Any] = {
            "@audit": col.GARDEN_PLAN_AUDIT,
            "cutoff": cutoff.astimezone(UTC).isoformat(),
            "batch": batch,
        }
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR a IN @@audit
                LET at = DATE_TIMESTAMP(a.at)
                FILTER at != null AND at < DATE_TIMESTAMP(@cutoff)
                LIMIT @batch
                REMOVE a IN @@audit
                RETURN 1
            """,
                bind_vars=bind_vars,
            ),
        )
        return sum(1 for _ in cursor)

    # ── Single resources (WP 1.9) ─────────────────────────────────────

    def load_bed_counters(self, location_keys: list[str], *, tenant_key: str) -> dict[str, BedCounters]:
        if not tenant_key:
            raise ValueError("load_bed_counters needs a tenant_key (an empty tenant is no tenant, #2107).")
        rows: dict[str, dict[str, Any]] = {}
        if not location_keys:
            return {}
        plants = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@plants
                FILTER p.tenant_key == @tenant_key AND p.location_key IN @location_keys AND p.removed_on == null
                COLLECT location = p.location_key INTO species = p.species_key
                RETURN {location, count: LENGTH(species), species: UNIQUE(species)}
            """,
                bind_vars={"@plants": col.PLANT_INSTANCES, "tenant_key": tenant_key, "location_keys": location_keys},
            ),
        )
        for row in plants:
            rows[row["location"]] = {
                "active_plant_count": row["count"],
                "species_keys": sorted(k for k in row["species"] if k),
            }
        for location, counter in self._task_counters(location_keys, tenant_key).items():
            rows[location] = {
                **rows.get(location, {}),
                "open_task_count": counter.open_task_count,
                "overdue_task_count": counter.overdue_task_count,
                "next_due_at": counter.next_due_at,
            }
        events = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR e IN @@events
                FILTER e.tenant_key == @tenant_key AND e.location_key IN @location_keys AND e.voided_at == null
                COLLECT location = e.location_key AGGREGATE last = MAX(e.performed_at)
                RETURN {location, last}
            """,
                bind_vars={"@events": col.CARE_EVENTS, "tenant_key": tenant_key, "location_keys": location_keys},
            ),
        )
        for row in events:
            rows[row["location"]] = {**rows.get(row["location"], {}), "last_care_at": row["last"]}
        # Validated here, so the stored ISO strings reach the caller as datetimes.
        return {location: BedCounters.model_validate(values) for location, values in rows.items()}

    def count_active_slots(self, site_key: SiteKey, *, tenant_key: str) -> int:
        if not tenant_key:
            raise ValueError("count_active_slots needs a tenant_key (an empty tenant is no tenant, #2107).")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            RETURN LENGTH(
                FOR l IN @@locations
                    FILTER l.site_key == @site_key
                    {_OWNED_BY_LOCATION_SITE}
                    FOR s IN @@slots
                        FILTER s.location_key == l._key AND s.archived_at == null
                        RETURN 1
            )
            """,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "@slots": col.SLOTS,
                    "site_key": site_key,
                    "sites": f"{col.SITES}/",
                    "tenant_key": tenant_key,
                },
            ),
        )
        return int(next(cursor, 0))

    def update_location_fields(self, location_key: str, fields: dict[str, Any]) -> None:
        if "irrigation_zone_key" in fields:
            self._update_location_fields_with_zone(location_key, fields)
            return
        try:
            self._db.collection(col.LOCATIONS).update(
                {"_key": location_key, **fields, "updated_at": _now()}, merge=False, keep_none=False
            )
        except DocumentUpdateError as exc:
            if exc.error_code == 1202:  # document not found: removed after the service read it
                raise NotFoundError("Location", location_key) from exc
            raise

    def set_site_underlay(
        self, site_key: SiteKey, *, tenant_key: str, underlay: SiteUnderlay | None
    ) -> tuple[bool, str | None]:
        if not tenant_key:
            raise ValueError("set_site_underlay needs a tenant_key (an empty tenant is no tenant, #2107).")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            LET site = DOCUMENT(CONCAT(@sites, @site_key))
            FILTER site != null AND site.tenant_key == @tenant_key AND site.plan != null
            LET previous = site.plan.underlay.attachment_key
            UPDATE site WITH { plan: { underlay: @underlay }, updated_at: @now } IN @@site_collection
                OPTIONS { mergeObjects: true, keepNull: false }
            RETURN { previous: previous }
            """,
                bind_vars={
                    "sites": f"{col.SITES}/",
                    "@site_collection": col.SITES,
                    "site_key": site_key,
                    "tenant_key": tenant_key,
                    "underlay": _dump(underlay, mode="json") if underlay is not None else None,
                    "now": _now(),
                },
            ),
        )
        row = next(cursor, None)
        if row is None:
            return False, None
        return True, row["previous"]

    def _update_location_fields_with_zone(self, location_key: str, fields: dict[str, Any]) -> None:
        """The column write of a PATCH that changes the bed's zone, with its ``zone_covers`` edge (WP 7.1).

        One transaction: the new zone's document is taken first (a zone deleted after the service resolved it is
        422 ``reference.not_found``, a zone being deleted right now conflicts), then the bed's columns, then the
        edge — the bed's old edge is removed whichever zone held it, so a bed stays in at most one zone.

        The zone is taken **under the bed's own site and that site's tenant** (read from the stored bed inside the
        transaction): the method takes no tenant (a location carries none, E-01), so the predicate is the bed's
        anchor — a zone of another site or another tenant is ``reference.not_found`` and nothing is written.
        """
        zone_key = fields["irrigation_zone_key"]
        location_id = f"{col.LOCATIONS}/{location_key}"
        now = _now()
        with stream_transaction(
            self._db,
            write=(col.IRRIGATION_ZONES, col.LOCATIONS, col.ZONE_COVERS),
            read=(col.SITES,),
            entity="location",
        ) as txn:
            if zone_key:
                taken = list(
                    txn.aql.execute(
                        """
                    LET bed = DOCUMENT(CONCAT(@locations, @location_key))
                    LET site = bed == null ? null : DOCUMENT(CONCAT(@sites, bed.site_key))
                    FOR z IN @@zones
                        FILTER site != null AND z._key == @key
                            AND z.site_key == bed.site_key AND z.tenant_key == site.tenant_key
                        UPDATE z WITH { updated_at: @now } IN @@zones
                        RETURN 1
                    """,
                        bind_vars={
                            "@zones": col.IRRIGATION_ZONES,
                            "locations": f"{col.LOCATIONS}/",
                            "sites": f"{col.SITES}/",
                            "location_key": location_key,
                            "key": zone_key,
                            "now": now,
                        },
                    )
                )
                if not taken:
                    raise PlanValidationError([(None, "irrigation_zone_key", ERROR_REFERENCE_NOT_FOUND, {})])
            try:
                txn.collection(col.LOCATIONS).update(
                    {"_key": location_key, **fields, "updated_at": now}, merge=False, keep_none=False
                )
            except DocumentUpdateError as exc:
                if exc.error_code == 1202:  # document not found: removed after the service read it
                    raise NotFoundError("Location", location_key) from exc
                raise
            self._remove_edges(txn, col.ZONE_COVERS, "_to", [location_id])
            if zone_key:
                txn.collection(col.ZONE_COVERS).insert(
                    {"_from": f"{col.IRRIGATION_ZONES}/{zone_key}", "_to": location_id, "created_at": now}
                )

    def update_slot_fields(self, slot_key: str, fields: dict[str, Any]) -> None:
        try:
            self._db.collection(col.SLOTS).update(
                {"_key": slot_key, **fields, "updated_at": _now()}, merge=False, keep_none=False
            )
        except DocumentUpdateError as exc:
            if exc.error_code == 1202:  # document not found: removed after the service read it
                raise NotFoundError("Slot", slot_key) from exc
            raise

    def irrigation_zone_site_key(self, zone_key: str, *, tenant_key: str) -> str | None:
        if not tenant_key:
            raise ValueError("irrigation_zone_site_key needs a tenant_key (an empty tenant is no tenant, #2107).")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            LET zone = DOCUMENT(CONCAT(@zones, @key))
            FILTER zone != null AND zone.tenant_key == @tenant_key
            RETURN zone.site_key
            """,
                bind_vars={"zones": f"{col.IRRIGATION_ZONES}/", "key": zone_key, "tenant_key": tenant_key},
            ),
        )
        return next(cursor, None)

    def substrate_visible(self, substrate_key: str, *, tenant_key: str) -> bool:
        if not tenant_key:
            raise ValueError("substrate_visible needs a tenant_key (an empty tenant is no tenant, #2107).")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            LET substrate = DOCUMENT(CONCAT(@substrates, @key))
            RETURN substrate != null AND (substrate.tenant_key == null OR substrate.tenant_key IN ["", @tenant_key])
            """,
                bind_vars={"substrates": f"{col.SUBSTRATES}/", "key": substrate_key, "tenant_key": tenant_key},
            ),
        )
        return bool(next(cursor, False))

    def reserved_among(self, candidates: list[str], *, tenant_key: str) -> set[str]:
        if not tenant_key:
            raise ValueError("reserved_among needs a tenant_key (an empty tenant is no tenant, #2107).")
        if not candidates:
            return set()
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR e IN @@edges
                FILTER e._to IN @ids
                LET run = DOCUMENT(e._from)
                FILTER run != null AND run.tenant_key == @tenant_key
                RETURN DISTINCT PARSE_IDENTIFIER(e._to).key
            """,
                bind_vars={
                    "@edges": col.RUN_PLANNED_AT,
                    "ids": [f"{col.SLOTS}/{key}" for key in candidates],
                    "tenant_key": tenant_key,
                },
            ),
        )
        return set(cursor)

    def replace_slots(self, write: SlotBatchWrite) -> SlotBatchOutcome:
        created_keys: list[str] = []
        with stream_transaction(
            self._db,
            write=_SLOT_BATCH_WRITE,
            read=_SLOT_BATCH_READ,
            entity="slots",
            time_budget_seconds=write.time_budget_seconds,
        ) as txn:
            now = _now()
            self._lock_location(txn, write.location_key, now)
            self._remove_slots(txn, write.delete_keys)
            slots = txn.collection(col.SLOTS)
            edges = txn.collection(col.HAS_SLOT)
            for slot in write.inserts:
                doc = _dump(slot, by_alias=True, exclude_none=True, mode="json")
                doc.pop("_key", None)
                doc["location_key"] = write.location_key
                doc["created_at"] = doc["updated_at"] = now
                created = slots.insert(doc, return_new=True)
                created_keys.append(created["_key"])
                edges.insert(
                    {
                        "_from": f"{col.LOCATIONS}/{write.location_key}",
                        "_to": f"{col.SLOTS}/{created['_key']}",
                        "created_at": now,
                    }
                )
                txn.check_budget()
        return SlotBatchOutcome(created_keys=created_keys, deleted_count=len(write.delete_keys))

    @staticmethod
    def _lock_location(txn: StreamTransaction, location_key: str, now: str) -> None:
        """Write the bed's own document first, so two slot batches of one bed — or a slot batch and the delete of the
        bed — cannot both pass: the loser fails with the write-write conflict (409) instead of committing a layout
        that the winner's V-04/V-06 check never saw. A bed that is gone is a 404."""
        touched = list(
            txn.aql.execute(
                "FOR l IN @@col FILTER l._key == @key UPDATE l WITH {updated_at: @now} IN @@col RETURN 1",
                bind_vars={"@col": col.LOCATIONS, "key": location_key, "now": now},
            )
        )
        if not touched:
            raise NotFoundError("Location", location_key)

    def _remove_slots(self, txn: StreamTransaction, keys: list[str]) -> None:
        """Delete slots that are still unoccupied and unreserved — re-checked here, after the service's read."""
        if not keys:
            return
        ids = [f"{col.SLOTS}/{key}" for key in keys]
        taken = list(
            txn.aql.execute(
                """
            RETURN LENGTH(
                FOR s IN @@slots
                    FILTER s._key IN @keys AND (s.currently_occupied == true OR s.archived_at != null)
                    RETURN 1
            ) + LENGTH(FOR e IN @@reserved FILTER e._to IN @ids RETURN 1)
            """,
                bind_vars={"@slots": col.SLOTS, "keys": keys, "@reserved": col.RUN_PLANNED_AT, "ids": ids},
            )
        )[0]
        if taken:
            raise WriteConflictError("slots", "a slot to replace was occupied or reserved concurrently")
        for edge, field_name in _SLOT_EDGES:
            self._remove_edges(txn, edge, field_name, ids)
        txn.aql.execute(
            "FOR s IN @@slots FILTER s._key IN @keys REMOVE s IN @@slots",
            bind_vars={"@slots": col.SLOTS, "keys": keys},
        )
