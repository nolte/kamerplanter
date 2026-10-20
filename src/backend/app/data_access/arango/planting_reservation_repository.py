"""Reservations of slots by planting runs and the writes around them (REQ-053 WP 3.2, GP-FR-055/064–066).

``run_planned_at`` edges (planting_runs → slots) carry the time window of a reservation. A slot, a location
and an edge carry no ``tenant_key`` (E-01, #2107): every read below filters on the **run's** tenant inside
the statement, and the caller has resolved the bed through ``location_ownership`` before a key arrives.

**One lock per bed.** Every write below first updates the bed's own ``locations`` document. Two writers of
one bed (a layout, a reservation, a clearing, a quick planting, a slot batch) then serialise: the loser fails
with the write-write conflict (409) instead of committing a state the winner's V-06/V-08 check never saw.
The reservation re-check runs *after* the lock, inside the transaction (``verify``), so a reservation placed
between the service's read and this write cannot slip through.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase
from pydantic import BaseModel

from app.common.exceptions import NotFoundError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import CARE_EVENT_WRITE_COLLECTIONS, write_care_event
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.engines.slot_reservation_engine import (
    LIVE_RUN_STATUSES,
    STATE_PLANNED,
    ActivePlant,
    Reservation,
    intersects_year,
    plant_state,
)
from app.domain.interfaces.planting_reservation_repository import IPlantingReservationRepository
from app.domain.models.care_event import MAX_PLANTS_PER_EVENT
from app.domain.models.planting_reservation import (
    ClearBedOutcome,
    ClearBedWrite,
    MixedRunsOutcome,
    MixedRunsWrite,
    PlantingRow,
    QuickPlantOutcome,
    QuickPlantWrite,
    ReservationReads,
    ReservationWrite,
    RunSlotsWrite,
)

logger = structlog.get_logger()

#: Statuses of a run that has ended; its reservations are gone (GP-FR-066).
_ENDED_STATUSES = ("completed", "cancelled")
_LIVE_STATUSES = sorted(LIVE_RUN_STATUSES)


def _edges_touching(vertex_collection: str) -> tuple[tuple[str, str], ...]:
    """``(edge collection, "_from" | "_to")`` for every named-graph edge that can end at *vertex_collection*."""
    found: list[tuple[str, str]] = []
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        edge = str(definition["edge_collection"])
        if vertex_collection in definition["from_vertex_collections"]:
            found.append((edge, "_from"))
        if vertex_collection in definition["to_vertex_collections"]:
            found.append((edge, "_to"))
    return tuple(found)


_SLOT_EDGES = _edges_touching(col.SLOTS)

#: Collections the layout / reservation writes touch.
_RESERVATION_WRITE = (col.LOCATIONS, col.SLOTS, col.HAS_SLOT, col.RUN_PLANNED_AT)
_RESERVATION_READ = (col.PLANTING_RUNS, col.PLANT_INSTANCES, col.PLACED_IN, col.RUN_CONTAINS)
#: A deleted layout slot takes every edge a slot may carry with it.
_DROP_WRITE = tuple(
    dict.fromkeys((col.LOCATIONS, col.SLOTS, col.HAS_SLOT, col.RUN_PLANNED_AT, *(edge for edge, _ in _SLOT_EDGES)))
)
_DROP_READ = tuple(c for c in (col.PLACED_IN, col.PLANTING_RUNS) if c not in _DROP_WRITE)
_RELEASE_WRITE = (col.LOCATIONS, col.RUN_PLANNED_AT)
_RELEASE_READ = (col.SLOTS,)
_CLEAR_WRITE = (
    col.LOCATIONS,
    col.SLOTS,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.RUN_PLANNED_AT,
    *CARE_EVENT_WRITE_COLLECTIONS,
)
_CLEAR_READ = (col.PLACED_IN, col.RUN_CONTAINS, col.RUN_AT_LOCATION)
_MIXED_WRITE = (
    col.LOCATIONS,
    col.SLOTS,
    col.HAS_SLOT,
    col.PLANTING_RUNS,
    col.PLANTING_RUN_ENTRIES,
    col.RUN_AT_LOCATION,
    col.HAS_ENTRY,
    col.ENTRY_FOR_SPECIES,
    col.RUN_PLANNED_AT,
)
_QUICK_WRITE = (
    col.LOCATIONS,
    col.SLOTS,
    col.HAS_SLOT,
    col.PLANTING_RUNS,
    col.PLANTING_RUN_ENTRIES,
    col.RUN_AT_LOCATION,
    col.HAS_ENTRY,
    col.ENTRY_FOR_SPECIES,
    col.PLANT_INSTANCES,
    col.PLACED_IN,
    col.RUN_CONTAINS,
    col.PHASE_HISTORIES,
    col.PHASE_HISTORY_EDGE,
)

# ── Queries ──────────────────────────────────────────────────────────────────

#: The reservations on some slots, with the status of their run; the tenant is the run's.
_RESERVATIONS_FOR_SLOTS = """
FOR e IN @@edges
    FILTER e._to IN @ids
    LET run = DOCUMENT(e._from)
    FILTER run != null AND run.tenant_key == @tenant_key
    RETURN {
        slot_key: PARSE_IDENTIFIER(e._to).key,
        run_key: run._key,
        run_status: run.status,
        entry_key: e.entry_key,
        planned_species_key: e.planned_species_key,
        sequence: e.sequence,
        planned_from: e.planned_from,
        planned_until: e.planned_until
    }
