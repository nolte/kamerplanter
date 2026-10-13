"""The species a tenant may read, for readers that follow a **stored** species key (#1963).

A species key stored on a row is not proof the row's tenant may read that species: rows
written before #1876 closed the #1871 B11 hole (a planting-run entry's ``species_key``)
may name another tenant's private species, and v0067 dropped only the edge. A reader
that follows the field therefore resolves it under the tenant first. The rule is the one
the species detail read and the calendar already apply — global, the tenant's own, or
explicitly granted (#1092) — kept in one place so the readers cannot drift apart.
"""

from __future__ import annotations

from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Species


def readable_species(species_repo: ISpeciesRepository, species_key: str, tenant_key: str) -> Species | None:
    """The species when ``tenant_key`` may read it, else ``None`` (unknown and foreign alike).

    Fail-closed on a missing tenant: an empty ``tenant_key`` reads only global species,
    as the species detail read does for an anonymous caller.
    """
    species = species_repo.get_by_key(species_key)
    if species is None:
        return None
    if species.tenant_key not in ("", tenant_key) and not species_repo.is_granted_to(species_key, tenant_key):
        return None
    return species
