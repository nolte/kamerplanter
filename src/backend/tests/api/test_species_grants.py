"""Explicit masterdata grants: share a species without making it global (#1092).

REQ-001 v4.0 names a `tenant_has_access` edge for grants beyond ownership. It was
created nowhere, declared nowhere, and read by exactly one consumer
(`starter_kit_service`) that degraded to *"return everything"* when the collection
was absent — so the read side was unenforced and the write side did not exist.

The decided use case: **a community garden shares a cultivar it maintains with a
member tenant**, without that row becoming global. Granted by the owning tenant's
`lead`, per record.

Three properties carry the security of this feature, and each is easy to ship
half-done:

* **read-only.** The grant makes a row *visible*; it must not make it editable or
  deletable. A grantee gaining write access would be a far worse outcome than the
  feature not existing.
* **revocation works.** A grant nobody can take back is a permanent share wearing
  a revocable label — which is why the revoke path ships with the grant path and
  not after it.
* **the grant list is owner-only.** A grantee enumerating the other grantees turns
  a share into a directory of which tenants exist.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.species.router import router as species_router
from app.common import auth as auth_mod
from app.common.dependencies import get_family_repo, get_species_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.models.species import Cultivar, Species
from app.domain.models.tenant_context import TenantContext

_OWNER = "tenant_garden"
_GRANTEE = "tenant_member"
_STRANGER = "tenant_other"


class _Repo:
    """Records grants, so "refused" is provable as an absent edge."""

    def __init__(self, owner: str = _OWNER) -> None:
        self.species = Species(key="sp1", scientific_name="Solanum lycopersicum", tenant_key=owner)
        self.grants: set[str] = set()

    def get_or_raise(self, key: str) -> Species:
        return self.species

    def grant_access(self, species_key: str, to_tenant_key: str) -> None:
        self.grants.add(to_tenant_key)

    def revoke_access(self, species_key: str, from_tenant_key: str) -> bool:
        if from_tenant_key in self.grants:
            self.grants.discard(from_tenant_key)
            return True
        return False

    def list_grants(self, species_key: str) -> list[str]:
        return sorted(self.grants)


def _client(repo: _Repo, *, acting_tenant: str = _OWNER, role: TenantRole = TenantRole.LEAD) -> TestClient:
    from app.domain.services.species_service import SpeciesService

    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(species_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="u1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: SimpleNamespace()
    app.dependency_overrides[auth_mod.get_is_platform_admin] = lambda: False
    app.dependency_overrides[auth_mod.get_active_tenant_key] = lambda: acting_tenant
    app.dependency_overrides[auth_mod.get_active_tenant_context] = lambda: TenantContext(
        tenant_key=acting_tenant, tenant_slug="acting", user_key="u1", role=role, admin_scopes=[]
    )
    return TestClient(app)


@pytest.fixture
def repo() -> _Repo:
    return _Repo()


# ── the owner may share ──────────────────────────────────────────────────────


def test_the_owner_can_grant_access(repo: _Repo) -> None:
    response = _client(repo).post("/api/v1/species/sp1/grants", json={"grantee_tenant_key": _GRANTEE})

    assert response.status_code == 204, response.text
    assert repo.grants == {_GRANTEE}


def test_granting_twice_leaves_one_grant(repo: _Repo) -> None:
    """Idempotent, so a double submit cannot make revocation partial."""
    client = _client(repo)
    client.post("/api/v1/species/sp1/grants", json={"grantee_tenant_key": _GRANTEE})
    client.post("/api/v1/species/sp1/grants", json={"grantee_tenant_key": _GRANTEE})

    assert repo.grants == {_GRANTEE}


def test_granting_to_the_owner_itself_is_refused(repo: _Repo) -> None:
    """Meaningless, and silently writing it would leave an edge revocation never
    looks for — a grant that exists but no path can remove."""
    response = _client(repo).post("/api/v1/species/sp1/grants", json={"grantee_tenant_key": _OWNER})

    assert response.status_code == 422, response.text
    assert repo.grants == set()


# ── who may not ──────────────────────────────────────────────────────────────


def test_a_foreign_tenant_cannot_share_someone_elses_species(repo: _Repo) -> None:
    """404, not 403: a foreign row must not be confirmed to exist.

    Ownership hiding, identical to the edit path — the gate is literally the same
    function, so the two cannot drift into answering differently.
    """
    response = _client(repo, acting_tenant=_STRANGER).post(
        "/api/v1/species/sp1/grants", json={"grantee_tenant_key": _GRANTEE}
    )

    assert response.status_code == 404, response.text
    assert repo.grants == set()


def test_a_viewer_of_the_owning_tenant_cannot_share(repo: _Repo) -> None:
    """Sharing is a write about the row, even though it does not change the row."""
    response = _client(repo, role=TenantRole.VIEWER).post(
        "/api/v1/species/sp1/grants", json={"grantee_tenant_key": _GRANTEE}
    )

    assert response.status_code == 403, response.text
    assert repo.grants == set()


def test_a_grantee_cannot_grant_onward(repo: _Repo) -> None:
    """A grant conveys visibility, not authority. Without this, one share would
    let the recipient redistribute a row it does not own."""
    repo.grants.add(_GRANTEE)

    response = _client(repo, acting_tenant=_GRANTEE).post(
        "/api/v1/species/sp1/grants", json={"grantee_tenant_key": _STRANGER}
    )

    assert response.status_code == 404, response.text
    assert repo.grants == {_GRANTEE}


# ── revocation, shipped with the grant rather than after it ──────────────────


def test_the_owner_can_revoke(repo: _Repo) -> None:
    repo.grants.add(_GRANTEE)

    response = _client(repo).delete(f"/api/v1/species/sp1/grants/{_GRANTEE}")

    assert response.status_code == 204, response.text
    assert repo.grants == set()


def test_revoking_a_grant_that_is_not_there_is_not_an_error(repo: _Repo) -> None:
    """The caller's intent — "this tenant must not see it" — is satisfied either way."""
    response = _client(repo).delete(f"/api/v1/species/sp1/grants/{_GRANTEE}")

    assert response.status_code == 204, response.text


