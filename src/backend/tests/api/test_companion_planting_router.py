"""API tests for the companion-planting router platform-admin guard (#8).

The two write endpoints — ``POST /companion-planting/compatible`` and
``POST /companion-planting/incompatible`` — create GLOBAL compatibility edges
shared across every tenant. Before this fix any authenticated user could write
them; now only platform admins may (``require_platform_admin``), while the read
(GET) endpoints stay open to all authenticated users.

Covers (NFR-015 negative test):
  * a normal (non-admin) user is rejected with 403 on both POSTs and the graph
    repository is never touched;
  * a platform admin succeeds with 201 on both POSTs;
  * light mode (REQ-027, no platform tenant) lets the anonymous system user
    through without consulting tenant memberships.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.companion_planting.router import router as companion_router
from app.common import auth as auth_mod
from app.common.auth import get_current_user
from app.common.dependencies import get_species_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


def _build_app(tenant_service: MagicMock) -> FastAPI:
    app = FastAPI()
    app.include_router(companion_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_species_service] = lambda: MagicMock()
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    return app


_COMPATIBLE_BODY = {"from_species_key": "s1", "to_species_key": "s2", "score": 0.9}
_INCOMPATIBLE_BODY = {"from_species_key": "s1", "to_species_key": "s2", "reason": "allelopathy"}


@pytest.mark.parametrize(
    ("path", "body", "graph_method"),
    [
        ("/api/v1/companion-planting/compatible", _COMPATIBLE_BODY, "set_compatibility"),
        ("/api/v1/companion-planting/incompatible", _INCOMPATIBLE_BODY, "set_incompatibility"),
    ],
)
def test_non_admin_is_rejected_full_mode(monkeypatch, path, body, graph_method):
    """A normal grower gets 403 and NO global edge is written."""
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.GROWER, is_active=True)
    graph = MagicMock()
    with patch("app.common.dependencies.get_graph_repo", return_value=graph):
        client = TestClient(_build_app(tenant_service))
        resp = client.post(path, json=body)
    assert resp.status_code == 403
    getattr(graph, graph_method).assert_not_called()


@pytest.mark.parametrize(
    ("path", "body", "graph_method"),
    [
        ("/api/v1/companion-planting/compatible", _COMPATIBLE_BODY, "set_compatibility"),
        ("/api/v1/companion-planting/incompatible", _INCOMPATIBLE_BODY, "set_incompatibility"),
    ],
)
def test_platform_admin_succeeds_full_mode(monkeypatch, path, body, graph_method):
    """A platform admin gets 201 and the edge is written."""
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.ADMIN, is_active=True)
    graph = MagicMock()
    with patch("app.common.dependencies.get_graph_repo", return_value=graph):
        client = TestClient(_build_app(tenant_service))
        resp = client.post(path, json=body)
    assert resp.status_code == 201
    getattr(graph, graph_method).assert_called_once()


@pytest.mark.parametrize(
    "path,body",
    [
        ("/api/v1/companion-planting/compatible", _COMPATIBLE_BODY),
        ("/api/v1/companion-planting/incompatible", _INCOMPATIBLE_BODY),
    ],
)
def test_light_mode_allows_system_user(monkeypatch, path, body):
    """Light mode (REQ-027): the anonymous system user writes without a membership check."""
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "light")
    tenant_service = MagicMock()
    graph = MagicMock()
    with patch("app.common.dependencies.get_graph_repo", return_value=graph):
        client = TestClient(_build_app(tenant_service))
        resp = client.post(path, json=body)
    assert resp.status_code == 201
    tenant_service.get_membership.assert_not_called()


def test_get_endpoints_remain_open_to_non_admin(monkeypatch):
    """The read endpoints stay reachable for any authenticated (non-admin) user."""
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.VIEWER, is_active=True)
    species_service = MagicMock()
    species_service.get_compatible_species.return_value = []
    app = FastAPI()
    app.include_router(companion_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_species_service] = lambda: species_service
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    client = TestClient(app)
    resp = client.get("/api/v1/companion-planting/species/s1/compatible")
    assert resp.status_code == 200
    species_service.get_compatible_species.assert_called_once_with("s1")


def test_compatible_endpoint_passes_through_common_names(monkeypatch):
    """GET /compatible surfaces the species common_names for layperson naming (#567)."""
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.VIEWER, is_active=True)
    species_service = MagicMock()
    species_service.get_compatible_species.return_value = [
        {
            "species_key": "leek",
            "scientific_name": "Allium porrum",
            "common_names": ["Lauch", "Leek"],
            "score": 0.9,
        }
    ]
    app = FastAPI()
    app.include_router(companion_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_species_service] = lambda: species_service
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    client = TestClient(app)

    resp = client.get("/api/v1/companion-planting/species/tomato/compatible")

    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["common_names"] == ["Lauch", "Leek"]
    assert body[0]["scientific_name"] == "Allium porrum"


def test_counts_endpoint_returns_per_species_counts(monkeypatch):
    """GET /counts returns the whole-catalogue aggregate keyed by species_key.

    Includes a species with 0 compatible companions (only incompatible edges) —
    the response fills the missing category with 0 via the SpeciesCompanionCounts
    schema default.
    """
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")
    tenant_service = MagicMock()
    tenant_service.get_membership.return_value = SimpleNamespace(role=TenantRole.VIEWER, is_active=True)
    species_service = MagicMock()
    species_service.get_companion_counts.return_value = {
        "tomato": {"compatible": 2, "incompatible": 1},
        "basil": {"compatible": 1, "incompatible": 0},
        "nettle": {"incompatible": 1},
    }
    app = FastAPI()
    app.include_router(companion_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_species_service] = lambda: species_service
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    client = TestClient(app)

    resp = client.get("/api/v1/companion-planting/counts")

    assert resp.status_code == 200
    body = resp.json()
    assert body["tomato"] == {"compatible": 2, "incompatible": 1}
    assert body["basil"] == {"compatible": 1, "incompatible": 0}
    # species with only an incompatible edge → compatible defaults to 0
    assert body["nettle"] == {"compatible": 0, "incompatible": 1}
    species_service.get_companion_counts.assert_called_once_with()
