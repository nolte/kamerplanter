"""REQ-013 §2 — API tests for the tenant-scoped succession-plans router."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.succession_plans.tenant_router import router as succession_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_succession_plan_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.models.tenant_context import TenantContext
from app.domain.services.succession_plan_service import SuccessionPlanService

TENANT_SLUG = "lisa"
TENANT_KEY = "tenant_lisa"


class _FakeSuccessionRepo:
    def __init__(self) -> None:
        self._store: dict[str, SuccessionPlan] = {}
        self._seq = 0
        self.run_edges: list[tuple[str, str]] = []
        self.location_edges: list[tuple[str, str]] = []

    def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
        items = [p for p in self._store.values() if p.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)

    def get_by_key(self, key):
        return self._store.get(key)

    def get_or_raise(self, key):
        plan = self._store.get(key)
        if plan is None:
            raise NotFoundError("SuccessionPlan", key)
        return plan

    def create(self, plan: SuccessionPlan) -> SuccessionPlan:
        self._seq += 1
        key = f"sp{self._seq}"
        stored = plan.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def update(self, key, plan: SuccessionPlan) -> SuccessionPlan:
        stored = plan.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def delete(self, key) -> bool:
        return self._store.pop(key, None) is not None

    def link_plan_to_run(self, plan_key, run_key) -> None:
        self.run_edges.append((plan_key, run_key))

    def link_plan_to_location(self, plan_key, location_key) -> None:
        self.location_edges.append((plan_key, location_key))

    def get_run_keys_for_plan(self, plan_key) -> list[str]:
        return [rk for pk, rk in self.run_edges if pk == plan_key]


class _FakeRunService:
    def __init__(self) -> None:
        self._seq = 0

    def create_run(self, run: PlantingRun, entries=None) -> PlantingRun:
        self._seq += 1
        return run.model_copy(update={"key": f"run{self._seq}"})


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user_lisa",
        role=TenantRole.LEAD,
    )


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _build() -> tuple[TestClient, _FakeSuccessionRepo]:
    repo = _FakeSuccessionRepo()
    service = SuccessionPlanService(repo, _FakeRunService())

    app = FastAPI()
    app.include_router(succession_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_succession_plan_service] = lambda: service
    return TestClient(app), repo


def _base(path: str = "") -> str:
    return f"/api/v1/t/{TENANT_SLUG}/succession-plans{path}"


_PLAN_BODY = {
    "name": "Salat-Staffel Beet C 2026",
    "species_key": "species_lactuca_sativa",
    "cultivar_key": "cultivar_lollo_rosso",
    "interval_days": 21,
    "start_date": "2026-04-01",
    "end_date": "2026-08-31",
    "plants_per_batch": 12,
    "location_key": "loc_beet_c",
}


class TestCrud:
    def test_create_and_get(self):
        client, _repo = _build()

        resp = client.post(_base(), json=_PLAN_BODY)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["total_batches"] == 8
        assert body["status"] == "planned"
        key = body["key"]

        resp = client.get(_base(f"/{key}"))
        assert resp.status_code == 200
        assert resp.json()["name"] == _PLAN_BODY["name"]

    def test_list(self):
        client, _repo = _build()
        client.post(_base(), json=_PLAN_BODY)
        resp = client.get(_base())
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_update(self):
        client, _repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]
        resp = client.put(_base(f"/{key}"), json={"interval_days": 42})
        assert resp.status_code == 200
        assert resp.json()["total_batches"] == 4

    def test_delete(self):
        client, _repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]
        resp = client.delete(_base(f"/{key}"))
        assert resp.status_code == 204
        assert client.get(_base(f"/{key}")).status_code == 404

    def test_end_before_start_rejected(self):
        client, _repo = _build()
        bad = {**_PLAN_BODY, "start_date": "2026-08-31", "end_date": "2026-04-01"}
        resp = client.post(_base(), json=bad)
        assert resp.status_code == 422

    def test_update_inverted_date_range_rejected(self):
        client, _repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]
        # Both dates in one patch: schema-level validator rejects with 422.
        resp = client.put(_base(f"/{key}"), json={"start_date": "2026-09-01", "end_date": "2026-04-01"})
        assert resp.status_code == 422

    def test_update_single_sided_start_after_end_rejected(self):
        client, _repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]
        # Only start_date supplied, later than the stored end_date (2026-08-31):
        # the service merge must translate the pydantic error into a 422, not a 500.
        resp = client.put(_base(f"/{key}"), json={"start_date": "2026-12-01"})
        assert resp.status_code == 422

    def test_update_single_sided_end_before_start_rejected(self):
        client, _repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]
        # Only end_date supplied, earlier than the stored start_date (2026-04-01).
        resp = client.put(_base(f"/{key}"), json={"end_date": "2026-01-01"})
        assert resp.status_code == 422


class TestGenerate:
    def test_generate_creates_eight_runs(self):
        client, repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]

        resp = client.post(_base(f"/{key}/generate"))
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["generated_count"] == 8
        assert len(body["runs"]) == 8
        assert body["runs"][0]["planned_start_date"] == "2026-04-01"
        assert body["runs"][1]["planned_start_date"] == "2026-04-22"
        assert body["plan"]["status"] == "active"
        assert body["plan"]["completed_batches"] == 8
        assert len(repo.run_edges) == 8
        assert repo.location_edges == [(key, "loc_beet_c")]

    def test_generate_next_advances_one_batch(self):
        client, _repo = _build()
        key = client.post(_base(), json=_PLAN_BODY).json()["key"]

        resp = client.post(_base(f"/{key}/generate-next"))
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["generated"] is True
        assert body["run"]["succession_sequence"] == 1
        assert body["plan"]["completed_batches"] == 1

    def test_get_unknown_plan_returns_404(self):
        client, _repo = _build()
        assert client.get(_base("/missing")).status_code == 404
