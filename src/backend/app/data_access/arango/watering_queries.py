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
from typing import cast

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


_SLOTS_OF = "FOR s IN @@slots FILTER s.location_key IN @location_keys RETURN {key: s._key, location: s.location_key}"

_NEXT_PLANNED = """
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
"""

_LOGGED_LITERS = """
RETURN SUM(
    FOR e IN @@events
        FILTER e.tenant_key == @tenant_key AND e.location_key IN @location_keys
            AND e.category == "watering" AND e.trigger != "task"
            AND DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@since)
            AND e.voided_at == null AND e.superseded_by_key == null AND e.unit == "l"
        RETURN e.quantity || 0
)
"""

_MEASURED_LITERS = """
RETURN SUM(
    FOR w IN @@watering
        FILTER w.tenant_key == @tenant_key AND DATE_TIMESTAMP(w.watered_at) >= DATE_TIMESTAMP(@since)
            AND LENGTH(INTERSECTION(w.slot_keys, @slot_keys)) > 0
        RETURN w.volume_liters
)
"""


def _parse(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _slots_of(db: StandardDatabase, location_keys: list[str]) -> dict[str, str]:
    """slot key → bed key, for the beds named (the keys come from an owned zone or plan)."""
    rows = cast("Cursor", db.aql.execute(_SLOTS_OF, bind_vars={"@slots": col.SLOTS, "location_keys": location_keys}))
    return {row["key"]: row["location"] for row in rows}


def _since(now: datetime, days: int) -> str:
    start: datetime = now.astimezone(UTC) - timedelta(days=days)
    return start.isoformat()


def last_waterings(
    db: StandardDatabase, location_keys: list[str], *, tenant_key: str, now: datetime
) -> dict[str, LastWatering]:
    """The newest watering per bed, from both sources; a bed without one is absent."""
    if not location_keys:
        return {}
    since = _since(now, LOOKBACK_DAYS)
    found: dict[str, LastWatering] = {}
    care_rows = cast(
        "Cursor",
        db.aql.execute(
            _CARE_LAST,
            bind_vars={
                "@events": col.CARE_EVENTS,
                "tenant_key": tenant_key,
                "location_keys": location_keys,
                "since": since,
            },
        ),
    )
    for row in care_rows:
        moment = _parse(row["at"])
        if moment is not None:
            found[row["location"]] = LastWatering(
                at=moment, source="care_event", location_key=row["location"], allocation=row["allocation"]
            )
    slot_to_bed = _slots_of(db, location_keys)
    if slot_to_bed:
        slot_rows = cast(
            "Cursor",
            db.aql.execute(
                _SLOT_LAST,
                bind_vars={
                    "@watering": col.WATERING_EVENTS,
                    "tenant_key": tenant_key,
                    "slot_keys": list(slot_to_bed),
                    "since": since,
                },
            ),
        )
        for row in slot_rows:
            moment = datetime.fromtimestamp(float(row["at"]) / 1000, UTC) if row["at"] is not None else None
            bed = slot_to_bed.get(row["slot"])
            if moment is not None and bed is not None and (bed not in found or moment > found[bed].at):
                found[bed] = LastWatering(at=moment, source="watering_event", location_key=bed, allocation="measured")
    return found


def _next_planned(db: StandardDatabase, location_keys: list[str], *, tenant_key: str) -> NextPlannedWatering | None:
    """The oldest open ``watering`` task of the beds (on the bed itself or on a plant standing in it)."""
    rows = cast(
        "Cursor",
        db.aql.execute(
            _NEXT_PLANNED,
            bind_vars={
                "@tasks": col.TASKS,
                "tenant_key": tenant_key,
                "open": list(OPEN_TASK_STATUSES),
                "plants": f"{col.PLANT_INSTANCES}/",
                "location_keys": location_keys,
            },
        ),
    )
    row = next(rows, None)
    if row is None:
        return None
    return NextPlannedWatering(task_key=row["task_key"], location_key=row["location"], due_date=_parse(row["due_date"]))


def _consumption_liters(
    db: StandardDatabase, location_keys: list[str], slot_keys: list[str], *, tenant_key: str, now: datetime
) -> float:
    """Litres of the last 30 days: ``watering_events`` of the beds' slots plus logged care events.

    A care event written by a task completion (``trigger = task``) has its ``watering_events`` twin and is not
    counted twice. A ``watering_events`` row that waters slots of several beds of the zone counts once.
    """
    since = _since(now, CONSUMPTION_DAYS)
    logged = cast(
        "Cursor",
        db.aql.execute(
            _LOGGED_LITERS,
            bind_vars={
                "@events": col.CARE_EVENTS,
                "tenant_key": tenant_key,
                "location_keys": location_keys,
                "since": since,
            },
        ),
    )
    measured = (
        cast(
            "Cursor",
            db.aql.execute(
                _MEASURED_LITERS,
                bind_vars={
                    "@watering": col.WATERING_EVENTS,
                    "tenant_key": tenant_key,
                    "slot_keys": slot_keys,
                    "since": since,
                },
            ),
        )
        if slot_keys
        else iter([0])
    )
    return round(float(next(logged, 0) or 0) + float(next(measured, 0) or 0), 3)


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
