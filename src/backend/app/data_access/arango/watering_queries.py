"""What was watered when: the read statements behind a zone's status and a bed's "last watered" (REQ-053 WP 7.3).

Two sources hold a watering (GP-FR-112): ``care_events`` with ``category = watering`` (a bed, the care log) and
``watering_events`` (plants or slots, REQ-013/014). A voided or superseded care event is not a watering. A
``watering_events`` row names slots; a slot names its bed.

**Bounded on purpose.** Every statement looks back :data:`LOOKBACK_DAYS` only, so a bed with years of events costs
what a year costs; "never watered" therefore reads "not within the last year". The tenant is a filter of every
statement; the location keys come from a zone or a plan the caller has resolved under the tenant already.

Shared by ``ArangoIrrigationZoneRepository`` (the status) and ``ArangoGardenPlanRepository`` (the read model),
which cannot import each other.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.models.irrigation_zone import LastWatering, NextPlannedWatering, ZoneWateringFacts

LOOKBACK_DAYS = 366
CONSUMPTION_DAYS = 30
WATERING_CATEGORY = "watering"
OPEN_TASK_STATUSES = ("pending", "in_progress")

_CARE_LAST = """
FOR location IN @location_keys
    LET top = FIRST(
        FOR e IN @@events
            FILTER e.tenant_key == @tenant_key AND e.location_key == location AND e.category == "watering"
                AND DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@since)
                AND e.voided_at == null AND e.superseded_by_key == null
            SORT DATE_TIMESTAMP(e.performed_at) DESC
            LIMIT 1
            RETURN e
    )
    FILTER top != null
    RETURN {location, at: top.performed_at, allocation: top.allocation || "measured"}
"""

_SLOT_LAST = """
FOR w IN @@watering
    FILTER w.tenant_key == @tenant_key AND DATE_TIMESTAMP(w.watered_at) >= DATE_TIMESTAMP(@since)
    FOR slot_key IN INTERSECTION(w.slot_keys, @slot_keys)
        COLLECT slot = slot_key AGGREGATE at = MAX(DATE_TIMESTAMP(w.watered_at))
        RETURN {slot, at}