def test_a_grantee_cannot_revoke_its_own_removal_or_anyone_elses(repo: _Repo) -> None:
    repo.grants.update({_GRANTEE, _STRANGER})

    response = _client(repo, acting_tenant=_GRANTEE).delete(f"/api/v1/species/sp1/grants/{_STRANGER}")

    assert response.status_code == 404, response.text
    assert repo.grants == {_GRANTEE, _STRANGER}


# ── the grant list is not a tenant directory ─────────────────────────────────


def test_the_owner_sees_who_it_shared_with(repo: _Repo) -> None:
    repo.grants.update({_GRANTEE, _STRANGER})

    response = _client(repo).get("/api/v1/species/sp1/grants")

    assert response.status_code == 200, response.text
    assert response.json() == sorted([_GRANTEE, _STRANGER])


def test_a_grantee_cannot_enumerate_the_other_grantees(repo: _Repo) -> None:
    """Otherwise a share becomes a directory of which tenants exist."""
    repo.grants.update({_GRANTEE, _STRANGER})

    response = _client(repo, acting_tenant=_GRANTEE).get("/api/v1/species/sp1/grants")

    assert response.status_code == 404, response.text


# ── the read predicate, which is where visibility actually widens ────────────


def test_the_grant_arm_is_opt_in_and_not_in_the_shared_predicate() -> None:
    """The shared two-arm predicate has 24 call sites — fertilizers, AI
    conversations, tasks — and one narrows further on purpose. Adding the grant arm
    there would have widened every one of them at once, which is not what an
    explicit *masterdata* grant means.
    """
    from app.data_access.arango.tenant_scope import (
        tenant_union_predicate,
        tenant_union_with_grants_predicate,
    )

    plain, _ = tenant_union_predicate("t1")
    with_grants, _ = tenant_union_with_grants_predicate("t1")

    assert "tenant_has_access" not in plain
    assert "tenant_has_access" in with_grants


