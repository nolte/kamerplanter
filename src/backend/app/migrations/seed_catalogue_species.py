"""How the seed loaders resolve a species name from their YAML: among the global catalogue rows only (#2857 SEC-001).

Before, every loader called ``get_by_scientific_name`` - the first row of that name, whoever owns it. A tenant that had
created a species under a catalogue name (before the catalogue seeded it) then received the seed's writes: lifecycle
and photoperiod type, Steckbrief light hours on its requirement profiles, phases replaced, names synced. A seed now
resolves through :meth:`~app.domain.interfaces.species_repository.ISpeciesRepository.get_global_by_scientific_name`.

``scientific_name`` is unique across catalogue and tenants (persistent index), so a name a tenant already holds cannot
get a catalogue row either: :func:`name_held_by_tenant` lets a create path skip it instead of failing on the index.
The log names only the species, never the tenant.
"""

from __future__ import annotations

from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Species


def catalogue_species(species_repo: ISpeciesRepository, name: str) -> Species | None:
    """The global catalogue species named ``name``; ``None`` when there is none (a tenant's row never counts)."""
    return species_repo.get_global_by_scientific_name(name)


def name_held_by_tenant(species_repo: ISpeciesRepository, name: str) -> bool:
    """Whether a tenant's own species holds ``name`` - with no catalogue row of it, a seed must not create one."""
    holder = species_repo.get_by_scientific_name(name)
    return holder is not None and bool(holder.tenant_key)
