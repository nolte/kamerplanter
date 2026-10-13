"""Hybrid-catalogue creates are role-gated — SEC-005 (#1113), the create sibling of C-4.

``SEC-005`` is qualified with its issue number throughout (R-7): the identifier
already names an unrelated #808 finding (the companion-anchor / ``search_species``
scoping pinned in ``test_species_write_scope.py``). This module is about the
*other* one — the create hole #1090 C-7 reported and #1113 tracks.

The state this closes: ``POST /species`` and ``POST /species/{k}/cultivars``
stamped the caller's active tenant onto the new row but never asked what standing
that caller had in it, while their PUT/DELETE neighbours had been ownership- and
role-gated since #808/#1090. On its own that was survivable — before #1091 the
active tenant was always the caller's *personal* one, where everybody is lead.
The ``X-Active-Tenant`` header (A-2) makes it reachable: an organisation **viewer**
sends the header and writes into the shared org catalogue every member reads.

Pinned here, at the layer that owns the decision — the shared
:func:`~app.domain.services.species_service._authorize_tenant_owned_create` both
entities call:

* viewer → :class:`ForbiddenError` (403). A 403, not a 404: the caller is a real
  member of the tenant, merely under-privileged, and no existing row's existence
  is being hidden.
* grower / lead → created (``can_edit_resource``, REQ-049 §2.3).
* platform admin → created whatever the domain rank, so light-mode curation
  (REQ-027) of the shared catalogue keeps working.
* no defaulted **system context** on these two methods since #2107: the seed
  loaders (``seed_plant_info``, ``seed_data``, ``seed_adventskalender``,
  ``seed_plant_info_extended``) and the CSV import reach the *repository*
  directly, and the identify→create path is the HTTP route — measured, the routes
  are the only callers of ``create_species`` / ``create_cultivar``. So the tenant,
  the role and the platform-admin flag are required, and an omitted one is a
  ``TypeError`` rather than an ungated create.

Plus the property the shared helper exists for: species and cultivar must answer
*identically* for the same role. Two copies of the same rule pass their own tests
and drift the first time one is edited — that is how the delete boundary came
apart from :class:`MembershipEngine` before REQ-049 §2.3 was re-pinned.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.species import Cultivar, Species
from app.domain.services.species_service import SpeciesService


class _FakeRepo:
    """In-memory catalogue covering both create paths of the service."""

    def __init__(self) -> None:
        self._species = {
            "sp_global": Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
            "sp_own": Species(_key="sp_own", scientific_name="Rosa canina", tenant_key="t1"),
            "sp_foreign": Species(_key="sp_foreign", scientific_name="Cannabis sativa", tenant_key="t2"),
        }
        self.created_species: list[Species] = []
        self.created_cultivars: list[Cultivar] = []

    def get_or_raise(self, key: str) -> Species:
        species = self._species.get(key)
        if species is None:
            raise NotFoundError("Species", key)
        return species

    # ── create_species collaborators ────────────────────────────────────────
    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        return None

    def get_by_normalized_scientific_name_for_tenant(self, name: str, tenant_key: str) -> Species | None:
        """Tenant-scoped dedup lookup (#1162). Empty catalogue, so every tenant
        gets the same honest ``None`` — the gate under test is the role check."""
        return None

    def find_synonym_match_candidates(self, species: Species, *, tenant_key: str) -> list[Species]:
        return []

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        self.created_species.append(species)
        return species

    # ── create_cultivar collaborator ────────────────────────────────────────
    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.created_cultivars.append(cultivar)
        return cultivar


@pytest.fixture
def repo() -> _FakeRepo:
    return _FakeRepo()


@pytest.fixture
def service(repo: _FakeRepo) -> SpeciesService:
    return SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]


def _create_species(service: SpeciesService, **gate: object) -> None:
    service.create_species(Species(scientific_name="Ocimum basilicum"), tenant_key="t1", **gate)  # type: ignore[arg-type]


def _create_cultivar(service: SpeciesService, **gate: object) -> None:
    service.create_cultivar(
        Cultivar(name="My Genovese", species_key="sp_global", tenant_key="t1"),
        tenant_key="t1",
        **gate,  # type: ignore[arg-type]
    )


#: The two hybrid-catalogue creates, driven through one matrix so a divergence
#: between them is a test failure rather than a discovery.
_CREATES: list[tuple[str, Callable[..., None]]] = [("species", _create_species), ("cultivar", _create_cultivar)]


# ── the refused arm ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(("entity", "create"), _CREATES)
def test_a_viewer_may_not_create(entity: str, create: Callable[..., None], service: SpeciesService, repo: _FakeRepo):
    # verifies_sprint_value: red-first — before #1113 this created the row and
    # returned 201, so an org viewer could write into the shared org catalogue.
    with pytest.raises(ForbiddenError):
        create(service, caller_role=TenantRole.VIEWER, is_platform_admin=False)

    assert repo.created_species == []
    assert repo.created_cultivars == []


@pytest.mark.parametrize(("entity", "create"), _CREATES)
def test_the_refusal_is_a_403_not_a_404(entity: str, create: Callable[..., None], service: SpeciesService):
    # Unlike the *write* gate's foreign-row arm there is nothing to hide here: the
    # caller is a member of the tenant they are creating in, so the honest signal is
    # "forbidden". A 404 would also be indistinguishable from the parent-species
    # 404 the cultivar create raises for a foreign species, which means something
    # entirely different.
    with pytest.raises(ForbiddenError) as refusal:
        create(service, caller_role=TenantRole.VIEWER, is_platform_admin=False)

    assert refusal.value.status_code == 403


# ── the admitted arms ────────────────────────────────────────────────────────


@pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
@pytest.mark.parametrize(("entity", "create"), _CREATES)
def test_a_writing_role_may_create(
    entity: str, create: Callable[..., None], role: TenantRole, service: SpeciesService, repo: _FakeRepo
):
    create(service, caller_role=role, is_platform_admin=False)

    assert len(repo.created_species) + len(repo.created_cultivars) == 1


@pytest.mark.parametrize(("entity", "create"), _CREATES)
def test_a_platform_admin_may_create_despite_the_viewer_role(
    entity: str, create: Callable[..., None], service: SpeciesService, repo: _FakeRepo
):
    # Light mode (REQ-027): the sole operator holds no membership, so their context
    # role is the fail-safe viewer. Without this arm light-mode curation of the
    # shared catalogue would stop working the moment the gate landed.
    create(service, caller_role=TenantRole.VIEWER, is_platform_admin=True)

    assert len(repo.created_species) + len(repo.created_cultivars) == 1


# ── no defaulted system context (#2107) ──────────────────────────────────────


@pytest.mark.parametrize("method", ["create_species", "create_cultivar"])
def test_the_tenant_role_and_admin_flag_are_required_keywords(method: str):
    # Until #2107 both creates defaulted to the system context (no tenant, no role →
    # no gate), justified by seeders that, measured, write through the repository.
    # A default no caller passes on purpose is one a new caller passes by forgetting.
    parameters = inspect.signature(getattr(SpeciesService, method)).parameters

    for name in ("tenant_key", "caller_role", "is_platform_admin"):
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY, name
        assert parameters[name].default is inspect.Parameter.empty, name


def test_create_species_stamps_the_tenant_it_is_given(service: SpeciesService, repo: _FakeRepo):
    # The model's own ``tenant_key`` (default ``""`` = global) no longer decides the owner:
    # a caller that forgot to stamp it created a global species.
    service.create_species(
        Species(scientific_name="Ocimum basilicum"),
        tenant_key="t1",
        caller_role=TenantRole.GROWER,
        is_platform_admin=False,
    )

    assert [s.tenant_key for s in repo.created_species] == ["t1"]


def test_create_cultivar_stamps_the_tenant_it_resolves_the_parent_in(service: SpeciesService, repo: _FakeRepo):
    service.create_cultivar(
        Cultivar(name="My Genovese", species_key="sp_global"),
        tenant_key="t1",
        caller_role=TenantRole.GROWER,
        is_platform_admin=False,
    )

    assert [c.tenant_key for c in repo.created_cultivars] == ["t1"]


# ── the anti-drift property the shared helper exists for ─────────────────────


@pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD])
def test_species_and_cultivar_answer_identically(role: TenantRole, service: SpeciesService):
    def _refused(create: Callable[..., None]) -> bool:
        try:
            create(service, caller_role=role, is_platform_admin=False)
        except ForbiddenError:
            return True
        return False

    assert _refused(_create_species) == _refused(_create_cultivar), role
