"""A caller cannot read another tenant's dashboard by naming it — #1853, through the deployed app.

``GET /api/v1/dashboard/summary?tenant_key=<key>`` handed the query value to
``DashboardService.get_summary`` behind ``get_current_user`` alone, so any
signed-in caller read any tenant's counters, upcoming tasks and activities. The
route had no consumer and is removed; the tenant-bound successor
``/t/{slug}/dashboard/aggregated`` resolves its tenant through
``get_current_tenant``.

The app is the real ``app.main`` one. Only the principal (``get_current_user``),
the tenant store and the dashboard service are doubled; ``get_current_tenant``
and its membership check run as in production, so what refuses tenant B is the
resolver, not this file.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_dashboard_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.dashboard_service import DashboardCounts, DashboardSummary

_CALLER = "caller"
_TENANTS = {
    "club-a": SimpleNamespace(key="tenant_a", slug="club-a"),
    "club-b": SimpleNamespace(key="tenant_b", slug="club-b"),
}


class _TenantService:
    """The caller is an active grower in club A and holds nothing in club B."""

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        if slug not in _TENANTS:
            raise NotFoundError("Tenant", slug)
        return _TENANTS[slug]

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        if user_key == _CALLER and tenant_key == "tenant_a":
            return SimpleNamespace(role=TenantRole.GROWER, admin_scopes=[], is_active=True)
        return None

    def get_personal_tenant(self, user_key: str) -> None:
        return None


class _RecordingDashboardService:
    def __init__(self) -> None:
        self.asked_for: list[str] = []

    def get_summary(self, tenant_key: str) -> DashboardSummary:
        self.asked_for.append(tenant_key)
        return DashboardSummary(
            generated_at=datetime(2026, 9, 25, 8, 0, tzinfo=UTC),
            tenant_key=tenant_key,
            counts=DashboardCounts(
                plants_total=7,
                plants_active=5,
                open_tasks_today=1,
                overdue_tasks=0,
                tanks_low=0,
                care_reminders_due=2,
            ),
            upcoming_tasks=[{"name": f"secret task of {tenant_key}"}],
            recent_activities=[],
            active_plants=[],
        )


@pytest.fixture
def service() -> _RecordingDashboardService:
    return _RecordingDashboardService()


@pytest.fixture
def client(service: _RecordingDashboardService) -> Iterator[TestClient]:
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: User(
        _key=_CALLER, email="caller@example.org", display_name="Caller"
    )
    app.dependency_overrides[get_tenant_service] = _TenantService
    app.dependency_overrides[get_dashboard_service] = lambda: service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_the_global_summary_route_does_not_answer_for_a_foreign_tenant(
    client: TestClient, service: _RecordingDashboardService
) -> None:
    response = client.get("/api/v1/dashboard/summary", params={"tenant_key": "tenant_b"})

    assert response.status_code == 404
    assert "tenant_b" not in response.text
    assert service.asked_for == []


def test_the_tenant_bound_route_refuses_a_tenant_the_caller_is_not_a_member_of(
    client: TestClient, service: _RecordingDashboardService
) -> None:
    response = client.get("/api/v1/t/club-b/dashboard/aggregated", params={"widgets": "tasks_today"})

    assert response.status_code == 403
    assert "secret task" not in response.text
    assert service.asked_for == []


def test_the_tenant_bound_route_serves_the_callers_own_tenant(
    client: TestClient, service: _RecordingDashboardService
) -> None:
    # Positive control: the refusal above is the membership check, not a route
    # that answers nobody.
    response = client.get("/api/v1/t/club-a/dashboard/aggregated", params={"widgets": "tasks_today"})

    assert response.status_code == 200
    assert response.json()["tenant_key"] == "tenant_a"
    assert service.asked_for == ["tenant_a"]


def test_the_summary_route_is_absent_from_the_openapi_document(client: TestClient) -> None:
    from app.main import app

    paths = app.openapi()["paths"]

    assert "/api/v1/dashboard/summary" not in paths
    assert "/api/v1/t/{tenant_slug}/dashboard/aggregated" in paths
