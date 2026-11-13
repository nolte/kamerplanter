"""Hints of a tent or shelf level: one light schedule for every plant in it (REQ-053 §9.2a, W-016.6, V-23) - pure.

A tent (and each lit level of a shelf, W-016.4: one level = one location with its own lamp) has **one** light
schedule. Plants whose current REQ-003 phase asks for a different photoperiod cannot all get theirs: the hint
``tent.photoperiod_conflict`` says so. It is a **hint, never an error** (V-23) - nothing is refused.

**Where the photoperiod comes from (E-10).** Only from phase data: the ``photoperiod_hours`` of the requirement
profile of the plant's current phase (REQ-003), read by the repository
(:meth:`~app.domain.interfaces.garden_plan_repository.IGardenPlanRepository.load_location_photoperiods`). A plant
whose phase has no such profile has an *unknown* photoperiod - it is never given a default. It takes no part in the
conflict; when unknown plants share the location with others, the hint ``tent.photoperiod_unknown`` names them.

**Only a sourced value is judged (#2857).** A requirement profile records where its ``photoperiod_hours`` came from
(``PhotoperiodSource``). Only ``sourced`` hours - from a Steckbrief or entered by a person in the profile editor - say
something about the plant; the 18/12 of the generator's phase-name table (``generated``), the fallback 18.0
(``default``) and a profile stored before the provenance existed (``None``) do not. Such a plant counts as unknown,
exactly like one without a profile (:func:`judged_photoperiod`). Day-neutral plants still take part, because a stored
``day_neutral`` type is not yet a classified one (see below) - so the conflict stays a ``warning`` and the text names
the light hours of the phase profiles, never that the plants *need* different light.

**Who takes part.** Only plants in a light-triggered phase: a young, establishing plant (``YOUNG_PHASE_NAMES`` -
germination, seedling, rooting and the establishment phases of cuttings and offsets) is left out entirely.
"""

from __future__ import annotations

from app.common.enums import PhotoperiodSource
from app.domain.engines.phase_role_map import is_young_phase
from app.domain.models.tent_hint import (
    HINT_PHOTOPERIOD_CONFLICT,
    HINT_PHOTOPERIOD_UNKNOWN,
    MAX_NAMED_UNKNOWN_PLANTS,
    PhaseLabel,
    PhotoperiodGroup,
    PlantPhotoperiod,
    TentHint,
)

#: The location types under one light schedule (W-016.4/6): a tent and a shelf level. Everything else - a bed, a
#: room with windows, a greenhouse - takes its light from the day, which no schedule of ours sets.
PHOTOPERIOD_SHARED_LOCATION_TYPES: frozenset[str] = frozenset({"tent", "shelf"})

#: Location types whose schedule is always a lamp's: a tent is closed. A shelf level counts only with a lamp of its own
#: (``Location.lighting.lamp_height_cm``); an unlit shelf on a windowsill gets its light from the day.
_ALWAYS_LIT_TYPES: frozenset[str] = frozenset({"tent"})

#: Two photoperiods less than this apart are one. A plug-in timer switches in 15- to 30-minute steps and growers set
#: whole hours; the real conflicts under one lamp are a light-cycle apart (18/6 against 12/12, 16/8 against 18/6), so
#: a difference below one hour is timer granularity, not a second schedule.
PHOTOPERIOD_EQUAL_TOLERANCE_HOURS = 1.0

# Follow-up to #2832: ``LifecycleConfig.photoperiod_type`` / ``PhaseSequence.photoperiod_type`` default to
# ``day_neutral``, so a stored ``day_neutral`` does not say the species was classified. Day-neutral plants are therefore
# NOT left out here - doing so would drop nearly every plant. Once the type has an ``unspecified`` value, a sourced
# ``day_neutral`` can leave the conflict like a young plant does.


def has_own_light_schedule(location_type_key: str, lamp_height_cm: float | None) -> bool:
    """Whether the location runs one light schedule for its plants: a tent always, a shelf level with its own lamp."""
    if location_type_key in _ALWAYS_LIT_TYPES:
        return True
    return location_type_key in PHOTOPERIOD_SHARED_LOCATION_TYPES and lamp_height_cm is not None