"""


def _parse(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _rows(db: StandardDatabase, query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
    return list(cast("Cursor", db.aql.execute(query, bind_vars=bind_vars)))


def _slots_of(db: StandardDatabase, location_keys: list[str]) -> dict[str, str]:
    """slot key → bed key, for the beds named (the keys come from an owned zone or plan)."""
    rows = _rows(
        db,
        "FOR s IN @@slots FILTER s.location_key IN @location_keys RETURN {key: s._key, location: s.location_key}",
        {"@slots": col.SLOTS, "location_keys": location_keys},
    )
    return {row["key"]: row["location"] for row in rows}


def _since(now: datetime, days: int) -> str:
    return (now.astimezone(UTC) - timedelta(days=days)).isoformat()


def last_waterings(
    db: StandardDatabase, location_keys: list[str], *, tenant_key: str, now: datetime
) -> dict[str, LastWatering]:
    """The newest watering per bed, from both sources; a bed without one is absent."""
    if not location_keys:
        return {}
    since = _since(now, LOOKBACK_DAYS)
    found: dict[str, LastWatering] = {}
    for row in _rows(
        db,
        _CARE_LAST,
        {"@events": col.CARE_EVENTS, "tenant_key": tenant_key, "location_keys": location_keys, "since": since},
    ):
        moment = _parse(row["at"])
        if moment is not None:
            found[row["location"]] = LastWatering(
                at=moment, source="care_event", location_key=row["location"], allocation=row["allocation"]
            )
    slot_to_bed = _slots_of(db, location_keys)
    if slot_to_bed:
        for row in _rows(
            db,
            _SLOT_LAST,
            {
                "@watering": col.WATERING_EVENTS,
                "tenant_key": tenant_key,
                "slot_keys": list(slot_to_bed),
                "since": since,
            },
        ):
            moment = datetime.fromtimestamp(float(row["at"]) / 1000, UTC) if row["at"] is not None else None
            bed = slot_to_bed.get(row["slot"])
            if moment is not None and bed is not None and (bed not in found or moment > found[bed].at):
                found[bed] = LastWatering(at=moment, source="watering_event", location_key=bed, allocation="measured")
    return found


def _next_planned(db: StandardDatabase, location_keys: list[str], *, tenant_key: str) -> NextPlannedWatering | None:
    """The oldest open ``watering`` task of the beds (on the bed itself or on a plant standing in it)."""
    rows = _rows(
        db,
        """
        FOR t IN @@tasks
            FILTER t.tenant_key == @tenant_key AND t.status IN @open AND t.suggested != true
                AND t.category == "watering" AND t.entity_type IN ["location", "plant_instance"]
            LET loc = t.entity_type == "location"
                ? t.entity_key
                : DOCUMENT(CONCAT(@plants, t.entity_key)).location_key
            FILTER loc IN @location_keys
            SORT t.due_date == null ASC, DATE_TIMESTAMP(t.due_date) ASC, t._key ASC
            LIMIT 1
            RETURN {task_key: t._key, location: loc, due_date: t.due_date}
        """,
        {
            "@tasks": col.TASKS,
            "tenant_key": tenant_key,
            "open": list(OPEN_TASK_STATUSES),
            "plants": f"{col.PLANT_INSTANCES}/",
            "location_keys": location_keys,
        },
    )
    if not rows:
        return None
    row = rows[0]
    return NextPlannedWatering(task_key=row["task_key"], location_key=row["location"], due_date=_parse(row["due_date"]))


def _consumption_liters(
    db: StandardDatabase, location_keys: list[str], slot_keys: list[str], *, tenant_key: str, now: datetime
) -> float:
    """Litres of the last 30 days: ``watering_events`` of the beds' slots plus logged care events.

    A care event written by a task completion (``trigger = task``) has its ``watering_events`` twin and is not
    counted twice. A ``watering_events`` row that waters slots of several beds of the zone counts once.
    """
    since = _since(now, CONSUMPTION_DAYS)
    bind = {"tenant_key": tenant_key, "since": since}
    logged = _rows(
        db,
        """
        RETURN SUM(
            FOR e IN @@events
                FILTER e.tenant_key == @tenant_key AND e.location_key IN @location_keys
                    AND e.category == "watering" AND e.trigger != "task"
                    AND DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@since)
                    AND e.voided_at == null AND e.superseded_by_key == null AND e.unit == "l"
                RETURN e.quantity || 0
        )
        """,
        {**bind, "@events": col.CARE_EVENTS, "location_keys": location_keys},
    )
    measured = (
        _rows(
            db,
            """
            RETURN SUM(
                FOR w IN @@watering
                    FILTER w.tenant_key == @tenant_key AND DATE_TIMESTAMP(w.watered_at) >= DATE_TIMESTAMP(@since)
                        AND LENGTH(INTERSECTION(w.slot_keys, @slot_keys)) > 0
                    RETURN w.volume_liters
            )
            """,
            {**bind, "@watering": col.WATERING_EVENTS, "slot_keys": slot_keys},
        )
        if slot_keys
        else [0]
    )
    return round(float(logged[0] or 0) + float(measured[0] or 0), 3)


def zone_watering_facts(
    db: StandardDatabase, location_keys: list[str], *, tenant_key: str, now: datetime
) -> ZoneWateringFacts:
    """Last watering, next planned watering and the 30-day consumption of a zone's beds (GP-API-052)."""
    if not location_keys:
        return ZoneWateringFacts(last_watering=None, next_planned=None, consumption_liters=0.0)
    newest = last_waterings(db, location_keys, tenant_key=tenant_key, now=now)
    last = max(newest.values(), key=lambda item: item.at, default=None)
    slot_keys = list(_slots_of(db, location_keys))
    return ZoneWateringFacts(
        last_watering=last,
        next_planned=_next_planned(db, location_keys, tenant_key=tenant_key),
        consumption_liters=_consumption_liters(db, location_keys, slot_keys, tenant_key=tenant_key, now=now),
    )
