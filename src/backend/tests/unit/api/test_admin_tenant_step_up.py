"""#2009 — a platform admin deactivating a tenant or removing a member passes the admin's own step-up.

Three platform-admin routes locked members out of a tenant with nothing but the admin
session (or one of its API keys):

* ``PATCH /admin/platform/tenants/{key}`` with ``is_active: false`` — every member of
  the tenant loses access;
* ``DELETE /admin/platform/tenants/{tenant_key}/members/{membership_key}`` and
* ``DELETE /admin/platform/users/{user_key}/memberships/{membership_key}`` — one
  member, also the tenant's last ``lead``, is removed.

``DELETE /admin/platform/tenants/{key}`` (#1791) and ``DELETE /admin/platform/users/{key}``
(#1814) already demanded the step-up; the rule of #1992 — "a change that can lead to
erasure or lockout of another account is a step-up act" — puts these three beside them
(operator decision on #2009, REQ-024 AK-56). The same :class:`StepUpVerifier`, the same
body shape as ``PATCH /admin/platform/users/{key}`` (``current_password`` /
``step_up_code`` / ``step_up_token``), the same answers: 401 without a valid step-up,
403 from an API key, 429 ``STEP_UP_LOCKED`` — and nothing changed in any of them. A
factor is bound to the tenant or the membership it was obtained for (#1884).

The requests run the real router, the real ``TenantService`` and the real verifier with
the real target rules; the repositories are in-memory doubles holding real models.
"Unchanged" is read off those stores. Every test uses a fresh admin key, so the
process-wide throttle and code tiers carry no state from one test into the next.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.admin.platform.router import router as admin_router
from app.api.v1.auth.router import limiter
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_auth_service, get_tenant_service, get_user_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.membership import MemberInfo, Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.step_up_service import default_step_up_verifier
from app.domain.services.step_up_targets import StepUpTargetAuthorizer
from app.domain.services.tenant_service import TenantService
from app.domain.services.user_service import UserService

# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
WRONG_PASSWORD = PASSWORD[::-1]
API_KEY = "kp_" + "x" * 24
SECRET = "test-secret-key-for-unit-tests-32chars!"

GARDEN = "t-garden"
OTHER_GARDEN = "t-other"
MEMBERSHIP = "m-lead"
OTHER_MEMBERSHIP = "m-other"
MEMBER = "u-member"

TENANT_VIEW = "/api/v1/admin/platform/tenants/{tenant}/members/{membership}"
USER_VIEW = "/api/v1/admin/platform/users/{user}/memberships/{membership}"


@pytest.fixture(autouse=True)
def _full_rate_limit_budget():
    """``POST /users/me/step-up-code`` is rate-limited per address; every test starts with the budget."""
    limiter.reset()
    yield
    limiter.reset()


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


def _tenant(key: str, *, is_active: bool = True, is_platform: bool = False) -> Tenant:
    return Tenant.model_validate(
        {
            "_key": key,
            "name": f"Garden {key}",
            "slug": key,
            "tenant_type": "organization",
            "owner_user_key": MEMBER,
            "is_active": is_active,
            "is_platform": is_platform,
            # An organisation is stored with its member limit (#2133); 50 is the founding default.
            "max_members": 50,
        }
    )


class _Users:
    def __init__(self, *users: User) -> None:
        self.rows = {u.key: u for u in users}

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def get_or_raise(self, key: str) -> User:
        if key not in self.rows:
            raise NotFoundError("User", key)
        return self.rows[key]


class _Tenants:
    """``ITenantRepository`` over a dict, with the narrow-write semantics of the Arango one."""

    def __init__(self, *tenants: Tenant) -> None:
        self.rows = {t.key: t for t in tenants}
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_by_key(self, key: str) -> Tenant | None:
        return self.rows.get(key)

    def get_by_slug(self, slug: str) -> Tenant | None:
        return next((t for t in self.rows.values() if t.slug == slug), None)

    def update_fields(self, key: str, fields: dict[str, Any]) -> Tenant | None:
        if key not in self.rows:
            return None
        self.writes.append((key, dict(fields)))
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]


class _Memberships:
    """``IMembershipRepository`` over a dict — what the removal and the target rule read."""

    def __init__(self, *memberships: Membership) -> None:
        self.rows = {m.key: m for m in memberships}
        self.deleted: list[str] = []
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_by_key(self, key: str) -> Membership | None:
        return self.rows.get(key)

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        return next((m for m in self.rows.values() if m.user_key == user_key and m.tenant_key == tenant_key), None)

    def delete(self, key: str) -> bool:
        self.deleted.append(key)
        return self.rows.pop(key, None) is not None

    def update_fields(self, key: str, fields: dict[str, Any]) -> Membership | None:
        if key not in self.rows:
            return None
        self.writes.append((key, dict(fields)))
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]

    def count_managers(self, tenant_key: str) -> int:
        return sum(1 for m in self.rows.values() if m.tenant_key == tenant_key and m.is_active and m.has_management)

    def count_active_members(self, *, tenant_key: str) -> int:
        return sum(1 for m in self.rows.values() if m.tenant_key == tenant_key and m.is_active)

    def list_by_tenant(self, tenant_key: str) -> list[MemberInfo]:
        return [
            MemberInfo(
                key=m.key or "",
                user_key=m.user_key,
                display_name=m.user_key,
                email=f"{m.user_key}@example.org",
                role=m.role,
                is_active=m.is_active,
                joined_at=None,
            )
            for m in self.rows.values()
            if m.tenant_key == tenant_key
        ]


class _World:
    """One platform admin, one tenant with its sole lead, the platform tenant — and the services the routes reach."""

    def __init__(self, *, password_hash: str | None = PASSWORD_HASH, garden_active: bool = True) -> None:
        self.admin_key = f"admin-{uuid.uuid4().hex[:12]}"
        self.admin = User.model_validate(
            {
                "_key": self.admin_key,
                "email": f"{self.admin_key}@example.org",
                "display_name": "Admin",
                "password_hash": password_hash,
            }
        )
        member = User.model_validate({"_key": MEMBER, "email": "member@example.org", "display_name": "Member"})
        self.users = _Users(self.admin, member)
        self.tenants = _Tenants(
            _tenant(GARDEN, is_active=garden_active), _tenant(OTHER_GARDEN), _tenant("platform", is_platform=True)
        )
        self.memberships = _Memberships(
            # The garden's last lead — the member #2009 says one request could strip.
            Membership(_key=MEMBERSHIP, user_key=MEMBER, tenant_key=GARDEN, role=TenantRole.LEAD),
            Membership(_key=OTHER_MEMBERSHIP, user_key=MEMBER, tenant_key=OTHER_GARDEN, role=TenantRole.GROWER),
            Membership(user_key=self.admin_key, tenant_key="platform", role=TenantRole.LEAD),
        )
        # The real target rules (#1884) over this world's repositories, on the process-wide
        # tiers — the issuing AuthService and the verifying TenantService share them, as in production.
        self.verifier = default_step_up_verifier(
            target_policy=StepUpTargetAuthorizer(
                user_repo=self.users,  # type: ignore[arg-type]
                membership_repo=self.memberships,  # type: ignore[arg-type]
                tenant_repo=self.tenants,  # type: ignore[arg-type]
                tenant_erasure_repo=None,
                auth_provider_repo=MagicMock(**{"list_by_user.return_value": []}),
                oidc_config_repo=MagicMock(),
            )
        )
        self.tenant_service = TenantService(
            tenant_repo=self.tenants,  # type: ignore[arg-type]
            membership_repo=self.memberships,  # type: ignore[arg-type]
            invitation_repo=MagicMock(),
            assignment_repo=MagicMock(),
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            step_up_verifier=self.verifier,
        )
        self.mail = MagicMock()
        self.auth = AuthService(
            user_repo=self.users,  # type: ignore[arg-type]
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine(SECRET, "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url="https://app.test",
            step_up_verifier=self.verifier,
        )

    def client(self) -> TestClient:
        app = FastAPI()
        for router in (users_router, admin_router):
            app.include_router(router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.admin
        app.dependency_overrides[get_is_platform_admin] = lambda: True
        app.dependency_overrides[get_tenant_service] = lambda: self.tenant_service
        app.dependency_overrides[get_user_service] = lambda: UserService(self.users)  # type: ignore[arg-type]
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        return TestClient(app, raise_server_exceptions=False)

    def send(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        bearer: str | None = None,
        ip: str = "198.51.100.7",
    ) -> Any:
        headers = {"X-Forwarded-For": ip}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        if body is None:
            return self.client().request(method, path, headers=headers)
        return self.client().request(method, path, json=body, headers=headers)

    def patch_tenant(self, key: str, fields: dict[str, Any], **kwargs: Any) -> Any:
        return self.send("PATCH", f"/api/v1/admin/platform/tenants/{key}", fields, **kwargs)

    def issue_code(self, action: str, target: str) -> str:
        resp = self.send("POST", "/api/v1/users/me/step-up-code", {"action": action, "target": target})
        assert resp.status_code == 202, resp.text
        return self.mail.send_step_up_code_email.call_args.kwargs["code"]

    # ── what survived ────────────────────────────────────────────────────

    def garden_active(self) -> bool:
        return self.tenants.rows[GARDEN].is_active

    def lead_still_member(self) -> bool:
        return MEMBERSHIP in self.memberships.rows and self.memberships.deleted == []


def _view_path(view: str, membership: str = MEMBERSHIP) -> str:
    if view == "tenant":
        return TENANT_VIEW.format(tenant=GARDEN, membership=membership)
    return USER_VIEW.format(user=MEMBER, membership=membership)


VIEWS = [pytest.param("tenant", id="tenant view"), pytest.param("user", id="user view")]


# ── PATCH /admin/platform/tenants/{key}: deactivation ────────────────────────


@pytest.mark.parametrize(
    "step_up",
    [
        pytest.param({}, id="no password"),
        pytest.param({"current_password": WRONG_PASSWORD}, id="wrong password"),
        pytest.param({"step_up_code": "12345678"}, id="a code instead of the password"),
    ],
)
def test_a_tenant_is_not_deactivated_without_the_admins_step_up(step_up: dict[str, Any]) -> None:
    world = _World()

    resp = world.patch_tenant(GARDEN, {"is_active": False, **step_up})

    assert resp.status_code == 401, resp.text
    assert world.garden_active() is True
    assert world.tenants.writes == []


def test_a_tenant_is_deactivated_with_the_admins_own_password() -> None:
    world = _World()

    resp = world.patch_tenant(GARDEN, {"is_active": False, "current_password": PASSWORD})

    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is False
    assert world.garden_active() is False
    # The step-up field is the admin's, never written to the tenant; the bool is the
    # suspension switch on the status model (#2123).
    assert world.tenants.writes == [(GARDEN, {"status": "suspended"})]


def test_an_api_key_cannot_deactivate_a_tenant_even_with_the_password() -> None:
    world = _World()

    resp = world.patch_tenant(GARDEN, {"is_active": False, "current_password": PASSWORD}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert world.garden_active() is True


def test_reactivating_a_tenant_passes_the_step_up_too() -> None:
    """Like an account (#1857): reactivating restores access a deliberate deactivation took away."""
    world = _World(garden_active=False)

    refused = world.patch_tenant(GARDEN, {"is_active": True})
    assert refused.status_code == 401, refused.text
    assert world.garden_active() is False

    accepted = world.patch_tenant(GARDEN, {"is_active": True, "current_password": PASSWORD})
    assert accepted.status_code == 200, accepted.text
    assert world.garden_active() is True


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param({"description": "New text"}, id="description"),
        # The edit form re-sends the value it loaded; nothing changes.
        pytest.param({"description": "New text", "is_active": True}, id="re-sent is_active"),
    ],
)
def test_an_edit_that_does_not_change_is_active_needs_no_step_up(fields: dict[str, Any]) -> None:
    world = _World()

    resp = world.patch_tenant(GARDEN, fields)

    assert resp.status_code == 200, resp.text
    # Only what changed reaches the store (#1992 review SEC-003): a re-sent value is not written back.
    assert world.tenants.writes == [(GARDEN, {"description": "New text"})]


