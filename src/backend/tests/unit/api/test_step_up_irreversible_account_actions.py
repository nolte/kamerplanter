"""#1813 / #1814 / #1816 — the step-up of every irreversible account action, through the real routes.

Three routes erase an account or a whole tenant, and one more re-checks a password:

* ``DELETE /users/me`` and ``POST /privacy/erasure`` — the account's own erasure (#1813).
  ``DELETE /users/me`` used to tombstone the user document with nothing but a session:
  no password, no erasure record, every personal record left behind.
* ``DELETE /admin/platform/users/{key}`` — a platform admin erasing another account at
  once (#1814), gated by ``require_platform_admin`` alone.
* ``DELETE /tenants/{slug}`` / ``DELETE /admin/platform/tenants/{key}`` — got a step-up
  in #1791; ``POST /users/me/password`` re-checks the current password.

The rule (REQ-023 §step-up, one ``StepUpVerifier`` for all of them): a signed-in session
of a human account, never an API key or a service account (403); the target typed back
(the account's e-mail, the tenant's slug — 422); the current password when the account has
one (401). Every refusal happens before anything is written.

#1816 — the password check is throttled: failures are counted per account *and* client
address, with an account-wide ceiling above it; a locked step-up answers 429
``STEP_UP_LOCKED`` without testing the password. The lockout covers step-ups only — the
login lockout (``failed_login_attempts``) is never touched, so a session thief cannot lock
the owner out of signing in.

The requests run the real routers and the real services; the repositories are in-memory
doubles with the real semantics. "Nothing erased" is read off the erasure store, the user
document and the tenant-erasure executor. Every test uses a fresh account key, so the
process-wide in-memory throttle tier never carries state from one test into another.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.admin.platform.router import router as admin_router
from app.api.v1.privacy.router import router as privacy_router
from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import (
    get_auth_service,
    get_privacy_service,
    get_tenant_service,
    get_user_service,
)
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.user_service import UserService
from tests.support.privacy_doubles import FakeErasureRepo
from tests.support.tenant_erasure_doubles import (
    SALT,
    FakeTenantErasureRepository,
    RecordingTenantErasureExecutor,
    tenant_service_for_deletion,
)

PASSWORD = "correct horse battery staple"
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
TARGET_PASSWORD_HASH = PasswordEngine().hash_password("the target's own password")
SLUG = "gemeinschaftsgarten"
TENANT_KEY = "t-garden"

SELF_ROUTES = [
    pytest.param(("DELETE", "/api/v1/users/me"), id="DELETE /users/me"),
    pytest.param(("POST", "/api/v1/privacy/erasure"), id="POST /privacy/erasure"),
]


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


class _Users:
    """``IUserRepository`` over a dict with the narrow-write semantics of the Arango one."""

    def __init__(self, *users: User) -> None:
        self.rows = {u.key: u for u in users}
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_or_raise(self, key: str) -> User:
        from app.common.exceptions import NotFoundError

        if key not in self.rows:
            raise NotFoundError("User", key)
        return self.rows[key]

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self.writes.append((key, dict(fields)))
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]


class _Memberships:
    def __init__(self, memberships: list[Membership]) -> None:
        self._rows = {(m.user_key, m.tenant_key): m for m in memberships}

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        return self._rows.get((user_key, tenant_key))

    def deactivate_all_for_tenant(self, tenant_key: str) -> int:
        return 0

    def get_user_memberships(self, user_key: str) -> list[Membership]:
        return [m for (u, _t), m in self._rows.items() if u == user_key]


class _World:
    """One caller, one other account, one tenant — and every service the routes reach."""

    def __init__(
        self,
        *,
        password_hash: str | None = PASSWORD_HASH,
        account_type: str = "human",
        platform_admin: bool = False,
    ) -> None:
        self.caller_key = f"caller-{uuid.uuid4().hex[:12]}"
        self.target_key = f"target-{uuid.uuid4().hex[:12]}"
        self.caller_email = f"{self.caller_key}@example.org"
        self.target_email = f"{self.target_key}@example.org"
        self.user = User.model_validate(
            {
                "_key": self.caller_key,
                "email": self.caller_email,
                "display_name": "Caller",
                "password_hash": password_hash,
                "account_type": account_type,
            }
        )
        target = User.model_validate(
            {
                "_key": self.target_key,
                "email": self.target_email,
                "display_name": "Target",
                "password_hash": TARGET_PASSWORD_HASH,
            }
        )
        self.users = _Users(self.user, target)
        self.erasures = FakeErasureRepo()
        self.refresh_tokens = MagicMock()
        memberships = [
            Membership(
                user_key=self.caller_key,
                tenant_key=TENANT_KEY,
                role=TenantRole.LEAD,
                admin_scopes=[AdminScope.MANAGEMENT],
            )
        ]
        if platform_admin:
            memberships.append(Membership(user_key=self.caller_key, tenant_key="platform", role=TenantRole.LEAD))
        self.platform_admin = platform_admin
        self.memberships = _Memberships(memberships)
        self.privacy = PrivacyService(
            export_repo=MagicMock(),
            consent_repo=MagicMock(),
            restriction_repo=MagicMock(),
            erasure_repo=self.erasures,
            email_change_repo=MagicMock(),
            user_repo=self.users,
            refresh_token_repo=self.refresh_tokens,
            data_export_engine=DataExportEngine(),
            erasure_engine=ErasureEngine(),
            consent_engine=ConsentEngine(),
            password_engine=PasswordEngine(),
            token_engine=MagicMock(),
            email_service=MagicMock(),
            frontend_url="https://app.test",
            membership_repo=self.memberships,
            reference_index_store=NoopReferenceIndexStore(),
            erasure_executor=MagicMock(),
            tombstone_salt=SALT,
        )
        # The immediate erasure run itself is pinned elsewhere
        # (test_erasure_immediate_entry.py); here only *whether* it started matters.
        self.immediate_runs = AsyncMock(return_value=None)
        self.privacy._finalize_erasure = self.immediate_runs  # type: ignore[method-assign]
        garden = Tenant.model_validate(
            {"_key": TENANT_KEY, "name": "Garden", "slug": SLUG, "tenant_type": "organization", "owner_user_key": "o"}
        )
        tenant_repo = MagicMock()
        tenant_repo.get_by_key.side_effect = lambda key: garden if key == TENANT_KEY else None
        tenant_repo.get_by_slug.side_effect = lambda slug: garden if slug == SLUG else None
        self.tenant_executor = RecordingTenantErasureExecutor()
        self.tenant_records = FakeTenantErasureRepository()
        self.tenants = tenant_service_for_deletion(
            existing=garden,
            executor=self.tenant_executor,
            record_repo=self.tenant_records,
            tenant_repo=tenant_repo,
            membership_repo=self.memberships,
        )
        self.auth = AuthService(
            user_repo=self.users,
            auth_provider_repo=MagicMock(),
            refresh_token_repo=self.refresh_tokens,
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="http://localhost:5173",
        )

    def client(self) -> TestClient:
        app = FastAPI()
        for router in (users_router, privacy_router, admin_router, tenants_router):
            app.include_router(router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.users.rows[self.caller_key]
        app.dependency_overrides[get_is_platform_admin] = lambda: self.platform_admin
        app.dependency_overrides[get_privacy_service] = lambda: self.privacy
        app.dependency_overrides[get_tenant_service] = lambda: self.tenants
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        app.dependency_overrides[get_user_service] = lambda: UserService(
            self.users, self.refresh_tokens, tombstone_salt=SALT
        )
        return TestClient(app, raise_server_exceptions=False)

    def call(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None,
        *,
        bearer: str | None = None,
        ip: str = "198.51.100.7",
    ) -> Any:
        headers = {"X-Forwarded-For": ip}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        client = self.client()
        if body is None:
            return client.request(method, path, headers=headers)
        return client.request(method, path, json=body, headers=headers)

    # ── what happened ────────────────────────────────────────────────────

    def account_untouched(self, key: str | None = None) -> bool:
        key = key or self.caller_key
        user = self.users.rows[key]
        return (
            not self.erasures.stored
            and user.is_active
            and user.password_hash is not None
            and not user.email.endswith(".invalid")
            and not any(k == key for k, _ in self.users.writes)
            and self.immediate_runs.await_count == 0
        )

    def tenant_untouched(self) -> bool:
        return self.tenant_executor.plans == [] and self.tenant_records.records == {}

    def self_step_up(self, password: str | None = PASSWORD) -> dict[str, Any]:
        body: dict[str, Any] = {"confirm_email": self.caller_email}
        if password is not None:
            body["password"] = password
        return body

    def admin_step_up(self, password: str | None = PASSWORD) -> dict[str, Any]:
        body: dict[str, Any] = {"confirm_email": self.target_email}
        if password is not None:
            body["password"] = password
        return body


# ── #1813: the account's own erasure ─────────────────────────────────────────


@pytest.mark.parametrize("route", SELF_ROUTES)
@pytest.mark.parametrize(
    ("body_of", "status"),
    [
        pytest.param(lambda w: None, 422, id="no body"),
        pytest.param(lambda w: {"password": PASSWORD}, 422, id="no e-mail echo"),
        pytest.param(lambda w: {"confirm_email": "someone@else.org", "password": PASSWORD}, 422, id="wrong echo"),
        pytest.param(lambda w: {"confirm_email": w.caller_email}, 401, id="local account, no password"),
        pytest.param(lambda w: {"confirm_email": w.caller_email, "password": "wrong"}, 401, id="wrong password"),
    ],
)
def test_the_own_erasure_without_a_valid_step_up_erases_nothing(route, body_of, status) -> None:
    world = _World()
    method, path = route

    resp = world.call(method, path, body_of(world))

    assert resp.status_code == status, resp.text
    assert world.account_untouched()


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_the_own_erasure_with_the_step_up_opens_the_art17_request(route) -> None:
    world = _World()
    method, path = route

    resp = world.call(method, path, world.self_step_up())

    assert resp.status_code in (200, 201), resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.user_key == world.caller_key
    assert erasure.origin == "self_service"
    assert erasure.step_up == "password"
    # The Art. 17 grace request: closed at once, hard-deleted by the beat later.
    assert world.users.rows[world.caller_key].is_active is False
    assert world.immediate_runs.await_count == 0


def test_delete_users_me_no_longer_tombstones_outside_art17() -> None:
    """#1813 — the old route wrote a tombstone e-mail and left every personal record behind."""
    world = _World()

    world.call("DELETE", "/api/v1/users/me", world.self_step_up())

    assert not world.users.rows[world.caller_key].email.endswith(".invalid")
    assert len(world.erasures.stored) == 1


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_the_e_mail_echo_ignores_case_and_surrounding_space(route) -> None:
    world = _World()
    method, path = route

    resp = world.call(method, path, {"confirm_email": f"  {world.caller_email.upper()} ", "password": PASSWORD})

    assert resp.status_code in (200, 201), resp.text


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_a_federated_account_confirms_with_the_echo_alone(route) -> None:
    world = _World(password_hash=None)
    method, path = route

    resp = world.call(method, path, {"confirm_email": world.caller_email})

    assert resp.status_code in (200, 201), resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.step_up == "echo"


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_a_federated_account_still_has_to_echo_its_e_mail(route) -> None:
    world = _World(password_hash=None)
    method, path = route

    resp = world.call(method, path, {"confirm_email": "wrong@example.org"})

    assert resp.status_code == 422, resp.text
    assert not world.erasures.stored


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_an_api_key_of_a_human_account_cannot_erase_it_even_with_the_password(route) -> None:
    world = _World()
    method, path = route

    resp = world.call(method, path, world.self_step_up(), bearer="kp_stored-in-some-integration")

    assert resp.status_code == 403, resp.text
    assert world.account_untouched()


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_a_service_account_cannot_erase_itself(route) -> None:
    world = _World(password_hash=None, account_type="service")
    method, path = route

    resp = world.call(method, path, {"confirm_email": world.caller_email})

    assert resp.status_code == 403, resp.text
    assert not world.erasures.stored


