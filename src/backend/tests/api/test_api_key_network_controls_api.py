"""An API key's ``ip_allowlist`` and rate limit bind on the REST API — #1850, through real HTTP.

Until #1850 only the MCP authenticator read the two controls; on REST a ``kp_``
bearer became its owner's account after the revoked/expiry/active checks. Nothing
here overrides ``get_current_user``: the principal comes out of the real
``get_current_user`` → ``FullAuthProvider`` → ``AuthService.authenticate_api_key``
chain from a raw key string, and the client address out of
``resolve_client_ip`` — so a test that passes proves the control is on the path
production takes, not on one this file declared.

The counter store is an in-memory INCR/EXPIRE/TTL double of the Redis subset the
limiter uses; a raising store stands for an outage.
"""

from __future__ import annotations

import hashlib

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.common.auth import get_current_user, get_current_user_optional
from app.common.dependencies import get_auth_provider
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey
from app.domain.models.user import User
from app.domain.services.api_key_controls import ApiKeyRateLimiter
from app.domain.services.auth_service import AuthService

_SECRET = "test-secret-key-for-unit-tests-32chars!"
# Assembled at runtime: a credential-shaped literal would be a secret-scanner hit.
_FENCED = "kp_" + "f" * 32
_LIMITED = "kp_" + "l" * 32
_FREE = "kp_" + "o" * 32


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class _ApiKeyRepo:
    def __init__(self) -> None:
        self._keys = {
            _hash(_FENCED): ApiKey(
                _key="ak-fenced",
                user_key="owner",
                label="lan-only",
                key_hash=_hash(_FENCED),
                key_prefix=_FENCED[:8],
                ip_allowlist=["10.0.0.0/8"],
            ),
            _hash(_LIMITED): ApiKey(
                _key="ak-limited",
                user_key="owner",
                label="two-a-minute",
                key_hash=_hash(_LIMITED),
                key_prefix=_LIMITED[:8],
                rate_limit_per_minute=2,
            ),
            _hash(_FREE): ApiKey(
                _key="ak-free",
                user_key="owner",
                label="unrestricted",
                key_hash=_hash(_FREE),
                key_prefix=_FREE[:8],
            ),
        }

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return self._keys.get(key_hash)

    def update_last_used(self, key: str) -> None:
        return None


class _UserRepo:
    def get_by_key(self, key: str) -> User | None:
        return User(_key="owner", email="owner@example.org", display_name="Owner") if key == "owner" else None


class _Redis:
    def __init__(self, *, fail: bool = False) -> None:
        self.counters: dict[str, int] = {}
        self._fail = fail

    def incr(self, key: str) -> int:
        if self._fail:
            raise ConnectionError("store down")
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key: str, seconds: int) -> None:
        return None

    def ttl(self, key: str) -> int:
        return 42


def _client(redis: _Redis | None = None) -> tuple[TestClient, _Redis]:
    redis = redis or _Redis()
    user_repo = _UserRepo()

    class _Noop:
        pass

    auth_service = AuthService(
        user_repo=user_repo,  # type: ignore[arg-type]
        auth_provider_repo=_Noop(),  # type: ignore[arg-type]
        refresh_token_repo=_Noop(),  # type: ignore[arg-type]
        password_engine=PasswordEngine(),
        token_engine=TokenEngine(_SECRET, "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=None,  # type: ignore[arg-type]
        frontend_url="http://localhost:5173",
        api_key_repo=_ApiKeyRepo(),  # type: ignore[arg-type]
        api_key_rate_limiter=ApiKeyRateLimiter(redis),
    )

    router = APIRouter()

    @router.get("/me-probe")
    def me_probe(user: User = Depends(get_current_user)) -> dict[str, str]:
        return {"user": user.key or ""}

    @router.get("/both-probe")
    def both_probe(
        user: User = Depends(get_current_user),
        maybe: User | None = Depends(get_current_user_optional),
    ) -> dict[str, str]:
        return {"user": user.key or "", "maybe": (maybe.key or "") if maybe else ""}

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_auth_provider] = lambda: FullAuthProvider(
        TokenEngine(_SECRET, "HS256"),
        user_repo,  # type: ignore[arg-type]
        auth_service,
    )
    return TestClient(app), redis


def _headers(raw: str, ip: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {raw}"}
    if ip is not None:
        headers["X-Forwarded-For"] = ip
    return headers


# ── ip_allowlist ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("ip", ["203.0.113.7", "not-an-ip"], ids=["outside", "unparsable"])
def test_a_key_is_refused_from_outside_its_allowlist(ip: str) -> None:
    client, _ = _client()

    response = client.get("/api/v1/me-probe", headers=_headers(_FENCED, ip))

    assert response.status_code == 401


def test_the_refusal_is_the_answer_the_mcp_path_gives() -> None:
    # One message on both surfaces (enforce_api_key_controls), so neither leaks
    # more than the other.
    from app.domain.services.api_key_controls import IP_NOT_PERMITTED

    client, _ = _client()

    response = client.get("/api/v1/me-probe", headers=_headers(_FENCED, "203.0.113.7"))

    assert response.json()["message"] == IP_NOT_PERMITTED


def test_the_same_key_is_admitted_from_inside_its_allowlist() -> None:
    client, _ = _client()

    response = client.get("/api/v1/me-probe", headers=_headers(_FENCED, "10.20.30.40"))

    assert response.status_code == 200, response.text
    assert response.json() == {"user": "owner"}


# ── rate_limit_per_minute ───────────────────────────────────────────────────


def test_a_key_is_refused_beyond_its_per_minute_budget() -> None:
    client, redis = _client()

    codes = [client.get("/api/v1/me-probe", headers=_headers(_LIMITED)).status_code for _ in range(3)]

    assert codes == [200, 200, 429]
    assert redis.counters == {"api_key_ratelimit:ak-limited": 3}


def test_one_request_is_counted_once_even_when_both_principal_dependencies_resolve() -> None:
    client, redis = _client()

    response = client.get("/api/v1/both-probe", headers=_headers(_LIMITED))

    assert response.status_code == 200, response.text
    assert response.json() == {"user": "owner", "maybe": "owner"}
    assert redis.counters == {"api_key_ratelimit:ak-limited": 1}


def test_the_limit_fails_closed_when_the_counter_store_is_down() -> None:
    client, _ = _client(_Redis(fail=True))

    assert client.get("/api/v1/me-probe", headers=_headers(_LIMITED)).status_code == 429


def test_a_key_without_controls_is_neither_fenced_nor_counted() -> None:
    client, redis = _client()

    codes = [client.get("/api/v1/me-probe", headers=_headers(_FREE, "203.0.113.7")).status_code for _ in range(3)]

    assert codes == [200, 200, 200]
    assert redis.counters == {}
