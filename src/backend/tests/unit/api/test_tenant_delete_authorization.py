"""#1791 — who may erase a whole tenant, driven through both HTTP routes.

Since #1769 a tenant deletion erases every tenant-scoped collection and
pseudonymises the retention rows irreversibly. Before #1791 the tenant route was
gated on the ``management`` scope alone, so a *viewer* holding it — the club
secretary REQ-049 §2.4 describes — could erase a community garden with one
request, and neither route asked the caller to prove it was really them.

The rule (REQ-024 §1a.2, REQ-049 §4.2):

* tenant route ``DELETE /tenants/{slug}``: an active membership with the domain
  role **lead** *and* the **management** scope — both axes, not either; being
  the tenant's owner neither suffices nor is required;
* platform route ``DELETE /admin/platform/tenants/{key}``: a platform admin;
* both: a step-up in the request body — the tenant's slug echoed back, plus the
  current password for an account that has one (a federated account has no
  local secret; the slug echo is its confirmation, the REQ-394 precedent);
* a service account never deletes a tenant: an API key cannot re-authenticate.

The requests run the real routers, the real ``get_current_tenant`` /
``require_platform_admin`` dependencies and the real ``TenantService``; only the
repositories and the executor are doubles. "Nothing was erased" is read off the
executor (no plan handed over) and the record store (no record written), so a
refusal that fires *after* the erasure started would still fail here.
"""

from __future__ import annotations

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
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError, KamerplanterError
from app.config.settings import settings
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantDeletionConfirmation, TenantErasureRecord
from app.domain.models.user import User
from tests.support.step_up import admitting_every_target
from tests.support.tenant_erasure_doubles import (
    FakeTenantErasureRepository,
    RecordingTenantErasureExecutor,
    tenant_service_for_deletion,
)

SLUG = "gemeinschaftsgarten"
TENANT_KEY = "t-garden"
OWNER = "owner-1"
CALLER = "caller-1"
PASSWORD = "correct horse battery staple"
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)

