"""API tests for the tenant-scoped REQ-008 post-harvest router.

Covers the two security-review findings:

* SEC-001 (RBAC): the four mutating endpoints require at least the ``grower``
  role — a ``viewer`` membership is read-only (REQ-024) and must get 403, while
  a ``grower`` is allowed through. The reads stay open to any membership.
* SEC-002 (error contract): a drying-progress weight above the batch start
  weight is invalid input and must surface as 422 (ValidationError), never as an
  opaque 500 from a bare calculator ValueError (NFR-006).
"""

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.post_harvest.tenant_router import router as post_harvest_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_post_harvest_service
from app.common.enums import PostHarvestStage, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.harvest import HarvestBatch
from app.domain.models.post_harvest import PostHarvestBatch
from app.domain.models.tenant_context import TenantContext
from app.domain.services.post_harvest_service import PostHarvestService

TENANT_KEY = "t-test-1"
BASE = "/api/v1/t/test-slug"


def _ctx(role: TenantRole) -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=role,
    )


def _build_app(service, role: TenantRole) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(post_harvest_router, prefix=BASE)
    app.dependency_overrides[get_post_harvest_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = lambda: _ctx(role)
    return app


# ── SEC-001: viewer is read-only, grower may write ──────────────────────────


class _FakePostHarvestRepo:
    """Minimal in-memory repo honouring the tenant-scope contract of the real repo."""

    def __init__(self):
        self.batches: dict[str, PostHarvestBatch] = {}
        self.drying: dict[str, list] = {}
        self.observations: dict[str, list] = {}
        self.alerts: dict[str, list] = {}
        self._seq = 0

    def _next_key(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}_{self._seq}"

    def create_batch(self, batch: PostHarvestBatch) -> PostHarvestBatch:
        batch.key = self._next_key("ph")
        batch.created_at = datetime.now()
        self.batches[batch.key] = batch
        return batch

    def get_batch_or_raise(self, key: str) -> PostHarvestBatch:
        batch = self.batches.get(key)
        if batch is None:
            raise NotFoundError("PostHarvestBatch", key)
        return batch

    def update_batch(self, key: str, batch: PostHarvestBatch) -> PostHarvestBatch:
        self.batches[key] = batch
        return batch

    def create_drying_progress(self, progress):
        progress.key = self._next_key("dp")
        self.drying.setdefault(progress.batch_key, []).insert(0, progress)
        return progress

    def get_latest_drying_progress(self, batch_key):
        items = self.drying.get(batch_key, [])
        return items[0] if items else None

    def create_observation(self, observation):
        observation.key = self._next_key("obs")
        self.observations.setdefault(observation.batch_key, []).insert(0, observation)
        return observation

    def create_mold_alert(self, alert):
        alert.key = self._next_key("alert")
        self.alerts.setdefault(alert.batch_key, []).insert(0, alert)
        return alert

    def list_mold_alerts(self, batch_key):
        return self.alerts.get(batch_key, [])


class _FakeHarvestRepo:
    def __init__(self, batches: dict[str, HarvestBatch]):
        self._batches = batches

    def get_batch_or_raise(self, key: str) -> HarvestBatch:
        batch = self._batches.get(key)
        if batch is None:
            raise NotFoundError("HarvestBatch", key)
        return batch


def _real_service_with_batch() -> tuple[PostHarvestService, str]:
    """Wire a real service on fake repos and seed one drying batch (start 450 g)."""
    harvest = HarvestBatch(_key="hb_1", tenant_key=TENANT_KEY, plant_key="plant_1", wet_weight_g=450.0)
    service = PostHarvestService(_FakePostHarvestRepo(), harvest_repo=_FakeHarvestRepo({"hb_1": harvest}))
    batch = service.start_drying(TENANT_KEY, "hb_1")
    return service, batch.key


# Each entry: (method, path suffix, json body).
_WRITE_ENDPOINTS = [
    ("post", "/start-drying", {"harvest_batch_key": "hb_1", "start_weight_g": 450.0}),
    ("post", "/ph_1/advance", {"target_stage": "curing"}),
    ("post", "/ph_1/drying-progress", {"current_weight_g": 180.0}),
    ("post", "/ph_1/observations", {"rh_percent": 45.0, "temperature_c": 18.0}),
]


def test_viewer_is_forbidden_on_every_write():
    # SEC-001: a viewer membership is read-only (REQ-024) — every mutating
    # endpoint must reject it with 403 before any service logic runs.
    from unittest.mock import MagicMock

    service = MagicMock()
    client = TestClient(_build_app(service, TenantRole.VIEWER))

    for method, suffix, body in _WRITE_ENDPOINTS:
        resp = client.request(method, f"{BASE}/post-harvest{suffix}", json=body)
        assert resp.status_code == 403, f"{suffix} should be forbidden for viewer"


def test_grower_is_allowed_on_writes():
    # SEC-001: a grower passes the role gate; the start-drying write succeeds.
    service, _ = _real_service_with_batch()
    client = TestClient(_build_app(service, TenantRole.GROWER))

    resp = client.post(
        f"{BASE}/post-harvest/start-drying",
        json={"harvest_batch_key": "hb_1", "start_weight_g": 450.0},
    )

    assert resp.status_code == 201
    assert resp.json()["stage"] == PostHarvestStage.DRYING.value


def test_viewer_may_read_batches():
    # Reads stay open to any membership — a viewer can list.
    from unittest.mock import MagicMock

    service = MagicMock()
    service.list_batches.return_value = ([], 0)
    client = TestClient(_build_app(service, TenantRole.VIEWER))

    resp = client.get(f"{BASE}/post-harvest")

    assert resp.status_code == 200
    assert resp.json() == []


# ── SEC-002: over-weight drying progress is 422, not 500 ─────────────────────


def test_drying_progress_over_start_weight_is_422():
    # A current weight above the batch start weight (450 g) is invalid input and
    # must be a 422 ValidationError, not an opaque 500 (NFR-006).
    service, batch_key = _real_service_with_batch()
    client = TestClient(_build_app(service, TenantRole.GROWER))

    resp = client.post(
        f"{BASE}/post-harvest/{batch_key}/drying-progress",
        json={"current_weight_g": 600.0},
    )

    assert resp.status_code == 422
    assert "start weight" in resp.text.lower()


def test_drying_progress_within_start_weight_is_created():
    # Control: a valid (lighter) weight is accepted and persisted.
    service, batch_key = _real_service_with_batch()
    client = TestClient(_build_app(service, TenantRole.GROWER))

    resp = client.post(
        f"{BASE}/post-harvest/{batch_key}/drying-progress",
        json={"current_weight_g": 180.0},
    )

    assert resp.status_code == 201
    assert resp.json()["current_weight_g"] == 180.0
