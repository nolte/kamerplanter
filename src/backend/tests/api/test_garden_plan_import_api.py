"""REQ-053 WP 5.3 (#2432) - ``POST /sites/{key}/plan/import`` on the wire.

``app.main`` with the real import service, the real tenant gate and the real rate limiter (only the auth provider
and the repository are doubles). What is measured is what a client receives: the lead-only gate (a grower or viewer
is refused **before** the file is read), the 404 of a foreign site, the 5 MB body ceiling of this one route (and
the 1 MiB of its neighbours), the per-tenant 3/min budget, and the report.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import (
    get_auth_provider,
    get_garden_plan_export_service,
    get_garden_plan_import_service,
    get_garden_plan_service,
    get_tenant_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.config.settings import settings
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.models.garden_plan_import import MAX_IMPORT_BYTES
from app.domain.models.site import SitePlan
from app.domain.models.user import User
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_import_service import GardenPlanImportService
from app.domain.services.garden_plan_service import GardenPlanService
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

_BASE = "/api/v1/t/own"
_IMPORT = f"{_BASE}/sites/{SITE}/plan/import"
_EXPORT = f"{_BASE}/sites/{SITE}/plan/export"


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
    repository = FakePlanRepo(FakeSites(site, foreign))
    repository.locations["bed"] = make_location("bed", "Beet 1", geometry=rect(1, 1, 2, 1))
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    plan_service = GardenPlanService(repo._sites, repo)
    export_service = GardenPlanExportService(repo._sites, repo, plan_service)
    import_service = GardenPlanImportService(repo._sites, repo, plan_service, export_service)
    app.dependency_overrides[get_auth_provider] = _Tokens
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_service] = lambda: plan_service
    app.dependency_overrides[get_garden_plan_export_service] = lambda: export_service
    app.dependency_overrides[get_garden_plan_import_service] = lambda: import_service

    def build(token: str = "token-sabine") -> TestClient:
        http = TestClient(app)
        http.headers["Authorization"] = f"Bearer {token}"
        return http

    try:
        yield build
    finally:
        _Tenants.role = TenantRole.LEAD
        app.dependency_overrides.clear()


def body(document: dict, **options) -> dict:
    return {"mode": "replace", "dry_run": True, **options, "document": document}


def a_file(client) -> dict:
    """The plan as ``GET /plan/export`` gives it - a real file, not a hand-written one."""
    return client().get(_EXPORT).json()


class TestTheReport:
    def test_a_dry_run_answers_the_counts_and_writes_nothing(self, client, repo) -> None:
        document = a_file(client)

        response = client().post(_IMPORT, json=body(document))

        assert response.status_code == 200, response.text
        report = response.json()
        assert report["dry_run"] is True and report["applied"] is False
        assert report["would_create"] == {
            "locations": 1,
            "garden_objects": 0,
            "slots": 0,
            "plan_settings": 0,
            "zones": 0,
        }
        assert report["would_delete"]["locations"] == 1 and report["would_update"]["plan_settings"] == 1
        assert report["errors"] == [] and report["dropped_references"] == []
        assert repo.applied == [] and list(repo.locations) == ["bed"]  # the positive control for "nothing written"

    def test_an_applied_replace_has_new_keys_and_a_snapshot(self, client, repo) -> None:
        document = a_file(client)

        response = client().post(_IMPORT, json=body(document, dry_run=False, confirm_site_name="Garten"))

        assert response.status_code == 200, response.text
        report = response.json()
        assert report["applied"] is True and report["snapshot_written"] is True and report["plan_revision"] == 5
        assert "bed" not in repo.locations and len(repo.locations) == 1  # new key; the old one is gone
        assert [snapshot["locations"][0]["key"] for snapshot in repo.snapshots] == ["bed"]

    def test_a_failing_file_in_a_dry_run_is_listed_not_raised(self, client) -> None:
        document = a_file(client)
        document["locations"].append({**document["locations"][0], "key": "dup", "name": "Beet 2"})  # on top of it

        response = client().post(_IMPORT, json=body(document))

        assert response.status_code == 200
        assert response.json()["errors_total"] >= 1 and "bed.overlap" in {e["code"] for e in response.json()["errors"]}
        assert client().post(_IMPORT, json=body(document, dry_run=False, confirm_site_name="Garten")).status_code == 422

    def test_replace_without_the_site_name_is_a_422_with_its_published_code(self, client, repo) -> None:
        document = a_file(client)

        response = client().post(_IMPORT, json=body(document, dry_run=False))

        assert response.status_code == 422 and response.json()["error_code"] == "import.site_name_mismatch"
        assert list(repo.locations) == ["bed"]

    def test_a_newer_file_is_refused_with_a_hint(self, client) -> None:
        document = {**a_file(client), "templates": []}

        response = client().post(_IMPORT, json=body(document))

        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert detail["code"] == "import.unknown_keys" and detail["keys"] == ["templates"]

    def test_the_envelope_takes_nothing_it_does_not_name(self, client) -> None:
        response = client().post(_IMPORT, json={**body(a_file(client)), "tenant_key": "ten_other"})

        assert response.status_code == 422


class TestWhoMayImport:
    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_a_grower_or_viewer_is_refused_before_the_file_is_read(self, client, repo, role) -> None:
        _Tenants.role = role

        refused = client().post(_IMPORT, content=b"not even json", headers={"content-type": "application/json"})

        assert refused.status_code == 403  # a 422 here would mean the body was parsed first
        assert repo.applied == []
        _Tenants.role = TenantRole.LEAD
        parsed = client().post(_IMPORT, content=b"not even json", headers={"content-type": "application/json"})
        assert parsed.status_code == 422  # the positive control: a lead's garbage is read, and refused as garbage

    def test_without_a_token_nothing_is_read(self, client) -> None:
        http = client()
        http.headers.pop("Authorization")

        assert http.post(_IMPORT, content=b"x" * 2_000_000).status_code == 401

    def test_a_foreign_site_is_a_404_and_does_not_name_its_owner(self, client, repo) -> None:
        document = a_file(client)

        response = client().post(f"{_BASE}/sites/site_foreign/plan/import", json=body(document))

        assert response.status_code == 404 and response.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert OTHER_TENANT not in json.dumps(response.json())
        absent = client().post(f"{_BASE}/sites/site_nobody/plan/import", json=body(document))
        assert absent.status_code == 404 and absent.json()["error_code"] == response.json()["error_code"]

    def test_my_site_under_another_tenants_slug_is_a_404(self, client) -> None:
        response = client().post(f"/api/v1/t/other/sites/{SITE}/plan/import", json=body(a_file(client)))

        assert response.status_code == 404


class TestTheFiveMegabyteCeiling:
    def _padded(self, megabytes: float) -> bytes:
        document = {"schema_version": "1", "padding": "x" * int(megabytes * 1024 * 1024)}
        return json.dumps(body(document)).encode()

    def test_a_file_above_1_mib_gets_through_to_the_service_on_this_route_only(self, client) -> None:
        content = self._padded(2)
        headers = {"content-type": "application/json"}

        on_import = client().post(_IMPORT, content=content, headers=headers)
        on_batch = client().post(f"{_BASE}/sites/{SITE}/plan/batch", content=content, headers=headers)

        assert on_import.status_code == 422 and on_import.json()["details"][0]["code"] == "import.unknown_keys"
        assert on_batch.status_code == 413  # the neighbours keep the 1 MiB ceiling

    def test_a_file_above_5_mb_is_a_413(self, client, repo) -> None:
        response = client().post(
            _IMPORT,
            content=self._padded(MAX_IMPORT_BYTES / 1024 / 1024 + 1),
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 413
        assert repo.applied == []

    def test_a_path_that_only_looks_like_the_import_keeps_the_small_ceiling(self, client) -> None:
        response = client().post(f"{_IMPORT}/x", content=self._padded(2), headers={"content-type": "application/json"})

        assert response.status_code == 413


class TestRateLimit:
    def test_the_budget_is_three_a_minute(self) -> None:
        assert settings.rate_limit_plan_import == "3/minute"

    def test_the_fourth_request_of_a_tenant_is_refused_whoever_sends_it(self, client) -> None:
        document = a_file(client)
        statuses = [client("token-sabine").post(_IMPORT, json=body(document)).status_code for _ in range(2)]
        statuses.append(client("token-anna").post(_IMPORT, json=body(document)).status_code)
        limited = client("token-anna").post(_IMPORT, json=body(document))

        assert statuses == [200, 200, 200]
        assert limited.status_code == 429
        assert 1 <= int(limited.headers["retry-after"]) <= 60


_SNAPSHOTS = f"{_BASE}/sites/{SITE}/plan/snapshots"


class TestScopedExportWp718:
    def test_a_selection_is_exactly_the_named_bed_and_carries_no_plan_settings(self, client, repo) -> None:
        repo.locations["bed2"] = make_location("bed2", "Beet 2", geometry=rect(5, 1, 2, 1))

        response = client().get(_EXPORT, params={"scope": "selection", "keys": "bed2"})

        assert response.status_code == 200, response.text
        document = response.json()
        assert [loc["name"] for loc in document["locations"]] == ["Beet 2"] and document["plan"] is None
        assert "selection" in response.headers["content-disposition"]
        whole = client().get(_EXPORT).json()  # positive control: the default is the whole plan
        assert len(whole["locations"]) == 2 and whole["plan"] is not None

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_every_role_may_read_a_partial_export(self, client, role) -> None:
        _Tenants.role = role

        assert client().get(_EXPORT, params={"scope": "subtree", "keys": "bed"}).status_code == 200

    @pytest.mark.parametrize(
        ("params", "status"),
        [
            ({"scope": "everything"}, 422),
            ({"scope": "selection"}, 422),  # keys required
            ({"scope": "site", "keys": "bed"}, 422),
            ({"scope": "selection", "keys": "bed;drop"}, 422),
            ({"scope": "selection", "keys": ",".join(str(n) for n in range(101))}, 422),
            ({"scope": "selection", "keys": "nope"}, 404),
            ({"scope": "subtree", "keys": "object:1"}, 422),
        ],
    )
    def test_a_bad_selection_is_refused_with_its_status(self, client, params, status) -> None:
        assert client().get(_EXPORT, params=params).status_code == status


class TestTargetAndOffsetWp718:
    def test_the_report_echoes_target_and_offset_and_the_geometry_moves(self, client, repo) -> None:
        document = a_file(client)
        sent = body(document, mode="merge", dry_run=False, target="other_site", offset_m=[2.0, 1.0])

        response = client().post(_IMPORT, json=sent)

        assert response.status_code == 200, response.text
        assert response.json()["target"] == "other_site" and response.json()["offset_m"] == [2.0, 1.0]
        moved = [loc for key, loc in repo.locations.items() if key != "bed"]
        assert [loc.geometry.origin for loc in moved] == [(3.0, 2.0)]

    @pytest.mark.parametrize("offset", [["inf", 0], ["nan", 0], [1e308, 0], [2000, 0], [1], [1, 2, 3], "x"])
    def test_a_bad_offset_is_a_422_and_never_a_500(self, client, repo, offset) -> None:
        response = client().post(_IMPORT, json=body(a_file(client), mode="merge", offset_m=offset))

        assert response.status_code == 422
        assert repo.applied == []

    def test_infinity_literals_in_the_raw_body_are_a_422_too(self, client) -> None:
        raw = json.dumps(body(a_file(client), mode="merge")).replace('"mode"', '"offset_m": [Infinity, 0], "mode"', 1)

        response = client().post(_IMPORT, content=raw.encode(), headers={"content-type": "application/json"})

        assert response.status_code == 422

    def test_an_offset_with_replace_and_an_unknown_target_are_422s(self, client) -> None:
        document = a_file(client)

        assert client().post(_IMPORT, json=body(document, offset_m=[1, 1])).json()["error_code"] == (
            "import.offset_requires_merge"
        )
        assert client().post(_IMPORT, json=body(document, target="elsewhere")).status_code == 422
        assert client().post(_IMPORT, json=body(document, mode="merge", target="same_site")).status_code == 200

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_a_cross_tenant_import_is_still_lead_only(self, client, role) -> None:
        _Tenants.role = role

        refused = client().post(_IMPORT, json=body({}, target="other_tenant"))

        assert refused.status_code == 403


class TestSnapshotsWp719:
    """GP-API-058 (list) and GP-API-059 (restore) on the wire."""

    def _replace(self, client) -> None:
        response = client().post(_IMPORT, json=body(a_file(client), dry_run=False, confirm_site_name="Garten"))
        assert response.status_code == 200, response.text

    def test_the_list_names_the_snapshot_by_counts_and_never_carries_the_plan(self, client, repo) -> None:
        assert client().get(_SNAPSHOTS).json() == []
        self._replace(client)

        response = client().get(_SNAPSHOTS)

        assert response.status_code == 200
        (entry,) = response.json()
        assert entry["locations"] == 1 and entry["audit_key"] and "snapshot" not in entry
        assert "snapshot" not in json.dumps(response.json())

    def test_the_list_is_bounded_by_the_page(self, client) -> None:
        self._replace(client)
        self._replace(client)

        assert len(client().get(_SNAPSHOTS).json()) == 2
        assert len(client().get(_SNAPSHOTS, params={"limit": 1}).json()) == 1

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_list_and_restore_are_lead_only(self, client, repo, role) -> None:
        self._replace(client)
        audit_key = client().get(_SNAPSHOTS).json()[0]["audit_key"]
        _Tenants.role = role

        assert client().get(_SNAPSHOTS).status_code == 403
        restore = client().post(f"{_SNAPSHOTS}/{audit_key}/restore", json={"dry_run": True})
        assert restore.status_code == 403
        _Tenants.role = TenantRole.LEAD
        assert client().post(f"{_SNAPSHOTS}/{audit_key}/restore", json={"dry_run": True}).status_code == 200

    def test_a_restore_puts_the_old_plan_back_and_writes_a_snapshot_of_its_own(self, client, repo) -> None:
        self._replace(client)
        repo.locations["extra"] = make_location("extra", "Beet 9", geometry=rect(6, 4, 1, 1))
        audit_key = client().get(_SNAPSHOTS).json()[0]["audit_key"]
        before = len(repo.snapshot_rows)

        response = client().post(
            f"{_SNAPSHOTS}/{audit_key}/restore", json={"dry_run": False, "confirm_site_name": "Garten"}
        )

        assert response.status_code == 200, response.text
        assert response.json()["applied"] is True and response.json()["snapshot_written"] is True
        assert len(repo.snapshot_rows) == before + 1
        assert {loc.name for loc in repo.locations.values()} == {"Beet 1"}

    def test_a_foreign_site_or_snapshot_is_a_404_and_a_missing_name_a_422(self, client, repo) -> None:
        self._replace(client)
        audit_key = client().get(_SNAPSHOTS).json()[0]["audit_key"]
        foreign = f"{_BASE}/sites/site_foreign/plan/snapshots"

        assert client().get(foreign).status_code == 404
        assert client().post(f"{foreign}/{audit_key}/restore", json={"dry_run": True}).status_code == 404
        assert client().post(f"{_SNAPSHOTS}/nope/restore", json={"dry_run": True}).status_code == 404
        assert client().post(f"{_SNAPSHOTS}/{audit_key}/restore", json={}).json()["error_code"] == (
            "import.site_name_mismatch"
        )
        assert client().post(f"{_SNAPSHOTS}/{audit_key}/restore", json={"dry_run": True, "x": 1}).status_code == 422


def test_the_request_schema_embedded_in_the_openapi_document_has_no_dangling_ref() -> None:
    """The route embeds ``model_json_schema()`` by hand (``openapi_extra``): a ``$defs`` reference inside it points
    nowhere in the published document and fails the Spectral lint (``invalid-ref``)."""
    from app.api.v1.garden_plan.schemas import PlanImportRequest

    assert "$ref" not in json.dumps(PlanImportRequest.model_json_schema())
