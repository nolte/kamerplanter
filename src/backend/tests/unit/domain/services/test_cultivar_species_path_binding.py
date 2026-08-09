"""A cultivar is only reachable under its own species (SEC-007, #1090).

The by-key cultivar routes are nested — ``/species/{species_key}/cultivars/{cultivar_key}``
— but the service never compared the two. C-7 found the consequence: any cultivar
key resolved under **any** species key, and PUT additionally wrote the *path's*
species into the model, so a caller could re-parent a cultivar to a different
species simply by mistyping the URL. The document moved; the ``has_cultivar``
edge, written once at create time, stayed on the old species. The catalogue then
disagrees with its own graph, and the C-9 owned-reference guard, the MCP tools and
the print/label dereferences all read one or the other.

Two independent layers close it, pinned separately here:

* :meth:`SpeciesService.get_cultivar` refuses a cultivar whose stored
  ``species_key`` is not the requested one — a 404, the same answer an absent key
  gets. ``update_cultivar`` / ``delete_cultivar`` inherit it through their own
  unscoped load.
* :meth:`SpeciesService.update_cultivar` carries the **stored** ``species_key``
  over the payload, exactly as it already does for ``origin`` and ``tenant_key``.
  So even the system-context writers (``tenant_key=None``, ``species_key=None`` —
  the seeders and the CSV import, which are not gated at all) cannot re-parent a
  row away from its edge.

Check order, and why
--------------------
Inside :meth:`get_cultivar` the **species mismatch is decided before ownership**:

1. load unscoped (the ownership arms need the stored owner, C-4);
2. species mismatch → 404;
3. ownership mismatch → 404;
4. (callers then run the role gate, which may answer 403).

The ordering is unobservable for a *foreign* row — both arms answer 404, so the
attacker learns nothing either way. It matters for a *global* row: with ownership
first, a non-admin PUT to ``/species/WRONG/cultivars/cv_global`` would answer
**403** ("you may not edit the global catalogue"), quietly confirming that
``cv_global`` exists and is global while the addressed resource does not exist at
all. Mismatch-first answers 404 there, which is both the honest REST answer for a
path that addresses nothing and strictly *less* information. The mismatch check
also never depends on the caller's role, so it cannot be probed by varying
privileges.

Red-first (measured 2026-08-10, before the fix): the four
``…under_the_wrong_species…`` tests failed — GET/DELETE returned/deleted the row,
and PUT returned it re-parented onto the wrong species with the repository write
already recorded.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.species import Cultivar, Species
from app.domain.services.species_service import SpeciesService


class _FakeRepo:
    """In-memory species + cultivar catalogue with full-replace update semantics."""

    def __init__(self, species: list[Species], cultivars: list[Cultivar]) -> None:
        self._species = {s.key: s for s in species}
        self._cultivars = {c.key: c for c in cultivars}
        self.updated: list[tuple[str, Cultivar]] = []
        self.deleted: list[str] = []

    def get_or_raise(self, key: str) -> Species:
        species = self._species.get(key)
        if species is None:
            raise NotFoundError("Species", key)
        return species

    def get_cultivar_or_raise(self, key: str) -> Cultivar:
        cultivar = self._cultivars.get(key)
        if cultivar is None:
            raise NotFoundError("Cultivar", key)
        return cultivar

    def update_cultivar(self, key: str, cultivar: Cultivar) -> Cultivar:
        self.updated.append((key, cultivar))
        self._cultivars[key] = cultivar
        return cultivar

    def delete_cultivar(self, key: str) -> bool:
        self.deleted.append(key)
        self._cultivars.pop(key, None)
        return True


@pytest.fixture
def repo() -> _FakeRepo:
    return _FakeRepo(
        [
            Species(_key="sp_basil", scientific_name="Ocimum basilicum", tenant_key=""),
            Species(_key="sp_rose", scientific_name="Rosa canina", tenant_key=""),
        ],
        [
            Cultivar(_key="cv_global", name="Genovese", species_key="sp_basil", tenant_key=""),
            Cultivar(_key="cv_own", name="Own Basil", species_key="sp_basil", tenant_key="t1"),
            Cultivar(_key="cv_foreign", name="Foreign Basil", species_key="sp_basil", tenant_key="t2"),
        ],
    )


@pytest.fixture
def service(repo: _FakeRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


def _incoming(species_key: str = "sp_rose") -> Cultivar:
    """The model the router builds — its species_key is the *path* value, not the stored one."""
    return Cultivar(name="Edited name", species_key=species_key)


# ── read: the mismatch is a 404 ──────────────────────────────────────────────


def test_get_under_the_wrong_species_is_404(service):
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_own", species_key="sp_rose", tenant_key="t1")


def test_get_under_the_right_species_is_unchanged(service):
    assert service.get_cultivar("cv_own", species_key="sp_basil", tenant_key="t1").name == "Own Basil"


def test_get_without_a_species_key_stays_the_system_read(service):
    # The seeders, the dereference paths and the service's own gate loads pass no
    # species — they must keep resolving any cultivar by key alone (P5).
    assert service.get_cultivar("cv_own").name == "Own Basil"


def test_a_wrong_species_is_indistinguishable_from_an_absent_cultivar(service):
    # Both are NotFoundError → the same 404 on the wire. Neither reveals that the
    # key exists somewhere else in the catalogue.
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_global", species_key="sp_rose", tenant_key="t1")
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_missing", species_key="sp_rose", tenant_key="t1")


def test_the_mismatch_outranks_the_global_403_arm(service):
    # The check-order decision, made observable: a *global* cultivar addressed under
    # the wrong species is a 404 for a non-admin, not the "only a platform admin may
    # edit the global catalogue" 403 that would confirm the row exists and is global.
    with pytest.raises(NotFoundError):
        service.update_cultivar(
            "cv_global",
            _incoming(),
            species_key="sp_rose",
            tenant_key="t1",
            caller_role=TenantRole.LEAD,
            is_platform_admin=False,
        )


def test_a_foreign_cultivar_answers_404_under_either_species(service):
    # The other half of the order argument: for a foreign row the two arms agree, so
    # the ordering leaks nothing there.
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_foreign", species_key="sp_basil", tenant_key="t1")
    with pytest.raises(NotFoundError):
        service.get_cultivar("cv_foreign", species_key="sp_rose", tenant_key="t1")


# ── update: no re-parenting ──────────────────────────────────────────────────


def test_update_under_the_wrong_species_is_404_and_writes_nothing(service, repo):
    with pytest.raises(NotFoundError):
        service.update_cultivar(
            "cv_own",
            _incoming("sp_rose"),
            species_key="sp_rose",
            tenant_key="t1",
            caller_role=TenantRole.LEAD,
        )

    assert repo.updated == [], "a PUT under the wrong species reached the repository"
    assert repo.get_cultivar_or_raise("cv_own").species_key == "sp_basil"
    assert repo.get_cultivar_or_raise("cv_own").name == "Own Basil"


def test_update_under_the_right_species_still_works(service, repo):
    updated = service.update_cultivar(
        "cv_own",
        _incoming("sp_basil"),
        species_key="sp_basil",
        tenant_key="t1",
        caller_role=TenantRole.LEAD,
    )

    assert updated.name == "Edited name"
    assert updated.species_key == "sp_basil"
    assert [key for key, _cv in repo.updated] == ["cv_own"]


def test_a_system_context_update_cannot_re_parent_either(service, repo):
    # The second layer: no species_key argument at all (the ungated seed/import
    # path) and a payload naming a different species. The stored parent wins, so the
    # document can never drift away from its has_cultivar edge.
    result = service.update_cultivar("cv_own", _incoming("sp_rose"))

    assert result.species_key == "sp_basil"
    assert repo.get_cultivar_or_raise("cv_own").species_key == "sp_basil"


# ── delete: same boundary ────────────────────────────────────────────────────


def test_delete_under_the_wrong_species_is_404_and_deletes_nothing(service, repo):
    with pytest.raises(NotFoundError):
        service.delete_cultivar("cv_own", species_key="sp_rose", tenant_key="t1", caller_role=TenantRole.LEAD)

    assert repo.deleted == []
    assert repo.get_cultivar_or_raise("cv_own").name == "Own Basil"


def test_delete_under_the_right_species_still_works(service, repo):
    assert service.delete_cultivar("cv_own", species_key="sp_basil", tenant_key="t1", caller_role=TenantRole.LEAD)
    assert repo.deleted == ["cv_own"]
