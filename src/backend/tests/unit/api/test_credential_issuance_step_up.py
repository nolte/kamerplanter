"""#1847 / #1857 — minting or removing a sign-in credential passes the one step-up.

Three routes created or removed a credential of the caller's own account on a
bare session — ``POST /auth/api-keys`` (also from a request that was itself
authenticated with a ``kp_`` key), ``POST /auth/device-pairing`` (a code that
redeems into a full session) and ``DELETE /users/me/providers/{key}`` — and
``PATCH /admin/platform/users/{key}`` set ``email_verified``, the trust anchor of
the OAuth auto-link, with nothing but the admin session. A stolen session could
leave a key behind that outlives the owner's password change.

The rule now (REQ-023 §3.9): each of them passes :class:`StepUpVerifier` —

* a signed-in session of a person; an API key or a service account is 403;
* the requester's current password (401 missing or wrong), for an account without
  one the mailed code (401 ``STEP_UP_CODE_REQUIRED``);
* in the one budget of every step-up (429 ``STEP_UP_LOCKED``);
* checked before anything is minted, removed or written.

The admin update is gated only when it raises trust — ``email_verified`` or
``is_active`` turning true. A display-name edit, a deactivation and a re-send of
the current values stay one click. In light mode the API key needs no step-up:
there is no person to confirm, every request already is the system account.

The requests run the real routers and services over in-memory doubles; every
test uses fresh account keys, so the process-wide throttle and code tiers carry
no state between tests.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.admin.platform.router import router as platform_admin_router
from app.api.v1.auth.router import api_keys_router, limiter
from app.api.v1.auth.router import router as auth_router
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user, require_platform_admin
from app.common.dependencies import get_auth_service, get_tenant_service, get_user_service
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey, AuthProvider, AuthProviderType
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.user_service import UserService

# Probe credentials are assembled at runtime: a literal shaped like one trips the
# secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
WRONG_PASSWORD = PASSWORD[::-1]
API_KEY = "kp_" + "x" * 24
SECRET = "test-secret-key-for-unit-tests-32chars!"

API_KEYS = "/api/v1/auth/api-keys"
PAIRING = "/api/v1/auth/device-pairing"


@pytest.fixture(autouse=True)
def _limiter_off(monkeypatch: pytest.MonkeyPatch):
    """Per-address rate limits are asserted elsewhere; here the step-up is under test."""
    limiter.reset()
    monkeypatch.setattr(limiter, "enabled", False)
    yield
    limiter.reset()


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


class _Users:
    def __init__(self, *users: User) -> None:
        self.rows = {u.key: u for u in users}
        self.writes: list[tuple[str, dict[str, Any]]] = []

    def get_or_raise(self, key: str) -> User:
        if key not in self.rows:
            raise NotFoundError("User", key)
        return self.rows[key]

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)

    def update_fields(self, key: str, fields: dict[str, Any]) -> User:
        self.writes.append((key, dict(fields)))
        self.rows[key] = User.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})
        return self.rows[key]


class _ApiKeys:
    def __init__(self) -> None:
        self.rows: list[ApiKey] = []

    def create(self, api_key: ApiKey) -> ApiKey:
        stored = api_key.model_copy(update={"key": f"ak-{len(self.rows) + 1}", "created_at": datetime.now(UTC)})
        self.rows.append(stored)
        return stored


class _PairingCodes:
    def __init__(self) -> None:
        self.issued: list[str] = []

    def issue(self, code: str, user_key: str) -> datetime:
        self.issued.append(user_key)
        return datetime.now(UTC) + timedelta(seconds=90)


class _Providers:
    def __init__(self, user_key: str) -> None:
        self.rows = [
            AuthProvider(
                key=f"{kind.value}-{user_key}",
                user_key=user_key,
                provider=kind,
                provider_user_id=f"{kind.value}-id",
                linked_at=datetime.now(UTC),
            )
            for kind in (AuthProviderType.LOCAL, AuthProviderType.GOOGLE)
        ]
        self.deleted: list[str] = []

    def list_by_user(self, user_key: str) -> list[AuthProvider]:
        return [p for p in self.rows if p.user_key == user_key]

    def delete(self, key: str) -> bool:
        self.deleted.append(key)
        return True


class _World:
    def __init__(
        self,
        *,
        password_hash: str | None = PASSWORD_HASH,
        account_type: str = "human",
        light_mode: bool = False,
        target_verified: bool = False,
        target_active: bool = True,
    ) -> None:
        self.key = f"owner-{uuid.uuid4().hex[:12]}"
        self.target_key = f"target-{self.key}"
        owner = User.model_validate(
            {
                "_key": self.key,
                "email": f"{self.key}@example.org",
                "display_name": "Owner",
                "password_hash": password_hash,
                "account_type": account_type,
            }
        )
        target = User.model_validate(
            {
                "_key": self.target_key,
                "email": f"{self.target_key}@example.org",
                "display_name": "Target",
                "email_verified": target_verified,
                "is_active": target_active,
            }
        )
        self.users = _Users(owner, target)
        self.api_keys = _ApiKeys()
        self.pairing = _PairingCodes()
        self.providers = _Providers(self.key)
        self.mail = MagicMock()
        self.auth = AuthService(
            user_repo=self.users,
            auth_provider_repo=self.providers,
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine(SECRET, "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url="https://app.test",
            api_key_repo=self.api_keys,
            device_pairing_code_store=self.pairing,
            light_mode=light_mode,
        )
        self.user_service = UserService(user_repo=self.users, refresh_token_repo=MagicMock())
        self.tenants = MagicMock()
        self.tenants.list_user_memberships.return_value = []

    def client(self) -> TestClient:
        app = FastAPI()
        for router in (auth_router, api_keys_router, users_router, platform_admin_router):
            app.include_router(router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.users.rows[self.key]
        app.dependency_overrides[require_platform_admin] = lambda: self.users.rows[self.key]
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        app.dependency_overrides[get_user_service] = lambda: self.user_service
        app.dependency_overrides[get_tenant_service] = lambda: self.tenants
        return TestClient(app, raise_server_exceptions=False)

    def send(self, method: str, path: str, body: dict[str, Any] | None = None, *, bearer: str | None = None):  # noqa: ANN201
        headers = {"X-Forwarded-For": "198.51.100.7"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        return self.client().request(method, path, json=body, headers=headers)

    def create_key(self, **step_up: Any):  # noqa: ANN201
        return self.send("POST", API_KEYS, {"label": "home-assistant", **step_up})

    def pair(self, **step_up: Any):  # noqa: ANN201
        return self.send("POST", PAIRING, step_up or None)

    def unlink(self, **step_up: Any):  # noqa: ANN201
        return self.send("DELETE", f"/api/v1/users/me/providers/google-{self.key}", step_up or None)

    def admin_update(self, fields: dict[str, Any], **step_up: Any):  # noqa: ANN201
        return self.send("PATCH", f"/api/v1/admin/platform/users/{self.target_key}", {**fields, **step_up})

    def issue_code(self, action: str) -> str:
        resp = self.send("POST", "/api/v1/users/me/step-up-code", {"action": action})
        assert resp.status_code == 202, resp.text
        return self.mail.send_step_up_code_email.call_args.kwargs["code"]

    def target(self) -> User:
        return self.users.rows[self.target_key]


# ── API keys ────────────────────────────────────────────────────────────────


def test_an_api_key_cannot_mint_an_api_key_even_with_the_password() -> None:
    world = _World()

    resp = world.send("POST", API_KEYS, {"label": "k", "current_password": PASSWORD}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert world.api_keys.rows == []


@pytest.mark.parametrize("password", [None, WRONG_PASSWORD])
def test_an_api_key_is_not_minted_without_the_current_password(password: str | None) -> None:
    world = _World()

    resp = world.create_key(current_password=password)

    assert resp.status_code == 401, resp.text
    assert world.api_keys.rows == []


def test_an_api_key_is_minted_with_the_current_password() -> None:
    world = _World()

    resp = world.create_key(current_password=PASSWORD)

    assert resp.status_code == 201, resp.text
    assert len(world.api_keys.rows) == 1


def test_a_federated_account_mints_an_api_key_with_the_mailed_code() -> None:
    world = _World(password_hash=None)

    refused = world.create_key()
    code = world.issue_code("api_key_creation")
    resp = world.create_key(step_up_code=code)

    assert refused.status_code == 401, refused.text
    assert refused.json()["error_code"] == "STEP_UP_CODE_REQUIRED"
    assert resp.status_code == 201, resp.text
    assert len(world.api_keys.rows) == 1


def test_a_code_for_another_act_does_not_mint_an_api_key() -> None:
    world = _World(password_hash=None)

    code = world.issue_code("device_pairing")
    resp = world.create_key(step_up_code=code)

    assert resp.status_code == 401, resp.text
    assert world.api_keys.rows == []


def test_api_key_creation_shares_the_step_up_lock() -> None:
    world = _World()

    for _ in range(MAX_ATTEMPTS):
        world.create_key(current_password=WRONG_PASSWORD)
    resp = world.create_key(current_password=PASSWORD)

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert world.api_keys.rows == []


def test_light_mode_mints_an_api_key_without_a_step_up() -> None:
    """The MCP key of a light-mode instance: there is no person, and no code could reach one."""
    world = _World(password_hash=None, light_mode=True)

    resp = world.create_key()

    assert resp.status_code == 201, resp.text
    assert len(world.api_keys.rows) == 1


# ── device pairing ──────────────────────────────────────────────────────────


def test_an_api_key_cannot_mint_a_pairing_code() -> None:
    world = _World()

    resp = world.send("POST", PAIRING, {"current_password": PASSWORD}, bearer=API_KEY)

    assert resp.status_code == 403, resp.text
    assert world.pairing.issued == []


@pytest.mark.parametrize("password", [None, WRONG_PASSWORD])
def test_a_pairing_code_is_not_minted_without_the_current_password(password: str | None) -> None:
    world = _World()

    resp = world.pair(current_password=password) if password else world.pair()

    assert resp.status_code == 401, resp.text
    assert world.pairing.issued == []


def test_a_pairing_code_is_minted_with_the_current_password() -> None:
    world = _World()

    resp = world.pair(current_password=PASSWORD)

    assert resp.status_code == 201, resp.text
    assert world.pairing.issued == [world.key]


# ── provider unlink ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("password", [None, WRONG_PASSWORD])
def test_a_provider_is_not_unlinked_without_the_current_password(password: str | None) -> None:
    world = _World()

    resp = world.unlink(current_password=password) if password else world.unlink()

    assert resp.status_code == 401, resp.text
    assert world.providers.deleted == []


def test_an_api_key_cannot_unlink_a_provider() -> None:
    world = _World()

    resp = world.send(
        "DELETE", f"/api/v1/users/me/providers/google-{world.key}", {"current_password": PASSWORD}, bearer=API_KEY
    )

    assert resp.status_code == 403, resp.text
    assert world.providers.deleted == []


def test_a_provider_is_unlinked_with_the_current_password() -> None:
    world = _World()

    resp = world.unlink(current_password=PASSWORD)

    assert resp.status_code == 200, resp.text
    assert world.providers.deleted == [f"google-{world.key}"]


# ── platform admin update (#1857) ───────────────────────────────────────────


@pytest.mark.parametrize("password", [None, WRONG_PASSWORD])
def test_an_admin_cannot_verify_an_address_without_the_step_up(password: str | None) -> None:
    world = _World()

    resp = world.admin_update({"email_verified": True}, current_password=password)

    assert resp.status_code == 401, resp.text
    assert world.target().email_verified is False
    assert world.users.writes == []


def test_an_admin_cannot_reactivate_an_account_without_the_step_up() -> None:
    world = _World(target_active=False)

    resp = world.admin_update({"is_active": True})

    assert resp.status_code == 401, resp.text
    assert world.target().is_active is False


def test_an_admin_api_key_cannot_verify_an_address() -> None:
    world = _World()

    resp = world.send(
        "PATCH",
        f"/api/v1/admin/platform/users/{world.target_key}",
        {"email_verified": True, "current_password": PASSWORD},
        bearer=API_KEY,
    )

    assert resp.status_code == 403, resp.text
    assert world.target().email_verified is False


def test_an_admin_verifies_an_address_with_the_own_password() -> None:
    world = _World()

    resp = world.admin_update({"email_verified": True}, current_password=PASSWORD)

    assert resp.status_code == 200, resp.text
    assert world.target().email_verified is True


@pytest.mark.parametrize(
    "fields",
    [
        {"display_name": "Renamed"},
        {"is_active": False},
        {"email_verified": False},
        # The edit form re-sends the current values; nothing is raised.
        {"display_name": "Renamed", "is_active": True},
    ],
)
def test_an_admin_update_that_raises_no_trust_needs_no_step_up(fields: dict[str, Any]) -> None:
    world = _World()

    resp = world.admin_update(fields)

    assert resp.status_code == 200, resp.text
    assert world.users.writes