# ── #1814: a platform admin erasing another account ──────────────────────────


def _admin_route(world: _World) -> str:
    return f"/api/v1/admin/platform/users/{world.target_key}"


@pytest.mark.parametrize(
    ("body_of", "status"),
    [
        pytest.param(lambda w: None, 422, id="no body"),
        pytest.param(lambda w: {"password": PASSWORD}, 422, id="no e-mail echo"),
        pytest.param(lambda w: {"confirm_email": w.caller_email, "password": PASSWORD}, 422, id="own e-mail echoed"),
        pytest.param(lambda w: {"confirm_email": w.target_email}, 401, id="no admin password"),
        pytest.param(lambda w: {"confirm_email": w.target_email, "password": "wrong"}, 401, id="wrong admin password"),
        pytest.param(
            lambda w: {"confirm_email": w.target_email, "password": "the target's own password"},
            401,
            id="the target's password instead of the admin's",
        ),
    ],
)
def test_a_platform_admin_without_a_valid_step_up_erases_nothing(body_of, status) -> None:
    world = _World(platform_admin=True)

    resp = world.call("DELETE", _admin_route(world), body_of(world))

    assert resp.status_code == status, resp.text
    assert world.account_untouched(world.target_key)


def test_a_platform_admin_erases_with_the_step_up_and_the_record_says_how() -> None:
    world = _World(platform_admin=True)

    resp = world.call("DELETE", _admin_route(world), world.admin_step_up())

    assert resp.status_code == 204, resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.user_key == world.target_key
    assert erasure.origin == "platform_admin"
    assert erasure.step_up == "password"
    # The requester by salted reference, never by key — the record outlives both accounts.
    assert erasure.requested_by_subject == ErasureEngine.log_subject(world.caller_key, SALT)
    assert world.caller_key not in (erasure.requested_by_subject or "")
    assert world.immediate_runs.await_count == 1