def judged_photoperiod(plant: PlantPhotoperiod) -> float | None:
    """The photoperiod the check may judge: the stored hours only when they are ``sourced`` (#2857), else ``None``.

    ``generated`` (the generator's phase-name table), ``default`` (nobody chose it), ``None`` (stored before the
    provenance existed) and a plant without a profile are all unknown - never a value to compare.
    """
    if plant.photoperiod_source != PhotoperiodSource.SOURCED:
        return None
    return plant.photoperiod_hours


def light_triggered(plants: list[PlantPhotoperiod]) -> list[PlantPhotoperiod]:
    """The plants that take part in the photoperiod check: every plant that is not in a young phase."""
    return [plant for plant in plants if not is_young_phase(plant.phase_code)]


def photoperiod_groups(plants: list[PlantPhotoperiod]) -> tuple[PhotoperiodGroup, ...]:
    """The plants with a known (:func:`judged_photoperiod`) photoperiod grouped by it, longest first.

    A group starts at its longest photoperiod and takes every plant less than :data:`PHOTOPERIOD_EQUAL_TOLERANCE_HOURS`
    below it; the group shows that longest value. Two or more groups exist exactly when the longest and the shortest
    known photoperiod lie at least the tolerance apart.
    """
    judged: list[tuple[float | None, PlantPhotoperiod]] = [(judged_photoperiod(plant), plant) for plant in plants]
    known: list[tuple[float, PlantPhotoperiod]] = sorted(
        ((hours, plant) for hours, plant in judged if hours is not None),
        key=lambda pair: -pair[0],
    )
    anchors: list[float] = []
    members: list[list[PlantPhotoperiod]] = []
    for hours, plant in known:
        if anchors and anchors[-1] - hours < PHOTOPERIOD_EQUAL_TOLERANCE_HOURS:
            members[-1] += [plant]
        else:
            anchors += [hours]
            members += [[plant]]
    return tuple(
        PhotoperiodGroup(
            photoperiod_hours=anchor,
            plant_count=len(group),
            phase_names=tuple(sorted({member.phase_name for member in group if member.phase_name})),
            phases=_phase_labels(group),
        )
        for anchor, group in zip(anchors, members, strict=True)
    )


def _phase_labels(plants: list[PlantPhotoperiod]) -> tuple[PhaseLabel, ...]:
    """One label per phase code, sorted by it; a display name one plant's phase lacks is taken from another's.

    A legacy growth phase and a sequence entry of the same name are one phase: the legacy one carries no German name,
    the phase definition does, and the hint names the phase once (#2889).
    """
    merged: dict[str, PhaseLabel] = {}
    for plant in plants:
        label = plant.phase_label
        if label is None or not label.code:
            continue
        known = merged.get(label.code)
        merged[label.code] = (
            label
            if known is None
            else PhaseLabel(
                code=label.code,
                display_name=known.display_name or label.display_name,
                display_name_de=known.display_name_de or label.display_name_de,
            )
        )
    return tuple(merged[code] for code in sorted(merged))


def _unknown_names(plants: list[PlantPhotoperiod]) -> tuple[str, ...]:
    names: list[str] = sorted(
        plant.display_name or plant.plant_key for plant in plants if judged_photoperiod(plant) is None
    )
    return tuple(names[:MAX_NAMED_UNKNOWN_PLANTS])


def photoperiod_hints(
    location_type_key: str, plants: list[PlantPhotoperiod], *, lamp_height_cm: float | None = None
) -> list[TentHint]:
    """The light-schedule hints of one location (V-23); empty for a location without a schedule of its own.

    * ``tent.photoperiod_conflict`` (``warning``): the light-triggered plants with a known photoperiod fall into two
      or more groups (:func:`photoperiod_groups`).
    * ``tent.photoperiod_unknown`` (``info``): no conflict among the known ones, but at least two light-triggered
      plants stand here and at least one of them has no sourced photoperiod - the check could not judge it (E-10,
      #2857). With a conflict the unknown plants are still counted and named on the conflict hint.
    """
    if not has_own_light_schedule(location_type_key, lamp_height_cm):
        return []
    considered = light_triggered(plants)
    groups = photoperiod_groups(considered)
    unknown = sum(1 for plant in considered if judged_photoperiod(plant) is None)
    names = _unknown_names(considered)
    if len(groups) >= 2:
        return [TentHint(HINT_PHOTOPERIOD_CONFLICT, "warning", groups, unknown, names)]
    if unknown and len(considered) >= 2:
        return [TentHint(HINT_PHOTOPERIOD_UNKNOWN, "info", groups, unknown, names)]
    return []
