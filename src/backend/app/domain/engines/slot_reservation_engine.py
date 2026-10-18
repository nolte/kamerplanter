"""Slot reservation with a time window (REQ-053 GP-FR-065, V-08) — pure, no I/O.

A ``run_planned_at`` edge reserves a slot for a planting run during ``[planned_from, planned_until]``.
Several runs may reserve one slot as long as their windows do not overlap (a lamb's lettuce after the
tomatoes); an overlap is the 409 ``slot.already_planned``. This module answers *whether* and *where* two
windows meet; the service decides what to read and what to refuse, the repository re-asks inside its
transaction (a reservation placed between the service's read and the write must not slip through).

**Windows are closed date intervals.** A run occupies its slot through ``planned_until`` inclusive, so the
next run may start on the following day; the same day overlaps. ``planned_until = None`` is open: it
overlaps every window that starts on or after ``planned_from`` and every window that reaches back to it.

**An active plant** (``placed_in`` with ``removed_on = null``) blocks a reservation whose ``planned_from``
lies before the *expected end* of the plant's run (its ``planned_until``; ``None`` = unknown = open).
A reservation that starts after that end is allowed (GP-FR-065): the slot is free again by then.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.common.enums import PlantingRunStatus

#: Runs whose reservations count. A completed or cancelled run released its slots (GP-FR-066).
LIVE_RUN_STATUSES: frozenset[str] = frozenset(
    {PlantingRunStatus.PLANNED.value, PlantingRunStatus.ACTIVE.value, PlantingRunStatus.HARVESTING.value}
)

CONFLICT_RESERVATION = "reservation"
CONFLICT_ACTIVE_PLANT = "active_plant"


@dataclass(frozen=True)
class Reservation:
    """A ``run_planned_at`` edge with the data of its run the engine needs."""

    slot_key: str
    run_key: str
    entry_key: str
    planned_species_key: str
    sequence: int
    planned_from: date | None
    planned_until: date | None
    run_status: str = PlantingRunStatus.PLANNED.value


@dataclass(frozen=True)
class ActivePlant:
    """A plant standing in a slot; ``expected_end`` is the ``planned_until`` of its run (``None``: unknown)."""

    slot_key: str
    plant_key: str
    run_key: str | None
    expected_end: date | None


@dataclass(frozen=True)
class SlotConflict:
    """Why a slot cannot be reserved for the requested window (V-08)."""

    slot_key: str
    kind: str
    conflicting_run_key: str | None
    overlap_from: date
    overlap_until: date | None

    def as_detail(self) -> dict[str, object]:
        """The wire form: dates as ISO strings, ``None`` for an open end."""
        return {
            "slot_key": self.slot_key,
            "kind": self.kind,
            "conflicting_run_key": self.conflicting_run_key,
            "overlap_from": self.overlap_from.isoformat(),
            "overlap_until": self.overlap_until.isoformat() if self.overlap_until else None,
        }


def window_overlap(
    first_from: date | None,
    first_until: date | None,
    second_from: date | None,
    second_until: date | None,
) -> tuple[date, date | None] | None:
    """The overlap of two closed windows as ``(from, until)``, or ``None`` when they are disjoint.

    A ``None`` start reaches back without limit, a ``None`` end forward without limit. The overlap's own
    end is ``None`` only when both windows are open.
    """
    start = max(d for d in (first_from, second_from, date.min) if d is not None)
    ends = [d for d in (first_until, second_until) if d is not None]
    end = min(ends) if ends else None
    if end is not None and end < start:
        return None
    return start, end


def find_conflicts(
    slot_keys: list[str],
    *,
    run_key: str,
    planned_from: date | None,
    planned_until: date | None,
    reservations: list[Reservation],
    plants: list[ActivePlant],
    entry_key: str | None = None,
) -> list[SlotConflict]:
    """The first conflict of each requested slot (V-08), in the order of ``slot_keys``.

    The run's own plants never conflict with it, and neither does its own reservation of the *same entry*:
    replacing that reservation is the normal path. A reservation of another entry of the same run does — one
    position cannot hold two entries. Without ``entry_key`` every reservation of the run is its own.
    """
    by_slot: dict[str, list[Reservation]] = {}
    for reservation in reservations:
        own = reservation.run_key == run_key and (entry_key is None or reservation.entry_key == entry_key)
        if not own and reservation.run_status in LIVE_RUN_STATUSES:
            by_slot.setdefault(reservation.slot_key, []).append(reservation)
    plants_by_slot: dict[str, list[ActivePlant]] = {}
    for plant in plants:
        if plant.run_key != run_key:
            plants_by_slot.setdefault(plant.slot_key, []).append(plant)

    conflicts: list[SlotConflict] = []
    for slot_key in slot_keys:
        found = _first_conflict(
            slot_key, planned_from, planned_until, by_slot.get(slot_key, []), plants_by_slot.get(slot_key, [])
        )
        if found is not None:
            conflicts.append(found)
    return conflicts


def _first_conflict(
    slot_key: str,
    planned_from: date | None,
    planned_until: date | None,
    reservations: list[Reservation],
    plants: list[ActivePlant],
) -> SlotConflict | None:
    for reservation in reservations:
        overlap = window_overlap(planned_from, planned_until, reservation.planned_from, reservation.planned_until)
        if overlap is not None:
            return SlotConflict(slot_key, CONFLICT_RESERVATION, reservation.run_key, overlap[0], overlap[1])
    for plant in plants:
        # The plant has stood there since long before any reservation: its window reaches back without limit.
        overlap = window_overlap(planned_from, planned_until, None, plant.expected_end)
        if overlap is not None:
            return SlotConflict(slot_key, CONFLICT_ACTIVE_PLANT, plant.run_key, overlap[0], overlap[1])
    return None


# ── Slot ids ─────────────────────────────────────────────────────────────────

_ID_CHARS = re.compile(r"[^A-Z0-9]+")
_ID_SUFFIX = re.compile(r"_(\d+)$")
#: The longest prefix taken from a bed name, so ``LOCATION_NNN`` stays readable on a label.
_PREFIX_LENGTH = 12


def slot_id_prefix(location_name: str, location_key: str) -> str:
    """The ``LOCATION`` part of ``LOCATION_NNN`` (GP-FR-064): the bed's name, upper-case, letters and digits only."""
    cleaned = _ID_CHARS.sub("", location_name.upper())[:_PREFIX_LENGTH]
    return cleaned or _ID_CHARS.sub("", f"L{location_key}".upper())[:_PREFIX_LENGTH] or "BED"


