"""API tests: REQ-045 tenant-scoped dashboard aggregation endpoint.

Exercises GET /t/{slug}/dashboard/aggregated. The regression focus is Issue #438:
the ``tasks_today`` slice must surface ``overdue_tasks`` as a distinct, honest
count alongside ``open_tasks_today`` (which keeps its literal "due today"
meaning). The overdue count originates from the same tenant-filtered
``DashboardCounts`` (SEC-001) — no separate query is introduced.
"""

from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.dashboard.tenant_router import router as dashboard_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_dashboard_service
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext
from app.domain.services.dashboard_service import DashboardCounts, DashboardSummary

TENANT_SLUG = "test-slug"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="t-1", tenant_slug=TENANT_SLUG, user_key="user-1", role=TenantRole.GROWER)


class _FakeDashboardService:
    """Returns a fixed summary so the slice mapping is exercised in isolation."""

    def __init__(self, *, open_today: int, overdue: int, active_plants: list[dict] | None = None) -> None:
        self._open_today = open_today
        self._overdue = overdue
        self._active_plants = active_plants or []

    def get_summary(self, tenant_key: str) -> DashboardSummary:
        counts = DashboardCounts(
            plants_total=3,
            plants_active=2,
            open_tasks_today=self._open_today,
            overdue_tasks=self._overdue,
            tanks_low=0,
            care_reminders_due=0,
        )
        return DashboardSummary(
            generated_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
            tenant_key=tenant_key,
            counts=counts,
            upcoming_tasks=[],
            recent_activities=[],
            active_plants=self._active_plants,
        )


def _client(service: _FakeDashboardService) -> TestClient:
    app = FastAPI()
    app.include_router(dashboard_router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_dashboard_service] = lambda: service
    return TestClient(app)


_AGGREGATED = f"/api/v1/t/{TENANT_SLUG}/dashboard/aggregated"


def test_tasks_today_slice_surfaces_overdue_count():
    """Issue #438: the ``tasks_today`` slice must include ``overdue_tasks``.

    Guards against the field being silently dropped again: an overdue backlog
    with nothing due today must still expose the non-zero overdue count.
    """
    resp = _client(_FakeDashboardService(open_today=0, overdue=12)).get(f"{_AGGREGATED}?widgets=tasks_today")
    assert resp.status_code == 200
    slice_payload = resp.json()["widgets"]["tasks_today"]
    assert slice_payload["open_tasks_today"] == 0
    assert slice_payload["overdue_tasks"] == 12
    assert "upcoming_tasks" in slice_payload


def test_tasks_today_slice_keeps_open_and_overdue_distinct():
    """``open_tasks_today`` keeps its literal "due today" meaning (approach A)."""
    resp = _client(_FakeDashboardService(open_today=4, overdue=7)).get(f"{_AGGREGATED}?widgets=tasks_today")
    slice_payload = resp.json()["widgets"]["tasks_today"]
    assert slice_payload["open_tasks_today"] == 4
    assert slice_payload["overdue_tasks"] == 7


def test_plant_grid_slice_returns_active_plants_with_keys():
    """Issue #461: the ``plant_grid`` slice must expose active plants with ``_key``
    so the frontend can deep-link each tile to the plant detail view."""
    plants = [
        {"_key": "p-1", "plant_name": "Basil", "species_key": "ocimum-basilicum"},
        {"_key": "p-2", "plant_name": None, "species_key": "solanum-lycopersicum"},
    ]
    service = _FakeDashboardService(open_today=0, overdue=0, active_plants=plants)
    resp = _client(service).get(f"{_AGGREGATED}?widgets=plant_grid")
    assert resp.status_code == 200
    slice_payload = resp.json()["widgets"]["plant_grid"]
    assert [p["_key"] for p in slice_payload["plants"]] == ["p-1", "p-2"]
