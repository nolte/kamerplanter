"""The provenance a Steckbrief seed gives a phase's photoperiod (#2857, REQ-003, REQ-053 §9.2a).

``seed_plant_info`` and ``seed_plant_info_extended`` patch the requirement profile of a phase that already exists
field by field: a field the YAML phase leaves out keeps what the profile holds, and with it its origin. Only a phase
that states ``photoperiod_hours`` makes the profile's photoperiod ``sourced`` - also when the stored value already
equals it. That last case is how an installation whose profiles predate the provenance gets them labelled on the next
seed run without a data migration; a profile whose value the YAML does not state is never relabelled.

``seed_adventskalender`` never patches phases that already exist; it vouches only for a stored value that still equals
the stated one (:func:`stamp_unchanged_photoperiods`). The generic phases ``seed_data`` and ``seed_lifecycles_outdoor``
write come from the generator and carry ``generated`` / ``default`` (``ResourceProfileGenerator``) - unless
``species.yaml`` ``steckbrief_phase_photoperiods`` lists the species: then ``seed_data`` writes the hours the Steckbrief
states for those phases as ``sourced`` (:func:`apply_steckbrief_phase_photoperiods`).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.common.enums import PhotoperiodSource, PhotoperiodType
from app.domain.interfaces.phase_repository import IPhaseRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import RequirementProfile


def fill_unspecified_photoperiod(lifecycle: LifecycleConfig, entry: Mapping[str, Any]) -> bool:
    """Give ``lifecycle`` the type a seed ``entry`` states, only while it holds none (#2857); ``True`` if set.

    A lifecycle the core seed created for a ``species.yaml`` species carries ``unspecified``: the core seed has no
    source for it (E-10). A ``lifecycles_outdoor`` entry that states a type is such a source, so it fills the gap. A
    stated type already on the lifecycle - from a ``plant_info`` lifecycle_config or a person - is never overwritten,
    and an entry without a type changes nothing.
    """
    stated = entry.get("photoperiod_type")
    if not stated or lifecycle.photoperiod_type != PhotoperiodType.UNSPECIFIED:
        return False
    value = PhotoperiodType(stated)
    if value == PhotoperiodType.UNSPECIFIED:
        return False
    lifecycle.photoperiod_type = value
    return True


def resolve_lifecycle_config_species(
    species_repo: ISpeciesRepository, names: Iterable[str], species_key_map: dict[str, str]
) -> set[str]:
    """Add the catalogue species a ``lifecycle_configs`` block names to ``species_key_map``; return their names.

    The plant-info loaders resolved a species only when the same file also created, enriched or referenced it. A
    species listed in ``lifecycle_configs`` alone was skipped (``lifecycle_species_not_found``), and its stated
    ``photoperiod_type`` never reached the lifecycle - hemp kept ``day_neutral`` although ``plant_info.yaml`` states
    ``short_day`` (#2857). Only a global catalogue row is taken: a tenant's own species of the same name is the
    tenant's, and a seed never writes to it.

    The caller updates only the lifecycle of the returned species: the file states no phases for them, and the
    loader's generic-phase replacement would delete the phases they have.
    """
    added: set[str] = set()
    for name in names:
        if name in species_key_map:
            continue
        species = species_repo.get_global_by_scientific_name(name)
        if species is None or not species.key:
            continue
        species_key_map[name] = species.key
        added.add(name)
    return added


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
        profile.photoperiod_source = PhotoperiodSource.SOURCED
        repo.update_requirement_profile(profile.key, profile)
        stamped += 1
    return stamped


@dataclass(frozen=True)
class StatedPhotoperiod:
    """The light hours a Steckbrief states for one default phase of a species (``species.yaml``)."""

    phase_name: str
    hours: float
    #: The Steckbrief's ``#### Phase: ...`` heading the hours are read from.
    steckbrief_phase: str


def parse_steckbrief_phase_photoperiods(block: Mapping[str, Any]) -> dict[str, list[StatedPhotoperiod]]:
    """``species.yaml`` ``steckbrief_phase_photoperiods`` -> scientific name -> its stated phases (schema-validated)."""
    stated: dict[str, list[StatedPhotoperiod]] = {}
    for scientific_name, entry in block.items():
        phases: Mapping[str, Mapping[str, Any]] = entry["phases"]
        stated[str(scientific_name)] = [
            StatedPhotoperiod(str(name), float(row["hours"]), str(row["steckbrief_phase"]))
            for name, row in phases.items()
        ]
    return stated


def apply_steckbrief_phase_photoperiods(
    repo: IPhaseRepository, stated: Mapping[str, Sequence[StatedPhotoperiod]], species_keys: Mapping[str, str]
) -> int:
    """Write the Steckbrief's light hours onto a species' default phases as ``sourced``; return how many changed.

    For the species ``seed_data`` seeds with the generic ``default_phases`` (their hours are ``generated``): the
    profile of the phase of that name gets the stated hours and ``sourced`` - on a fresh seed and on every later
    start, so an existing installation needs no migration. A profile someone already saved as ``sourced`` is theirs
    and stays. A profile from before the provenance (``None``) whose value differs from the Steckbrief's may be a
    person's old edit, which nobody can tell any more: it is left alone, like ``stamp_unchanged_photoperiods`` does. A
    ``generated`` or ``default`` value is nobody's choice and is replaced.
    """
    changed = 0
    for scientific_name, phases in stated.items():
        species_key = species_keys.get(scientific_name)
        if not species_key:
            continue
        lifecycle = repo.get_lifecycle_by_species(species_key)
        if lifecycle is None or not lifecycle.key:
            continue
        by_name: dict[str, GrowthPhase] = {phase.name: phase for phase in repo.get_phases_by_lifecycle(lifecycle.key)}
        for stated_phase in phases:
            phase = by_name.get(stated_phase.phase_name)
            if phase is None or not phase.key:
                continue
            profile = repo.get_requirement_profile(phase.key)
            if profile is None or not profile.key or profile.photoperiod_source == PhotoperiodSource.SOURCED:
                continue
            if profile.photoperiod_source is None and profile.photoperiod_hours != stated_phase.hours:
                continue
            profile.photoperiod_hours = stated_phase.hours
            profile.photoperiod_source = PhotoperiodSource.SOURCED
            repo.update_requirement_profile(profile.key, profile)
            changed += 1
    return changed
