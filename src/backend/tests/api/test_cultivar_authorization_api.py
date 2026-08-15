"""End-to-end cultivar authorization wiring (C-4, #1090).

The Cultivar pendant of ``test_species_authorization_api.py``. Proves the *route
wiring*, not just the service: the real :class:`SpeciesService` runs behind a fake
repository, so the by-key read, the create and the update/delete mutations
exercise the actual tenant scoping and role gate through the HTTP boundary. The
tenant/role/admin dependencies are overridden to model the caller without
reaching the real tenant service.

Matrix pinned here (the route is ``/api/v1/species/{species_key}/cultivars`` — the
router module moved in #1090, the HTTP route did not, K2):

* GET ``/{cultivar_key}`` — foreign → 404, own/global → 200 (C-3, re-pinned here
  so the whole matrix lives in one place);
* PUT/DELETE ``/{cultivar_key}`` — foreign → 404, global by non-admin → 403,
  global by platform admin → 200/204, own viewer → 403, own grower update → 200
  but delete → 403 (REQ-049 §2.3), own lead delete → 204;
* POST ``""`` — under a *foreign* tenant's species → 404 instead of the 201 plus
  foreign-graph ``has_cultivar`` edge the unscoped lookup produced;
* POST ``""`` — SEC-005 (#1113), qualified because ``SEC-005`` names two unrelated
  findings (R-7): viewer → 403, grower/lead → 201, platform admin → 201.

Red-first: against the pre-C-4 router (PUT/DELETE with no tenant dependencies at
all) every mutation answered 200/204 regardless of owner or role; against the
pre-#1113 router the create carried no role dependency, so a viewer answered 201.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.cultivars.router import router as cultivars_router
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_species_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.species import Cultivar, Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.species_service import SpeciesService
from tests.support.grant_fakes import NoGrantsMixin


class _FakeRepo(NoGrantsMixin):
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
        return cultivar.model_copy(update={"key": "cv_new"})

    def update_cultivar(self, key: str, cultivar: Cultivar) -> Cultivar:
        self.updated.append(key)
        return cultivar.model_copy(update={"key": key})

    def delete_cultivar(self, key: str) -> bool:
        self.deleted.append(key)
        return True


def _catalogue() -> _FakeRepo:
    return _FakeRepo(
        [
            Species(_key="sp_global", scientific_name="Ocimum basilicum", tenant_key=""),
            Species(_key="sp_own", scientific_name="Rosa canina", tenant_key="t1"),
            Species(_key="sp_foreign", scientific_name="Cannabis sativa", tenant_key="t2"),
        ],
        [
            Cultivar(_key="cv_global", name="Genovese", species_key="sp_global", tenant_key=""),
            Cultivar(_key="cv_own", name="Own Basil", species_key="sp_global", tenant_key="t1"),
            Cultivar(_key="cv_foreign", name="Foreign Basil", species_key="sp_global", tenant_key="t2"),
        ],
    )


def _app(
    *,
    repo: _FakeRepo,
    active_tenant: str = "t1",
    role: TenantRole = TenantRole.LEAD,
    is_platform_admin: bool = False,
) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(cultivars_router, prefix="/api/v1")
    service = SpeciesService(repo, graph_repo=None)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_active_tenant_key] = lambda: active_tenant
    app.dependency_overrides[get_creating_tenant_key] = lambda: active_tenant
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=active_tenant, tenant_slug="t", user_key="user_1", role=role
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: is_platform_admin
    return app


_BODY = {"name": "Edited name", "species_key": "sp_global"}


# ── by-key read (C-3, re-pinned as part of the matrix) ───────────────────────


def test_get_own_cultivar_returns_200():
    client = TestClient(_app(repo=_catalogue()))
    assert client.get("/api/v1/species/sp_global/cultivars/cv_own").status_code == 200


def test_get_global_cultivar_returns_200():
    client = TestClient(_app(repo=_catalogue()))
    assert client.get("/api/v1/species/sp_global/cultivars/cv_global").status_code == 200


def test_get_foreign_cultivar_returns_404():
    # verifies_sprint_value: a foreign cultivar by key is not an enumerable oracle.
    client = TestClient(_app(repo=_catalogue()))
    assert client.get("/api/v1/species/sp_global/cultivars/cv_foreign").status_code == 404


# ── PUT: ownership + role gate ───────────────────────────────────────────────


def test_update_foreign_cultivar_returns_404():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.LEAD))

    assert client.put("/api/v1/species/sp_global/cultivars/cv_foreign", json=_BODY).status_code == 404
    assert repo.updated == []


def test_update_global_cultivar_by_non_admin_returns_403():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.LEAD, is_platform_admin=False))

    assert client.put("/api/v1/species/sp_global/cultivars/cv_global", json=_BODY).status_code == 403
    assert repo.updated == []


def test_update_global_cultivar_by_platform_admin_returns_200():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.VIEWER, is_platform_admin=True))

    assert client.put("/api/v1/species/sp_global/cultivars/cv_global", json=_BODY).status_code == 200
    assert repo.updated == ["cv_global"]


def test_update_own_cultivar_by_viewer_returns_403():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.VIEWER))

    assert client.put("/api/v1/species/sp_global/cultivars/cv_own", json=_BODY).status_code == 403
    assert repo.updated == []


def test_update_own_cultivar_by_grower_returns_200():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.GROWER))

    resp = client.put("/api/v1/species/sp_global/cultivars/cv_own", json=_BODY)

    assert resp.status_code == 200
    assert repo.updated == ["cv_own"]


# ── DELETE: the stricter lead-only boundary ──────────────────────────────────


def test_delete_foreign_cultivar_returns_404():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.LEAD))

    assert client.delete("/api/v1/species/sp_global/cultivars/cv_foreign").status_code == 404
    assert repo.deleted == []


def test_delete_global_cultivar_by_non_admin_returns_403():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.LEAD))

    assert client.delete("/api/v1/species/sp_global/cultivars/cv_global").status_code == 403
    assert repo.deleted == []


def test_delete_global_cultivar_by_platform_admin_returns_204():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.VIEWER, is_platform_admin=True))

    assert client.delete("/api/v1/species/sp_global/cultivars/cv_global").status_code == 204
    assert repo.deleted == ["cv_global"]


def test_delete_own_cultivar_by_grower_returns_403():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.GROWER))

    assert client.delete("/api/v1/species/sp_global/cultivars/cv_own").status_code == 403
    assert repo.deleted == []


def test_delete_own_cultivar_by_lead_returns_204():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.LEAD))

    assert client.delete("/api/v1/species/sp_global/cultivars/cv_own").status_code == 204
    assert repo.deleted == ["cv_own"]


# ── POST: the parent species is co-scoped (C-3 hand-over) ────────────────────


def test_create_under_a_foreign_species_returns_404():
    # verifies_sprint_value: the unscoped lookup answered 201 and hung a has_cultivar
    # edge off tenant t2's species — an oracle plus a foreign-graph write.
    repo = _catalogue()
    client = TestClient(_app(repo=repo))

    resp = client.post(
        "/api/v1/species/sp_foreign/cultivars",
        json={"name": "Sneaky", "species_key": "sp_foreign"},
    )

    assert resp.status_code == 404
    assert repo.created == []


def test_create_under_a_global_species_returns_201():
    repo = _catalogue()
    client = TestClient(_app(repo=repo))

    resp = client.post(
        "/api/v1/species/sp_global/cultivars",
        json={"name": "My Genovese", "species_key": "sp_global"},
    )

    assert resp.status_code == 201
    assert [c.tenant_key for c in repo.created] == ["t1"]


def test_create_under_the_callers_own_species_returns_201():
    repo = _catalogue()
    client = TestClient(_app(repo=repo))

    resp = client.post(
        "/api/v1/species/sp_own/cultivars",
        json={"name": "My Rose", "species_key": "sp_own"},
    )

    assert resp.status_code == 201


# ── POST: the create role gate (SEC-005, #1113) ──────────────────────────────


_CREATE_BODY = {"name": "My Genovese", "species_key": "sp_global"}


def test_create_cultivar_by_viewer_returns_403():
    # verifies_sprint_value: red-first. Before #1113 the POST route carried no role
    # dependency, so an org viewer acting through a valid ``X-Active-Tenant`` header
    # got 201 and wrote a cultivar into the shared org catalogue.
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.VIEWER))

    resp = client.post("/api/v1/species/sp_global/cultivars", json=_CREATE_BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    assert repo.created == []


def test_create_cultivar_by_grower_returns_201():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.GROWER))

    assert client.post("/api/v1/species/sp_global/cultivars", json=_CREATE_BODY).status_code == 201
    assert [c.tenant_key for c in repo.created] == ["t1"]


def test_create_cultivar_by_lead_returns_201():
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.LEAD))

    assert client.post("/api/v1/species/sp_global/cultivars", json=_CREATE_BODY).status_code == 201
    assert [c.tenant_key for c in repo.created] == ["t1"]


def test_create_cultivar_by_platform_admin_is_allowed_despite_the_viewer_role():
    # Light-mode curation (REQ-027), mirroring the update/delete platform-admin arm.
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.VIEWER, is_platform_admin=True))

    assert client.post("/api/v1/species/sp_global/cultivars", json=_CREATE_BODY).status_code == 201
    assert len(repo.created) == 1


def test_create_under_a_foreign_species_by_viewer_is_still_the_404():
    # Order pinned: the parent-species scope (structural) is decided before the role
    # (privilege), exactly as in update_cultivar/delete_cultivar. A URL addressing a
    # species the caller cannot see answers 404 whatever their role, so the refusal
    # never varies with privilege — see SpeciesService.get_cultivar's order note.
    repo = _catalogue()
    client = TestClient(_app(repo=repo, role=TenantRole.VIEWER))

    resp = client.post(
        "/api/v1/species/sp_foreign/cultivars",
        json={"name": "Sneaky", "species_key": "sp_foreign"},
    )

    assert resp.status_code == 404
    assert repo.created == []