def test_the_grant_arm_stays_inside_the_parentheses() -> None:
    """A caller drops this fragment into a larger FILTER. An arm spliced outside
    the parentheses would bind by OR against the *whole* filter and make every row
    visible — the widest possible failure, from a missing bracket."""
    from app.data_access.arango.tenant_scope import tenant_union_with_grants_predicate

    predicate, _ = tenant_union_with_grants_predicate("t1")

    assert predicate.startswith("(")
    assert predicate.endswith(")")
    assert predicate.count("(") == predicate.count(")")


def test_the_predicate_binds_the_tenant_rather_than_interpolating_it() -> None:
    """SEC-B4: the tenant value is never spliced into AQL text."""
    from app.data_access.arango.tenant_scope import tenant_union_with_grants_predicate

    predicate, binds = tenant_union_with_grants_predicate("tenant_acme")

    assert "tenant_acme" not in predicate
    assert binds == {"tenant_key": "tenant_acme"}


def test_the_grant_arm_matches_by_document_id_so_it_serves_both_catalogues() -> None:
    """Species and cultivars share one edge and one predicate.

    The arm compares ``__g._to`` to ``doc._id``, and an ArangoDB ``_id`` already
    carries its collection — so the same fragment scopes species and cultivar
    reads without a collection parameter. A predicate that hard-coded ``species/``
    would have made the cultivar grant silently inert, which is the record type
    #1092 was actually decided for.
    """
    from app.data_access.arango.tenant_scope import tenant_union_with_grants_predicate

    predicate, _ = tenant_union_with_grants_predicate("t1")

    assert "doc._id" in predicate
    assert "species/" not in predicate
    assert "cultivars/" not in predicate


# ── the detail read, the half that is easiest to leave out ───────────────────


class _DetailRepo(_Repo):
    """Adds the by-key lookups ``get_species`` performs."""

    def is_granted_to(self, species_key: str, tenant_key: str) -> bool:
        return tenant_key in self.grants


def test_a_granted_species_can_actually_be_opened() -> None:
    """A grant that lists the row but 404s when it is opened is shipped half-done,
    and the missing half is the one the recipient uses.

    The list query and the detail read are separate code paths — a predicate arm
    does nothing for a by-key load — so this is not implied by the read-predicate
    tests above.
    """
    from app.domain.services.species_service import SpeciesService

    repo = _DetailRepo()
    repo.grants.add(_GRANTEE)
    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]

    assert service.get_species("sp1", tenant_key=_GRANTEE).key == "sp1"


def test_an_ungranted_foreign_species_still_404s_on_the_detail_read() -> None:
    """The counterfactual for the test above: without the grant the same call must
    still refuse, or the new arm would simply have opened the detail read to
    everyone."""
    from app.common.exceptions import NotFoundError
    from app.domain.services.species_service import SpeciesService

    service = SpeciesService(_DetailRepo(), graph_repo=None)  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        service.get_species("sp1", tenant_key=_STRANGER)


def test_an_anonymous_caller_is_not_treated_as_a_granted_tenant() -> None:
    """``tenant_key == ""`` is the light-mode/anonymous caller. It is also what an
    unset grant edge would compare equal to, so the check is guarded on a truthy
    tenant — otherwise "no tenant" could match "granted to nobody"."""
    from app.common.exceptions import NotFoundError
    from app.domain.services.species_service import SpeciesService

    repo = _DetailRepo()
    repo.grants.add("")
    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        service.get_species("sp1", tenant_key="")


# ── the cultivar pendant, which is the record type #1092 was decided for ─────