def test_a_federated_platform_admin_confirms_with_the_echo_alone() -> None:
    world = _World(platform_admin=True, password_hash=None)

    resp = world.call("DELETE", _admin_route(world), {"confirm_email": world.target_email})

    assert resp.status_code == 204, resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.step_up == "echo"


def test_a_platform_admin_api_key_cannot_erase_an_account() -> None:
    world = _World(platform_admin=True)

    resp = world.call("DELETE", _admin_route(world), world.admin_step_up(), bearer="kp_admin-automation")

    assert resp.status_code == 403, resp.text
    assert world.account_untouched(world.target_key)


def test_a_caller_who_is_no_platform_admin_is_refused() -> None:
    world = _World(platform_admin=False)

    resp = world.call("DELETE", _admin_route(world), world.admin_step_up())

    assert resp.status_code == 403, resp.text
    assert world.account_untouched(world.target_key)


def test_the_service_itself_refuses_a_requester_without_the_platform_membership() -> None:
    """The route gate is not the only one: the service re-proves the platform-admin membership."""
    world = _World(platform_admin=False)
    world.platform_admin = True  # the route's gate says yes; the stored membership says no

    resp = world.call("DELETE", _admin_route(world), world.admin_step_up())

    assert resp.status_code == 403, resp.text
    assert world.account_untouched(world.target_key)


