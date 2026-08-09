"""End-to-end species authorization wiring (SEC-001/002/004/005, #808).

Proves the *route wiring*, not just the service: the real :class:`SpeciesService`
runs behind a fake repository, so the by-key read, the update/delete mutations and
the companion existence check exercise the actual tenant-scoping and role gate
through the HTTP boundary. The tenant/role/admin dependencies are overridden to
model the caller without reaching the real tenant service.

* SEC-001 — GET /species/{key}: foreign → 404, own/global → 200; the
  reference-images gallery inherits the same scoping (shared read root).
* SEC-002 — PUT/DELETE /species/{key}: foreign → 404, global by non-admin → 403,
  viewer → 403, own by an eligible role → 2xx.
* SEC-004 — POST /species: full mode with no active tenant → 422; light mode ok.
* SEC-005 — companion existence check 404s a foreign anchor species.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.companion_planting.router import router as companion_router
from app.api.v1.species.router import router as species_router
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_family_repo, get_species_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.config.settings import settings
from app.domain.models.species import Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.species_service import SpeciesService


class _FakeRepo:
    def __init__(self, species: list[Species]) -> None:
        self._by_key = {s.key: s for s in species}
        self.updated: list[str] = []
        self.deleted: list[str] = []

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


def _catalogue() -> list[Species]:
    return [
        Species(_key="global_seed", scientific_name="Rosa canina", tenant_key=""),
        Species(_key="own", scientific_name="Ocimum basilicum", tenant_key="t1"),
        Species(_key="foreign", scientific_name="Cannabis sativa", tenant_key="t2"),
    ]


def _app(
    *,
    repo: _FakeRepo,
    active_tenant: str = "t1",
    role: TenantRole = TenantRole.LEAD,
    is_platform_admin: bool = False,
    graph: object | None = None,
) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(species_router, prefix="/api/v1")
    app.include_router(companion_router, prefix="/api/v1")
    service = SpeciesService(repo, graph_repo=graph)  # type: ignore[arg-type]
    family_repo = SimpleNamespace(get_by_key=lambda _key: None)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: family_repo
    app.dependency_overrides[get_active_tenant_key] = lambda: active_tenant
    app.dependency_overrides[get_creating_tenant_key] = lambda: active_tenant
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=active_tenant, tenant_slug="t", user_key="user_1", role=role
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: is_platform_admin
    return app


# ── SEC-001: by-key read ─────────────────────────────────────────────────────


def test_get_own_species_returns_200():
    client = TestClient(_app(repo=_FakeRepo(_catalogue()), active_tenant="t1"))
    resp = client.get("/api/v1/species/own")
    assert resp.status_code == 200
    assert resp.json()["scientific_name"] == "Ocimum basilicum"


def test_get_global_species_returns_200():
    client = TestClient(_app(repo=_FakeRepo(_catalogue()), active_tenant="t1"))
    assert client.get("/api/v1/species/global_seed").status_code == 200


def test_get_foreign_species_returns_404():
    # verifies_sprint_value: a foreign species by key is not an enumerable oracle.
    client = TestClient(_app(repo=_FakeRepo(_catalogue()), active_tenant="t1"))
    assert client.get("/api/v1/species/foreign").status_code == 404


def test_reference_images_inherits_the_scoping():
    client = TestClient(_app(repo=_FakeRepo(_catalogue()), active_tenant="t1"))
    # Foreign anchor → 404 before the inference-service is ever contacted.
    assert client.get("/api/v1/species/foreign/reference-images").status_code == 404


# ── SEC-002: update / delete ─────────────────────────────────────────────────

_BODY = {"scientific_name": "Edited name"}


def test_update_foreign_species_returns_404():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD))
    assert client.put("/api/v1/species/foreign", json=_BODY).status_code == 404
    assert repo.updated == []


def test_update_global_species_by_non_admin_returns_403():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD, is_platform_admin=False))
    assert client.put("/api/v1/species/global_seed", json=_BODY).status_code == 403
    assert repo.updated == []


def test_update_own_species_by_viewer_returns_403():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.VIEWER))
    assert client.put("/api/v1/species/own", json=_BODY).status_code == 403
    assert repo.updated == []


def test_update_own_species_by_grower_returns_200():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.GROWER))
    assert client.put("/api/v1/species/own", json=_BODY).status_code == 200
    assert repo.updated == ["own"]


def test_delete_foreign_species_returns_404():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD))
    assert client.delete("/api/v1/species/foreign").status_code == 404
    assert repo.deleted == []


def test_delete_global_species_by_non_admin_returns_403():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD))
    assert client.delete("/api/v1/species/global_seed").status_code == 403
    assert repo.deleted == []


def test_delete_own_species_by_lead_returns_204():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD))
    assert client.delete("/api/v1/species/own").status_code == 204
    assert repo.deleted == ["own"]


def test_global_species_editable_by_platform_admin():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD, is_platform_admin=True))
    assert client.put("/api/v1/species/global_seed", json=_BODY).status_code == 200
    assert repo.updated == ["global_seed"]


# ── SEC-004: create requires an active tenant in full mode ───────────────────


def test_full_mode_create_without_active_tenant_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    service = MagicMock()
    service.create_species.side_effect = lambda s: s
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(species_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: SimpleNamespace(get_by_key=lambda _k: None)
    app.dependency_overrides[get_creating_tenant_key] = lambda: ""  # no active tenant

    resp = TestClient(app).post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 422
    service.create_species.assert_not_called()


def test_light_mode_create_without_active_tenant_still_works(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    service = MagicMock()
    service.create_species.side_effect = lambda s: s
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(species_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: SimpleNamespace(get_by_key=lambda _k: None)
    app.dependency_overrides[get_creating_tenant_key] = lambda: ""

    resp = TestClient(app).post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 201
    assert service.create_species.call_args.args[0].tenant_key == ""


# ── SEC-005: companion existence check is no longer a foreign oracle ──────────


def test_companion_compatible_404s_a_foreign_anchor():
    graph = MagicMock()
    client = TestClient(_app(repo=_FakeRepo(_catalogue()), active_tenant="t1", graph=graph))
    resp = client.get("/api/v1/companion-planting/species/foreign/compatible")
    assert resp.status_code == 404
    # The graph is never consulted for a species the caller cannot see.
    graph.get_compatible_species.assert_not_called()


def test_companion_recommendations_404s_a_foreign_anchor():
    graph = MagicMock()
    client = TestClient(_app(repo=_FakeRepo(_catalogue()), active_tenant="t1", graph=graph))
    assert client.get("/api/v1/companion-planting/species/foreign/recommendations").status_code == 404