class _CultivarRepo:
    """Cultivar-side double. Separate from ``_Repo`` on purpose: the point of these
    tests is that the *cultivar* routes carry their own gate, and reusing the
    species double would have let a missing cultivar path pass on a species one."""

    def __init__(self, owner: str = _OWNER) -> None:
        self.cultivar = Cultivar(key="cv1", name="Gardener's Delight", species_key="sp1", tenant_key=owner)
        self.grants: set[str] = set()

    def get_cultivar_or_raise(self, key: str) -> Cultivar:
        return self.cultivar

    def grant_cultivar_access(self, cultivar_key: str, to_tenant_key: str) -> None:
        self.grants.add(to_tenant_key)

    def revoke_cultivar_access(self, cultivar_key: str, from_tenant_key: str) -> bool:
        if from_tenant_key in self.grants:
            self.grants.discard(from_tenant_key)
            return True
        return False

    def list_cultivar_grants(self, cultivar_key: str) -> list[str]:
        return sorted(self.grants)

    def is_cultivar_granted_to(self, cultivar_key: str, tenant_key: str) -> bool:
        return tenant_key in self.grants


def _cultivar_client(
    repo: _CultivarRepo, *, acting_tenant: str = _OWNER, role: TenantRole = TenantRole.LEAD
) -> TestClient:
    from app.api.v1.cultivars.router import router as cultivars_router
    from app.domain.services.species_service import SpeciesService

    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(cultivars_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="u1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[auth_mod.get_is_platform_admin] = lambda: False
    app.dependency_overrides[auth_mod.get_active_tenant_key] = lambda: acting_tenant
    app.dependency_overrides[auth_mod.get_creating_tenant_key] = lambda: acting_tenant
    app.dependency_overrides[auth_mod.get_active_tenant_context] = lambda: TenantContext(
        tenant_key=acting_tenant, tenant_slug="acting", user_key="u1", role=role, admin_scopes=[]
    )
    return TestClient(app)


_CV_GRANTS = "/api/v1/species/sp1/cultivars/cv1/grants"


def test_the_owner_can_share_a_cultivar() -> None:
    repo = _CultivarRepo()

    response = _cultivar_client(repo).post(_CV_GRANTS, json={"grantee_tenant_key": _GRANTEE})

    assert response.status_code == 204, response.text
    assert repo.grants == {_GRANTEE}


def test_a_foreign_tenant_cannot_share_someone_elses_cultivar() -> None:
    repo = _CultivarRepo()

    response = _cultivar_client(repo, acting_tenant=_STRANGER).post(_CV_GRANTS, json={"grantee_tenant_key": _GRANTEE})

    assert response.status_code == 404, response.text
    assert repo.grants == set()


def test_a_viewer_cannot_share_a_cultivar() -> None:
    repo = _CultivarRepo()

    response = _cultivar_client(repo, role=TenantRole.VIEWER).post(_CV_GRANTS, json={"grantee_tenant_key": _GRANTEE})

    assert response.status_code == 403, response.text
    assert repo.grants == set()


def test_a_cultivar_grant_can_be_revoked() -> None:
    repo = _CultivarRepo()
    repo.grants.add(_GRANTEE)

    response = _cultivar_client(repo).delete(f"{_CV_GRANTS}/{_GRANTEE}")

    assert response.status_code == 204, response.text
    assert repo.grants == set()


def test_a_cultivar_grantee_cannot_enumerate_the_other_grantees() -> None:
    repo = _CultivarRepo()
    repo.grants.update({_GRANTEE, _STRANGER})

    response = _cultivar_client(repo, acting_tenant=_GRANTEE).get(_CV_GRANTS)

    assert response.status_code == 404, response.text


def test_a_granted_cultivar_can_actually_be_opened() -> None:
    """The cultivar detail read has its own ownership check, so the species-side
    test above proves nothing about it."""
    from app.domain.services.species_service import SpeciesService

    repo = _CultivarRepo()
    repo.grants.add(_GRANTEE)
    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]

    assert service.get_cultivar("cv1", tenant_key=_GRANTEE).key == "cv1"


def test_an_ungranted_foreign_cultivar_still_404s() -> None:
    from app.common.exceptions import NotFoundError
    from app.domain.services.species_service import SpeciesService

    service = SpeciesService(_CultivarRepo(), graph_repo=None)  # type: ignore[arg-type]

    with pytest.raises(NotFoundError):
        service.get_cultivar("cv1", tenant_key=_STRANGER)
