"""Species by-key read + write tenant isolation and role gating (SEC-001/002/005, #808).

The security-review of the sprint-2 species tenant-scoping work found that the
by-key read (:meth:`SpeciesService.get_species`) and the mutations
(:meth:`~SpeciesService.update_species` / :meth:`~SpeciesService.delete_species`)
were unscoped: any authenticated caller could read, edit or delete *any* tenant's
species by key, and the global seed catalogue (``tenant_key == ""``) too.

These service-level tests pin the fix at the layer that owns the decision:

* SEC-001 — a foreign species answers 404 (ownership hiding, never a 403 oracle);
  the caller's own and the global seeds resolve; ``tenant_key=None`` stays the
  unscoped internal load.
* SEC-002 — a foreign mutation → 404; a *global* mutation → platform-admin only
  (403 for anyone else); an *own* mutation → domain role gate (a viewer may not
  edit, only a lead may delete).
* SEC-005 — the latent ``search_species`` threads the tenant into the repository.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.species import Species
from app.domain.services.species_service import SpeciesService
from tests.support.grant_fakes import NoGrantsMixin


class _FakeRepo(NoGrantsMixin):
    """Minimal repo over an in-memory catalogue keyed by document key."""

    def __init__(self, species: list[Species]) -> None:
        self._by_key = {s.key: s for s in species}
        self.updated: list[str] = []
        self.deleted: list[str] = []
        self.search_calls: list[dict] = []

    def get_or_raise(self, key: str) -> Species:
        s = self._by_key.get(key)
        if s is None:
            raise NotFoundError("Species", key)
        return s

    def update(self, key: str, species: Species) -> Species:
        self.updated.append(key)
        return species

    def delete(self, key: str) -> bool:
        self.deleted.append(key)
        return True

    def search(self, name=None, family_key=None, *, tenant_key=None):
        self.search_calls.append({"name": name, "family_key": family_key, "tenant_key": tenant_key})
        return []


def _catalogue() -> list[Species]:
    return [
        Species(_key="global_seed", scientific_name="Rosa canina", tenant_key=""),
        Species(_key="own", scientific_name="Ocimum basilicum", tenant_key="t1"),
        Species(_key="foreign", scientific_name="Cannabis sativa", tenant_key="t2"),
    ]


def _service(repo: _FakeRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


# ── SEC-001: single-species read scoping ─────────────────────────────────────


def test_get_species_own_and_global_resolve_for_the_caller():
    service = _service(_FakeRepo(_catalogue()))
    assert service.get_species("own", tenant_key="t1").key == "own"
    assert service.get_species("global_seed", tenant_key="t1").key == "global_seed"


def test_get_species_foreign_is_hidden_as_404():
    # verifies_sprint_value: a foreign species must not be readable by key, and the
    # signal is 404 (ownership hiding), never 403 — no cross-tenant existence oracle.
    service = _service(_FakeRepo(_catalogue()))
    with pytest.raises(NotFoundError):
        service.get_species("foreign", tenant_key="t1")


def test_get_species_anonymous_sees_only_global():
    service = _service(_FakeRepo(_catalogue()))
    assert service.get_species("global_seed", tenant_key="").key == "global_seed"
    # An anonymous caller ("") sees a tenant-owned species (even its own would-be
    # rows) as absent — the union collapses to global-only.
    with pytest.raises(NotFoundError):
        service.get_species("own", tenant_key="")


def test_get_species_unscoped_none_is_the_internal_system_load():
    # Internal callers (migrations/enrichment/companion existence checks) pass no
    # tenant and must still resolve any row, regardless of owner.
    service = _service(_FakeRepo(_catalogue()))
    assert service.get_species("foreign").key == "foreign"


# ── SEC-002: update ownership + role gating ──────────────────────────────────


def _incoming() -> Species:
    return Species(scientific_name="Edited name")


def test_update_foreign_species_is_hidden_as_404():
    repo = _FakeRepo(_catalogue())
    with pytest.raises(NotFoundError):
        _service(repo).update_species(
            "foreign", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False
        )
    assert repo.updated == []


def test_update_global_species_by_non_admin_is_forbidden():
    repo = _FakeRepo(_catalogue())
    with pytest.raises(ForbiddenError):
        _service(repo).update_species(
            "global_seed", _incoming(), tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False
        )
    assert repo.updated == []


def test_update_global_species_by_platform_admin_proceeds():
    repo = _FakeRepo(_catalogue())
    _service(repo).update_species(
        "global_seed", _incoming(), tenant_key="t1", caller_role=TenantRole.VIEWER, is_platform_admin=True
    )
    assert repo.updated == ["global_seed"]


def test_update_own_species_by_viewer_is_forbidden():
    # verifies_sprint_value: a viewer must not write, mirroring the sibling
    # tenant-scoped mutations' role gate (MembershipEngine.can_edit_resource).
    repo = _FakeRepo(_catalogue())
    with pytest.raises(ForbiddenError):
        _service(repo).update_species(
            "own", _incoming(), tenant_key="t1", caller_role=TenantRole.VIEWER, is_platform_admin=False
        )
    assert repo.updated == []


def test_update_own_species_by_grower_proceeds():
    repo = _FakeRepo(_catalogue())
    _service(repo).update_species(
        "own", _incoming(), tenant_key="t1", caller_role=TenantRole.GROWER, is_platform_admin=False
    )
    assert repo.updated == ["own"]


def test_update_unscoped_none_keeps_internal_callers_working():
    # The system-context update path (no tenant) applies no ownership/role gate.
    repo = _FakeRepo(_catalogue())
    _service(repo).update_species("foreign", _incoming())
    assert repo.updated == ["foreign"]


# ── SEC-002: delete ownership + the stricter delete role boundary ────────────


def test_delete_foreign_species_is_hidden_as_404():
    repo = _FakeRepo(_catalogue())
    with pytest.raises(NotFoundError):
        _service(repo).delete_species("foreign", tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False)
    assert repo.deleted == []


def test_delete_global_species_by_non_admin_is_forbidden():
    repo = _FakeRepo(_catalogue())
    with pytest.raises(ForbiddenError):
        _service(repo).delete_species(
            "global_seed", tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False
        )
    assert repo.deleted == []


def test_delete_own_species_by_grower_is_forbidden_only_lead_may_delete():
    # REQ-049 §2.3 irreversibility boundary: a grower may edit but not delete.
    repo = _FakeRepo(_catalogue())
    with pytest.raises(ForbiddenError):
        _service(repo).delete_species("own", tenant_key="t1", caller_role=TenantRole.GROWER, is_platform_admin=False)
    assert repo.deleted == []


def test_delete_own_species_by_lead_proceeds():
    repo = _FakeRepo(_catalogue())
    _service(repo).delete_species("own", tenant_key="t1", caller_role=TenantRole.LEAD, is_platform_admin=False)
    assert repo.deleted == ["own"]


# ── SEC-005: latent search threads the tenant into the repository ────────────


def test_search_species_threads_the_tenant_key():
    repo = _FakeRepo(_catalogue())
    _service(repo).search_species(name="Rosa", tenant_key="t1")
    assert repo.search_calls == [{"name": "Rosa", "family_key": None, "tenant_key": "t1"}]


def test_search_species_defaults_to_unscoped_none():
    repo = _FakeRepo(_catalogue())
    _service(repo).search_species(name="Rosa")
    assert repo.search_calls[0]["tenant_key"] is None
