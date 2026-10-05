"""API tests of the platform-admin Home Assistant entity allowlist (MT-015, #2112).

* ``require_platform_admin`` gates every route — a tenant lead or a grower with the
  TECHNICAL scope of their own tenant is still refused (real gating, full mode).
* Grants are per tenant, idempotent, shape-checked; an unknown tenant is 404.
* The inventory lists the instance's entities with the tenant's grant state.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.ha_entity_grants.router import router as grants_router
from app.common import auth as auth_mod
from app.common.auth import get_current_user
from app.common.dependencies import get_ha_entity_grant_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from tests.support.ha_entity_grants import grant_service

BASE = "/api/v1/admin/ha-entity-grants/tenants"
A, B = "tenant-a", "tenant-b"


class _Inventory:
    def list_entities(self) -> list[dict]:
        return [
            {"entity_id": "sensor.tent", "domain": "sensor", "friendly_name": "Tent"},
            {"entity_id": "binary_sensor.front_door", "domain": "binary_sensor", "friendly_name": "Door"},
        ]


def _tenant_service(role: TenantRole | None) -> MagicMock:
    service = MagicMock()
    service.get_membership.return_value = SimpleNamespace(role=role, is_active=True) if role else None

    def get_tenant(key: str):
        if key not in (A, B):
            raise NotFoundError("Tenant", key)
        return SimpleNamespace(key=key)

    service.get_tenant.side_effect = get_tenant
    return service


@pytest.fixture
def full_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_mod.settings, "kamerplanter_mode", "full")


def _client(platform_role: TenantRole | None = TenantRole.LEAD, grants=None) -> tuple[TestClient, object]:
    grants = grants or grant_service({A: {"sensor.tent"}}, ha_client_factory=_Inventory)
    app = FastAPI()
    app.include_router(grants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="user-1")
    app.dependency_overrides[get_tenant_service] = lambda: _tenant_service(platform_role)
    app.dependency_overrides[get_ha_entity_grant_service] = lambda: grants
    return TestClient(app), grants


ROUTES = [
    ("GET", f"{BASE}/{A}", None),
    ("GET", f"{BASE}/{A}/inventory", None),
    ("POST", f"{BASE}/{A}", {"entity_ids": ["binary_sensor.front_door"]}),
    ("DELETE", f"{BASE}/{A}/sensor.tent", None),
]


@pytest.mark.usefixtures("full_mode")
class TestPlatformAdminOnly:
    @pytest.mark.parametrize(("method", "path", "body"), ROUTES)
    @pytest.mark.parametrize("platform_role", [None, TenantRole.VIEWER, TenantRole.GROWER])
    def test_anyone_but_a_platform_admin_is_refused(self, method, path, body, platform_role) -> None:
        client, grants = _client(platform_role)

        response = client.request(method, path, json=body)

        assert response.status_code == 403
        assert grants.granted_entity_ids(A) == frozenset({"sensor.tent"})


@pytest.mark.usefixtures("full_mode")
class TestMaintainingTheAllowlist:
    def test_listing_a_tenants_grants(self) -> None:
        client, _ = _client()

        body = client.get(f"{BASE}/{A}").json()

        assert [g["entity_id"] for g in body] == ["sensor.tent"]
        assert client.get(f"{BASE}/{B}").json() == []

    def test_granting_is_per_tenant_and_idempotent(self) -> None:
        client, grants = _client()

        first = client.post(f"{BASE}/{B}", json={"entity_ids": ["sensor.tent", "notify.mobile_app_phone"]})
        again = client.post(f"{BASE}/{B}", json={"entity_ids": ["sensor.tent"]})

        assert first.status_code == 200 and first.json()["created"] == 2
        assert again.json()["created"] == 0
        assert grants.granted_entity_ids(B) == frozenset({"sensor.tent", "notify.mobile_app_phone"})
        assert grants.granted_entity_ids(A) == frozenset({"sensor.tent"})

    @pytest.mark.parametrize("bad", ["../secret", "Sensor.Tent", "sensor", ""])
    def test_a_malformed_entity_id_is_422_and_grants_nothing(self, bad: str) -> None:
        client, grants = _client()

        response = client.post(f"{BASE}/{B}", json={"entity_ids": ["sensor.ok", bad]})

        assert response.status_code == 422
        assert grants.granted_entity_ids(B) == frozenset()

    def test_an_empty_request_is_422(self) -> None:
        client, _ = _client()

        assert client.post(f"{BASE}/{A}", json={"entity_ids": []}).status_code == 422

    def test_revoking_a_grant(self) -> None:
        client, grants = _client()

        assert client.delete(f"{BASE}/{A}/sensor.tent").status_code == 204
        assert client.delete(f"{BASE}/{A}/sensor.tent").status_code == 404
        assert grants.granted_entity_ids(A) == frozenset()

    @pytest.mark.parametrize(("method", "path", "body"), ROUTES)
    def test_an_unknown_tenant_is_404(self, method, path, body) -> None:
        client, grants = _client()

        response = client.request(method, path.replace(A, "nobody"), json=body)

        assert response.status_code == 404
        assert grants.granted_entity_ids("nobody") == frozenset()

    def test_the_inventory_marks_the_tenants_grants(self) -> None:
        client, _ = _client()

        body = client.get(f"{BASE}/{A}/inventory").json()

        assert body["ha_configured"] is True
        assert {e["entity_id"]: e["granted"] for e in body["entities"]} == {
            "binary_sensor.front_door": False,
            "sensor.tent": True,
        }
        assert all("state" not in e for e in body["entities"])
