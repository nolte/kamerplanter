"""SpeciesService cultivar reads are tenant-isolated — both directions (C-3, #1090).

The Cultivar pendant of ``test_species_tenant_scope.py``. Two acceptance halves,
both load-bearing (#324 taught that closing one re-opens the other):

* the global seed catalogue (``tenant_key == ""``) AND the caller's own cultivars
  stay visible — a strict ``== @caller`` filter would blank the catalogue that
  migration ``v0038`` deliberately left global;
* a *foreign* tenant's cultivar never appears in another tenant's list, and its
  by-key read answers :class:`NotFoundError` (404, never 403 — no existence
  oracle), exactly like :meth:`SpeciesService.get_species`.

The fake repository models the real hand-written AQL union in Python, so these
tests exercise the service's *wiring*: dropping the ``tenant_key`` pass-through
makes the fake fall back to its unscoped whole-collection branch and the foreign
cultivar leaks — the red-first state these tests guard against.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.species import Cultivar, Species
from app.domain.services.species_service import SpeciesService

_SPECIES = [
    Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
    Species(_key="sp_own", scientific_name="Rosa canina", tenant_key="tenant_self"),
    Species(_key="sp_foreign", scientific_name="Cannabis sativa", tenant_key="tenant_other"),
]

_CULTIVARS = [
    Cultivar(_key="cv_global", name="Genovese", species_key="sp_global", tenant_key=""),
    Cultivar(_key="cv_own", name="Own Basil", species_key="sp_global", tenant_key="tenant_self"),
    Cultivar(_key="cv_foreign", name="Foreign Basil", species_key="sp_global", tenant_key="tenant_other"),
]


class _FakeUnionSpeciesRepo:
    """Models the repository's three-arm hybrid-catalogue union for cultivars.

    ``tenant_key is None`` is the unscoped system read (whole collection); a string
    (including ``""``) applies the union: rows owned by that tenant, the global
    seeds (``""``) and legacy ``null`` — never a foreign tenant's.
    """

    def __init__(self) -> None:
        self.get_cultivars_calls: list[tuple[str, str | None]] = []

    def get_or_raise(self, key: str) -> Species:
        for species in _SPECIES:
            if species.key == key:
                return species
        raise NotFoundError("Species", key)

    def get_cultivars(self, species_key: str, *, tenant_key: str | None = None) -> list[Cultivar]:
        self.get_cultivars_calls.append((species_key, tenant_key))
        rows = [c for c in _CULTIVARS if c.species_key == species_key]
        if tenant_key is None:
            return rows
        return [c for c in rows if c.tenant_key in (tenant_key, "", None)]

    def get_cultivar_or_raise(self, key: str) -> Cultivar:
        for cultivar in _CULTIVARS:
            if cultivar.key == key:
                return cultivar
        raise NotFoundError("Cultivar", key)


@pytest.fixture
def repo() -> _FakeUnionSpeciesRepo:
    return _FakeUnionSpeciesRepo()


@pytest.fixture
def service(repo: _FakeUnionSpeciesRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


def _names(cultivars: list[Cultivar]) -> set[str]:
    return {c.name for c in cultivars}


# ── list_cultivars: both directions ──────────────────────────────────────────


def test_own_tenant_sees_global_and_own_cultivars(service):
    # Direction 1 (#324): the shared seed catalogue stays visible next to own rows.
    result = service.list_cultivars("sp_global", tenant_key="tenant_self")

    assert _names(result) == {"Genovese", "Own Basil"}


def test_foreign_tenant_cultivar_does_not_leak(service):
    # Direction 2 (the leak #1090 closes): tenant_other's cultivar is absent from
    # tenant_self's list. Dropping the tenant pass-through in the service makes the
    # fake take its unscoped branch and this assertion fails.
    result = service.list_cultivars("sp_global", tenant_key="tenant_self")

    assert "Foreign Basil" not in _names(result)


def test_the_other_direction_also_isolates(service):
    # Symmetry: tenant_other sees global + its own, never tenant_self's.
    result = service.list_cultivars("sp_global", tenant_key="tenant_other")

    assert _names(result) == {"Genovese", "Foreign Basil"}


def test_anonymous_caller_sees_exactly_the_global_catalogue(service):
    # No resolvable tenant → "" → global-only: never an error, never all tenants
    # (REQ-027 light mode / anonymous, P4).
    result = service.list_cultivars("sp_global", tenant_key="")

    assert _names(result) == {"Genovese"}


def test_system_context_read_stays_unscoped(service, repo):
    # P5: the default (no tenant argument) is the unscoped system read every seeder
    # and dereference path relies on — it must still see tenant-owned rows.
    result = service.list_cultivars("sp_global")

    assert _names(result) == {"Genovese", "Own Basil", "Foreign Basil"}
    assert repo.get_cultivars_calls[-1] == ("sp_global", None)


def test_the_tenant_is_threaded_into_the_repository_read(service, repo):
    # Non-inertness: the scoping must happen in the repository query, not by a
    # post-filter the next caller can forget.
    service.list_cultivars("sp_global", tenant_key="tenant_self")

    assert repo.get_cultivars_calls[-1] == ("sp_global", "tenant_self")


# ── Q3: the species-existence check is co-scoped ─────────────────────────────


def test_listing_cultivars_of_a_foreign_species_is_a_404(service, repo):
    # Operator decision Q3: a foreign tenant's species must not answer with an empty
    # list (which would confirm the key exists) — it answers 404, like the species
    # by-key read. The cultivar read must not even be attempted.
    with pytest.raises(NotFoundError):
        service.list_cultivars("sp_foreign", tenant_key="tenant_self")

    assert repo.get_cultivars_calls == []


def test_listing_cultivars_of_a_global_species_is_allowed(service):
    result = service.list_cultivars("sp_global", tenant_key="tenant_self")

    assert result  # the global species resolves for every tenant


def test_system_context_may_list_cultivars_of_any_species(service):
    # tenant_key=None keeps the pre-#1090 behaviour for internal callers.
    assert service.list_cultivars("sp_foreign") == []


# ── get_cultivar: ownership hiding (404, never 403) ──────────────────────────


def test_get_cultivar_hides_a_foreign_tenants_row_as_404(service):
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_foreign", tenant_key="tenant_self")


def test_get_cultivar_resolves_a_global_row_for_every_tenant(service):
    assert service.get_cultivar("cv_global", tenant_key="tenant_self").name == "Genovese"


def test_get_cultivar_resolves_the_callers_own_row(service):
    assert service.get_cultivar("cv_own", tenant_key="tenant_self").name == "Own Basil"


def test_get_cultivar_for_an_anonymous_caller_sees_only_global(service):
    assert service.get_cultivar("cv_global", tenant_key="").name == "Genovese"
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_own", tenant_key="")


def test_get_cultivar_without_a_tenant_stays_the_system_read(service):
    # P5: update/delete and the dereference paths load unscoped on purpose.
    assert service.get_cultivar("cv_foreign").name == "Foreign Basil"


def test_the_list_read_and_the_by_key_read_agree_on_visibility(service):
    """A cultivar is listed if and only if it also resolves by key (C-6, #816 spirit).

    The two cultivar reads express the *same* visibility rule in two languages: the
    list read as the three-arm AQL union inside the repository, the by-key read as
    the Python post-load check ``cultivar.tenant_key not in (tenant_key, "")`` in
    :meth:`SpeciesService.get_cultivar`. Two encodings of one rule is exactly the
    drift #816 was raised about, and nothing else pins them against each other:
    the tests above grade each read on its own.

    A divergence in either direction is a defect, which is why this is an
    equivalence and not two one-sided checks. Narrowing the by-key check to
    ``!= tenant_key`` would drop the global arm: ``cv_global`` would still be
    listed but 404 by key — a user follows the list into a detail page that says
    the row does not exist. Widening it would do the reverse and hand out a
    foreign row the list correctly hides.
    """
    for tenant in ("tenant_self", "tenant_other", ""):
        listed = {c.key for c in service.list_cultivars("sp_global", tenant_key=tenant)}
        assert listed, f"fixture broken: no cultivar is visible to {tenant!r} at all"

        for cultivar in _CULTIVARS:
            try:
                service.get_cultivar(cultivar.key, tenant_key=tenant)
            except NotFoundError:
                resolves_by_key = False
            else:
                resolves_by_key = True

            assert resolves_by_key is (cultivar.key in listed), (
                f"{cultivar.key} is {'listed' if cultivar.key in listed else 'hidden'} for {tenant!r} but "
                f"{'resolves' if resolves_by_key else 'does not resolve'} by key — the AQL union and the "
                "post-load ownership check disagree about who may see this row (#816)."
            )


def test_a_missing_key_is_the_same_404_as_a_foreign_one(service):
    # No existence oracle: the caller cannot distinguish "not yours" from "not
    # there" — both raise NotFoundError for the same entity name.
    with pytest.raises(NotFoundError) as absent:
        service.get_cultivar("cv_nope", tenant_key="tenant_self")
    with pytest.raises(NotFoundError) as foreign:
        service.get_cultivar("cv_foreign", tenant_key="tenant_self")

    assert type(absent.value) is type(foreign.value)
    assert absent.value.status_code == foreign.value.status_code == 404
