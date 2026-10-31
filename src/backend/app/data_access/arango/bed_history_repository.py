"""ArangoDB read model of the combined bed history (REQ-053 GP-API-038; WP 4.5, #2423).

The care events and the derived planting events are merged in one AQL ``UNION`` and cut with one ``LIMIT``, so a page
holds the 50 newest lines of both sources together. A bed has no ``tenant_key`` (#2107): the caller resolves it
through the ownership anchor first; plants, runs and events are filtered on ``@tenant_key`` here as well.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import PLANT_NAMES_AQL, plant_names_of
from app.domain.interfaces.bed_history_repository import (
    BedHistoryFilter,
    BedHistoryRow,
    IBedHistoryRepository,
    PlantingEvent,
    PlantingEventKind,
)
from app.domain.interfaces.care_event_repository import CareEventRow
from app.domain.models.care_event import CareEvent

#: The AQL of one page. ``@want_planting`` / ``@want_removal`` say which derived categories the filters leave in.
#: The ``care`` subquery projects only what the sort needs; the performer names and the plant names are resolved in
#: the outer loop *after* ``LIMIT``, so a page costs the lookups of its own lines, not of the bed's whole history
#: (#2514). A derived line has no ``x.care``: ``e`` is ``null`` there and every lookup short-circuits to nothing.
_HISTORY_AQL = """
LET bed_slots = (FOR s IN @@slots FILTER s.location_key == @location_key RETURN s._key)
LET plants = (
    FOR p IN @@plants
        FILTER p.tenant_key == @tenant_key
        FILTER p.slot_key IN bed_slots OR p.location_key == @location_key
        RETURN p
)
LET care = (
    FOR e IN @@events
        FILTER e.tenant_key == @tenant_key AND e.location_key == @location_key
        {care_filters}
        RETURN {{id: CONCAT("care:", e._key), ts: DATE_TIMESTAMP(e.performed_at), care: {{event: e}}}}
)
LET planted = @want_planting ? (
    FOR p IN plants
        FILTER @plant_key == null OR p._key == @plant_key
        FILTER p.planted_on != null {planted_window}
        RETURN {{
            id: CONCAT("plant_planted:", p._key),
            ts: DATE_TIMESTAMP(p.planted_on),
            planting: {{
                kind: "plant_planted", at: DATE_ISO8601(DATE_TIMESTAMP(p.planted_on)), category: "planting",
                plant_key: p._key, species_key: p.species_key,
                plant_name: p.plant_name != null ? p.plant_name : p.instance_id
            }}
        }}
) : []
LET removed = @want_removal ? (
    FOR p IN plants
        FILTER @plant_key == null OR p._key == @plant_key
        FILTER p.removed_on != null {removed_window}
        RETURN {{
            id: CONCAT("plant_removed:", p._key),
            ts: DATE_TIMESTAMP(p.removed_on),
            planting: {{
                kind: "plant_removed", at: DATE_ISO8601(DATE_TIMESTAMP(p.removed_on)), category: "removal",
                plant_key: p._key, species_key: p.species_key,
                plant_name: p.plant_name != null ? p.plant_name : p.instance_id,
                termination_type: p.termination_type
            }}
        }}
) : []
LET run_keys = (
    FOR p IN plants
        FOR r, e IN 1..1 INBOUND p._id @@run_contains
            FILTER e.detached_at == null
            RETURN DISTINCT r._key
)
LET runs = @plant_key == null ? (
    FOR r IN @@runs
        FILTER r.tenant_key == @tenant_key
        FILTER r.location_key == @location_key OR r._key IN run_keys
        RETURN r
) : []
LET started = @want_planting ? (
    FOR r IN runs
        FILTER r.started_at != null {started_window}
        RETURN {{
            id: CONCAT("run_started:", r._key),
            ts: DATE_TIMESTAMP(r.started_at),
            planting: {{
                kind: "run_started", at: r.started_at, category: "planting",
                run_key: r._key, run_name: r.name, run_status: r.status
            }}
        }}
) : []
LET completed = @want_removal ? (
    FOR r IN runs
        FILTER r.completed_at != null {completed_window}
        RETURN {{
            id: CONCAT("run_completed:", r._key),
            ts: DATE_TIMESTAMP(r.completed_at),
            planting: {{
                kind: "run_completed", at: r.completed_at, category: "removal",
                run_key: r._key, run_name: r.name, run_status: r.status
            }}
        }}
) : []
FOR x IN UNION(care, planted, removed, started, completed)
    SORT x.ts DESC, x.id DESC
    LIMIT @offset, @limit
    LET e = x.care.event
    LET by = e.performed_by_user_key == null ? null : DOCUMENT(CONCAT(@users, e.performed_by_user_key))
    LET for_user = e.performed_for_user_key == null ? null : DOCUMENT(CONCAT(@users, e.performed_for_user_key))
    {plant_names}
    RETURN x.care == null ? x : MERGE(x, {{
        care: {{
            event: e, performed_by_name: by.display_name, performed_for_name: for_user.display_name,
            plant_names: plant_names
        }}
    }})