"""

#: The reservations of one run, in the order ``create-plants`` consumes them.
_RESERVATIONS_OF_RUN = """
LET run = DOCUMENT(CONCAT(@runs, @run_key))
FILTER run != null AND run.tenant_key == @tenant_key
FOR e IN @@edges
    FILTER e._from == run._id
    SORT e.entry_key, e.sequence
    RETURN {
        slot_key: PARSE_IDENTIFIER(e._to).key,
        run_key: run._key,
        run_status: run.status,
        entry_key: e.entry_key,
        planned_species_key: e.planned_species_key,
        sequence: e.sequence,
        planned_from: e.planned_from,
        planned_until: e.planned_until
    }
"""

#: The plants standing in some slots, with the expected end of their run.
_ACTIVE_PLANTS_IN_SLOTS = """
FOR e IN @@placed_in
    FILTER e._to IN @ids
    LET plant = DOCUMENT(e._from)
    FILTER plant != null AND plant.tenant_key == @tenant_key AND plant.removed_on == null
    LET link = FIRST(FOR r IN @@run_contains FILTER r._to == e._from AND r.detached_at == null RETURN r)
    LET run = link == null ? null : DOCUMENT(link._from)
    RETURN {
        slot_key: PARSE_IDENTIFIER(e._to).key,
        plant_key: plant._key,
        run_key: run == null ? null : run._key,
        expected_end: run == null ? null : run.planned_until
    }
"""


def _date(value: Any) -> date | None:
    """An ISO date (or datetime) string of a stored document as a ``date``; anything else is ``None``."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def _insert_doc(model: BaseModel, now: str) -> dict[str, Any]:
    """A model as the document to insert: serialised by alias, ``_key`` left to the database, timestamps stamped."""
    data = _dump(model, by_alias=True, exclude_none=True, mode="json")
    data.pop("_key", None)
    data["created_at"] = data["updated_at"] = now
    return data


class _Reads:
    """The two V-08 reads, executed by ``aql`` — the database's, or an open transaction's for the re-check."""

    def __init__(self, aql: Any) -> None:
        self._aql = aql

    def reservations_for(self, slot_keys: list[str], *, tenant_key: str) -> list[Reservation]:
        if not tenant_key:
            raise ValueError("reservations_for needs a tenant_key (an empty tenant is no tenant, #2107).")
        if not slot_keys:
            return []
        rows = self._aql.execute(
            _RESERVATIONS_FOR_SLOTS,
            bind_vars={
                "@edges": col.RUN_PLANNED_AT,
                "ids": [f"{col.SLOTS}/{key}" for key in slot_keys],
                "tenant_key": tenant_key,
            },
        )
        return [_reservation(row) for row in rows]

    def active_plants_in(self, slot_keys: list[str], *, tenant_key: str) -> list[ActivePlant]:
        if not tenant_key:
            raise ValueError("active_plants_in needs a tenant_key (an empty tenant is no tenant, #2107).")
        if not slot_keys:
            return []
        rows = self._aql.execute(
            _ACTIVE_PLANTS_IN_SLOTS,
            bind_vars={
                "@placed_in": col.PLACED_IN,
                "@run_contains": col.RUN_CONTAINS,
                "ids": [f"{col.SLOTS}/{key}" for key in slot_keys],
                "tenant_key": tenant_key,
            },
        )
        return [
            ActivePlant(
                slot_key=row["slot_key"],
                plant_key=row["plant_key"],
                run_key=row["run_key"],
                expected_end=_date(row["expected_end"]),
            )
            for row in rows
        ]


def _reservation(row: dict[str, Any]) -> Reservation:
    return Reservation(
        slot_key=row["slot_key"],
        run_key=row["run_key"],
        entry_key=row.get("entry_key") or "",
        planned_species_key=row.get("planned_species_key") or "",
        sequence=int(row.get("sequence") or 0),
        planned_from=_date(row.get("planned_from")),
        planned_until=_date(row.get("planned_until")),
        run_status=row.get("run_status") or "planned",
    )


