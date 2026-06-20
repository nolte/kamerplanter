"""API tests: REQ-042 module visibility on user preferences.

Exercises GET/PATCH /t/{slug}/user-preferences for the additive
``module_visibility`` field: round-trip persistence, enum validation (422),
serverside drop of core-module overrides, and the empty-dict default.

The tenant auth dependency is overridden; the service runs against an in-memory
fake repository so the real Pydantic model validator (core-drop) and the
schema enum validation are exercised end to end.
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
    """Minimal in-memory stand-in for BaseArangoRepository."""

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


def test_default_module_visibility_is_empty_dict():
    client = _build_client()
    resp = client.get(_BASE)
    assert resp.status_code == 200
    assert resp.json()["module_visibility"] == {}


def test_patch_module_visibility_round_trips():
    client = _build_client()
    patch = client.patch(
        _BASE,
        json={"module_visibility": {"tanks": "disabled", "ipm": "enabled"}},
    )
    assert patch.status_code == 200
    assert patch.json()["module_visibility"] == {"tanks": "disabled", "ipm": "enabled"}

    get = client.get(_BASE)
    assert get.status_code == 200
    assert get.json()["module_visibility"] == {"tanks": "disabled", "ipm": "enabled"}


def test_patch_invalid_enum_value_returns_422():
    client = _build_client()
    resp = client.patch(_BASE, json={"module_visibility": {"tanks": "maybe"}})
    assert resp.status_code == 422


def test_patch_core_override_is_dropped():
    client = _build_client()
    resp = client.patch(
        _BASE,
        json={"module_visibility": {"dashboard": "disabled", "tanks": "disabled"}},
    )
    assert resp.status_code == 200
    mv = resp.json()["module_visibility"]
    assert "dashboard" not in mv
    assert mv == {"tanks": "disabled"}