"""


def _window(field: str, *, date_only: bool = False) -> str:
    """The ``from`` / ``to`` clauses over one timestamp field of a derived event.

    A date-only field (``planted_on``, ``removed_on``) is ordered at 00:00 UTC of its day, so the lower bound is
    cut to the start of *its* UTC day: a viewer west of UTC who picks "from 12 May" sends ``12 May 05:00Z`` and must
    still see a plant put in on 12 May. Day-level inclusive can show one day more at the edge, never one less.
    """
    lower = 'DATE_TRUNC(@performed_from, "day")' if date_only else "@performed_from"
    return (
        f"FILTER @performed_from == null OR DATE_TIMESTAMP({field}) >= DATE_TIMESTAMP({lower}) "
        f"FILTER @performed_to == null OR DATE_TIMESTAMP({field}) <= DATE_TIMESTAMP(@performed_to)"
    )


def _instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


class ArangoBedHistoryRepository(IBedHistoryRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _care_filters(criteria: BedHistoryFilter) -> str:
        clauses = []
        if criteria.category:
            clauses.append("e.category == @category")
        if criteria.plant_key:
            clauses.append("@plant_key IN e.plant_keys")
        if criteria.performed_by:
            clauses.append("e.performed_by_user_key == @performed_by")
        if not criteria.include_corrections:
            clauses.append('e.superseded_by_key == null AND e.category != "position_corrected"')
        clauses.append("(@performed_from == null OR DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@performed_from))")
        clauses.append("(@performed_to == null OR DATE_TIMESTAMP(e.performed_at) <= DATE_TIMESTAMP(@performed_to))")
        return "\n        ".join(f"FILTER {clause}" for clause in clauses)

    def list_history(
        self, location_key: str, criteria: BedHistoryFilter, *, tenant_key: str, offset: int, limit: int
    ) -> list[BedHistoryRow]:
        if not tenant_key:
            raise ValueError("list_history needs a tenant_key (an empty tenant is no tenant, #2107).")
        # A planting event has no performer: a person filter leaves the derived events out, and so does a
        # category the derived events do not belong to.
        derived = criteria.performed_by is None
        binds: dict[str, Any] = {
            "@slots": col.SLOTS,
            "@plants": col.PLANT_INSTANCES,
            "@events": col.CARE_EVENTS,
            "@runs": col.PLANTING_RUNS,
            "@run_contains": col.RUN_CONTAINS,
            "users": f"{col.USERS}/",
            "plants": f"{col.PLANT_INSTANCES}/",
            "location_key": location_key,
            "tenant_key": tenant_key,
            "plant_key": criteria.plant_key,
            "performed_from": criteria.performed_from.astimezone(UTC).isoformat() if criteria.performed_from else None,
            "performed_to": criteria.performed_to.astimezone(UTC).isoformat() if criteria.performed_to else None,
            "want_planting": derived and criteria.category in (None, "planting"),
            "want_removal": derived and criteria.category in (None, "removal"),
            "offset": offset,
            "limit": limit,
        }
        if criteria.category:
            binds["category"] = criteria.category
        if criteria.performed_by:
            binds["performed_by"] = criteria.performed_by
        query = _HISTORY_AQL.format(
            care_filters=self._care_filters(criteria),
            planted_window=_window("p.planted_on", date_only=True),
            removed_window=_window("p.removed_on", date_only=True),
            started_window=_window("r.started_at"),
            completed_window=_window("r.completed_at"),
            plant_names=PLANT_NAMES_AQL,
        )
        cursor = cast("Cursor", self._db.aql.execute(query, bind_vars=binds))
        return [self._row(row) for row in cursor]

    @staticmethod
    def _row(row: dict[str, Any]) -> BedHistoryRow:
        if "care" in row:
            care = row["care"]
            doc = dict(care["event"])
            doc["_key"] = doc.get("_key", doc.get("_id", "").split("/")[-1])
            event = CareEvent.model_validate(doc)
            return BedHistoryRow(
                at=event.performed_at,
                care=CareEventRow(
                    event=event,
                    performed_by_name=care.get("performed_by_name"),
                    performed_for_name=care.get("performed_for_name"),
                    plant_names=plant_names_of(care.get("plant_names")),
                ),
            )
        data = row["planting"]
        kind: PlantingEventKind = data["kind"]
        planting = PlantingEvent(
            kind=kind,
            at=_instant(data["at"]),
            category=data["category"],
            plant_key=data.get("plant_key"),
            species_key=data.get("species_key"),
            plant_name=data.get("plant_name"),
            termination_type=data.get("termination_type"),
            run_key=data.get("run_key"),
            run_name=data.get("run_name"),
            run_status=data.get("run_status"),
        )
        return BedHistoryRow(at=planting.at, planting=planting)
