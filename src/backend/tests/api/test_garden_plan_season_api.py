"""REQ-053 WP 7.16 (#2482) - ``POST /sites/{key}/plan/new-season`` on the wire (GP-API-057).

``app.main`` with the real season service, the real tenant gate and the real rate limiter (only the auth provider
and the repository are doubles): the lead-only gate, the 404 of a foreign site, the validation of ``year``, the
revision conflict and the report.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_provider, get_garden_plan_season_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.config.settings import settings
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.site import SitePlan, Slot
from app.domain.models.user import User
from app.domain.services.garden_plan_season_service import GardenPlanSeasonService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

_URL = f"/api/v1/t/own/sites/{SITE}/plan/new-season"


class _Tokens(IAuthProvider):
    def resolve_user(self, authorization, *, client_ip):
        user = self.resolve_user_optional(authorization, client_ip=client_ip)
        if user is None:
            raise UnauthorizedError("no token")
        return user

    def resolve_user_optional(self, authorization, *, client_ip):
        token = (authorization or "").removeprefix("Bearer ")
        if not token.startswith("token-"):
            return None
        name = token.removeprefix("token-")
        return User(_key=f"u_{name}", email=f"{name}@example.org", display_name=name.title())

    def is_authentication_required(self) -> bool:
        return True


class _Tenants:
    role = TenantRole.LEAD

    def get_tenant_by_slug(self, slug: str):
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str):
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str):
        return None


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(plan_revision=4)
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    repository = FakePlanRepo(FakeSites(site, foreign))
    repository.locations["bed"] = make_location("bed", "Beet 1", geometry=rect(1, 1, 3, 1))
    repository.slots = [
        Slot(
            _key="old",
            slot_id="BED_A",
            location_key="bed",
            geometry={"kind": "point", "origin": [0.5, 0.5]},
            archived_at=datetime(2026, 8, 1, tzinfo=UTC),
        )
    ]
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = GardenPlanSeasonService(repo._sites, repo)
    app.dependency_overrides[get_auth_provider] = _Tokens
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_season_service] = lambda: service

    def build(token: str = "token-sabine") -> TestClient:
        http = TestClient(app)
        http.headers["Authorization"] = f"Bearer {token}"
        return http

    try:
        yield build
    finally:
        _Tenants.role = TenantRole.LEAD
        app.dependency_overrides.clear()


class TestTheReport:
    def test_a_dry_run_answers_the_report_and_writes_nothing(self, client, repo) -> None:
        response = client().post(_URL, json={"year": 2027, "dry_run": True})

        assert response.status_code == 200
        report = response.json()
        assert (report["slots_to_create"], report["beds_copied"], report["applied"]) == (1, 1, False)
        assert report["beds"] == [{"location_key": "bed", "status": "copied", "slots": 1, "slots_outside_bed": 0}]
        assert repo.applied == []

    def test_the_request_defaults_to_a_dry_run(self, client, repo) -> None:
        assert client().post(_URL, json={"year": 2027}).json()["dry_run"] is True
        assert repo.applied == []

    def test_an_applied_run_bumps_the_revision(self, client, repo) -> None:
        report = client().post(_URL, json={"year": 2027, "dry_run": False, "expected_revision": 4}).json()

        assert report["applied"] is True and report["plan_revision"] == 5
        assert [s.geometry_source.value for s in repo.slots if s.archived_at is None] == ["season_copy"]

    def test_a_stale_revision_is_a_409(self, client, repo) -> None:
        response = client().post(_URL, json={"year": 2027, "dry_run": False, "expected_revision": 3})

        assert response.status_code == 409 and repo.applied == []


class TestTheYear:
    @pytest.mark.parametrize("year", [2026.5, "2027", True, None, 0, -5, 1900, 2101, 10**20, [2027], {"y": 1}])
    def test_nonsense_is_a_422(self, client, repo, year) -> None:
        response = client().post(_URL, json={"year": year, "dry_run": True})

        assert response.status_code == 422 and repo.applied == []

    def test_a_year_beyond_next_year_is_a_422_with_its_published_code(self, client) -> None:
        response = client().post(_URL, json={"year": datetime.now(UTC).year + 2, "dry_run": True})

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "season.invalid_year"

    def test_a_raw_infinity_literal_is_a_422_not_a_500(self, client) -> None:
        response = client().post(
            _URL, content=b'{"year": Infinity, "dry_run": true}', headers={"content-type": "application/json"}
        )

        assert response.status_code == 422

    def test_unknown_fields_are_refused(self, client) -> None:
        assert client().post(_URL, json={"year": 2027, "target": "other_site"}).status_code == 422


class TestWhoMay:
    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_a_grower_or_viewer_is_refused(self, client, repo, role) -> None:
        _Tenants.role = role

        assert client().post(_URL, json={"year": 2027, "dry_run": False}).status_code == 403
        assert repo.applied == []

    def test_without_a_token_nothing_happens(self, client, repo) -> None:
        http = client()
        http.headers.pop("Authorization")

        assert http.post(_URL, json={"year": 2027, "dry_run": False}).status_code == 401

    def test_a_foreign_site_is_a_404_and_does_not_name_its_owner(self, client, repo) -> None:
        response = client().post("/api/v1/t/own/sites/site_foreign/plan/new-season", json={"year": 2027})

        assert response.status_code == 404 and OTHER_TENANT not in response.text
        assert client().post("/api/v1/t/own/sites/site_nobody/plan/new-season", json={"year": 2027}).status_code == 404

    def test_my_site_under_another_tenants_slug_is_a_404(self, client) -> None:
        assert client().post(f"/api/v1/t/other/sites/{SITE}/plan/new-season", json={"year": 2027}).status_code == 404


class TestRateLimit:
    def test_it_shares_the_budget_of_the_import(self) -> None:
        assert settings.rate_limit_plan_import == "3/minute"

    def test_the_fourth_request_of_a_tenant_is_refused(self, client) -> None:
        statuses = [client().post(_URL, json={"year": 2027}).status_code for _ in range(3)]
        limited = client("token-anna").post(_URL, json={"year": 2027})

        assert statuses == [200, 200, 200] and limited.status_code == 429