def test_a_platform_admin_cannot_erase_their_own_account_here() -> None:
    world = _World(platform_admin=True)

    resp = world.call(
        "DELETE",
        f"/api/v1/admin/platform/users/{world.caller_key}",
        {"confirm_email": world.caller_email, "password": PASSWORD},
    )

    assert resp.status_code == 403, resp.text
    assert world.account_untouched()


# ── #1816: the password check is throttled, and only the step-up is locked ───


def _fail(world: _World, times: int, *, ip: str = "198.51.100.7") -> None:
    for _ in range(times):
        resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up("wrong"), ip=ip)
        assert resp.status_code == 401, resp.text


def test_five_wrong_step_up_passwords_lock_the_step_up_even_for_the_right_one() -> None:
    world = _World()
    _fail(world, 5)

    resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up())

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert world.account_untouched()


def test_the_step_up_lockout_spans_every_step_up_site_of_the_account() -> None:
    """Failures on one route lock the others: one counter per account, not per route."""
    world = _World(platform_admin=True)
    _fail(world, 5)

    tenant = world.call("DELETE", f"/api/v1/tenants/{SLUG}", {"confirm_slug": SLUG, "password": PASSWORD})
    admin = world.call("DELETE", _admin_route(world), world.admin_step_up())
    own = world.call("DELETE", "/api/v1/users/me", world.self_step_up())
    change = world.call(
        "POST", "/api/v1/users/me/password", {"current_password": PASSWORD, "new_password": "An0ther-long-passphrase!"}
    )

    assert [r.status_code for r in (tenant, admin, own, change)] == [429, 429, 429, 429], [
        r.text for r in (tenant, admin, own, change)
    ]
    assert world.tenant_untouched()
    assert world.account_untouched(world.target_key)
    assert world.users.rows[world.caller_key].password_hash == PASSWORD_HASH


