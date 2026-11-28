"""ArangoDB read model of what stood in a bed (REQ-053 GP-FR-131, GP-FR-103; WP 3.4).

``locations`` and ``slots`` carry no ``tenant_key`` (E-01, #2107): the caller resolves the bed through the ownership
anchor first, and every query below still filters the *plants*, the *events* and the *runs* on ``@tenant_key`` — a
plant, an event or a run of another tenant that happens to name this bed's key is never part of the answer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.rotation_history_repository import (
    BackfillRow,
    IRotationHistoryRepository,
    PlannedRunRow,
    PlantedRow,
)
from app.domain.models.care_event import RotationEntry


class ArangoRotationHistoryRepository(IRotationHistoryRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _require_tenant(tenant_key: str, method: str) -> None:
        if not tenant_key:
            raise ValueError(f"{method} needs a tenant_key (an empty tenant is no tenant, #2107).")

    def list_plantings(self, location_key: str, *, since: date, tenant_key: str) -> list[PlantedRow]:
        self._require_tenant(tenant_key, "list_plantings")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
                LET bed_slots = (FOR s IN @@slots FILTER s.location_key == @location_key RETURN s._key)
                FOR p IN @@plants
                    FILTER p.tenant_key == @tenant_key
                    FILTER p.slot_key IN bed_slots OR p.location_key == @location_key
                    FILTER p.removed_on == null OR p.removed_on >= @since
                    LET run = FIRST(
                        FOR r, e IN 1..1 INBOUND p._id @@run_contains
                            FILTER e.detached_at == null
                            SORT r._key
                            LIMIT 1
                            RETURN r
                    )
                    RETURN {
                        plant_key: p._key,
                        species_key: p.species_key,
                        planted_on: p.planted_on,
                        removed_on: p.removed_on,
                        plan_role: run != null AND run.plan_role != null ? run.plan_role : "main_crop",
                        termination_type: p.termination_type,
                        termination_cause: p.termination_cause,
                        cultivar_key: p.cultivar_key,
                        failure_cause_class: p.failure_cause_class,
                        failure_pathogen: p.failure_pathogen,
                        failure_pathogen_confirmed: p.failure_pathogen_confirmed
                    }
                """,
                bind_vars={
                    "@slots": col.SLOTS,
                    "@plants": col.PLANT_INSTANCES,
                    "@run_contains": col.RUN_CONTAINS,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                    "since": since.isoformat(),
                },
            ),
        )
        return [_planted(row) for row in cursor if row["planted_on"] and row["species_key"]]

    def list_backfills(self, location_key: str, *, since: datetime, tenant_key: str) -> list[BackfillRow]:
        self._require_tenant(tenant_key, "list_backfills")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
                FOR e IN @@events
                    FILTER e.tenant_key == @tenant_key AND e.location_key == @location_key
                    FILTER e.category == "planting" AND e.trigger == "backfill"
                    FILTER e.voided_at == null AND e.superseded_by_key == null
                    FILTER e.rotation_entry != null
                    FILTER DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@since)
                    SORT DATE_TIMESTAMP(e.performed_at) DESC, e._key DESC
                    RETURN {
                        event_key: e._key,
                        performed_at: e.performed_at,
                        rotation_entry: e.rotation_entry,
                        created_by: e.created_by
                    }
                """,
                bind_vars={
                    "@events": col.CARE_EVENTS,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                    "since": since.isoformat(),
                },
            ),
        )
        return [_backfill(row) for row in cursor]

    def list_planned_runs(self, location_key: str, *, tenant_key: str) -> list[PlannedRunRow]:
        self._require_tenant(tenant_key, "list_planned_runs")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
                LET bed_slots = (FOR s IN @@slots FILTER s.location_key == @location_key RETURN s._id)
                LET by_edge = (
                    FOR e IN @@planned_at
                        FILTER e._to IN bed_slots
                        RETURN DISTINCT e._from
                )
                LET by_location = (
                    FOR r IN @@runs
                        FILTER r.location_key == @location_key AND r.status == "planned"
                        RETURN r._id
                )
                FOR run_id IN UNION_DISTINCT(by_edge, by_location)
                    LET r = DOCUMENT(run_id)
                    FILTER r != null AND r.tenant_key == @tenant_key AND r.status == "planned"
                    LET edges = (
                        FOR e IN @@planned_at
                            FILTER e._from == r._id AND e._to IN bed_slots
                            RETURN e
                    )
                    LET open_edge = LENGTH(edges[* FILTER CURRENT.planned_until == null]) > 0
                    LET species = (
                        FOR entry IN 1..1 OUTBOUND r._id @@has_entry
                            FILTER entry.species_key != null
                            SORT entry.species_key
                            RETURN DISTINCT entry.species_key
                    )
                    SORT r._key
                    RETURN {
                        run_key: r._key,
                        plan_role: r.plan_role != null ? r.plan_role : "main_crop",
                        species_keys: species,
                        planned_from: NOT_NULL(r.planned_from, MIN(edges[*].planned_from), r.planned_start_date),
                        planned_until: r.planned_until != null ? r.planned_until
                            : (open_edge ? null : MAX(edges[*].planned_until))
                    }
                """,
                bind_vars={
                    "@slots": col.SLOTS,
                    "@planned_at": col.RUN_PLANNED_AT,
                    "@runs": col.PLANTING_RUNS,
                    "@has_entry": col.HAS_ENTRY,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        return [_planned_run(row) for row in cursor if row["species_keys"]]


def _planned_run(row: dict[str, Any]) -> PlannedRunRow:
    start, end = row["planned_from"], row["planned_until"]
    return PlannedRunRow(
        run_key=row["run_key"],
        plan_role=row["plan_role"],
        species_keys=tuple(row["species_keys"]),
        planned_from=date.fromisoformat(start[:10]) if start else None,
        planned_until=date.fromisoformat(end[:10]) if end else None,
    )


def _planted(row: dict[str, Any]) -> PlantedRow:
    removed = row["removed_on"]
    return PlantedRow(
        plant_key=row["plant_key"],
        species_key=row["species_key"],
        planted_on=date.fromisoformat(row["planted_on"][:10]),
        removed_on=date.fromisoformat(removed[:10]) if removed else None,
        plan_role=row["plan_role"],
        termination_type=row.get("termination_type"),
        termination_cause=row.get("termination_cause"),
        cultivar_key=row.get("cultivar_key"),
        failure_cause_class=row.get("failure_cause_class"),
        failure_pathogen=row.get("failure_pathogen"),
        failure_pathogen_confirmed=row.get("failure_pathogen_confirmed"),
    )


def _backfill(row: dict[str, Any]) -> BackfillRow:
    return BackfillRow(
        event_key=row["event_key"],
        performed_at=datetime.fromisoformat(row["performed_at"]),
        entry=RotationEntry.model_validate(row["rotation_entry"]),
        created_by=row["created_by"],
    )
