"""API tests: REQ-045 dashboard widget catalog endpoint.

Exercises GET /t/{slug}/dashboard/widgets/catalog: default availability, module
gating (REQ-042, Szenario 3), and Light-Mode gating (REQ-027, Szenario 6).
"""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.dashboard.tenant_router as dashboard_tenant_router
from app.api.v1.dashboard.tenant_router import router as dashboard_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_user_preference_service
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user_preference import UserPreference

TENANT_SLUG = "test-slug"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="t-1", tenant_slug=TENANT_SLUG, user_key="user-1", role=TenantRole.GROWER)


class _FakePrefService:
    def __init__(self, module_visibility: dict[str, Any] | None = None) -> None:
        self._mv = module_visibility or {}

    def get_preferences(self, user_key: str) -> UserPreference:
        return UserPreference(user_key=user_key, module_visibility=self._mv)


def _client(pref_service: _FakePrefService) -> TestClient:
    app = FastAPI()
    app.include_router(dashboard_router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_user_preference_service] = lambda: pref_service
    return TestClient(app)


_CATALOG = f"/api/v1/t/{TENANT_SLUG}/dashboard/widgets/catalog"


def _entry(body: dict[str, Any], key: str) -> dict[str, Any]:
    return next(w for w in body["widgets"] if w["widget_key"] == key)


def test_catalog_lists_all_widgets_available_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(dashboard_tenant_router.settings, "kamerplanter_mode", "full")
    resp = _client(_FakePrefService()).get(_CATALOG)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["widgets"]) == 17
    assert all(w["available"] for w in body["widgets"])


def test_hidden_module_greys_out_widget(monkeypatch: pytest.MonkeyPatch):  # Szenario 3
    monkeypatch.setattr(dashboard_tenant_router.settings, "kamerplanter_mode", "full")
    resp = _client(_FakePrefService({"tanks": "disabled"})).get(_CATALOG)
    tank = _entry(resp.json(), "tank_status")
    assert tank["available"] is False
    assert tank["unavailable_reason"] == "dashboard.gate.moduleHidden"


def test_light_mode_gates_community_and_daily_tip(monkeypatch: pytest.MonkeyPatch):  # Szenario 6
    monkeypatch.setattr(dashboard_tenant_router.settings, "kamerplanter_mode", "light")
    body = _client(_FakePrefService()).get(_CATALOG).json()
    community = _entry(body, "community_activity")
    daily = _entry(body, "daily_tip")
    assert community["available"] is False
    assert community["unavailable_reason"] == "dashboard.gate.lightMode"
    assert daily["available"] is False
    assert daily["unavailable_reason"] == "dashboard.gate.aiDisabled"
    # Core widgets stay available in Light mode.
    assert _entry(body, "quick_actions")["available"] is True
