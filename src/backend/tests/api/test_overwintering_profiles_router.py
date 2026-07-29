"""REQ-022 §OverwinteringProfile — API tests (tenant router).

Covers the CRUD happy path, the D5-invariant 422 rejection and the dashboard
hardiness overview through ``TestClient`` with an in-memory repository.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.overwintering_profiles.tenant_router import router as tenant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_overwintering_profile_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.interfaces.overwintering_profile_repository import IOverwinteringProfileRepository
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.tenant_context import TenantContext
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant_anna"


class _FakeRepo(IOverwinteringProfileRepository):
    def __init__(self) -> None:
        self.store: dict[str, OverwinteringProfile] = {}
        self._seq = 0

    def get_profile_by_key(self, key):
        return self.store.get(key)

    def get_profile_by_plant_key(self, plant_key):
        return next((p for p in self.store.values() if p.plant_key == plant_key), None)

    def get_profile_by_run_key(self, run_key):
        return next((p for p in self.store.values() if p.planting_run_key == run_key), None)

    def create_profile(self, profile):
        self._seq += 1
        key = f"ow{self._seq}"
        stored = profile.model_copy(update={"key": key})
        self.store[key] = stored
        return stored

    def update_profile(self, key, profile):
        stored = profile.model_copy(update={"key": key})
        self.store[key] = stored
        return stored

    def delete_profile(self, key):
        return self.store.pop(key, None) is not None

    def list_by_tenant(self, tenant_key, offset=0, limit=50):
        items = [p for p in self.store.values() if p.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)

    def create_subject_edge(self, profile_key, *, plant_key=None, planting_run_key=None):
        pass

    def create_winter_quarter_edge(self, profile_key, location_key):
        pass


def _ctx(role: TenantRole = TenantRole.LEAD) -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key="user_anna", role=role)


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build():
    service = OverwinteringProfileService(_FakeRepo())
    app = FastAPI()
    app.include_router(tenant_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: _ctx()
    app.dependency_overrides[get_overwintering_profile_service] = lambda: service
    return app, service


def _base(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/overwintering-profiles{path}"


class TestCrud:
    def test_create_and_get(self) -> None:
        app, _service = _build()
        client = TestClient(app)
        resp = client.post(
            _base(),
            json={
                "plant_key": "p1",
                "hardiness_rating": "hardy",
                "winter_action": "none",
                "winter_action_month": 10,
            },
        )
        assert resp.status_code == 201, resp.text
        key = resp.json()["key"]
        assert resp.json()["hardiness_rating"] == "hardy"

        got = client.get(_base(f"/{key}"))
        assert got.status_code == 200
        assert got.json()["key"] == key

    def test_delete(self) -> None:
        app, _service = _build()
        client = TestClient(app)
        key = client.post(
            _base(),
            json={
                "plant_key": "p1",
                "hardiness_rating": "hardy",
                "winter_action": "none",
                "winter_action_month": 10,
            },
        ).json()["key"]
        assert client.delete(_base(f"/{key}")).status_code == 204
        assert client.get(_base(f"/{key}")).status_code == 404


class TestTuberStatusRejection:
    def test_create_invalid_tuber_status_returns_422(self) -> None:
        """B2 — tuber_status on a non-dig-and-store rating must be 422, not 500."""
        app, _service = _build()
        client = TestClient(app)
        resp = client.post(
            _base(),
            json={
                "plant_key": "p1",
                "hardiness_rating": "hardy",
                "winter_action": "none",
                "winter_action_month": 10,
                "tuber_status": "stored",
            },
        )
        assert resp.status_code == 422, resp.text

    def test_update_invalid_tuber_status_returns_422(self) -> None:
        """B2 — the PUT merge path must also return 422 (not 500) for an invalid
        tuber_status / hardiness_rating combination."""
        app, _service = _build()
        client = TestClient(app)
        key = client.post(
            _base(),
            json={
                "plant_key": "p1",
                "hardiness_rating": "hardy",
                "winter_action": "none",
                "winter_action_month": 10,
            },
        ).json()["key"]

        resp = client.put(_base(f"/{key}"), json={"tuber_status": "stored"})
        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"


class TestD5Rejection:
    def test_d5_contradiction_returns_422(self) -> None:
        app, _service = _build()
        client = TestClient(app)
        # path A rating (hardy) with a path B action (move_indoors) → 422
        resp = client.post(
            _base(),
            json={
                "plant_key": "p1",
                "hardiness_rating": "hardy",
                "winter_action": "move_indoors",
                "winter_action_month": 10,
            },
        )
        assert resp.status_code == 422
        assert resp.json()["error_code"] == "WINTER_PATH_VIOLATION"


class TestHardinessOverview:
    def test_overview_aggregates(self) -> None:
        app, _service = _build()
        client = TestClient(app)
        client.post(
            _base(),
            json={
                "plant_key": "p1",
                "hardiness_rating": "hardy",
                "winter_action": "none",
                "winter_action_month": 10,
            },
        )
        client.post(
            _base(),
            json={
                "plant_key": "p2",
                "hardiness_rating": "frost_free",
                "winter_action": "move_indoors",
                "winter_action_month": 10,
            },
        )
        resp = client.get(_base("/hardiness-overview"))
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["green"] == 1
        assert body["red"] == 1
        assert body["total"] == 2
        assert body["red_plants"][0]["plant_key"] == "p2"