TENANT_ROUTE = f"/api/v1/tenants/{SLUG}"
ADMIN_ROUTE = f"/api/v1/admin/platform/tenants/{TENANT_KEY}"
STEP_UP = {"confirm_slug": SLUG, "password": PASSWORD}


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that can erase has a log salt (#1812): the erasure refuses to run without one."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code})


class _Memberships:
    """``get_by_user_and_tenant`` / ``deactivate_all_for_tenant`` over a dict, like the AQL."""

    def __init__(self, memberships: list[Membership]) -> None:
        self._rows = {(m.user_key, m.tenant_key): m for m in memberships}

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        return self._rows.get((user_key, tenant_key))

    def deactivate_all_for_tenant(self, tenant_key: str) -> int:
        hits = [k for k in self._rows if k[1] == tenant_key]
        for k in hits:
            self._rows[k] = self._rows[k].model_copy(update={"is_active": False})
        return len(hits)


class _World:
    def __init__(
        self,
        *,
        role: TenantRole | None,
        scopes: list[AdminScope],
        platform_admin: bool = False,
        owner: str = OWNER,
        password_hash: str | None = PASSWORD_HASH,
        account_type: str = "human",
        membership_active: bool = True,
        light_mode: bool = False,
        tenant_gone: bool = False,
    ) -> None:
        memberships = []
        if role is not None:
            memberships.append(
                Membership(
                    user_key=CALLER, tenant_key=TENANT_KEY, role=role, admin_scopes=scopes, is_active=membership_active
                )
            )
        if platform_admin:
            memberships.append(Membership(user_key=CALLER, tenant_key="platform", role=TenantRole.LEAD))
        garden = Tenant.model_validate(
            {"_key": TENANT_KEY, "name": "Garden", "slug": SLUG, "tenant_type": "organization", "owner_user_key": owner}
        )
        tenant_repo = MagicMock()
        tenant_repo.get_by_key.side_effect = lambda key: garden if key == TENANT_KEY and not tenant_gone else None
        tenant_repo.get_by_slug.side_effect = lambda slug: garden if slug == SLUG else None
        self.executor = RecordingTenantErasureExecutor()
        self.records = FakeTenantErasureRepository()
        self.service = tenant_service_for_deletion(
            existing=garden,
            executor=self.executor,
            record_repo=self.records,
            tenant_repo=tenant_repo,
            membership_repo=_Memberships(memberships),
            light_mode=light_mode,
        )
        self.user = User.model_validate(
            {
                "_key": CALLER,
                "email": "caller@example.org",
                "display_name": "Caller",
                "password_hash": password_hash,
                "account_type": account_type,
            }
        )

    def client(self) -> TestClient:
        app = FastAPI()
        app.include_router(tenants_router, prefix="/api/v1")
        app.include_router(admin_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.user
        app.dependency_overrides[get_tenant_service] = lambda: self.service
        return TestClient(app, raise_server_exceptions=False)

    def delete(self, path: str, body: dict[str, Any] | None, *, bearer: str | None = None) -> Any:
        client = self.client()
        headers = {"Authorization": f"Bearer {bearer}"} if bearer else None
        if body is None:
            return client.delete(path, headers=headers)
        return client.request("DELETE", path, json=body, headers=headers)

    def nothing_erased(self) -> bool:
        return self.executor.plans == [] and self.records.records == {}

    def record(self) -> dict[str, Any]:
        return self.records.records[TenantErasureEngine.record_key(TENANT_KEY)]


# ── Tenant route: who ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("role", "scopes"),
    [
        pytest.param(TenantRole.VIEWER, [AdminScope.MANAGEMENT], id="management-scope-only-viewer"),
        pytest.param(TenantRole.GROWER, [AdminScope.MANAGEMENT], id="grower-with-management"),
        pytest.param(TenantRole.GROWER, [], id="grower"),
        pytest.param(TenantRole.LEAD, [], id="lead-without-management"),
        pytest.param(TenantRole.LEAD, [AdminScope.TECHNICAL], id="lead-with-technical-only"),
        pytest.param(TenantRole.VIEWER, [AdminScope.MANAGEMENT, AdminScope.TECHNICAL], id="viewer-both-scopes"),
    ],
)
def test_the_tenant_route_refuses_every_caller_short_of_lead_and_management(
    role: TenantRole, scopes: list[AdminScope]
) -> None:
    world = _World(role=role, scopes=scopes)

    resp = world.delete(TENANT_ROUTE, STEP_UP)

    assert resp.status_code == 403, resp.text
    assert world.nothing_erased()


def test_a_non_member_is_refused_before_anything_happens() -> None:
    world = _World(role=None, scopes=[])

    resp = world.delete(TENANT_ROUTE, STEP_UP)

    assert resp.status_code == 403
    assert world.nothing_erased()


def test_a_lead_with_management_who_is_not_the_owner_may_delete() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], owner="someone-else")

    resp = world.delete(TENANT_ROUTE, STEP_UP)

    assert resp.status_code == 200, resp.text
    assert len(world.executor.plans) == 1
    assert world.record()["status"] == "completed"


def test_the_owner_holding_lead_and_management_may_delete() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], owner=CALLER)

    resp = world.delete(TENANT_ROUTE, STEP_UP)

    assert resp.status_code == 200, resp.text
    assert world.record()["status"] == "completed"


def test_an_owner_without_the_lead_role_is_refused() -> None:
    world = _World(role=TenantRole.VIEWER, scopes=[AdminScope.MANAGEMENT], owner=CALLER)

    resp = world.delete(TENANT_ROUTE, STEP_UP)

    assert resp.status_code == 403
    assert world.nothing_erased()


def test_a_service_account_is_refused_even_as_lead_with_management() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], password_hash=None, account_type="service")

    resp = world.delete(TENANT_ROUTE, {"confirm_slug": SLUG})

    assert resp.status_code == 403
    assert world.nothing_erased()


# ── Tenant route: step-up ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("body", "status"),
    [
        pytest.param(None, 422, id="no-body"),
        pytest.param({"password": PASSWORD}, 422, id="no-slug-echo"),
        pytest.param({"confirm_slug": "another-garden", "password": PASSWORD}, 422, id="wrong-slug-echo"),
        pytest.param({"confirm_slug": SLUG}, 401, id="no-password"),
        pytest.param({"confirm_slug": SLUG, "password": ""}, 401, id="empty-password"),
        pytest.param({"confirm_slug": SLUG, "password": "not the password"}, 401, id="wrong-password"),
    ],
)
def test_a_missing_or_wrong_step_up_erases_nothing(body: dict[str, Any] | None, status: int) -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    resp = world.delete(TENANT_ROUTE, body)

    assert resp.status_code == status, resp.text
    assert world.nothing_erased()


