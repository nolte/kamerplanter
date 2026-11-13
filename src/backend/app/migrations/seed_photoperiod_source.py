"""The provenance a Steckbrief seed gives a phase's photoperiod (#2857, REQ-003, REQ-053 §9.2a).

``seed_plant_info`` and ``seed_plant_info_extended`` patch the requirement profile of a phase that already exists
field by field: a field the YAML phase leaves out keeps what the profile holds, and with it its origin. Only a phase
that states ``photoperiod_hours`` makes the profile's photoperiod ``sourced`` - also when the stored value already
equals it. That last case is how an installation whose profiles predate the provenance gets them labelled on the next
seed run without a data migration; a profile whose value the YAML does not state is never relabelled.

``seed_adventskalender`` never patches phases that already exist; it vouches only for a stored value that still equals
the stated one (:func:`stamp_unchanged_photoperiods`). The generic phases ``seed_data`` and ``seed_lifecycles_outdoor``
write come from the generator and carry ``generated`` / ``default`` (``ResourceProfileGenerator``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.common.enums import PhotoperiodSource
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.models.lifecycle import GrowthPhase
from app.domain.models.phase import RequirementProfile

#: The YAML key of a Steckbrief phase's light hours (``requirement_profile`` of a ``growth_phases`` entry).
PHOTOPERIOD_KEY = "photoperiod_hours"


def stamp_steckbrief_photoperiod(profile: RequirementProfile, requirement: Mapping[str, Any]) -> bool:
    """Mark ``profile``'s photoperiod ``sourced`` when the Steckbrief phase states its hours; ``True`` if it changed.

    The value itself is patched by the caller's field loop; this only records where it came from. A phase without
    ``photoperiod_hours`` leaves the profile's value and its origin alone.
    """
    if PHOTOPERIOD_KEY not in requirement or requirement[PHOTOPERIOD_KEY] is None:
        return False
    if profile.photoperiod_source == PhotoperiodSource.SOURCED:
        return False
    profile.photoperiod_source = PhotoperiodSource.SOURCED
    return True


def stamp_unchanged_photoperiods(
    repo: IPhaseRepository, phases: Sequence[GrowthPhase], stated_hours: Mapping[str, float]
) -> int:
    """Mark ``sourced`` the stored photoperiods that still equal the hours the Steckbrief states; return how many.

    For a loader that never patches existing phases (``seed_adventskalender``): it does not overwrite a stored value,
    so it can only vouch for one that is exactly the stated value. A stored value that differs keeps its origin -
    it may be a person's edit from before the provenance existed, which nobody can tell any more. ``stated_hours`` maps
    the phase name to the hours its Steckbrief entry states.
    """
    stamped = 0
    for phase in phases:
        hours = stated_hours.get(phase.name)
        if hours is None or not phase.key:
            continue
        profile = repo.get_requirement_profile(phase.key)
        if profile is None or not profile.key or profile.photoperiod_source == PhotoperiodSource.SOURCED:
            continue
        if profile.photoperiod_hours != float(hours):
            continue
        repo.update_requirement_profile(
            profile.key, profile.model_copy(update={"photoperiod_source": PhotoperiodSource.SOURCED})
        )
        stamped += 1
    return stamped
