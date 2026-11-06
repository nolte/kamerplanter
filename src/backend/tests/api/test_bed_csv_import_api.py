"""REQ-053 WP 8.26 (#2669) - ``POST /t/{slug}/sites/{key}/beds/import-csv`` on the wire.

``app.main`` with the real import service, the real plan service, the real tenant gate and the real rate limiter
(only the auth provider, the tenant lookup and the repositories are doubles). What a client receives is measured:
the lead-only gate (a grower is refused **before** the file is read), the 404 of a foreign site, the 1 MiB ceiling,
the per-user budget, the 422 of the quota, and the report of a dry run and of its confirmation.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import (
    get_auth_provider,
    get_bed_csv_import_service,
    get_garden_plan_service,
    get_tenant_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.config.settings import settings
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.bed_csv_import import MAX_CSV_BYTES
from app.domain.models.site import SitePlan
from app.domain.models.user import User
from app.domain.services.bed_csv_import_service import BedCsvImportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.bed_csv_fakes import FakeLocationTypes, FakeZones, zone
from tests.support.garden_plan_fakes import OTHER_TENANT, SITE, TENANT, FakePlanRepo, FakeSites, make_site

_BASE = "/api/v1/t/own"
_IMPORT = f"{_BASE}/sites/{SITE}/beds/import-csv"
_CSV = {"content-type": "text/csv"}


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
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0}, plan_revision=4
    )
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    return FakePlanRepo(FakeSites(site, foreign))


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    plan_service = GardenPlanService(repo._sites, repo)
    service = BedCsvImportService(
        repo._sites, repo, plan_service, FakeLocationTypes(), FakeZones(zone("z_1", "Tropfer"))
    )
    app.dependency_overrides[get_auth_provider] = _Tokens
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_service] = lambda: plan_service
    app.dependency_overrides[get_bed_csv_import_service] = lambda: service

    def build(token: str = "token-sabine") -> TestClient:
        http = TestClient(app)
        http.headers["Authorization"] = f"Bearer {token}"
        return http

    try:
        yield build
    finally:
        _Tenants.role = TenantRole.LEAD
        app.dependency_overrides.clear()


def bed_list(*lines: str) -> bytes:
    return "\r\n".join(["Name;Typ;Breite_m;Länge_m;Zone", *lines, ""]).encode("utf-8")


_MIXED = bed_list("Beet 1;Beet;2,5;1,2;Tropfer", "Kaputt;Beet;breit;1;", "Hochbeet;raised bed;1.5;0.8;")


class TestTheReport:
    def test_a_dry_run_reports_lines_and_errors_and_writes_nothing(self, client, repo) -> None:
        response = client().post(_IMPORT, content=_MIXED, headers=_CSV)

        assert response.status_code == 200, response.text
        report = response.json()
        assert report["dry_run"] is True and report["applied"] is False and report["plan_revision"] == 4
        assert [(row["line"], row["name"], row["width_m"]) for row in report["rows"]] == [
            (2, "Beet 1", 2.5),
            (4, "Hochbeet", 1.5),
        ]
        assert report["rows"][0]["irrigation_zone_key"] == "z_1" and report["rows"][0]["location_key"] is None
        assert report["errors"] == [{"line": 3, "column": "Breite_m", "code": "csv.invalid_number"}]
        assert report["rows_total"] == 3 and report["rows_valid"] == 2 and report["rows_skipped"] == 1
        assert repo.applied == [] and repo.locations == {}  # nothing written
        assert repo._sites.sites[SITE].plan.plan_revision == 4  # no revision bump either

    def test_the_confirmation_writes_the_valid_lines_and_skips_the_faulty_one(self, client, repo) -> None:
        planned = client().post(_IMPORT, content=_MIXED, headers=_CSV).json()

        response = client().post(
            _IMPORT,
            params={"dry_run": "false", "expected_revision": planned["plan_revision"]},
            content=_MIXED,
            headers=_CSV,
        )

        assert response.status_code == 200, response.text
        report = response.json()
        assert report["applied"] is True and report["plan_revision"] == 5
        assert report["errors"] == planned["errors"]  # the faulty line is reported again, and skipped
        keys = [row["location_key"] for row in report["rows"]]
        assert all(keys) and sorted(repo.locations) == sorted(keys)
        assert sorted(location.name for location in repo.locations.values()) == ["Beet 1", "Hochbeet"]
        assert [row["origin"] for row in report["rows"]] == [row["origin"] for row in planned["rows"]]

    def test_a_stale_revision_is_a_409_and_writes_nothing(self, client, repo) -> None:
        response = client().post(
            _IMPORT, params={"dry_run": "false", "expected_revision": 3}, content=_MIXED, headers=_CSV
        )

        assert response.status_code == 409 and response.json()["error_code"] == "plan.revision_conflict"
        assert repo.applied == []

    def test_a_file_that_is_no_bed_list_is_a_422_with_its_code(self, client) -> None:
        response = client().post(_IMPORT, content=b"Name,Typ,Breite_m,Laenge_m\r\n", headers=_CSV)

        assert response.status_code == 422 and response.json()["error_code"] == "csv.invalid_delimiter"

    def test_more_than_500_rows_is_the_plan_quota(self, client, repo) -> None:
        content = bed_list(*[f"B{n};Beet;0,1;0,1;" for n in range(501)])

        response = client().post(_IMPORT, params={"dry_run": "false"}, content=content, headers=_CSV)

        assert response.status_code == 422, response.text
        body = response.json()
        assert body["error_code"] == "plan.quota_exceeded" and body["details"][0]["limit"] == 500
        assert repo.applied == []


class TestWhoMayImport:
    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_a_grower_or_viewer_is_refused_before_the_file_is_read(self, client, repo, role) -> None:
        _Tenants.role = role

        refused = client().post(_IMPORT, params={"dry_run": "false"}, content=b"\xff\xfe not a csv", headers=_CSV)

        assert refused.status_code == 403  # a 422 here would mean the body was read first
        assert repo.applied == []
        _Tenants.role = TenantRole.LEAD
        read = client().post(_IMPORT, content=b"\xff\xfe not a csv", headers=_CSV)
        assert read.status_code == 422 and read.json()["error_code"] == "csv.invalid_encoding"  # positive control

    def test_without_a_token_nothing_is_read(self, client) -> None:
        http = client()
        http.headers.pop("Authorization")

        assert http.post(_IMPORT, content=_MIXED, headers=_CSV).status_code == 401

    def test_a_foreign_site_is_a_404_like_an_absent_one(self, client, repo) -> None:
        response = client().post(f"{_BASE}/sites/site_foreign/beds/import-csv", content=_MIXED, headers=_CSV)

        assert response.status_code == 404 and response.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert OTHER_TENANT not in json.dumps(response.json())
        absent = client().post(f"{_BASE}/sites/site_nobody/beds/import-csv", content=_MIXED, headers=_CSV)
        assert absent.status_code == 404 and absent.json()["error_code"] == response.json()["error_code"]

    def test_my_site_under_another_tenants_slug_is_a_404(self, client) -> None:
        response = client().post(f"/api/v1/t/other/sites/{SITE}/beds/import-csv", content=_MIXED, headers=_CSV)

        assert response.status_code == 404


class TestTheOneMebibyteCeiling:
    def test_a_file_above_1_mib_is_a_413(self, client, repo) -> None:
        content = _MIXED + b"x" * MAX_CSV_BYTES

        response = client().post(_IMPORT, params={"dry_run": "false"}, content=content, headers=_CSV)

        assert response.status_code == 413
        assert repo.applied == []

    def test_a_file_just_below_1_mib_is_read(self, client) -> None:
        content = _MIXED + b";" * (MAX_CSV_BYTES - len(_MIXED) - 1)

        response = client().post(_IMPORT, content=content, headers=_CSV)

        assert response.status_code == 200, response.text[:300]


class TestRateLimit:
    def test_the_budgets_are_ten_per_account_and_thirty_per_tenant(self) -> None:
        assert settings.rate_limit_plan_csv_import == "10/minute"
        assert settings.rate_limit_plan_csv_import_tenant == "30/minute"

    def test_the_eleventh_request_of_a_user_is_refused_another_user_still_passes(self, client) -> None:
        statuses = [client("token-sabine").post(_IMPORT, content=_MIXED, headers=_CSV).status_code for _ in range(10)]
        limited = client("token-sabine").post(_IMPORT, content=_MIXED, headers=_CSV)
        other = client("token-anna").post(_IMPORT, content=_MIXED, headers=_CSV)

        assert statuses == [200] * 10
        assert limited.status_code == 429 and 1 <= int(limited.headers["retry-after"]) <= 60
        assert other.status_code == 200

    def test_the_tenant_bucket_is_shared_by_its_members(self, client) -> None:
        """SEC-003: three members spend the tenant's 30 a minute, a fourth is refused inside his own budget."""
        statuses = [
            client(f"token-{name}").post(_IMPORT, content=_MIXED, headers=_CSV).status_code
            for name in ("sabine", "anna", "jonas")
            for _ in range(10)
        ]
        fourth = client("token-mia").post(_IMPORT, content=_MIXED, headers=_CSV)

        assert statuses == [200] * 30
        assert fourth.status_code == 429


