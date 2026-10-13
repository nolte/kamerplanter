"""Which seed file owns a species' growth phases (#2002).

Three loaders write species-specific growth phases — ``seed_adventskalender``,
``seed_plant_info`` and ``seed_plant_info_extended`` — and each replaces the phases
it finds on a species' lifecycle when they are not its own. A file may carry a
species' ``lifecycle_configs`` entry without carrying its ``growth_phases``; the
loader then deleted the existing phases and wrote none. Where *another* file carries
the phases, that made two loaders trade them on every start: measured on a real
ArangoDB, ``adventskalender`` created the five phases of *Cichorium intybus* and
``plant_info_extended`` (which lists the species' lifecycle but no phases) deleted
them again, every boot.

The rule the three loaders share: a loader that carries no phases for a species
leaves the species' phases alone when some seed file carries them — that file owns
them. A species no seed file gives phases keeps the loaders' previous behaviour.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cache

from app.migrations.yaml_loader import load_yaml

#: The single-file phase sources besides ``seed_plant_info_extended.YAML_FILES``.
_PHASE_FILES = ("adventskalender.yaml", "plant_info.yaml")


@cache
def species_with_seeded_phases() -> frozenset[str]:
    """Scientific names some seed file lists ``growth_phases`` for (read once per process)."""
    from app.migrations.seed_plant_info_extended import YAML_FILES

    names: set[str] = set()
    for filename in (*_PHASE_FILES, *YAML_FILES):
        try:
            data = load_yaml(filename) or {}
        except FileNotFoundError:
            continue  # the loaders skip a missing file the same way
        names.update(name for name, phases in (data.get("growth_phases") or {}).items() if phases)
    return frozenset(names)


def phases_owned_elsewhere(scientific_name: str, own_phase_data: Mapping[str, object]) -> bool:
    """Whether a loader whose file carries ``own_phase_data`` must leave the species' phases alone."""
    return scientific_name not in own_phase_data and scientific_name in species_with_seeded_phases()
