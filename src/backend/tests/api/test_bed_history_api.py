"""REQ-053 WP 4.5 (#2423) — ``GET /locations/{key}/history`` through the deployed app (GP-API-038, GP-ACC-027).

``app.main`` with the real ``BedHistoryService``, the real tenant gate and a double of the
history read. The statement itself is proven against ArangoDB in ``tests/integration/test_bed_history.py``; here the
wire is: that the filters reach the read as typed criteria, that the person filter follows the care log's role rule
(E-16), that a derived event carries no care body and an account key never appears, and that a foreign bed is 404.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_bed_history_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.interfaces.bed_history_repository import (
    BedHistoryFilter,
    BedHistoryRow,
    IBedHistoryRepository,
    PlantingEvent,
)
from app.domain.interfaces.care_event_repository import CareEventRow
from app.domain.models.care_event import CareEvent
from app.domain.models.user import User
from app.domain.services.bed_history_service import BedHistoryService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

_OWN = "/api/v1/t/own/locations/bed/history"


class FakeHistory(IBedHistoryRepository):
    def __init__(self) -> None:
        self.calls: list[tuple[str, BedHistoryFilter, str, int, int]] = []
        self.rows: list[BedHistoryRow] = []

    def list_history(self, location_key, criteria, *, tenant_key, offset, limit):
        self.calls.append((location_key, criteria, tenant_key, offset, limit))
        return self.rows


def _care_row() -> BedHistoryRow:
    event = CareEvent(
        _key="ce_1",
        tenant_key=TENANT,
        site_key="site_1",
        location_key="bed",
        category="watering",
        summary="Watered",
        performed_at=datetime(2026, 6, 1, 8, tzinfo=UTC),
        trigger="manual",
        performed_by_user_key="u_sabine",
        created_by="u_sabine",
    )
    return BedHistoryRow(at=event.performed_at, care=CareEventRow(event=event, performed_by_name="Sabine"))


def _planting_row() -> BedHistoryRow:
    planting = PlantingEvent(
        kind="plant_planted",
        at=datetime(2026, 5, 1, tzinfo=UTC),
        category="planting",
        plant_key="pi_1",
        species_key="sp",
        plant_name="Tomato",
    )
    return BedHistoryRow(at=planting.at, planting=planting)


class _Tenants:
    role = TenantRole.GROWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1))
    history = FakeHistory()
    return SimpleNamespace(history=history, service=BedHistoryService(sites, history))


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_bed_history_service] = lambda: world.service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestTheList:
    def test_a_care_event_and_a_planting_event_share_one_list(self, client, world) -> None:
        world.history.rows = [_care_row(), _planting_row()]

        response = client(TenantRole.VIEWER).get(_OWN)

        assert response.status_code == 200
        care, planted = response.json()
        assert (care["id"], care["kind"], care["category"]) == ("care:ce_1", "care_event", "watering")
        assert care["care_event"]["performed_by"] == "Sabine"
        assert (planted["id"], planted["kind"], planted["plant_name"]) == (
            "plant_planted:pi_1",
            "plant_planted",
            "Tomato",
        )
        assert planted["care_event"] is None

    def test_no_account_key_is_in_the_response(self, client, world) -> None:
        world.history.rows = [_care_row()]

        text = client().get(_OWN).text

        assert "u_sabine" not in text and "tenant_key" not in text and "performed_by_user_key" not in text

    def test_the_page_is_fifty_and_the_filters_arrive_typed(self, client, world) -> None:
        client(TenantRole.LEAD).get(
            _OWN,
            params={
                "category": "watering",
                "plant_key": "pi_1",
                "from": "2026-01-01T00:00:00",
                "to": "2026-12-31T00:00:00Z",
                "performed_by": "u_tom",
                "include_corrections": "true",
                "offset": 50,
            },
        )

        ((location, criteria, tenant, offset, limit),) = world.history.calls
        assert (location, tenant, offset, limit) == ("bed", TENANT, 50, 50)
        assert criteria == BedHistoryFilter(
            category="watering",
            plant_key="pi_1",
            performed_from=datetime(2026, 1, 1, tzinfo=UTC),
            performed_to=datetime(2026, 12, 31, tzinfo=UTC),
            performed_by="u_tom",
            include_corrections=True,
        )

    def test_corrections_are_off_by_default(self, client, world) -> None:
        client().get(_OWN)

        assert world.history.calls[0][1].include_corrections is False


class TestValidation:
    def test_an_unknown_category_is_422(self, client, world) -> None:
        assert client().get(_OWN, params={"category": "nonsense"}).status_code == 422
        assert world.history.calls == []

    def test_to_before_from_is_422(self, client, world) -> None:
        response = client().get(_OWN, params={"from": "2026-06-02T00:00:00Z", "to": "2026-06-01T00:00:00Z"})

        assert response.status_code == 422 and world.history.calls == []

    def test_the_limit_is_bounded(self, client) -> None:
        assert client().get(_OWN, params={"limit": 500}).status_code == 422


class TestFilterByPerson:
    """E-16 / SR-020: the same rule as ``GET /care-events``."""

    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER])
    def test_a_viewer_or_grower_may_filter_by_themselves(self, client, world, role) -> None:
        assert client(role).get(_OWN, params={"performed_by": "u_sabine"}).status_code == 200

    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER])
    def test_a_viewer_or_grower_may_not_filter_by_a_colleague(self, client, world, role) -> None:
        response = client(role).get(_OWN, params={"performed_by": "u_tom"})

        assert response.status_code == 403 and world.history.calls == []

    def test_a_lead_may_filter_by_a_colleague(self, client) -> None:
        assert client(TenantRole.LEAD).get(_OWN, params={"performed_by": "u_tom"}).status_code == 200

    def test_the_erased_member_marker_is_422_for_everybody(self, client, world) -> None:
        response = client(TenantRole.LEAD).get(_OWN, params={"performed_by": "_anonymized"})

        assert response.status_code == 422 and world.history.calls == []


class TestAnotherTenant:
    def test_a_bed_of_another_tenant_is_404_and_the_read_never_runs(self, client, world) -> None:
        response = client(TenantRole.LEAD).get("/api/v1/t/other/locations/bed/history")

        assert response.status_code == 404 and world.history.calls == []

    def test_an_absent_bed_is_404_alike(self, client) -> None:
        assert client().get("/api/v1/t/own/locations/nowhere/history").status_code == 404