def test_the_platform_tenant_is_refused_before_a_step_up_is_asked_for() -> None:
    world = _World()

    resp = world.patch_tenant("platform", {"is_active": False})

    assert resp.status_code == 403, resp.text
    assert world.tenants.rows["platform"].is_active is True


def test_a_federated_admin_deactivates_with_a_code_bound_to_this_tenant() -> None:
    world = _World(password_hash=None)
    code = world.issue_code("admin_tenant_update", GARDEN)

    # #1884 — the code obtained for this tenant does not deactivate another one …
    refused = world.patch_tenant(OTHER_GARDEN, {"is_active": False, "step_up_code": code})
    assert refused.status_code == 401, refused.text
    assert world.tenants.rows[OTHER_GARDEN].is_active is True

    # … and is not spent by the mismatch: it still deactivates the tenant it names.
    accepted = world.patch_tenant(GARDEN, {"is_active": False, "step_up_code": code})
    assert accepted.status_code == 200, accepted.text
    assert world.garden_active() is False


def test_no_code_is_issued_to_deactivate_the_platform_tenant() -> None:
    world = _World(password_hash=None)

    resp = world.send("POST", "/api/v1/users/me/step-up-code", {"action": "admin_tenant_update", "target": "platform"})

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_repeated_wrong_passwords_lock_the_deactivation_even_for_the_right_one() -> None:
    world = _World()
    for _ in range(MAX_ATTEMPTS):
        assert world.patch_tenant(GARDEN, {"is_active": False, "current_password": WRONG_PASSWORD}).status_code == 401

    resp = world.patch_tenant(GARDEN, {"is_active": False, "current_password": PASSWORD})

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert world.garden_active() is True