def test_a_federated_account_no_longer_deletes_on_the_slug_alone() -> None:
    """#1815 — the slug echo proves nobody present; a federated account needs the mailed code."""
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], password_hash=None)

    resp = world.delete(TENANT_ROUTE, {"confirm_slug": SLUG})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert world.nothing_erased()


def test_a_federated_account_deletes_with_the_mailed_code() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], password_hash=None)
    with admitting_every_target(world.service._step_up_verifier) as verifier:
        code, _expires_at = verifier.issue_code(
            world.user, action="tenant_deletion", target=TENANT_KEY, authenticated_with_api_key=False, client_ip=None
        )

    resp = world.delete(TENANT_ROUTE, {"confirm_slug": SLUG, "step_up_code": code})

    assert resp.status_code == 200, resp.text
    assert world.record()["step_up"] == "email_code"


def test_a_federated_account_still_has_to_echo_the_slug() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], password_hash=None)

    resp = world.delete(TENANT_ROUTE, {"confirm_slug": "wrong"})

    assert resp.status_code == 422
    assert world.nothing_erased()


def test_the_record_names_the_requester_by_reference_and_the_step_up(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings

    log_salt = "log-pseudonym-test-salt-not-a-secret-01234"
    monkeypatch.setattr(settings, "log_pseudonym_salt", log_salt)  # #1812: the reference is a LOG pseudonym
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    world.delete(TENANT_ROUTE, STEP_UP)

    record = world.record()
    assert record["step_up"] == "password"
    assert record["origin"] == "tenant_management"
    # The record outlives the tenant: it names the caller by the salted log
    # reference, never by the account key itself.
    assert record["requested_by_subject"] == ErasureEngine.log_subject(CALLER, log_salt)
    assert CALLER not in str(record)


# ── Platform route ────────────────────────────────────────────────────────────


def test_a_platform_admin_deletes_with_the_step_up() -> None:
    world = _World(role=None, scopes=[], platform_admin=True)

    resp = world.delete(ADMIN_ROUTE, STEP_UP)

    assert resp.status_code == 204, resp.text
    record = world.record()
    assert record["origin"] == "platform_admin"
    assert record["step_up"] == "password"


@pytest.mark.parametrize(
    ("body", "status"),
    [
        pytest.param(None, 422, id="no-body"),
        pytest.param({"confirm_slug": "another-garden", "password": PASSWORD}, 422, id="wrong-slug-echo"),
        pytest.param({"confirm_slug": SLUG}, 401, id="no-password"),
        pytest.param({"confirm_slug": SLUG, "password": "not the password"}, 401, id="wrong-password"),
    ],
)
def test_a_platform_admin_without_a_valid_step_up_erases_nothing(body: dict[str, Any] | None, status: int) -> None:
    world = _World(role=None, scopes=[], platform_admin=True)

    resp = world.delete(ADMIN_ROUTE, body)

    assert resp.status_code == status, resp.text
    assert world.nothing_erased()


def test_the_platform_route_refuses_a_tenant_lead_who_is_no_platform_admin() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    resp = world.delete(ADMIN_ROUTE, STEP_UP)

    assert resp.status_code == 403
    assert world.nothing_erased()


# ── #1791 review: API keys, deactivated memberships, light mode, retries ──────


@pytest.mark.parametrize(
    ("route", "world_kwargs"),
    [
        pytest.param(TENANT_ROUTE, {"role": TenantRole.LEAD, "scopes": [AdminScope.MANAGEMENT]}, id="tenant-route"),
        pytest.param(ADMIN_ROUTE, {"role": None, "scopes": [], "platform_admin": True}, id="platform-route"),
    ],
)
def test_an_api_key_of_a_human_account_cannot_delete_even_with_the_password(
    route: str, world_kwargs: dict[str, Any]
) -> None:
    """Review SEC-001: every account may issue ``kp_`` keys, and they resolve to that human account.

    A key sits in an integration (Home Assistant, Grafana); it is no person who
    can re-authenticate, so it is refused whatever the body carries.
    """
    world = _World(**world_kwargs)

    resp = world.delete(route, STEP_UP, bearer="kp_stored-in-some-integration")

    assert resp.status_code == 403, resp.text
    assert world.nothing_erased()


def test_a_session_token_is_not_mistaken_for_an_api_key() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT])

    resp = world.delete(TENANT_ROUTE, STEP_UP, bearer="eyJhbGciOiJIUzI1NiJ9.session.token")

    assert resp.status_code == 200, resp.text