class ArangoPlantingReservationRepository(IPlantingReservationRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    # ── Reads ─────────────────────────────────────────────────────────

    def reservations_for(self, slot_keys: list[str], *, tenant_key: str) -> list[Reservation]:
        return _Reads(self._db.aql).reservations_for(slot_keys, tenant_key=tenant_key)

    def active_plants_in(self, slot_keys: list[str], *, tenant_key: str) -> list[ActivePlant]:
        return _Reads(self._db.aql).active_plants_in(slot_keys, tenant_key=tenant_key)

    def reservations_of_run(self, run_key: str, *, tenant_key: str) -> list[Reservation]:
        if not tenant_key:
            raise ValueError("reservations_of_run needs a tenant_key (an empty tenant is no tenant, #2107).")
        rows = cast(
            "Cursor",
            self._db.aql.execute(
                _RESERVATIONS_OF_RUN,
                bind_vars={
                    "@edges": col.RUN_PLANNED_AT,
                    "runs": f"{col.PLANTING_RUNS}/",
                    "run_key": run_key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        return [_reservation(row) for row in rows]

    def list_plantings(
        self, location_key: str, *, tenant_key: str, state: str | None, year: int | None
    ) -> list[PlantingRow]:
        if not tenant_key:
            raise ValueError("list_plantings needs a tenant_key (an empty tenant is no tenant, #2107).")
        plants = self._plant_rows(location_key, tenant_key)
        rows: list[PlantingRow] = []
        planted_pairs = {(row.run_key, row.slot_key) for row in plants if row.run_key and row.slot_key}
        for row in plants:
            if year is None or intersects_year(row.planted_on, row.removed_on, year):
                rows.append(row)
        for row in self._planned_rows(location_key, tenant_key):
            if (row.run_key, row.slot_key) in planted_pairs:
                continue  # consumed: the run planted this slot, the plant is the row
            if year is None or intersects_year(row.planned_from, row.planned_until, year):
                rows.append(row)
        if state is not None:
            rows = [row for row in rows if row.state == state]
        rows.sort(key=lambda r: (r.slot_id or "", r.sequence or 0, r.instance_id or ""))
        return rows

    def _planned_rows(self, location_key: str, tenant_key: str) -> list[PlantingRow]:
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR s IN @@slots
                FILTER s.location_key == @location_key AND s.archived_at == null
                FOR e IN @@edges
                    FILTER e._to == s._id
                    LET run = DOCUMENT(e._from)
                    FILTER run != null AND run.tenant_key == @tenant_key AND run.status IN @live
                    RETURN {
                        slot_key: s._key,
                        slot_id: s.slot_id,
                        run_key: run._key,
                        entry_key: e.entry_key,
                        species_key: e.planned_species_key,
                        sequence: e.sequence,
                        planned_from: e.planned_from,
                        planned_until: e.planned_until
                    }
            """,
                bind_vars={
                    "@slots": col.SLOTS,
                    "@edges": col.RUN_PLANNED_AT,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                    "live": _LIVE_STATUSES,
                },
            ),
        )
        return [
            PlantingRow(
                state=STATE_PLANNED,
                slot_key=row["slot_key"],
                slot_id=row["slot_id"],
                species_key=row.get("species_key") or "",
                run_key=row["run_key"],
                entry_key=row.get("entry_key"),
                sequence=row.get("sequence"),
                planned_from=_date(row.get("planned_from")),
                planned_until=_date(row.get("planned_until")),
            )
            for row in cursor
        ]

    def _plant_rows(self, location_key: str, tenant_key: str) -> list[PlantingRow]:
        """The bed's plants: those placed in its slots, and the unplaced ones that name the bed."""
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            LET placed = (
                FOR s IN @@slots
                    FILTER s.location_key == @location_key
                    FOR e IN @@placed_in
                        FILTER e._to == s._id
                        RETURN {plant: DOCUMENT(e._from), slot_key: s._key, slot_id: s.slot_id}
            )
            LET loose = (
                FOR plant IN @@plants
                    FILTER plant.location_key == @location_key AND plant.slot_key == null
                    RETURN {plant: plant, slot_key: null, slot_id: null}
            )
            FOR item IN APPEND(placed, loose)
                FILTER item.plant != null AND item.plant.tenant_key == @tenant_key
                LET link = FIRST(FOR r IN @@run_contains FILTER r._to == item.plant._id RETURN r)
                RETURN {
                    slot_key: item.slot_key,
                    slot_id: item.slot_id,
                    plant_key: item.plant._key,
                    instance_id: item.plant.instance_id,
                    species_key: item.plant.species_key,
                    cultivar_key: item.plant.cultivar_key,
                    planted_on: item.plant.planted_on,
                    removed_on: item.plant.removed_on,
                    termination_type: item.plant.termination_type,
                    run_key: link == null ? null : PARSE_IDENTIFIER(link._from).key
                }
            """,
                bind_vars={
                    "@slots": col.SLOTS,
                    "@placed_in": col.PLACED_IN,
                    "@plants": col.PLANT_INSTANCES,
                    "@run_contains": col.RUN_CONTAINS,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        rows: list[PlantingRow] = []
        for row in cursor:
            removed_on = _date(row.get("removed_on"))
            rows.append(
                PlantingRow(
                    state=plant_state(removed_on, row.get("termination_type")),
                    slot_key=row["slot_key"],
                    slot_id=row["slot_id"],
                    species_key=row["species_key"],
                    cultivar_key=row.get("cultivar_key"),
                    plant_key=row["plant_key"],
                    instance_id=row["instance_id"],
                    run_key=row["run_key"],
                    planted_on=_date(row.get("planted_on")),
                    removed_on=removed_on,
                    termination_type=row.get("termination_type"),
                )
            )
        return rows

    # ── Locking ───────────────────────────────────────────────────────

    @staticmethod
    def _lock_location(txn: StreamTransaction, location_key: str, now: str, *, must_exist: bool = True) -> None:
        """Write the bed's own document first: two writers of one bed cannot both pass (see the module docstring).

        ``must_exist=False`` for the writes that tidy up after a run (release, drop): a bed that is gone has
        nothing left to serialise with, and the tidying must still go through.
        """
        touched = list(
            txn.aql.execute(
                "FOR l IN @@col FILTER l._key == @key UPDATE l WITH {updated_at: @now} IN @@col RETURN 1",
                bind_vars={"@col": col.LOCATIONS, "key": location_key, "now": now},
            )
        )
        if not touched and must_exist:
            raise NotFoundError("Location", location_key)

    @staticmethod
    def _edge_doc(run_key: str, slot_key: str, now: str, **properties: Any) -> dict[str, Any]:
        return {
            "_from": f"{col.PLANTING_RUNS}/{run_key}",
            "_to": f"{col.SLOTS}/{slot_key}",
            "planned_at": now,
            "created_at": now,
            **properties,
        }

    # ── Writes ────────────────────────────────────────────────────────

    def place_run_layout(self, write: RunSlotsWrite) -> list[str]:
        created: list[str] = []
        with stream_transaction(
            self._db,
            write=_RESERVATION_WRITE,
            entity="planting_run_slots",
            time_budget_seconds=write.time_budget_seconds,
        ) as txn:
            now = _now()
            self._lock_location(txn, write.location_key, now)
            slots = txn.collection(col.SLOTS)
            has_slot = txn.collection(col.HAS_SLOT)
            planned_at = txn.collection(col.RUN_PLANNED_AT)
            for item in write.slots:
                doc = _insert_doc(item.slot, now)
                doc["location_key"] = write.location_key
                stored = slots.insert(doc, return_new=True)["new"]
                created.append(stored["_key"])
                has_slot.insert(
                    {
                        "_from": f"{col.LOCATIONS}/{write.location_key}",
                        "_to": f"{col.SLOTS}/{stored['_key']}",
                        "created_at": now,
                    }
                )
                planned_at.insert(
                    self._edge_doc(
                        write.run_key,
                        stored["_key"],
                        now,
                        entry_key=item.entry_key,
                        planned_species_key=item.planned_species_key,
                        sequence=item.sequence,
                        planned_from=write.planned_from.isoformat(),
                        planned_until=write.planned_until.isoformat() if write.planned_until else None,
                    )
                )
                txn.check_budget()
        return created

    def set_reservation(self, write: ReservationWrite, verify: Callable[[ReservationReads], None]) -> None:
        with stream_transaction(
            self._db,
            write=_RESERVATION_WRITE,
            read=_RESERVATION_READ,
            entity="planting_run_reservation",
            time_budget_seconds=write.time_budget_seconds,
        ) as txn:
            now = _now()
            self._lock_location(txn, write.location_key, now)
            self._require_usable_slots(txn, write.location_key, write.ordered_slot_keys)
            verify(_Reads(txn.aql))
            txn.aql.execute(
                "FOR e IN @@edges FILTER e._from == @run_id AND e.entry_key == @entry_key REMOVE e IN @@edges",
                bind_vars={
                    "@edges": col.RUN_PLANNED_AT,
                    "run_id": f"{col.PLANTING_RUNS}/{write.run_key}",
                    "entry_key": write.entry_key,
                },
            )
            edges = txn.collection(col.RUN_PLANNED_AT)
            for sequence, slot_key in enumerate(write.ordered_slot_keys, start=1):
                edges.insert(
                    self._edge_doc(
                        write.run_key,
                        slot_key,
                        now,
                        entry_key=write.entry_key,
                        planned_species_key=write.planned_species_key,
                        sequence=sequence,
                        planned_from=write.planned_from.isoformat(),
                        planned_until=write.planned_until.isoformat() if write.planned_until else None,
                    )
                )
                txn.check_budget()

    @staticmethod
    def _require_usable_slots(txn: StreamTransaction, location_key: str, slot_keys: list[str]) -> None:
        """Every slot still exists in the bed and is not history: a slot archived or removed after the read is a 409."""
        usable = list(
            txn.aql.execute(
                """
                FOR s IN @@slots
                    FILTER s._key IN @keys AND s.location_key == @location_key AND s.archived_at == null
                    RETURN s._key
                """,
                bind_vars={"@slots": col.SLOTS, "keys": slot_keys, "location_key": location_key},
            )
        )
        if len(set(usable)) != len(set(slot_keys)):
            raise WriteConflictError("slots", "a slot to reserve was removed or archived concurrently")

    def release_reservation(self, run_key: str, slot_key: str) -> bool:
        with stream_transaction(
            self._db, write=_RELEASE_WRITE, read=_RELEASE_READ, entity="planting_run_reservation"
        ) as txn:
            for location_key in txn.aql.execute(
                "RETURN DOCUMENT(CONCAT(@slots, @key)).location_key",
                bind_vars={"slots": f"{col.SLOTS}/", "key": slot_key},
            ):
                if location_key:
                    self._lock_location(txn, location_key, _now(), must_exist=False)
            removed = list(
                txn.aql.execute(
                    """
                    FOR e IN @@edges
                        FILTER e._from == @run_id AND e._to == @slot_id
                        REMOVE e IN @@edges
                        RETURN 1
                    """,
                    bind_vars={
                        "@edges": col.RUN_PLANNED_AT,
                        "run_id": f"{col.PLANTING_RUNS}/{run_key}",
                        "slot_id": f"{col.SLOTS}/{slot_key}",
                    },
                )
            )
        return bool(removed)

    def drop_run_reservations(self, run_key: str, *, remove_layout_slots: bool) -> int:
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        with stream_transaction(self._db, write=_DROP_WRITE, read=_DROP_READ, entity="planting_run_reservation") as txn:
            for location_key in txn.aql.execute(
                "RETURN DOCUMENT(CONCAT(@runs, @key)).location_key",
                bind_vars={"runs": f"{col.PLANTING_RUNS}/", "key": run_key},
            ):
                if location_key:
                    self._lock_location(txn, location_key, _now(), must_exist=False)
            slot_ids = list(
                txn.aql.execute(
                    "FOR e IN @@edges FILTER e._from == @run_id RETURN e._to",
                    bind_vars={"@edges": col.RUN_PLANNED_AT, "run_id": run_id},
                )
            )
            if not slot_ids:
                return 0
            txn.aql.execute(
                "FOR e IN @@edges FILTER e._from == @run_id REMOVE e IN @@edges",
                bind_vars={"@edges": col.RUN_PLANNED_AT, "run_id": run_id},
            )
            if remove_layout_slots:
                self._remove_orphan_layout_slots(txn, slot_ids)
        logger.info(
            "planting_reservation.run_reservations_dropped",
            run_key=run_key,
            edges=len(slot_ids),
            layout_slots_removed=remove_layout_slots,
        )
        return len(slot_ids)

    @staticmethod
    def _remove_orphan_layout_slots(txn: StreamTransaction, slot_ids: list[str]) -> None:
        """Delete the layout slots that nothing uses any more: unoccupied, unarchived, unreserved, no plant ever."""
        free = list(
            txn.aql.execute(
                """
                FOR s IN @@slots
                    FILTER s._id IN @ids AND s.geometry_source == 'layout'
                        AND s.currently_occupied != true AND s.archived_at == null
                    LET reserved = LENGTH(FOR e IN @@planned FILTER e._to == s._id LIMIT 1 RETURN 1)
                    LET planted = LENGTH(FOR p IN @@placed_in FILTER p._to == s._id LIMIT 1 RETURN 1)
                    FILTER reserved == 0 AND planted == 0
                    RETURN s._id
                """,
                bind_vars={
                    "@slots": col.SLOTS,
                    "@planned": col.RUN_PLANNED_AT,
                    "@placed_in": col.PLACED_IN,
                    "ids": slot_ids,
                },
            )
        )
        if not free:
            return
        for edge, field_name in _SLOT_EDGES:
            txn.aql.execute(
                f"FOR e IN @@edge FILTER e.{aql_field(field_name)} IN @ids REMOVE e IN @@edge",
                bind_vars={"@edge": edge, "ids": free},
            )
        txn.aql.execute(
            "FOR s IN @@slots FILTER s._id IN @ids REMOVE s IN @@slots",
            bind_vars={"@slots": col.SLOTS, "ids": free},
        )

    def clear_bed(self, write: ClearBedWrite) -> ClearBedOutcome:
        with stream_transaction(
            self._db,
            write=_CLEAR_WRITE,
            read=_CLEAR_READ,
            entity="bed_clearing",
            time_budget_seconds=write.time_budget_seconds,
        ) as txn:
            now = _now()
            self._lock_location(txn, write.location_key, now)
            plants = self._live_plants(txn, write.location_key, write.tenant_key)
            plant_ids = [p["id"] for p in plants]
            runs = self._runs_to_end(txn, write.location_key, write.tenant_key, plant_ids)
            end_status = "cancelled" if write.termination_type == "cancelled" else "completed"
            plant_updates = {"removed_on": write.removed_on.isoformat(), "termination_type": write.termination_type}
            txn.aql.execute(
                "FOR p IN @@plants FILTER p._id IN @ids UPDATE p WITH MERGE(@fields, {updated_at: @now}) IN @@plants",
                bind_vars={"@plants": col.PLANT_INSTANCES, "ids": plant_ids, "fields": plant_updates, "now": now},
            )
            run_ids = [r["id"] for r in runs]
            txn.aql.execute(
                "FOR r IN @@runs FILTER r._id IN @ids "
                "UPDATE r WITH {status: @status, completed_at: @now, updated_at: @now} IN @@runs",
                bind_vars={"@runs": col.PLANTING_RUNS, "ids": run_ids, "status": end_status, "now": now},
            )
            touched_slots = {p["slot_id"] for p in plants if p["slot_id"]} | set(
                txn.aql.execute(
                    "FOR e IN @@edges FILTER e._from IN @ids RETURN DISTINCT e._to",
                    bind_vars={"@edges": col.RUN_PLANNED_AT, "ids": run_ids},
                )
            )
            txn.aql.execute(
                "FOR e IN @@edges FILTER e._from IN @ids REMOVE e IN @@edges",
                bind_vars={"@edges": col.RUN_PLANNED_AT, "ids": run_ids},
            )
            archived, released = self._archive_or_release(txn, sorted(touched_slots), now)
            plant_keys = [p["key"] for p in plants]
            event = write.event.model_copy(update={"plant_keys": plant_keys[:MAX_PLANTS_PER_EVENT]})
            stored = write_care_event(txn, event, now)
        logger.info(
            "bed_clearing.done",
            location_key=write.location_key,
            plants=len(plant_keys),
            runs=len(run_ids),
            archived=archived,
            released=released,
        )
        return ClearBedOutcome(
            plants_removed=len(plant_keys),
            runs_completed=len(run_ids),
            slots_archived=archived,
            slots_released=released,
            care_event_key=stored["_key"],
            removed_plant_keys=plant_keys,
        )

    @staticmethod
    def _live_plants(txn: StreamTransaction, location_key: str, tenant_key: str) -> list[dict[str, Any]]:
        """The tenant's plants standing in the bed: placed in its slots, or naming the bed without a slot."""
        return list(
            txn.aql.execute(
                """
                LET placed = (
                    FOR s IN @@slots
                        FILTER s.location_key == @location_key
                        FOR e IN @@placed_in
                            FILTER e._to == s._id
                            RETURN {plant: DOCUMENT(e._from), slot_id: s._id}
                )
                LET loose = (
                    FOR plant IN @@plants
                        FILTER plant.location_key == @location_key AND plant.slot_key == null
                        RETURN {plant: plant, slot_id: null}
                )
                FOR item IN APPEND(placed, loose)
                    FILTER item.plant != null AND item.plant.tenant_key == @tenant_key
                        AND item.plant.removed_on == null
                    RETURN DISTINCT {id: item.plant._id, key: item.plant._key, slot_id: item.slot_id}
                """,
                bind_vars={
                    "@slots": col.SLOTS,
                    "@placed_in": col.PLACED_IN,
                    "@plants": col.PLANT_INSTANCES,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                },
            )
        )

    @staticmethod
    def _runs_to_end(
        txn: StreamTransaction, location_key: str, tenant_key: str, plant_ids: list[str]
    ) -> list[dict[str, Any]]:
        """The tenant's active or harvesting runs of the bed: those that planted it and those placed at it."""
        return list(
            txn.aql.execute(
                """
                LET by_plant = (
                    FOR e IN @@run_contains FILTER e._to IN @plant_ids AND e.detached_at == null
                        RETURN DOCUMENT(e._from)
                )
                LET by_place = (
                    FOR e IN @@at_location FILTER e._to == @location_id RETURN DOCUMENT(e._from)
                )
                FOR run IN APPEND(by_plant, by_place)
                    FILTER run != null AND run.tenant_key == @tenant_key AND run.status IN ['active', 'harvesting']
                    LET standing_elsewhere = LENGTH(
                        FOR e IN @@run_contains
                            FILTER e._from == run._id AND e.detached_at == null AND e._to NOT IN @plant_ids
                            LET other = DOCUMENT(e._to)
                            FILTER other != null AND other.removed_on == null
                            LIMIT 1
                            RETURN 1
                    )
                    FILTER standing_elsewhere == 0
                    RETURN DISTINCT {id: run._id, key: run._key}
                """,
                bind_vars={
                    "@run_contains": col.RUN_CONTAINS,
                    "@at_location": col.RUN_AT_LOCATION,
                    "plant_ids": plant_ids,
                    "location_id": f"{col.LOCATIONS}/{location_key}",
                    "tenant_key": tenant_key,
                },
            )
        )

    @staticmethod
    def _archive_or_release(txn: StreamTransaction, slot_ids: list[str], now: str) -> tuple[int, int]:
        """Slots nothing live reserves any more become history; one a later planned run reserves is only freed."""
        if not slot_ids:
            return 0, 0
        still_reserved = set(
            txn.aql.execute(
                """
                FOR e IN @@edges
                    FILTER e._to IN @ids
                    LET run = DOCUMENT(e._from)
                    FILTER run != null AND run.status IN @live
                    RETURN DISTINCT e._to
                """,
                bind_vars={"@edges": col.RUN_PLANNED_AT, "ids": slot_ids, "live": _LIVE_STATUSES},
            )
        )
        archive = [s for s in slot_ids if s not in still_reserved]
        release = [s for s in slot_ids if s in still_reserved]
        if archive:
            txn.aql.execute(
                "FOR s IN @@slots FILTER s._id IN @ids "
                "UPDATE s WITH {currently_occupied: false, archived_at: @now, updated_at: @now} IN @@slots",
                bind_vars={"@slots": col.SLOTS, "ids": archive, "now": now},
            )
        if release:
            txn.aql.execute(
                "FOR s IN @@slots FILTER s._id IN @ids "
                "UPDATE s WITH {currently_occupied: false, updated_at: @now} IN @@slots",
                bind_vars={"@slots": col.SLOTS, "ids": release, "now": now},
            )
        return len(archive), len(release)

    def create_mixed_runs(self, write: MixedRunsWrite) -> MixedRunsOutcome:
        run_keys: list[str] = []
        slot_keys: list[str] = []
        with stream_transaction(
            self._db,
            write=_MIXED_WRITE,
            entity="mixed_culture_runs",
            time_budget_seconds=write.time_budget_seconds,
        ) as txn:
            now = _now()
            self._lock_location(txn, write.location_key, now)
            location_id = f"{col.LOCATIONS}/{write.location_key}"
            for item in write.runs:
                run_key = txn.collection(col.PLANTING_RUNS).insert(_insert_doc(item.run, now), return_new=True)["new"][
                    "_key"
                ]
                run_keys.append(run_key)
                run_id = f"{col.PLANTING_RUNS}/{run_key}"
                txn.collection(col.RUN_AT_LOCATION).insert({"_from": run_id, "_to": location_id, "created_at": now})
                entry_doc = _insert_doc(item.entry, now)
                entry_doc["run_key"] = run_key
                entry_key = txn.collection(col.PLANTING_RUN_ENTRIES).insert(entry_doc, return_new=True)["new"]["_key"]
                entry_id = f"{col.PLANTING_RUN_ENTRIES}/{entry_key}"
                txn.collection(col.HAS_ENTRY).insert({"_from": run_id, "_to": entry_id, "created_at": now})
                txn.collection(col.ENTRY_FOR_SPECIES).insert(
                    {"_from": entry_id, "_to": f"{col.SPECIES}/{item.entry.species_key}", "created_at": now}
                )
                for reserved in item.slots:
                    doc = _insert_doc(reserved.slot, now)
                    doc["location_key"] = write.location_key
                    stored = txn.collection(col.SLOTS).insert(doc, return_new=True)["new"]
                    slot_keys.append(stored["_key"])
                    txn.collection(col.HAS_SLOT).insert(
                        {"_from": location_id, "_to": f"{col.SLOTS}/{stored['_key']}", "created_at": now}
                    )
                    txn.collection(col.RUN_PLANNED_AT).insert(
                        self._edge_doc(
                            run_key,
                            stored["_key"],
                            now,
                            entry_key=entry_key,
                            planned_species_key=item.entry.species_key,
                            sequence=reserved.sequence,
                            planned_from=item.planned_from.isoformat(),
                            planned_until=item.planned_until.isoformat() if item.planned_until else None,
                        )
                    )
                    txn.check_budget()
                txn.check_budget()
        return MixedRunsOutcome(run_keys=run_keys, created_slot_keys=slot_keys)

    def quick_plant(self, write: QuickPlantWrite) -> QuickPlantOutcome:
        with stream_transaction(
            self._db,
            write=_QUICK_WRITE,
            entity="quick_planting",
            time_budget_seconds=write.time_budget_seconds,
        ) as txn:
            now = _now()
            self._lock_location(txn, write.location_key, now)
            location_id = f"{col.LOCATIONS}/{write.location_key}"

            slot_keys: list[str] = []
            slots = txn.collection(col.SLOTS)
            has_slot = txn.collection(col.HAS_SLOT)
            for slot in write.slots:
                doc = _insert_doc(slot, now)
                doc["location_key"] = write.location_key
                stored = slots.insert(doc, return_new=True)["new"]
                slot_keys.append(stored["_key"])
                has_slot.insert({"_from": location_id, "_to": f"{col.SLOTS}/{stored['_key']}", "created_at": now})
                txn.check_budget()

            run_doc = _insert_doc(write.run, now)
            run_key = txn.collection(col.PLANTING_RUNS).insert(run_doc, return_new=True)["new"]["_key"]
            run_id = f"{col.PLANTING_RUNS}/{run_key}"
            txn.collection(col.RUN_AT_LOCATION).insert({"_from": run_id, "_to": location_id, "created_at": now})

            entry_doc = _insert_doc(write.entry, now)
            entry_doc["run_key"] = run_key
            entry_key = txn.collection(col.PLANTING_RUN_ENTRIES).insert(entry_doc, return_new=True)["new"]["_key"]
            entry_id = f"{col.PLANTING_RUN_ENTRIES}/{entry_key}"
            txn.collection(col.HAS_ENTRY).insert({"_from": run_id, "_to": entry_id, "created_at": now})
            txn.collection(col.ENTRY_FOR_SPECIES).insert(
                {"_from": entry_id, "_to": f"{col.SPECIES}/{write.entry.species_key}", "created_at": now}
            )

            plant_keys = self._insert_plants(txn, write, run_id, slot_keys, now)
            if write.run_history is not None:
                self._insert_history(txn, write.run_history, run_key, now)
        return QuickPlantOutcome(
            run_key=run_key,
            entry_key=entry_key,
            created_slot_keys=slot_keys,
            plant_keys=plant_keys,
            created_at=datetime.fromisoformat(now),
        )

    def _insert_plants(
        self, txn: StreamTransaction, write: QuickPlantWrite, run_id: str, slot_keys: list[str], now: str
    ) -> list[str]:
        plants = txn.collection(col.PLANT_INSTANCES)
        placed_in = txn.collection(col.PLACED_IN)
        run_contains = txn.collection(col.RUN_CONTAINS)
        keys: list[str] = []
        for item in write.plants:
            slot_key = slot_keys[item.slot_index] if item.slot_index is not None else None
            doc = _insert_doc(item.plant, now)
            if slot_key is not None:
                doc["slot_key"] = slot_key
            stored = plants.insert(doc, return_new=True)["new"]
            plant_key = stored["_key"]
            keys.append(plant_key)
            plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
            if slot_key is not None:
                placed_in.insert({"_from": plant_id, "_to": f"{col.SLOTS}/{slot_key}", "created_at": now})
            run_contains.insert({"_from": run_id, "_to": plant_id, "created_at": now})
            if item.history is not None:
                self._insert_history(txn, item.history, plant_key, now)
            txn.check_budget()
        return keys

    @staticmethod
    def _insert_history(txn: StreamTransaction, history: BaseModel, owner_key: str, now: str) -> None:
        """A phase-history row and its ``phase_history_edge`` from ``plant_instances/<owner_key>``.

        The run-level row hangs off the *run's* key under the plant collection, exactly as
        ``PlantingRunService.create_plants`` writes it — the edge is how both are read back.
        """
        doc = _insert_doc(history, now)
        doc["plant_instance_key"] = owner_key
        stored = txn.collection(col.PHASE_HISTORIES).insert(doc, return_new=True)["new"]
        txn.collection(col.PHASE_HISTORY_EDGE).insert(
            {
                "_from": f"{col.PLANT_INSTANCES}/{owner_key}",
                "_to": f"{col.PHASE_HISTORIES}/{stored['_key']}",
                "created_at": now,
            }
        )
