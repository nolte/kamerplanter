"""API tests: UI-NFR-019 kiosk-mode flags on user preferences.

Exercises GET/PATCH /t/{slug}/user-preferences for the additive
``kiosk_enabled`` and ``high_contrast`` booleans: default value, round-trip
persistence, and independence of the two flags (high-contrast standalone,
R-045). The service runs against an in-memory fake repository so the real
Pydantic model and schema validation are exercised end to end.
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


def test_kiosk_flags_default_to_false():
    client = _build_client()
    resp = client.get(_BASE)
    assert resp.status_code == 200
    body = resp.json()
    assert body["kiosk_enabled"] is False
    assert body["high_contrast"] is False


def test_patch_kiosk_enabled_round_trips():
    client = _build_client()
    patch = client.patch(_BASE, json={"kiosk_enabled": True, "high_contrast": True})
    assert patch.status_code == 200
    assert patch.json()["kiosk_enabled"] is True
    assert patch.json()["high_contrast"] is True

    get = client.get(_BASE)
    assert get.status_code == 200
    assert get.json()["kiosk_enabled"] is True
    assert get.json()["high_contrast"] is True


def test_high_contrast_is_independent_of_kiosk():
    """R-045 — the high-contrast theme is usable without kiosk mode."""
    client = _build_client()
    patch = client.patch(_BASE, json={"high_contrast": True})
    assert patch.status_code == 200
    assert patch.json()["high_contrast"] is True
    assert patch.json()["kiosk_enabled"] is False


def test_patch_invalid_kiosk_type_returns_422():
    client = _build_client()
    # A list is not coercible to bool (unlike "true"/"1"/0/1 which Pydantic accepts).
    resp = client.patch(_BASE, json={"kiosk_enabled": []})
    assert resp.status_code == 422
