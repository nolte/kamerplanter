"""API tests: REQ-045 dashboard_layout on user preferences.

Exercises GET/PATCH /t/{slug}/user-preferences for the additive
``dashboard_layout`` field: round-trip persistence, reset semantics (explicit
null vs. unset), tolerant sanitize of unknown widget keys, and placement
validation. Mirrors the module-visibility test harness.
"""

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.user_preferences.tenant_router import router as pref_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_user_preference_service
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user_preference import UserPreference
from app.domain.services.user_preference_service import UserPreferenceService

TENANT_SLUG = "test-slug"
USER_KEY = "user-1"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key="t-test-1",
        tenant_slug=TENANT_SLUG,
        user_key=USER_KEY,
        role=TenantRole.GROWER,
    )


class _FakeRepo:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._seq = 0

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [d for d in self._store.values() if d.get(field) == value]

    def create(self, model: UserPreference) -> dict[str, Any]:
        self._seq += 1
        key = f"pref-{self._seq}"
        doc = model.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        doc["_key"] = key
        self._store[key] = doc
        return dict(doc)

    def update(self, key: str, model: UserPreference) -> dict[str, Any]:
        doc = model.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc["_key"] = key
        self._store[key] = doc
        return dict(doc)


def _build_client() -> TestClient:
    service = UserPreferenceService.__new__(UserPreferenceService)
    service._repo = _FakeRepo()  # type: ignore[attr-defined]

    app = FastAPI()
    app.include_router(pref_router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_user_preference_service] = lambda: service
    return TestClient(app)


_BASE = f"/api/v1/t/{TENANT_SLUG}/user-preferences"


def _layout(*widgets: str) -> dict[str, Any]:
    instances = [{"instance_id": f"w-{i}", "widget_key": k, "config": {}} for i, k in enumerate(widgets)]
    placements = [
        {"instance_id": inst["instance_id"], "x": 0, "y": i, "w": 4, "h": 4} for i, inst in enumerate(instances)
    ]
    return {"schema_version": 2, "widgets": instances, "placements": {"lg": placements}}


def test_default_dashboard_layout_is_null():
    client = _build_client()
    resp = client.get(_BASE)
    assert resp.status_code == 200
    assert resp.json()["dashboard_layout"] is None


def test_patch_dashboard_layout_round_trips():
    client = _build_client()
    patch = client.patch(_BASE, json={"dashboard_layout": _layout("tasks_today", "tank_status")})
    assert patch.status_code == 200
    body = patch.json()["dashboard_layout"]
    assert [w["widget_key"] for w in body["widgets"]] == ["tasks_today", "tank_status"]
    assert len(body["placements"]["lg"]) == 2

    get = client.get(_BASE)
    assert [w["widget_key"] for w in get.json()["dashboard_layout"]["widgets"]] == ["tasks_today", "tank_status"]


def test_reset_layout_with_explicit_null(  # Szenario 2
):
    client = _build_client()
    client.patch(_BASE, json={"dashboard_layout": _layout("tasks_today")})
    assert client.get(_BASE).json()["dashboard_layout"] is not None

    reset = client.patch(_BASE, json={"dashboard_layout": None})
    assert reset.status_code == 200
    assert reset.json()["dashboard_layout"] is None
    assert client.get(_BASE).json()["dashboard_layout"] is None


def test_unset_layout_is_left_untouched():
    client = _build_client()
    client.patch(_BASE, json={"dashboard_layout": _layout("tasks_today")})
    # A PATCH that does not mention dashboard_layout must not wipe it.
    other = client.patch(_BASE, json={"theme": "dark"})
    assert other.status_code == 200
    assert other.json()["dashboard_layout"] is not None


def test_unknown_widget_key_is_dropped_tolerantly(  # Szenario 5
):
    client = _build_client()
    resp = client.patch(_BASE, json={"dashboard_layout": _layout("tasks_today", "experimental_x", "tank_status")})
    assert resp.status_code == 200  # not 422 for the whole layout
    keys = [w["widget_key"] for w in resp.json()["dashboard_layout"]["widgets"]]
    assert keys == ["tasks_today", "tank_status"]
    # Orphaned placement of the dropped widget is pruned too.
    assert len(resp.json()["dashboard_layout"]["placements"]["lg"]) == 2


def test_placement_out_of_range_returns_422():
    client = _build_client()
    bad = _layout("tasks_today")
    bad["placements"]["lg"][0]["w"] = 99  # exceeds GRID_MAX_COLUMNS
    resp = client.patch(_BASE, json={"dashboard_layout": bad})
    assert resp.status_code == 422


def test_unknown_breakpoint_returns_422():
    client = _build_client()
    bad = _layout("tasks_today")
    bad["placements"]["xxl"] = bad["placements"].pop("lg")
    resp = client.patch(_BASE, json={"dashboard_layout": bad})
    assert resp.status_code == 422