class TestTheContentType:
    @pytest.mark.parametrize(
        "content_type", ["text/csv", "text/csv; charset=utf-8", "TEXT/PLAIN", "application/vnd.ms-excel"]
    )
    def test_what_browsers_send_for_a_csv_file_is_accepted(self, client, content_type) -> None:
        response = client().post(_IMPORT, content=_MIXED, headers={"content-type": content_type})

        assert response.status_code == 200, response.text

    @pytest.mark.parametrize("content_type", ["application/json", "multipart/form-data; boundary=x", "image/png"])
    def test_any_other_type_is_a_415_and_nothing_is_read(self, client, repo, content_type) -> None:
        response = client().post(
            _IMPORT, params={"dry_run": "false"}, content=_MIXED, headers={"content-type": content_type}
        )

        assert response.status_code == 415 and response.json()["error_code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert repo.applied == []

    def test_a_foreign_site_is_a_404_before_the_content_type_and_the_body(self, client) -> None:
        """SEC-005: the ownership is resolved before the body is read - a foreign site never sees a 415 or 422."""
        response = client().post(
            f"{_BASE}/sites/site_foreign/beds/import-csv", content=b"\xff garbage", headers={"content-type": "x/y"}
        )

        assert response.status_code == 404


class TestTheContract:
    def test_the_openapi_document_names_the_csv_body_and_the_report(self) -> None:
        from app.main import app

        operation = app.openapi()["paths"]["/api/v1/t/{tenant_slug}/sites/{key}/beds/import-csv"]["post"]

        assert "text/csv" in operation["requestBody"]["content"]
        assert {p["name"] for p in operation["parameters"]} >= {"key", "dry_run", "expected_revision"}
        assert "REQUEST_BODY_TOO_LARGE" in operation["responses"]["413"]["description"]
        assert "415" in operation["responses"]
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/BedCsvImportResponse")
