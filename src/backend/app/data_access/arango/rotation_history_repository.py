"""ArangoDB read model of what stood in a bed (REQ-053 GP-FR-131, GP-FR-103; WP 3.4).

``locations`` and ``slots`` carry no ``tenant_key`` (E-01, #2107): the caller resolves the bed through the ownership
anchor first, and every query below still filters the *plants* and the *events* on ``@tenant_key`` — a plant or an
event of another tenant that happens to name this bed's key is never part of the answer.
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
                        plan_role: run != null AND run.plan_role != null ? run.plan_role : "main_crop"
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
        return [
            PlantedRow(
                plant_key=row["plant_key"],
                species_key=row["species_key"],
                planted_on=date.fromisoformat(row["planted_on"][:10]),
                removed_on=date.fromisoformat(row["removed_on"][:10]) if row.get("removed_on") else None,
                plan_role=row["plan_role"],
            )
            for row in cursor
            if row.get("planted_on") and row.get("species_key")
        ]

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
        rows: list[BackfillRow] = []
        for row in cursor:
            data: dict[str, Any] = row
            rows.append(
                BackfillRow(
                    event_key=data["event_key"],
                    performed_at=datetime.fromisoformat(data["performed_at"]),
                    entry=RotationEntry.model_validate(data["rotation_entry"]),
                    created_by=data.get("created_by"),
                )
            )
        return rows
