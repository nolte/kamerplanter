"""In-memory stand-in for the species lookups of :class:`ISpeciesRepository`.

Behaves like the Arango repository on the three reads a tenant-scoped resolver
uses: ``get_by_key`` / ``get_or_raise`` are **unscoped** key reads (they return
another tenant's private species as readily as a global one — exactly what the
production ``BaseArangoRepository`` does), ``is_granted_to`` answers from an
explicit grant set (#1092). Global species carry ``tenant_key=""``, the
production convention. ``lookups`` records every key read so a test can assert a
refused request never resolved a species.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.common.exceptions import NotFoundError


class FakeSpeciesRepo:
    def __init__(self) -> None:
        self._species: dict[str, SimpleNamespace] = {}
        self._grants: set[tuple[str, str]] = set()
        self.lookups: list[str] = []

    def add(self, key: str, scientific_name: str, *, tenant_key: str = "") -> SimpleNamespace:
        species = SimpleNamespace(key=key, scientific_name=scientific_name, tenant_key=tenant_key)
        self._species[key] = species
        return species

    def grant(self, species_key: str, to_tenant_key: str) -> None:
        self._grants.add((species_key, to_tenant_key))

    def get_by_key(self, key: str) -> SimpleNamespace | None:
        self.lookups.append(key)
        return self._species.get(key)

    def get_or_raise(self, key: str) -> SimpleNamespace:
        species = self.get_by_key(key)
        if species is None:
            raise NotFoundError("Species", key)
        return species

    def is_granted_to(self, species_key: str, tenant_key: str) -> bool:
        return (species_key, tenant_key) in self._grants
