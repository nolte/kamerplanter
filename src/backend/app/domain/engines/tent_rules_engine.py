"""Hints of a tent or shelf level: one light schedule for every plant in it (REQ-053 §9.2a, W-016.6, V-23) - pure.

A tent (and each level of a shelf, W-016.4: one level = one location with its own lamp) has **one** light
schedule. Plants whose current REQ-003 phase asks for a different photoperiod cannot all get theirs: the hint
``tent.photoperiod_conflict`` says so. It is a **hint, never an error** (V-23) - nothing is refused.

**Where the photoperiod comes from (E-10).** Only from phase data: the ``photoperiod_hours`` of the requirement
profile of the plant's current phase (REQ-003), read by the repository
(:meth:`~app.domain.interfaces.garden_plan_repository.IGardenPlanRepository.load_location_photoperiods`). A plant
whose phase has no such profile has an *unknown* photoperiod - it is never given a default. It takes no part in the
conflict; when unknown plants share the location with others, the hint ``tent.photoperiod_unknown`` says the check
could not judge them.
"""

from __future__ import annotations

from collections import defaultdict

from app.domain.models.tent_hint import (
    HINT_PHOTOPERIOD_CONFLICT,
    HINT_PHOTOPERIOD_UNKNOWN,
    PhotoperiodGroup,
    PlantPhotoperiod,
    TentHint,
)

#: The location types under one light schedule (W-016.4/6): a tent and a shelf level. Everything else - a bed, a
#: room with windows, a greenhouse - takes its light from the day, which no schedule of ours sets.
PHOTOPERIOD_SHARED_LOCATION_TYPES: frozenset[str] = frozenset({"tent", "shelf"})

#: Two photoperiods closer than this are one (a profile stores ``18.0`` or ``18``; a timer has no finer step).
PHOTOPERIOD_RESOLUTION_HOURS = 0.25


def _rounded(hours: float) -> float:
    return round(hours / PHOTOPERIOD_RESOLUTION_HOURS) * PHOTOPERIOD_RESOLUTION_HOURS


def photoperiod_groups(plants: list[PlantPhotoperiod]) -> tuple[PhotoperiodGroup, ...]:
    """The plants with a known photoperiod grouped by it (to :data:`PHOTOPERIOD_RESOLUTION_HOURS`), longest first."""
    counts: dict[float, int] = defaultdict(int)
    names: dict[float, set[str]] = defaultdict(set)
    for plant in plants:
        if plant.photoperiod_hours is None:
            continue
        hours = _rounded(plant.photoperiod_hours)
        counts[hours] += 1
        if plant.phase_name:
            names[hours] |= {plant.phase_name}
    return tuple(
        PhotoperiodGroup(photoperiod_hours=hours, plant_count=counts[hours], phase_names=tuple(sorted(names[hours])))
        for hours in sorted(counts, reverse=True)
    )


def photoperiod_hints(location_type_key: str, plants: list[PlantPhotoperiod]) -> list[TentHint]:
    """The light-schedule hints of one location (V-23); empty for a location without a schedule of its own.

    * ``tent.photoperiod_conflict`` (``warning``): the plants with a known photoperiod ask for two or more.
    * ``tent.photoperiod_unknown`` (``info``): no conflict among the known ones, but at least two plants stand
      here and at least one of them has no photoperiod - the check could not judge it (E-10).
    """
    if location_type_key not in PHOTOPERIOD_SHARED_LOCATION_TYPES:
        return []
    groups = photoperiod_groups(plants)
    unknown = sum(1 for plant in plants if plant.photoperiod_hours is None)
    if len(groups) >= 2:
        return [TentHint(HINT_PHOTOPERIOD_CONFLICT, "warning", groups, unknown)]
    if unknown and len(plants) >= 2:
        return [TentHint(HINT_PHOTOPERIOD_UNKNOWN, "info", groups, unknown)]
    return []
