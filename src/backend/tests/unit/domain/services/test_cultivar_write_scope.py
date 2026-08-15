"""Cultivar mutations are ownership- and role-gated (C-4, #1090).

The Cultivar pendant of ``test_species_write_scope.py``. C-3 closed the cultivar
*read* paths; the mutations were still completely ungated: any authenticated
caller could edit or delete **any** tenant's cultivar by key, and the global seed
catalogue too. These service-level tests pin the fix at the layer that owns the
decision — the shared :func:`_authorize_tenant_owned_write` both entities call:

* a *foreign* cultivar → :class:`NotFoundError` (404). Ownership hiding, byte-for-
  byte the answer an absent key gets, so a mutation cannot be used as a
  cross-tenant existence oracle either.
* the *global* catalogue (``tenant_key == ""``) → platform admin only, else
  :class:`ForbiddenError` (403). The row is visible to everyone, so the honest
  signal is "not allowed", not "not there".
* the caller's *own* cultivar → the domain role gate: ``can_edit_resource`` for
  update (a viewer is refused), ``can_delete_resource`` for delete — lead-only,
  the REQ-049 §2.3 irreversibility boundary.
* ``tenant_key is None`` (system context) → no gate at all, so the seeders, the
  CSV import and the migration paths keep working unchanged (P5).

Plus the create-path leak C-3 handed over: ``create_cultivar`` resolved its parent
species **unscoped**, so a POST under a *foreign* tenant's species answered 201 and
hung a ``has_cultivar`` edge off that foreign species — an existence oracle *and* a
write into a foreign tenant's graph. The species lookup is co-scoped on the
interactive path (operator decision Q3, same rule as ``list_cultivars``).
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.species import Cultivar, Species
from app.domain.services.species_service import SpeciesService
from tests.support.grant_fakes import NoGrantsMixin


class _FakeRepo(NoGrantsMixin):
    """Minimal repo over in-memory species + cultivar catalogues, keyed by document key."""

    def __init__(self, species: list[Species], cultivars: list[Cultivar]) -> None:
        self._species = {s.key: s for s in species}
        self._cultivars = {c.key: c for c in cultivars}
        self.created: list[Cultivar] = []
        self.updated: list[str] = []
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

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.created.append(cultivar)
        return cultivar

    def update_cultivar(self, key: str, cultivar: Cultivar) -> Cultivar:
        self.updated.append(key)
        return cultivar

    def delete_cultivar(self, key: str) -> bool:
        self.deleted.append(key)
        return True


def _catalogue() -> tuple[list[Species], list[Cultivar]]:
    species = [
        Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
        Species(_key="sp_own", scientific_name="Rosa canina", tenant_key="t1"),
        Species(_key="sp_foreign", scientific_name="Cannabis sativa", tenant_key="t2"),
    ]
    cultivars = [
        Cultivar(_key="cv_global", name="Genovese", species_key="sp_global", tenant_key=""),
        Cultivar(_key="cv_own", name="Own Basil", species_key="sp_global", tenant_key="t1"),
        Cultivar(_key="cv_foreign", name="Foreign Basil", species_key="sp_global", tenant_key="t2"),
    ]
    return species, cultivars


@pytest.fixture
def repo() -> _FakeRepo:
    return _FakeRepo(*_catalogue())


@pytest.fixture
def service(repo: _FakeRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


def _incoming() -> Cultivar:
    return Cultivar(name="Edited name", species_key="sp_global")


# ── update: ownership + role gating ──────────────────────────────────────────


def test_update_foreign_cultivar_is_hidden_as_404(service, repo):
    # verifies_sprint_value: a foreign cultivar must not be editable, and the signal
    # is 404 (ownership hiding), never 403 — no cross-tenant existence oracle.
    with pytest.raises(NotFoundError):
        service.update_cultivar(
            "cv_foreign", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False
        )

    assert repo.updated == []


def test_update_global_cultivar_by_non_admin_is_forbidden(service, repo):
    with pytest.raises(ForbiddenError):
        service.update_cultivar(
            "cv_global", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False
        )

    assert repo.updated == []


def test_update_global_cultivar_by_platform_admin_proceeds(service, repo):
    service.update_cultivar(
        "cv_global", _incoming(), tenant_key="t1", caller_role=TenantRole.VIEWER, is_platform_admin=True
    )

    assert repo.updated == ["cv_global"]


def test_update_own_cultivar_by_viewer_is_forbidden(service, repo):
    # verifies_sprint_value: a viewer must not write (MembershipEngine.can_edit_resource).
    with pytest.raises(ForbiddenError):
        service.update_cultivar(
            "cv_own", _incoming(), tenant_key="t1", caller_role=TenantRole.VIEWER, is_platform_admin=False
        )

    assert repo.updated == []


def test_update_own_cultivar_by_grower_proceeds(service, repo):
    service.update_cultivar(
        "cv_own", _incoming(), tenant_key="t1", caller_role=TenantRole.GROWER, is_platform_admin=False
    )

    assert repo.updated == ["cv_own"]


def test_update_own_cultivar_by_lead_proceeds(service, repo):
    service.update_cultivar("cv_own", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD)

    assert repo.updated == ["cv_own"]


def test_update_unscoped_none_keeps_internal_callers_working(service, repo):
    # P5: the system-context update (no tenant argument) applies no ownership/role
    # gate — the seeders and the CSV import rely on it.
    service.update_cultivar("cv_foreign", _incoming())

    assert repo.updated == ["cv_foreign"]


def test_update_still_preserves_the_stored_owner(service, repo):
    # The C-1 ownership preservation must survive the new gate: an own row edited by
    # its owner keeps its tenant_key, it is never reset to the global default.
    updated = service.update_cultivar(
        "cv_own", _incoming(), tenant_key="t1", caller_role=TenantRole.GROWER, is_platform_admin=False
    )

    assert updated.tenant_key == "t1"


# ── delete: the stricter irreversibility boundary ────────────────────────────


def test_delete_foreign_cultivar_is_hidden_as_404(service, repo):
    with pytest.raises(NotFoundError):
        service.delete_cultivar("cv_foreign", tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False)

    assert repo.deleted == []


def test_delete_global_cultivar_by_non_admin_is_forbidden(service, repo):
    with pytest.raises(ForbiddenError):
        service.delete_cultivar("cv_global", tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False)

    assert repo.deleted == []


def test_delete_global_cultivar_by_platform_admin_proceeds(service, repo):
    service.delete_cultivar("cv_global", tenant_key="t1", caller_role=TenantRole.VIEWER, is_platform_admin=True)

    assert repo.deleted == ["cv_global"]


def test_delete_own_cultivar_by_grower_is_forbidden_only_lead_may_delete(service, repo):
    # REQ-049 §2.3 irreversibility boundary: a grower may edit but not delete.
    with pytest.raises(ForbiddenError):
        service.delete_cultivar("cv_own", tenant_key="t1", caller_role=TenantRole.GROWER, is_platform_admin=False)

    assert repo.deleted == []


def test_delete_own_cultivar_by_viewer_is_forbidden(service, repo):
    with pytest.raises(ForbiddenError):
        service.delete_cultivar("cv_own", tenant_key="t1", caller_role=TenantRole.VIEWER, is_platform_admin=False)

    assert repo.deleted == []


def test_delete_own_cultivar_by_lead_proceeds(service, repo):
    service.delete_cultivar("cv_own", tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False)

    assert repo.deleted == ["cv_own"]


def test_delete_unscoped_none_keeps_internal_callers_working(service, repo):
    service.delete_cultivar("cv_foreign")

    assert repo.deleted == ["cv_foreign"]


# ── the mutation gate is not an existence oracle ─────────────────────────────


def test_a_foreign_mutation_is_indistinguishable_from_an_absent_key(service):
    # No oracle: "not yours" and "not there" raise the same error type with the same
    # status. A ForbiddenError here would confirm the foreign key exists.
    with pytest.raises(NotFoundError) as absent:
        service.update_cultivar("cv_nope", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD)
    with pytest.raises(NotFoundError) as foreign:
        service.update_cultivar("cv_foreign", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD)

    assert type(absent.value) is type(foreign.value)
    assert absent.value.status_code == foreign.value.status_code == 404


def test_the_anonymous_caller_cannot_mutate_a_tenant_owned_cultivar(service, repo):
    # An anonymous/light-mode caller resolves to "" — a tenant-owned row is a
    # foreign row for them (404), and the global catalogue needs platform admin.
    with pytest.raises(NotFoundError):
        service.delete_cultivar("cv_own", tenant_key="", caller_role=TenantRole.LEAD, is_platform_admin=False)

    assert repo.deleted == []


# ── create: the parent-species lookup is co-scoped (C-3 hand-over) ───────────


def test_create_under_a_foreign_species_is_a_404(service, repo):
    # The leak C-3 found: unscoped, this answered 201 and attached a has_cultivar
    # edge to tenant t2's species — a cross-tenant existence oracle plus a write
    # into a foreign tenant's graph.
    with pytest.raises(NotFoundError):
        service.create_cultivar(Cultivar(name="Sneaky", species_key="sp_foreign", tenant_key="t1"), tenant_key="t1")

    assert repo.created == []


def test_create_under_a_global_species_is_allowed(service, repo):
    # The main use case: a tenant adds its own cultivar to a global seed species.
    service.create_cultivar(Cultivar(name="My Genovese", species_key="sp_global", tenant_key="t1"), tenant_key="t1")

    assert [c.name for c in repo.created] == ["My Genovese"]


def test_create_under_the_callers_own_species_is_allowed(service, repo):
    service.create_cultivar(Cultivar(name="My Rose", species_key="sp_own", tenant_key="t1"), tenant_key="t1")

    assert [c.name for c in repo.created] == ["My Rose"]


def test_create_under_a_missing_species_is_still_a_404(service, repo):
    with pytest.raises(NotFoundError):
        service.create_cultivar(Cultivar(name="Nowhere", species_key="sp_nope", tenant_key="t1"), tenant_key="t1")

    assert repo.created == []


def test_create_in_system_context_stays_unscoped(service, repo):
    # P5: the seed loaders and the CSV import create cultivars for every species in
    # the catalogue with no tenant context — they must not start 404-ing.
    service.create_cultivar(Cultivar(name="Seeded", species_key="sp_foreign"))

    assert [c.name for c in repo.created] == ["Seeded"]