def test_a_deactivated_lead_with_management_is_refused() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], membership_active=False)

    resp = world.delete(TENANT_ROUTE, STEP_UP)

    assert resp.status_code == 403
    assert world.nothing_erased()


def test_the_service_itself_refuses_a_deactivated_membership() -> None:
    """The route refuses it in ``get_current_tenant`` already; the service must not rely on that."""
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], membership_active=False)

    with pytest.raises(ForbiddenError):
        world.service.delete_tenant(
            TENANT_KEY,
            requester=world.user,
            authenticated_with_api_key=False,
            confirmation=TenantDeletionConfirmation(confirm_slug=SLUG, password=PASSWORD),
            origin="tenant_management",
            client_ip="203.0.113.1",
        )
    assert world.nothing_erased()


def test_the_platform_route_in_light_mode_erases_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """In light mode ``require_platform_admin`` lets the sole operator through; the service still refuses."""
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    world = _World(role=None, scopes=[], light_mode=True)

    resp = world.delete(ADMIN_ROUTE, STEP_UP)

    assert resp.status_code == 403
    assert world.nothing_erased()


def test_a_retry_whose_tenant_document_is_gone_echoes_the_key() -> None:
    """An earlier attempt removed the tenant document but left the deletion open: the key is the only name left."""
    world = _World(role=None, scopes=[], platform_admin=True, tenant_gone=True)
    world.records.create_with_key(
        TenantErasureRecord(
            tenant_key=TENANT_KEY, tenant_type="organization", origin="platform_admin", status="partially_completed"
        ),
        TenantErasureEngine.record_key(TENANT_KEY),
    )

    refused = world.delete(ADMIN_ROUTE, STEP_UP)
    accepted = world.delete(ADMIN_ROUTE, {"confirm_slug": TENANT_KEY, "password": PASSWORD})

    assert refused.status_code == 422, refused.text
    assert accepted.status_code == 204, accepted.text


def test_a_retry_after_the_document_went_still_accepts_the_slug_the_dialog_sends() -> None:
    """/code-review finding: the first attempt removed the tenant document, then failed (502/500).

    The admin dialog stays open and resends the slug it showed. The record keeps
    a salted digest of that slug (never the slug itself — a personal tenant's
    slug is its owner's name), so the retry is recognised.
    """
    world = _World(role=None, scopes=[], platform_admin=True)
    world.executor._raises = RuntimeError("storage phase failed after the ArangoDB commit")
    first = world.delete(ADMIN_ROUTE, STEP_UP)
    assert first.status_code == 500, first.text
    assert SLUG not in str(world.record())

    world.executor._raises = None
    world.service._tenant_repo.get_by_key.side_effect = lambda key: None  # the document is gone now
    retry = world.delete(ADMIN_ROUTE, STEP_UP)

    assert retry.status_code == 204, retry.text
    assert world.record()["status"] == "completed"


def test_a_federated_account_deletes_with_a_fresh_re_authentication() -> None:
    """#1815 — the token of a fresh OIDC sign-in confirms the tenant deletion; the record says so."""
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], password_hash=None)
    token = world.service._step_up_verifier.issue_reauth_token(world.user, action="tenant_deletion", target=TENANT_KEY)

    resp = world.delete(TENANT_ROUTE, {"confirm_slug": SLUG, "step_up_token": token})

    assert resp.status_code == 200, resp.text
    assert world.record()["step_up"] == "oidc_reauth"


def test_a_re_authentication_for_another_act_deletes_nothing() -> None:
    world = _World(role=TenantRole.LEAD, scopes=[AdminScope.MANAGEMENT], password_hash=None)
    token = world.service._step_up_verifier.issue_reauth_token(world.user, action="password_change", target=None)

    resp = world.delete(TENANT_ROUTE, {"confirm_slug": SLUG, "step_up_token": token})

    assert resp.status_code == 401, resp.text
    assert world.nothing_erased()
