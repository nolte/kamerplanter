"""#2123 (REQ-024 AK-52) — the two cancellation routes, driven through the real routers.

``POST /tenants/{slug}/erasure/cancel`` cannot stand on ``get_current_tenant``: a
``pending_deletion`` tenant resolves for nobody (#2105). The guards
(``test_api_key_scope_binds_every_tenant_resolution``,
``test_tenant_selector_routes_depend_on_a_resolver``) admit it on the claim that it
depends on ``require_account_principal`` and that the service refuses every API key and
proves lead + management from the stored membership. These tests hold that claim at the
HTTP surface — and that an unknown slug answers like a forbidden one.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.admin.platform.router import router as admin_router
from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole, TenantStatus
from app.common.exceptions import KamerplanterError
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureRecord
from app.domain.models.user import User
from tests.support.tenant_erasure_doubles import FakeTenantErasureRepository, tenant_service_for_deletion

SLUG = "gemeinschaftsgarten"
TENANT_KEY = "t-garden"
CALLER = "caller-1"
PASSWORD = "correct horse battery staple"
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
DUE = NOW + timedelta(days=90)

TENANT_ROUTE = f"/api/v1/tenants/{SLUG}/erasure/cancel"
ADMIN_ROUTE = f"/api/v1/admin/platform/tenants/{TENANT_KEY}/erasure/cancel"


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


class _World:
    def __init__(
        self,
        *,
        role: TenantRole | None,
        scopes: list[AdminScope],
        platform_admin: bool = False,
        status: TenantStatus = TenantStatus.PENDING_DELETION,
    ) -> None:
        rows: dict[tuple[str, str], Membership] = {}
        if role is not None:
            rows[(CALLER, TENANT_KEY)] = Membership(
                user_key=CALLER, tenant_key=TENANT_KEY, role=role, admin_scopes=scopes
            )
        if platform_admin:
            rows[(CALLER, "platform")] = Membership(user_key=CALLER, tenant_key="platform", role=TenantRole.LEAD)
        memberships = MagicMock()
        memberships.get_by_user_and_tenant.side_effect = lambda user_key, tenant_key: rows.get((user_key, tenant_key))
        # The admin answer carries the active-member count, counted in the database (#2131).
        memberships.count_active_members.return_value = 3
        memberships.list_by_tenant.side_effect = AssertionError("member_count must not read the member list")
        self.tenant = Tenant.model_validate(
            {
                "_key": TENANT_KEY,
                "name": "Garden",
                "slug": SLUG,
                "tenant_type": "organization",
                "owner_user_key": "owner-1",
                "status": status,
                "deletion_scheduled_at": DUE if status != TenantStatus.ACTIVE else None,
            }
        )
        tenants = MagicMock()
        tenants.get_by_key.side_effect = lambda key: self.tenant if key == TENANT_KEY else None
        tenants.get_by_slug.side_effect = lambda slug: self.tenant if slug == SLUG else None

        def update_fields(key: str, fields: dict[str, Any]) -> Tenant | None:
            self.tenant = Tenant.model_validate({**self.tenant.model_dump(by_alias=True), **fields})
            return self.tenant

        tenants.update_fields.side_effect = update_fields
        self.records = FakeTenantErasureRepository()
        if status == TenantStatus.PENDING_DELETION:
            self.records.create_with_key(
                TenantErasureRecord(
                    tenant_key=TENANT_KEY,
                    tenant_type="organization",
                    origin="tenant_management",
                    status="scheduled",
                    requested_at=NOW,
                    scheduled_for=DUE,
                ),
                TenantErasureEngine.record_key(TENANT_KEY),
            )
        self.service = tenant_service_for_deletion(
            record_repo=self.records, tenant_repo=tenants, membership_repo=memberships, tenant_erasure_grace_days=90
        )
        self.user = User.model_validate(
            {"_key": CALLER, "email": "caller@example.org", "display_name": "Caller", "password_hash": PASSWORD_HASH}
        )

    def post(self, path: str, body: dict[str, Any], *, bearer: str | None = None) -> Any:
        app = FastAPI()
        app.include_router(tenants_router, prefix="/api/v1")
        app.include_router(admin_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_tenant_service] = lambda: self.service
        headers = {"Authorization": f"Bearer {bearer}"} if bearer else None
        return TestClient(app, raise_server_exceptions=False).post(path, json=body, headers=headers)

    def still_scheduled(self) -> bool:
        return (
            self.tenant.status == TenantStatus.PENDING_DELETION
            and TenantErasureEngine.record_key(TENANT_KEY) in self.records.records
        )


def test_lead_with_management_cancels_with_the_password() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    resp = world.post(TENANT_ROUTE, {"current_password": PASSWORD})

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "active"
    assert resp.json()["is_active"] is True
    assert resp.json()["deletion_scheduled_at"] is None
    assert world.records.records == {}


@pytest.mark.parametrize(
    ("role", "scopes"),
    [
        pytest.param(TenantRole.LEAD, [], id="lead-without-management"),
        pytest.param(TenantRole.VIEWER, [AdminScope.MANAGEMENT], id="management-scope-only-viewer"),
        pytest.param(None, [], id="non-member"),
    ],
)
def test_everybody_short_of_lead_and_management_is_refused(role: TenantRole | None, scopes: list) -> None:
    world = _World(role=role, scopes=scopes)

    resp = world.post(TENANT_ROUTE, {"current_password": PASSWORD})

    assert resp.status_code == 403, resp.text
    assert world.still_scheduled()


def test_an_unknown_slug_is_the_same_403_as_a_forbidden_tenant() -> None:
    world = _World(role=None, scopes=[])

    unknown = world.post("/api/v1/tenants/no-such-garden/erasure/cancel", {"current_password": PASSWORD})
    forbidden = world.post(TENANT_ROUTE, {"current_password": PASSWORD})

    assert unknown.status_code == forbidden.status_code == 403
    assert unknown.json() == forbidden.json()


@pytest.mark.parametrize(
    ("route", "world_kwargs"),
    [
        pytest.param(TENANT_ROUTE, {"role": TenantRole.LEAD, "scopes": [AdminScope.MANAGEMENT]}, id="tenant-route"),
        pytest.param(ADMIN_ROUTE, {"role": None, "scopes": [], "platform_admin": True}, id="platform-route"),
    ],
)
def test_an_api_key_never_cancels(route: str, world_kwargs: dict[str, Any]) -> None:
    world = _World(**world_kwargs)

    resp = world.post(route, {"current_password": PASSWORD}, bearer="kp_stored-in-some-integration")

    assert resp.status_code == 403, resp.text
    assert world.still_scheduled()


def test_a_wrong_password_cancels_nothing() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    resp = world.post(TENANT_ROUTE, {"current_password": "not the password"})

    assert resp.status_code == 401, resp.text
    assert world.still_scheduled()


def test_a_platform_admin_cancels_on_the_admin_route() -> None:
    world = _World(role=None, scopes=[], platform_admin=True)

    resp = world.post(ADMIN_ROUTE, {"current_password": PASSWORD})

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "active"
    assert resp.json()["member_count"] == 3


def test_an_active_tenant_has_nothing_to_cancel() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], status=TenantStatus.ACTIVE)

    resp = world.post(TENANT_ROUTE, {"current_password": PASSWORD})

    assert resp.status_code == 422, resp.text


def test_the_body_takes_no_lifecycle_fields() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    resp = world.post(TENANT_ROUTE, {"current_password": PASSWORD, "status": "active"})

    assert resp.status_code == 422, resp.text
    assert world.still_scheduled()