def allocate_slot_ids(prefix: str, existing_ids: set[str], count: int) -> list[str]:
    """``count`` new ``PREFIX_NNN`` ids that are free in the bed (V-20), numbered on from the highest in use.

    Archived slots keep their id (history), so ``existing_ids`` must include them: the unique index of a bed
    does not look at ``archived_at``.
    """
    highest = 0
    for slot_id in existing_ids:
        if slot_id.startswith(f"{prefix}_"):
            match = _ID_SUFFIX.search(slot_id)
            if match:
                highest = max(highest, int(match.group(1)))
    ids: list[str] = []
    number = highest
    while len(ids) < count:
        number += 1
        candidate = f"{prefix}_{number:03d}"
        if candidate not in existing_ids:
            ids.append(candidate)
    return ids


# ── Planting states (§11.3) ───────────────────────────────────────────────────

STATE_PLANNED = "planned"
STATE_ACTIVE = "active"
STATE_HARVESTED = "harvested"
STATE_HISTORICAL = "historical"
PLANTING_STATES: tuple[str, ...] = (STATE_PLANNED, STATE_ACTIVE, STATE_HARVESTED, STATE_HISTORICAL)


def plant_state(removed_on: date | None, termination_type: str | None) -> str:
    """``active`` while the plant stands, ``harvested`` when it ended by harvest, else ``historical``."""
    if removed_on is None:
        return STATE_ACTIVE
    return STATE_HARVESTED if termination_type == "harvested" else STATE_HISTORICAL


def intersects_year(start: date | None, end: date | None, year: int) -> bool:
    """Whether the closed window ``[start, end]`` (open ends allowed) touches calendar ``year``."""
    year_start, year_end = date(year, 1, 1), date(year, 12, 31)
    return window_overlap(start, end, year_start, year_end) is not None