def test_the_password_change_counts_into_the_same_step_up_budget() -> None:
    world = _World()
    for _ in range(5):
        resp = world.call(
            "POST",
            "/api/v1/users/me/password",
            {"current_password": "wrong", "new_password": "An0ther-long-passphrase!"},
        )
        assert resp.status_code == 401, resp.text

    resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up())

    assert resp.status_code == 429, resp.text


def test_the_step_up_lockout_never_touches_the_login_lockout() -> None:
    """A session thief failing step-ups must not be able to lock the owner out of signing in."""
    world = _World()
    _fail(world, 5)
    for _ in range(3):
        locked = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up("wrong"))
        assert locked.status_code == 429, locked.text

    stored = world.users.rows[world.caller_key]
    assert stored.failed_login_attempts == 0
    assert stored.locked_until is None
    world.auth.login_local(world.caller_email, PASSWORD)  # does not raise


def test_the_lockout_is_per_client_address_below_the_account_ceiling() -> None:
    world = _World()
    _fail(world, 5, ip="198.51.100.7")

    resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up(), ip="203.0.113.20")

    assert resp.status_code == 201, resp.text


def test_rotating_addresses_hits_the_account_wide_ceiling() -> None:
    world = _World()
    for n in range(3):
        _fail(world, 5, ip=f"192.0.2.{n + 1}")

    resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up(), ip="192.0.2.99")

    assert resp.status_code == 429, resp.text
    assert world.account_untouched()


def test_an_api_key_request_is_refused_before_it_can_count() -> None:
    """Otherwise a leaked key could be used to lock the owner's step-ups."""
    world = _World()
    for _ in range(8):
        resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up("wrong"), bearer="kp_leaked")
        assert resp.status_code == 403, resp.text

    resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up())

    assert resp.status_code == 201, resp.text


def test_a_wrong_echo_is_not_counted() -> None:
    """The echo tests nothing secret; counting it would let a typo lock the step-up."""
    world = _World()
    for _ in range(8):
        resp = world.call("POST", "/api/v1/privacy/erasure", {"confirm_email": "typo@example.org", "password": "x"})
        assert resp.status_code == 422, resp.text

    resp = world.call("POST", "/api/v1/privacy/erasure", world.self_step_up())

    assert resp.status_code == 201, resp.text


def test_a_success_clears_the_counter() -> None:
    world = _World()
    _fail(world, 4)
    ok = world.call(
        "POST", "/api/v1/users/me/password", {"current_password": PASSWORD, "new_password": "An0ther-long-passphrase!"}
    )
    assert ok.status_code == 200, ok.text

    for _ in range(4):
        resp = world.call(
            "POST",
            "/api/v1/users/me/password",
            {"current_password": "wrong", "new_password": "Yet-an0ther-long-passphrase!"},
        )
        assert resp.status_code == 401, resp.text
