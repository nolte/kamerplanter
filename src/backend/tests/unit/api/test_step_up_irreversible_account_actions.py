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

#1815 — an account without a local password (federated sign-in only) no longer passes on
the echo alone: it asks ``POST /users/me/step-up-code`` for a one-time code mailed to its
address and sends it as ``step_up_code`` (401 ``STEP_UP_CODE_REQUIRED`` without one). The
code attempts count into the same throttle as the password ones.

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
from app.api.v1.auth.router import limiter
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
from app.domain.services.step_up_service import default_step_up_verifier
from app.domain.services.step_up_targets import StepUpTargetAuthorizer
from app.domain.services.user_service import UserService
from tests.support.privacy_doubles import FakeErasureRepo, FakePersonalTenants
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


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A deployment that can erase has a log salt (#1812): the erasure refuses to run without one."""
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


@pytest.fixture(autouse=True)
def _full_rate_limit_budget():
    """``POST /users/me/step-up-code`` is rate-limited per address; every test starts with the budget."""
    limiter.reset()
    yield
    limiter.reset()


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

    def list_by_user_with_tenant(self, user_key: str) -> list[Any]:
        return []


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
            # #1788 — an account erasure also erases the personal tenant; wired so
            # the deployment counts as able to erase.
            tenant_service=FakePersonalTenants(),
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
        self.mail = MagicMock()
        self.auth = AuthService(
            user_repo=self.users,
            auth_provider_repo=MagicMock(),
            refresh_token_repo=self.refresh_tokens,
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url="http://localhost:5173",
            # The real target rules (#1884) over this world's repositories, on the
            # process-wide tiers every unwired service here verifies against.
            step_up_verifier=default_step_up_verifier(
                target_policy=StepUpTargetAuthorizer(
                    user_repo=self.users,
                    membership_repo=self.memberships,
                    tenant_repo=tenant_repo,
                    tenant_erasure_repo=self.tenant_records,
                    auth_provider_repo=MagicMock(),
                    oidc_config_repo=MagicMock(),
                )
            ),
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

    def issue_code(self, action: str, *, ip: str = "198.51.100.7") -> str:
        """Ask for a step-up code for *action* through the real route; return the one the mail carried.

        An act on another account or on the tenant names it as the target (#1884).
        """
        body: dict[str, Any] = {"action": action}
        target = {"admin_account_erasure": self.target_key, "tenant_deletion": TENANT_KEY}.get(action)
        if target is not None:
            body["target"] = target
        resp = self.call("POST", "/api/v1/users/me/step-up-code", body, ip=ip)
        assert resp.status_code == 202, resp.text
        return self.mail.send_step_up_code_email.call_args.kwargs["code"]

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
def test_a_federated_account_no_longer_erases_on_the_echo_alone(route) -> None:
    """#1815 — the echo is typed by whoever holds the session; it proves nobody present."""
    world = _World(password_hash=None)
    method, path = route

    resp = world.call(method, path, {"confirm_email": world.caller_email})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert not world.erasures.stored
    assert world.users.rows[world.caller_key].is_active
    assert world.immediate_runs.await_count == 0


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_a_federated_account_erases_with_the_mailed_code(route) -> None:
    world = _World(password_hash=None)
    method, path = route
    code = world.issue_code("account_erasure")

    resp = world.call(method, path, {"confirm_email": world.caller_email, "step_up_code": code})

    assert resp.status_code in (200, 201), resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.step_up == "email_code"


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_a_federated_account_with_a_wrong_code_erases_nothing(route) -> None:
    world = _World(password_hash=None)
    method, path = route
    code = world.issue_code("account_erasure")
    wrong = f"{(int(code) + 1) % 10**8:08d}"

    resp = world.call(method, path, {"confirm_email": world.caller_email, "step_up_code": wrong})

    assert resp.status_code == 401, resp.text
    assert not world.erasures.stored


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


def test_a_platform_admin_erases_with_the_step_up_and_the_record_says_how(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings

    log_salt = "log-pseudonym-test-salt-not-a-secret-01234"
    monkeypatch.setattr(settings, "log_pseudonym_salt", log_salt)  # #1812: the reference is a LOG pseudonym
    world = _World(platform_admin=True)

    resp = world.call("DELETE", _admin_route(world), world.admin_step_up())

    assert resp.status_code == 204, resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.user_key == world.target_key
    assert erasure.origin == "platform_admin"
    assert erasure.step_up == "password"
    # The requester by salted reference, never by key — the record outlives both accounts.
    assert erasure.requested_by_subject == ErasureEngine.log_subject(world.caller_key, log_salt)
    assert world.caller_key not in (erasure.requested_by_subject or "")
    assert world.immediate_runs.await_count == 1


def test_a_federated_platform_admin_no_longer_erases_on_the_echo_alone() -> None:
    world = _World(platform_admin=True, password_hash=None)

    resp = world.call("DELETE", _admin_route(world), {"confirm_email": world.target_email})

    assert resp.status_code == 401, resp.text
    assert resp.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert world.account_untouched(world.target_key)


def test_a_federated_platform_admin_erases_with_the_mailed_code() -> None:
    world = _World(platform_admin=True, password_hash=None)
    code = world.issue_code("admin_account_erasure")

    resp = world.call("DELETE", _admin_route(world), {"confirm_email": world.target_email, "step_up_code": code})

    assert resp.status_code == 204, resp.text
    (erasure,) = world.erasures.stored.values()
    assert erasure.step_up == "email_code"


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


# ── security review SEC-003: light mode has one shared system account ────────


@pytest.mark.parametrize("route", SELF_ROUTES)
def test_light_mode_never_opens_an_erasure_of_its_system_account(route) -> None:
    """In light mode every caller *is* the system user; its e-mail is public in the seed.

    ``DELETE /users/me`` is mounted in light mode too, and the echo alone confirms
    an account without a password — so anyone reaching the instance could schedule
    the erasure of the installation's only account. Refused like the light-mode
    tenant deletion (#1769 review SEC-002).
    """
    world = _World(password_hash=None)
    world.privacy._light_mode = True  # type: ignore[attr-defined]
    method, path = route

    resp = world.call(method, path, {"confirm_email": world.caller_email})

    assert resp.status_code == 403, resp.text
    assert not world.erasures.stored
    assert world.users.rows[world.caller_key].is_active


def test_light_mode_never_runs_an_admin_account_erasure() -> None:
    world = _World(platform_admin=True)
    world.privacy._light_mode = True  # type: ignore[attr-defined]

    resp = world.call("DELETE", _admin_route(world), world.admin_step_up())

    assert resp.status_code == 403, resp.text
    assert world.account_untouched(world.target_key)


# ── #1815: the e-mailed step-up code ─────────────────────────────────────────


def test_a_federated_account_gets_a_code_by_mail() -> None:
    world = _World(password_hash=None)

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 202, resp.text
    assert resp.json()["expires_in"] == 600
    assert "expires_at" in resp.json()
    kwargs = world.mail.send_step_up_code_email.call_args.kwargs
    assert kwargs["to_email"] == world.caller_email
    assert len(kwargs["code"]) == 8 and kwargs["code"].isdigit()
    assert kwargs["code"] not in resp.text


def test_an_api_key_gets_no_code() -> None:
    world = _World(password_hash=None)

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"}, bearer="kp_" + "x" * 24)

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_a_service_account_gets_no_code() -> None:
    world = _World(password_hash=None, account_type="service")

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_an_account_with_a_password_gets_no_code() -> None:
    world = _World()

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 422, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


def test_a_locked_step_up_gets_no_code() -> None:
    world = _World(password_hash=None)
    code = world.issue_code("account_erasure")
    wrong = f"{(int(code) + 1) % 10**8:08d}"
    for _ in range(5):
        resp = world.call(
            "POST", "/api/v1/privacy/erasure", {"confirm_email": world.caller_email, "step_up_code": wrong}
        )
        assert resp.status_code == 401, resp.text
    world.mail.reset_mock()

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    world.mail.send_step_up_code_email.assert_not_called()


def test_the_step_up_code_route_is_rate_limited_with_the_auth_budget() -> None:
    from app.api.v1.users import router as users_module
    from app.config.settings import settings

    route = f"{users_module.__name__}.send_step_up_code"
    limits = [str(limit.limit) for limit in limiter._route_limits.get(route, [])]

    assert limits, f"{route} carries no rate limit"
    assert limits == [str(__import__("limits").parse(settings.rate_limit_auth))]


def test_a_code_is_spent_by_one_act() -> None:
    world = _World(password_hash=None)
    code = world.issue_code("account_erasure")
    first = world.call("POST", "/api/v1/privacy/erasure", {"confirm_email": world.caller_email, "step_up_code": code})
    assert first.status_code == 201, first.text

    again = world.call("DELETE", f"/api/v1/tenants/{SLUG}", {"confirm_slug": SLUG, "step_up_code": code})

    assert again.status_code == 401, again.text
    assert world.tenant_untouched()


def test_a_federated_tenant_deletion_needs_the_code() -> None:
    world = _World(password_hash=None)

    refused = world.call("DELETE", f"/api/v1/tenants/{SLUG}", {"confirm_slug": SLUG})

    assert refused.status_code == 401, refused.text
    assert refused.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert world.tenant_untouched()

    code = world.issue_code("tenant_deletion")
    resp = world.call("DELETE", f"/api/v1/tenants/{SLUG}", {"confirm_slug": SLUG, "step_up_code": code})

    assert resp.status_code == 200, resp.text
    (record,) = world.tenant_records.records.values()
    assert record["step_up"] == "email_code"


def test_a_federated_admin_tenant_deletion_needs_the_code() -> None:
    world = _World(password_hash=None, platform_admin=True)
    route = f"/api/v1/admin/platform/tenants/{TENANT_KEY}"

    refused = world.call("DELETE", route, {"confirm_slug": SLUG})

    assert refused.status_code == 401, refused.text
    assert refused.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert world.tenant_untouched()

    code = world.issue_code("tenant_deletion")
    resp = world.call("DELETE", route, {"confirm_slug": SLUG, "step_up_code": code})

    assert resp.status_code == 204, resp.text


def test_a_federated_account_sets_its_first_password_only_with_the_code() -> None:
    """#1815 — setting a first password on a federated account passed on nothing at all."""
    world = _World(password_hash=None)
    new_password = "An0ther-long-" + "passphrase!"

    refused = world.call("POST", "/api/v1/users/me/password", {"new_password": new_password})

    assert refused.status_code == 401, refused.text
    assert refused.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert world.users.rows[world.caller_key].password_hash is None
    assert not world.users.writes

    code = world.issue_code("password_change")
    resp = world.call("POST", "/api/v1/users/me/password", {"new_password": new_password, "step_up_code": code})

    assert resp.status_code == 200, resp.text
    assert world.users.rows[world.caller_key].password_hash


STEP_UP_OPERATIONS = [
    ("post", "/api/v1/users/me/step-up-code"),
    ("post", "/api/v1/users/me/password"),
    ("delete", "/api/v1/users/me"),
    ("post", "/api/v1/privacy/erasure"),
    ("post", "/api/v1/privacy/email-change"),
    ("delete", "/api/v1/tenants/{tenant_slug}"),
    ("delete", "/api/v1/admin/platform/tenants/{key}"),
    ("delete", "/api/v1/admin/platform/users/{key}"),
]


@pytest.mark.parametrize(("method", "path"), STEP_UP_OPERATIONS)
def test_every_step_up_route_documents_its_refusals(method: str, path: str) -> None:
    """A client generated from the schema must learn about 401 STEP_UP_CODE_REQUIRED, 403 and 429."""
    schema = _World().client().app.openapi()

    responses = schema["paths"][path][method]["responses"]

    assert {"401", "403", "429"} <= responses.keys(), sorted(responses)
    assert "STEP_UP_CODE_REQUIRED" in responses["401"]["description"]


def test_light_mode_issues_no_step_up_code() -> None:
    """Light mode: every caller is the system account, whose address is public in the seed (review SEC-003)."""
    world = _World(password_hash=None)
    world.auth._light_mode = True  # type: ignore[attr-defined]

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


# ── review SEC-003: a code confirms the act it was requested for, and no other ──


def test_a_code_requested_for_the_password_change_erases_nothing() -> None:
    """A code the owner asked for to set a password must not confirm the erasure of the account."""
    world = _World(password_hash=None)
    code = world.issue_code("password_change")

    resp = world.call("POST", "/api/v1/privacy/erasure", {"confirm_email": world.caller_email, "step_up_code": code})

    assert resp.status_code == 401, resp.text
    assert not world.erasures.stored
    assert world.users.rows[world.caller_key].is_active


def test_the_code_mail_names_the_act() -> None:
    world = _World(password_hash=None)

    world.issue_code("tenant_deletion")

    purpose = world.mail.send_step_up_code_email.call_args.kwargs["purpose"]
    assert "garden" in purpose.lower() or "tenant" in purpose.lower()


def test_a_code_request_without_an_act_is_refused() -> None:
    world = _World(password_hash=None)

    for body in (None, {}, {"action": "login"}):
        resp = world.call("POST", "/api/v1/users/me/step-up-code", body)
        assert resp.status_code == 422, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


# ── review SEC-002: code issuance is bounded per account ─────────────────────


def test_a_second_code_within_a_minute_is_refused_and_the_first_stays_valid() -> None:
    world = _World(password_hash=None)
    code = world.issue_code("account_erasure")
    world.mail.reset_mock()

    again = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"}, ip="203.0.113.99")

    assert again.status_code == 429, again.text
    assert again.json()["error_code"] == "STEP_UP_LOCKED"
    world.mail.send_step_up_code_email.assert_not_called()
    resp = world.call("POST", "/api/v1/privacy/erasure", {"confirm_email": world.caller_email, "step_up_code": code})
    assert resp.status_code == 201, resp.text


# ── /code-review of #1862: an undeliverable code is a 503, not a 202 ────────────


@pytest.mark.parametrize(
    "failure",
    [
        pytest.param(lambda: __import__("smtplib").SMTPServerDisconnected("gone"), id="smtp"),
        pytest.param(lambda: NotImplementedError("adapter"), id="not implemented"),
        pytest.param(
            lambda: __import__(
                "app.domain.interfaces.email_service", fromlist=["EmailUndeliverableError"]
            ).EmailUndeliverableError("console"),
            id="console adapter without debug",
        ),
    ],
)
def test_an_undeliverable_code_answers_503_and_gives_the_issuance_back(failure) -> None:
    world = _World(password_hash=None)
    world.mail.send_step_up_code_email.side_effect = failure()

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})

    assert resp.status_code == 503, resp.text
    assert resp.json()["error_code"] == "STEP_UP_CODE_UNDELIVERABLE"
    # Given back: the next request is not held by the one-minute wait.
    world.mail.send_step_up_code_email.side_effect = None
    assert world.issue_code("account_erasure")


def test_an_undelivered_code_confirms_nothing() -> None:
    world = _World(password_hash=None)
    world.mail.send_step_up_code_email.side_effect = __import__("smtplib").SMTPServerDisconnected("gone")

    world.call("POST", "/api/v1/users/me/step-up-code", {"action": "account_erasure"})
    undelivered = world.mail.send_step_up_code_email.call_args.kwargs["code"]
    resp = world.call(
        "POST", "/api/v1/privacy/erasure", {"confirm_email": world.caller_email, "step_up_code": undelivered}
    )

    assert resp.status_code == 401, resp.text
    assert not world.erasures.stored


def test_the_step_up_code_route_documents_the_undeliverable_503() -> None:
    schema = _World().client().app.openapi()

    responses = schema["paths"]["/api/v1/users/me/step-up-code"]["post"]["responses"]

    assert "503" in responses and "STEP_UP_CODE_UNDELIVERABLE" in responses["503"]["description"]


# ── #1884: a mailed code confirms the target it was requested for, only ────────


def _third_account(world: _World) -> str:
    key = f"third-{uuid.uuid4().hex[:12]}"
    world.users.rows[key] = User.model_validate(
        {"_key": key, "email": f"{key}@example.org", "display_name": "Third", "email_verified": False}
    )
    return key


def test_a_code_to_verify_one_account_does_not_verify_another() -> None:
    """The acceptance of #1884 through the real routes: issued for A, refused for B, not spent by the refusal."""
    world = _World(platform_admin=True, password_hash=None)
    other = _third_account(world)
    resp = world.call(
        "POST", "/api/v1/users/me/step-up-code", {"action": "admin_account_update", "target": world.target_key}
    )
    assert resp.status_code == 202, resp.text
    code = world.mail.send_step_up_code_email.call_args.kwargs["code"]

    refused = world.call(
        "PATCH", f"/api/v1/admin/platform/users/{other}", {"email_verified": True, "step_up_code": code}
    )
    assert refused.status_code == 401, refused.text
    assert world.users.rows[other].email_verified is False

    meant = world.call(
        "PATCH", f"/api/v1/admin/platform/users/{world.target_key}", {"email_verified": True, "step_up_code": code}
    )
    assert meant.status_code == 200, meant.text
    assert world.users.rows[world.target_key].email_verified is True


def test_a_code_to_erase_one_account_does_not_erase_another() -> None:
    world = _World(platform_admin=True, password_hash=None)
    other = _third_account(world)
    code = world.issue_code("admin_account_erasure")  # bound to world.target_key

    resp = world.call(
        "DELETE",
        f"/api/v1/admin/platform/users/{other}",
        {"confirm_email": f"{other}@example.org", "step_up_code": code},
    )

    assert resp.status_code == 401, resp.text
    assert not world.erasures.stored
    assert world.immediate_runs.await_count == 0
    assert world.users.rows[other].is_active


@pytest.mark.parametrize(
    ("body", "status"),
    [
        pytest.param({"action": "admin_account_update"}, 422, id="targeted act without target"),
        pytest.param({"action": "account_erasure", "target": "someone"}, 422, id="own-account act with target"),
        pytest.param({"action": "admin_account_update", "target": "no-such-user"}, 404, id="unknown target"),
        pytest.param({"action": "admin_account_erasure", "target": "SELF"}, 403, id="own account via admin act"),
        pytest.param({"action": "tenant_deletion", "target": "t-elsewhere"}, 404, id="unknown tenant"),
    ],
)
def test_no_code_is_mailed_for_a_target_the_act_would_refuse(body: dict[str, Any], status: int) -> None:
    """Operator decision D2: the target is checked when the code is issued, not only when it is used."""
    world = _World(platform_admin=True, password_hash=None)
    if body.get("target") == "SELF":
        body = {**body, "target": world.caller_key}

    resp = world.call("POST", "/api/v1/users/me/step-up-code", body)

    assert resp.status_code == status, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


@pytest.mark.parametrize(
    ("action", "target"),
    [
        pytest.param("admin_account_update", "TARGET", id="admin act on an existing account"),
        pytest.param("admin_account_update", "no-such-user", id="admin act on a missing account"),
        pytest.param("tenant_deletion", "t-elsewhere", id="a tenant the caller holds no role in"),
    ],
)
def test_who_may_not_act_gets_no_code_and_learns_nothing_about_existence(action: str, target: str) -> None:
    """403 for an existing and a missing target alike — the refusal is no existence oracle."""
    world = _World(platform_admin=False, password_hash=None)
    target = world.target_key if target == "TARGET" else target

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": action, "target": target})

    assert resp.status_code == 403, resp.text
    world.mail.send_step_up_code_email.assert_not_called()