# ── DELETE …/members/{key} and …/memberships/{key}: removal ──────────────────


@pytest.mark.parametrize("view", VIEWS)
@pytest.mark.parametrize(
    "body",
    [
        pytest.param(None, id="no body"),
        pytest.param({}, id="empty body"),
        pytest.param({"current_password": WRONG_PASSWORD}, id="wrong password"),
    ],
)
def test_the_last_lead_is_not_removed_without_the_admins_step_up(view: str, body: dict[str, Any] | None) -> None:
    world = _World()

    resp = world.send("DELETE", _view_path(view), body)

    assert resp.status_code == 401, resp.text
    assert world.lead_still_member()


@pytest.mark.parametrize("view", VIEWS)
def test_a_member_is_removed_with_the_admins_own_password(view: str) -> None:
    world = _World()

    resp = world.send("DELETE", _view_path(view), {"current_password": PASSWORD})

    assert resp.status_code == 204, resp.text
    assert MEMBERSHIP not in world.memberships.rows
    assert world.memberships.deleted == [MEMBERSHIP]


@pytest.mark.parametrize("view", VIEWS)
def test_an_api_key_cannot_remove_a_member_even_with_the_password(view: str) -> None:
    world = _World()

    resp = world.send("DELETE", _view_path(view), {"current_password": PASSWORD}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert world.lead_still_member()


@pytest.mark.parametrize("view", VIEWS)
def test_a_federated_admin_removes_with_a_code_bound_to_this_membership(view: str) -> None:
    world = _World(password_hash=None)
    code = world.issue_code("admin_membership_removal", MEMBERSHIP)
    other = (
        TENANT_VIEW.format(tenant=OTHER_GARDEN, membership=OTHER_MEMBERSHIP)
        if view == "tenant"
        else USER_VIEW.format(user=MEMBER, membership=OTHER_MEMBERSHIP)
    )

    # #1884 — the code obtained for this membership does not remove another one …
    refused = world.send("DELETE", other, {"step_up_code": code})
    assert refused.status_code == 401, refused.text
    assert OTHER_MEMBERSHIP in world.memberships.rows
    assert world.memberships.deleted == []

    # … and is not spent by the mismatch: it still removes the membership it names.
    accepted = world.send("DELETE", _view_path(view), {"step_up_code": code})
    assert accepted.status_code == 204, accepted.text
    assert MEMBERSHIP not in world.memberships.rows


def test_a_code_obtained_to_deactivate_the_tenant_does_not_remove_its_member() -> None:
    """The act is part of the binding (review SEC-003): one step-up, one act."""
    world = _World(password_hash=None)
    code = world.issue_code("admin_tenant_update", GARDEN)

    resp = world.send("DELETE", _view_path("tenant"), {"step_up_code": code})

    assert resp.status_code == 401, resp.text
    assert world.lead_still_member()


@pytest.mark.parametrize("view", VIEWS)
def test_a_membership_under_another_parent_is_404_before_any_step_up(view: str) -> None:
    world = _World()
    path = (
        TENANT_VIEW.format(tenant=OTHER_GARDEN, membership=MEMBERSHIP)
        if view == "tenant"
        else USER_VIEW.format(user=world.admin_key, membership=MEMBERSHIP)
    )

    resp = world.send("DELETE", path, {"current_password": PASSWORD})

    assert resp.status_code == 404, resp.text
    assert world.lead_still_member()


def test_no_code_is_issued_for_a_membership_that_does_not_exist() -> None:
    world = _World(password_hash=None)

    resp = world.send(
        "POST", "/api/v1/users/me/step-up-code", {"action": "admin_membership_removal", "target": "m-404"}
    )

    assert resp.status_code == 404, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("patch", "/api/v1/admin/platform/tenants/{key}"),
        ("delete", "/api/v1/admin/platform/tenants/{tenant_key}/members/{membership_key}"),
        ("delete", "/api/v1/admin/platform/users/{user_key}/memberships/{membership_key}"),
    ],
)
def test_every_new_step_up_route_documents_its_refusals(method: str, path: str) -> None:
    app = FastAPI()
    app.include_router(admin_router, prefix="/api/v1")
    responses = app.openapi()["paths"][path][method]["responses"]

    assert {"401", "403", "429"} <= set(responses), sorted(responses)


def test_the_shared_update_path_refuses_is_active_so_no_caller_writes_it_past_the_step_up() -> None:
    """``PATCH /t/{slug}`` reaches ``update_tenant``; only ``admin_update_tenant`` may change the flag."""
    world = _World()

    with pytest.raises(ValueError, match="admin_update_tenant"):
        world.tenant_service.update_tenant(GARDEN, {"is_active": False})

    assert world.garden_active() is True
    assert world.tenants.writes == []
