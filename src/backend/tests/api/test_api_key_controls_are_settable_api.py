"""#2137 (MT-041) — an API key's network controls are set where the key is minted, through real HTTP.

``ip_allowlist``, ``rate_limit_per_minute`` and ``expires_at`` were enforced on
both key surfaces (``enforce_api_key_controls``, #1850; the expiry check in
``authenticate_api_key`` and the MCP authenticator) but no route wrote them:
``POST /auth/api-keys`` took a label and a tenant scope and nothing else, so every
key ever minted was unrestricted and immortal.

Now the create request carries the three controls, checked **before** the
step-up asks for a password (a request that cannot succeed is not asked for one):

* ``ip_allowlist`` — CIDR ranges (a bare address is its own ``/32`` / ``/128``),
  at most :data:`~app.domain.models.auth.API_KEY_IP_ALLOWLIST_MAX_ENTRIES`, no
  host bits set, never wider than ``/8`` (IPv4) or ``/32`` (IPv6) — so
  ``0.0.0.0/0`` cannot be written as an "allowlist";
* ``rate_limit_per_minute`` — 1..10000, the bounds of the stored model;
* ``expires_at`` — timezone-aware, in the future, at most
  :data:`~app.domain.models.auth.API_KEY_MAX_LIFETIME_DAYS` ahead.

The second half drives the minted key through the production chain
(``get_current_user`` → ``FullAuthProvider`` → ``authenticate_api_key``): a key
created with an allowlist is refused from an address outside it — the control
reaches the request because the route wrote it, not because a fixture did.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth.router import api_keys_router
from app.common.auth import get_current_user, require_account_principal
from app.common.dependencies import get_auth_provider, get_auth_service
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import API_KEY_IP_ALLOWLIST_MAX_ENTRIES, API_KEY_MAX_LIFETIME_DAYS, ApiKey
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

# Assembled at runtime: a credential-shaped literal is a secret-scanner hit (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
WRONG_PASSWORD = PASSWORD[::-1]
SECRET = "test-secret-key-for-unit-tests-32chars!"
API_KEYS = "/api/v1/auth/api-keys"


class _Users:
    def __init__(self, user: User) -> None:
        self.rows = {user.key: user}

    def get_or_raise(self, key: str) -> User:
        return self.rows[key]

    def get_by_key(self, key: str) -> User | None:
        return self.rows.get(key)


class _ApiKeys:
    def __init__(self) -> None:
        self.rows: list[ApiKey] = []

    def create(self, api_key: ApiKey) -> ApiKey:
        stored = api_key.model_copy(update={"key": f"ak-{len(self.rows) + 1}", "created_at": datetime.now(UTC)})
        self.rows.append(stored)
        return stored

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return next((k for k in self.rows if k.key_hash == key_hash and not k.revoked), None)

    def update_last_used(self, key: str) -> None:
        return None

    def list_by_user(self, user_key: str) -> list[ApiKey]:
        return [k for k in self.rows if k.user_key == user_key]


class _World:
    def __init__(self) -> None:
        self.key = f"owner-{uuid.uuid4().hex[:12]}"
        owner = User.model_validate(
            {
                "_key": self.key,
                "email": f"{self.key}@example.org",
                "display_name": "Owner",
                "password_hash": PASSWORD_HASH,
            }
        )
        self.users = _Users(owner)
        self.api_keys = _ApiKeys()
        self.auth = AuthService(
            user_repo=self.users,  # type: ignore[arg-type]
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine(SECRET, "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="https://app.test",
            api_key_repo=self.api_keys,  # type: ignore[arg-type]
        )

    def _app(self, *, session: bool) -> FastAPI:
        app = FastAPI()
        app.include_router(api_keys_router, prefix="/api/v1")
        probe = APIRouter()

        @probe.get("/me-probe")
        def me_probe(user: User = Depends(get_current_user)) -> dict[str, str]:
            return {"user": user.key or ""}

        app.include_router(probe, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        if session:
            # The minting request is a signed-in person (the step-up needs one).
            app.dependency_overrides[get_current_user] = lambda: self.users.rows[self.key]
            app.dependency_overrides[require_account_principal] = lambda: self.users.rows[self.key]
        else:
            app.dependency_overrides[get_auth_provider] = lambda: FullAuthProvider(
                TokenEngine(SECRET, "HS256"),
                self.users,  # type: ignore[arg-type]
                self.auth,
            )
        return app

    def create(self, body: dict[str, Any], *, password: str = PASSWORD) -> Any:
        client = TestClient(self._app(session=True), raise_server_exceptions=False)
        return client.post(
            API_KEYS,
            json={"label": "home-assistant", "current_password": password, **body},
            headers={"X-Forwarded-For": "198.51.100.7"},
        )

    def call_with(self, raw_key: str, ip: str) -> int:
        client = TestClient(self._app(session=False), raise_server_exceptions=False)
        response = client.get("/api/v1/me-probe", headers={"Authorization": f"Bearer {raw_key}", "X-Forwarded-For": ip})
        return response.status_code


def _in(days: float) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


# ── the controls are written ────────────────────────────────────────────────


def test_the_three_controls_are_stored_and_echoed() -> None:
    world = _World()
    expires = _in(30)

    response = world.create(
        {
            "ip_allowlist": ["10.0.0.0/8", "2001:db8::/48", "192.0.2.10"],
            "rate_limit_per_minute": 120,
            "expires_at": expires,
        }
    )

    assert response.status_code == 201, response.text
    (stored,) = world.api_keys.rows
    assert stored.ip_allowlist == ["10.0.0.0/8", "2001:db8::/48", "192.0.2.10/32"]
    assert stored.rate_limit_per_minute == 120
    assert stored.expires_at == datetime.fromisoformat(expires)
    body = response.json()
    assert body["ip_allowlist"] == ["10.0.0.0/8", "2001:db8::/48", "192.0.2.10/32"]
    assert body["rate_limit_per_minute"] == 120
    assert datetime.fromisoformat(body["expires_at"]) == datetime.fromisoformat(expires)


def test_a_key_without_controls_stays_unrestricted() -> None:
    world = _World()

    response = world.create({})

    assert response.status_code == 201, response.text
    (stored,) = world.api_keys.rows
    assert (stored.ip_allowlist, stored.rate_limit_per_minute, stored.expires_at) == (None, None, None)


def test_an_empty_allowlist_is_stored_as_no_allowlist() -> None:
    """``[]`` and ``None`` both admit everything on the enforcing side; one stored spelling, not two."""
    world = _World()

    response = world.create({"ip_allowlist": []})

    assert response.status_code == 201, response.text
    assert world.api_keys.rows[0].ip_allowlist is None


def test_the_list_shows_the_controls() -> None:
    world = _World()
    world.create({"ip_allowlist": ["10.0.0.0/8"], "rate_limit_per_minute": 5})

    client = TestClient(world._app(session=True))
    (listed,) = client.get(API_KEYS).json()

    assert listed["ip_allowlist"] == ["10.0.0.0/8"]
    assert listed["rate_limit_per_minute"] == 5
    assert listed["expires_at"] is None


# ── the controls are validated before the password is asked for ─────────────


@pytest.mark.parametrize(
    "body",
    [
        {"ip_allowlist": ["not-a-network"]},
        {"ip_allowlist": ["10.0.0.5/8"]},  # host bits set: the caller meant something else
        {"ip_allowlist": ["0.0.0.0/0"]},
        {"ip_allowlist": ["10.0.0.0/7"]},
        {"ip_allowlist": ["::/0"]},
        {"ip_allowlist": ["2001:db8::/31"]},
        {"ip_allowlist": [f"10.0.{i}.0/24" for i in range(API_KEY_IP_ALLOWLIST_MAX_ENTRIES + 1)]},
        {"rate_limit_per_minute": 0},
        {"rate_limit_per_minute": 10001},
        {"expires_at": _in(-1)},
        {"expires_at": _in(API_KEY_MAX_LIFETIME_DAYS + 1)},
        {"expires_at": "2099-01-01T00:00:00"},  # no timezone: which midnight?
    ],
    ids=[
        "unparsable",
        "host-bits",
        "ipv4-everything",
        "ipv4-wider-than-8",
        "ipv6-everything",
        "ipv6-wider-than-32",
        "too-many-entries",
        "rate-zero",
        "rate-above-model-bound",
        "expiry-in-the-past",
        "expiry-beyond-horizon",
        "expiry-naive",
    ],
)
def test_an_invalid_control_is_refused_with_422_before_the_step_up(body: dict[str, Any]) -> None:
    """A wrong password next to it: 422 proves the control was decided first and nothing was minted."""
    world = _World()

    response = world.create(body, password=WRONG_PASSWORD)

    assert response.status_code == 422, response.text
    assert world.api_keys.rows == []


def test_a_valid_control_still_needs_the_password() -> None:
    """The control of the 422s above: valid controls with a wrong password are the step-up's 401."""
    world = _World()

    response = world.create({"ip_allowlist": ["10.0.0.0/8"]}, password=WRONG_PASSWORD)

    assert response.status_code == 401, response.text
    assert world.api_keys.rows == []


# ── the written control binds on the production chain ───────────────────────


def test_a_key_minted_with_an_allowlist_is_refused_from_a_foreign_address() -> None:
    world = _World()
    raw_key = world.create({"ip_allowlist": ["10.0.0.0/8"]}).json()["raw_key"]

    assert world.call_with(raw_key, "203.0.113.7") == 401
    assert world.call_with(raw_key, "10.20.30.40") == 200


def test_a_key_minted_with_an_expiry_stops_working_after_it() -> None:
    world = _World()
    raw_key = world.create({"expires_at": _in(1)}).json()["raw_key"]
    assert world.call_with(raw_key, "203.0.113.7") == 200

    # The expiry passes: the stored value is moved back instead of waiting a day.
    world.api_keys.rows[0] = world.api_keys.rows[0].model_copy(
        update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)}
    )

    assert world.call_with(raw_key, "203.0.113.7") == 401
