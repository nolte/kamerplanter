"""End-to-end species authorization wiring (SEC-001/002/004/005, #808; #1113).

Proves the *route wiring*, not just the service: the real :class:`SpeciesService`
runs behind a fake repository, so the by-key read, the create, the update/delete
mutations and the companion existence check exercise the actual tenant-scoping and
role gate through the HTTP boundary. The tenant/role/admin dependencies are
overridden to model the caller without reaching the real tenant service.

* SEC-001 — GET /species/{key}: foreign → 404, own/global → 200; the
  reference-images gallery inherits the same scoping (shared read root).
* SEC-002 — PUT/DELETE /species/{key}: foreign → 404, global by non-admin → 403,
  viewer → 403, own by an eligible role → 2xx.
* SEC-004 — POST /species: full mode with no active tenant → 422; light mode ok.
* SEC-005 (#808) — companion existence check 404s a foreign anchor species.
* SEC-005 (#1113) — POST /species: viewer → 403, grower/lead → 201, platform
  admin → 201. Qualified with its issue number on purpose: ``SEC-005`` names two
  unrelated findings (R-7), the companion-anchor one above and this create gate.
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
        self.created: list[Species] = []
        self.updated: list[str] = []
        self.deleted: list[str] = []

    def get_or_raise(self, key: str) -> Species:
        s = self._by_key.get(key)
        if s is None:
            raise NotFoundError("Species", key)
        return s

    # The three reads/writes ``create_species`` performs. Recording the insert lets
    # the create matrix below assert not just the status code but that a refused
    # create wrote *nothing* — a 403 that still persisted a row would pass a
    # status-only assertion.
    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        return None

    def find_synonym_match_candidates(self, species: Species) -> list[Species]:
        return []

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        self.created.append(species)
        return species.model_copy(update={"key": "sp_new"})

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
    context_tenant: str | None = None,
    role: TenantRole = TenantRole.LEAD,
    is_platform_admin: bool = False,
    graph: object | None = None,
) -> FastAPI:
    """Mount the species + companion routers over ``repo`` for a modelled caller.

    ``context_tenant`` defaults to ``active_tenant`` (production: both come from
    the same :func:`~app.common.auth._resolve_active_tenant` call, so they cannot
    differ). It can be set apart deliberately to prove *which* of the two
    dependencies a route reads — see the create-stamping test below.
    """
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
        tenant_key=active_tenant if context_tenant is None else context_tenant,
        tenant_slug="t",
        user_key="user_1",
        role=role,
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


def _mocked_create_app(
    *,
    creating_tenant_key: str,
    role: TenantRole = TenantRole.LEAD,
    is_platform_admin: bool = False,
) -> tuple[FastAPI, MagicMock]:
    """Species router over a *mocked* service — for the create guards, not the gate.

    The role-bearing context and the platform-admin flag are overridden alongside
    the stamping resolver because POST depends on all three since SEC-005 (#1113);
    without the overrides the route would resolve the real tenant service and the
    tier's datastore guard would fire.
    """
    service = MagicMock()
    service.create_species.side_effect = lambda s, **_kwargs: s
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(species_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_species_service] = lambda: service
    app.dependency_overrides[get_family_repo] = lambda: SimpleNamespace(get_by_key=lambda _k: None)
    app.dependency_overrides[get_creating_tenant_key] = lambda: creating_tenant_key
    app.dependency_overrides[get_active_tenant_context] = lambda: TenantContext(
        tenant_key=creating_tenant_key, tenant_slug="t", user_key="user_1", role=role
    )
    app.dependency_overrides[get_is_platform_admin] = lambda: is_platform_admin
    return app, service


def test_full_mode_create_without_active_tenant_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    app, service = _mocked_create_app(creating_tenant_key="")  # no active tenant

    resp = TestClient(app).post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 422
    service.create_species.assert_not_called()


def test_light_mode_create_without_active_tenant_still_works(monkeypatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    app, service = _mocked_create_app(creating_tenant_key="")

    resp = TestClient(app).post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 201
    assert service.create_species.call_args.args[0].tenant_key == ""


def test_the_light_mode_operator_can_still_curate_the_catalogue(monkeypatch):
    # Light mode (REQ-027) modelled as it actually is, all three parts at once: no
    # resolvable tenant (""), no membership — so the context role is the fail-safe
    # VIEWER — and the anonymous operator counted as platform admin. Without the
    # platform-admin arm of the new gate, SEC-005 (#1113) would have locked the sole
    # light-mode user out of creating master data at all.
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    app, service = _mocked_create_app(creating_tenant_key="", role=TenantRole.VIEWER, is_platform_admin=True)

    resp = TestClient(app).post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 201
    assert service.create_species.call_args.kwargs["is_platform_admin"] is True


def test_the_missing_tenant_guard_answers_before_the_role_gate(monkeypatch):
    # SEC-004 vs SEC-005 (#1113) ordering, pinned: a full-mode caller with neither
    # an active tenant nor a writing role gets the 422, not the 403. The 422 is a
    # request-precondition failure ("this request names no tenant to create in"),
    # and with no resolvable tenant the context role is the fail-safe VIEWER
    # default rather than a standing the caller actually holds — answering 403
    # would report a role nobody assigned them. It is also the order the wiring
    # already produces (route body before service call), so SEC-004's shipped
    # answer is unchanged by the new gate.
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    app, service = _mocked_create_app(creating_tenant_key="", role=TenantRole.VIEWER)

    resp = TestClient(app).post("/api/v1/species", json={"scientific_name": "Ocimum basilicum"})

    assert resp.status_code == 422
    service.create_species.assert_not_called()


# ── SEC-005 (#1113): the create role gate ────────────────────────────────────


_CREATE_BODY = {"scientific_name": "Ocimum basilicum"}


def test_create_species_by_viewer_returns_403():
    # verifies_sprint_value: red-first. Before #1113 the POST route carried no role
    # dependency at all, so this returned 201 — an org viewer with a valid
    # ``X-Active-Tenant`` header could write into the shared org catalogue.
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.VIEWER))

    resp = client.post("/api/v1/species", json=_CREATE_BODY)

    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"
    # Refused before the repository: nothing was written.
    assert repo.created == []


def test_create_species_by_grower_returns_201():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.GROWER))

    assert client.post("/api/v1/species", json=_CREATE_BODY).status_code == 201
    assert [s.tenant_key for s in repo.created] == ["t1"]


def test_create_species_by_lead_returns_201():
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.LEAD))

    assert client.post("/api/v1/species", json=_CREATE_BODY).status_code == 201
    assert [s.tenant_key for s in repo.created] == ["t1"]


def test_create_species_by_platform_admin_is_allowed_despite_the_viewer_role():
    # Light-mode curation (REQ-027): the sole operator holds no domain membership,
    # so the context role is the fail-safe VIEWER — the platform-admin bypass is
    # what keeps the shared catalogue curatable, exactly as for update/delete.
    repo = _FakeRepo(_catalogue())
    client = TestClient(_app(repo=repo, active_tenant="t1", role=TenantRole.VIEWER, is_platform_admin=True))

    assert client.post("/api/v1/species", json=_CREATE_BODY).status_code == 201
    assert len(repo.created) == 1


def test_create_species_still_stamps_the_creating_tenant_key_dependency():
    # F-3 back-compat (AC 4): the *stamp* keeps coming from ``get_creating_tenant_key``
    # and the new context dependency supplies only the role. The two are deliberately
    # set apart here (they cannot differ in production — one resolver feeds both), so
    # a route that started stamping ``ctx.tenant_key`` instead would fail here and the
    # four test files overriding the alias would not silently certify nothing.
    repo = _FakeRepo(_catalogue())
    client = TestClient(
        _app(repo=repo, active_tenant="t_stamped", context_tenant="t_role_only", role=TenantRole.GROWER)
    )

    assert client.post("/api/v1/species", json=_CREATE_BODY).status_code == 201
    assert [s.tenant_key for s in repo.created] == ["t_stamped"]


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
