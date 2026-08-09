"""SpeciesService.list_species tenant isolation — both directions (F-5, #808).

The load-bearing pair (#324 both directions, #808 acceptance-1 + acceptance-2):

* acceptance-1 — the global seed catalogue (``tenant_key == ""``) AND the caller's
  own-tenant species stay visible;
* acceptance-2 (verifies_sprint_value) — a *foreign* tenant's species never
  appears in another tenant's list.

The fake repository below models the real repository's hybrid-catalogue union
(``tenant_key == caller OR "" OR null``) in Python, so these tests exercise the
service's *wiring*: ``list_species`` must thread the caller's tenant into the
repository read. Dropping it (the pre-F-5 ``get_all(offset, limit)`` call) makes
the fake fall back to the unscoped whole-catalogue branch and the foreign species
leaks — which is exactly the red-first state acceptance-2 guards against.
"""

from __future__ import annotations

import pytest

from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService


class _FakeUnionSpeciesRepo:
    """Models the repository's three-arm hybrid-catalogue union read.

    ``tenant_key is None`` is the unscoped system read (whole catalogue); a string
    (including ``""``) applies the union: rows owned by that tenant, the global
    seeds (``""``) and legacy ``null`` — never a foreign tenant's.
    """

    def __init__(self, species: list[Species]) -> None:
        self._species = list(species)

    def get_all(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None) -> tuple[list[Species], int]:
        if tenant_key is None:
            rows = list(self._species)
        else:
            rows = [s for s in self._species if s.tenant_key in (tenant_key, "", None)]
        return rows[offset : offset + limit], len(rows)


def _service(repo: _FakeUnionSpeciesRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


@pytest.fixture
def catalogue() -> list[Species]:
    return [
        Species(_key="global_seed", scientific_name="Rosa canina", tenant_key=""),
        Species(_key="own", scientific_name="Ocimum basilicum", tenant_key="tenant_self"),
        Species(_key="foreign", scientific_name="Cannabis sativa", tenant_key="tenant_other"),
    ]


def _names(result) -> set[str]:
    items, _total = result
    return {s.scientific_name for s in items}


def test_own_tenant_sees_global_and_own_species(catalogue):
    # acceptance-1: the shared seed catalogue stays visible alongside own rows.
    result = _service(_FakeUnionSpeciesRepo(catalogue)).list_species(tenant_key="tenant_self")

    assert _names(result) == {"Rosa canina", "Ocimum basilicum"}


def test_foreign_tenant_species_does_not_leak(catalogue):
    # acceptance-2 (verifies_sprint_value): tenant_other's private species is absent
    # from tenant_self's list. This is the isolation that proves the sprint value.
    items, total = _service(_FakeUnionSpeciesRepo(catalogue)).list_species(tenant_key="tenant_self")

    assert "Cannabis sativa" not in {s.scientific_name for s in items}
    assert total == 2


def test_the_other_direction_also_isolates(catalogue):
    # Symmetry: tenant_other sees global + its own, never tenant_self's.
    result = _service(_FakeUnionSpeciesRepo(catalogue)).list_species(tenant_key="tenant_other")

    assert _names(result) == {"Rosa canina", "Cannabis sativa"}


def test_anonymous_caller_sees_only_the_global_catalogue(catalogue):
    # No resolvable tenant → "" → global-only, never an error, never all-tenants.
    result = _service(_FakeUnionSpeciesRepo(catalogue)).list_species(tenant_key="")

    assert _names(result) == {"Rosa canina"}


def test_pagination_is_honoured_within_the_scoped_set(catalogue):
    items, total = _service(_FakeUnionSpeciesRepo(catalogue)).list_species(offset=0, limit=1, tenant_key="tenant_self")

    assert len(items) == 1
    assert total == 2  # total reflects the scoped set, not the whole catalogue
