"""REQ-033 §5 — security tests for /auth/service-accounts/validate (SEC-003).

Proves the three hardening properties of the M2M validation endpoint:

* it is gated behind the MCP enable flag (404 when MCP is off);
* a *valid non-service* key yields the SAME generic 401 as an invalid key (no
  oracle that would confirm a valid non-service key exists);
* it is per-IP rate limited (429 once the auth limiter is exhausted).

The endpoint is exercised end-to-end against a minimal app mounting the real
auth router, with the authenticator wired to in-memory fakes.
"""

from __future__ import annotations

import hashlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import limiter
from app.api.v1.auth.router import router as auth_router
from app.common.dependencies import get_mcp_authenticator
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.models.auth import ApiKey
from app.domain.models.user import User
from app.mcp_server.auth import McpAuthenticator

_RAW = "kp_secretkey"
_HASH = hashlib.sha256(_RAW.encode()).hexdigest()


class _FakeApiKeyRepo:
    def __init__(self, api_key: ApiKey | None) -> None:
        self._api_key = api_key

    def get_by_hash(self, key_hash: str):
        return self._api_key

    def update_last_used(self, key: str) -> None:  # pragma: no cover - trivial
        pass


class _FakeUserRepo:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def get_by_key(self, key: str):
        return self._user


class _Tenant:
    def __init__(self, key, slug, role):
        self.key = key
        self.slug = slug
        self.name = slug.title()
        self.role = role


class _FakeTenantService:
    def __init__(self, tenants):
        self._tenants = tenants

    def list_my_tenants(self, user_key: str):
        return self._tenants


def _api_key(**overrides) -> ApiKey:
    base = dict(key="ak-1", user_key="sa-1", label="mcp", key_hash=_HASH, key_prefix="kp_secre")
    base.update(overrides)
    return ApiKey(**base)


def _service_user() -> User:
    return User(key="sa-1", email="bot@example.org", display_name="daily-bot", account_type="service", is_active=True)


def _human_user() -> User:
    return User(key="u-1", email="alice@example.org", display_name="Alice", account_type="user", is_active=True)


def _authenticator(api_key, user, tenants) -> McpAuthenticator:
    return McpAuthenticator(
        _FakeApiKeyRepo(api_key),
        _FakeUserRepo(user),
        _FakeTenantService(tenants),
    )


def _build_app(authenticator: McpAuthenticator) -> TestClient:
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(auth_router, prefix="/api/v1")
    app.dependency_overrides[get_mcp_authenticator] = lambda: authenticator
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_limiter():
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def _enable_mcp(monkeypatch):
    monkeypatch.setattr(settings, "mcp_server_enabled", True)
    yield


def test_validate_returns_grants_for_service_account():
    auth = _authenticator(_api_key(), _service_user(), [_Tenant("home", "home", TenantRole.GROWER)])
    client = _build_app(auth)
    resp = client.post("/api/v1/auth/service-accounts/validate", json={"api_key": _RAW})
    assert resp.status_code == 200
    body = resp.json()
    # The grants are per tenant now: the acting tenant is chosen per tool call.
    assert [t["tenant_slug"] for t in body["tenants"]] == ["home"]
    assert "mcp.read" in body["tenants"][0]["mcp_permissions"]


def test_validate_is_404_when_mcp_disabled(monkeypatch):
    # SEC-003: gated behind the MCP enable flag — the endpoint appears not to exist.
    monkeypatch.setattr(settings, "mcp_server_enabled", False)
    auth = _authenticator(_api_key(), _service_user(), [_Tenant("home", "home", TenantRole.GROWER)])
    client = _build_app(auth)
    resp = client.post("/api/v1/auth/service-accounts/validate", json={"api_key": _RAW})
    assert resp.status_code == 404


def test_validate_masks_valid_non_service_key_as_generic_401():
    # SEC-003: a VALID non-service (human) key must NOT be distinguishable from an
    # invalid/revoked key — both return the same generic 401, no 403 oracle.
    auth = _authenticator(_api_key(), _human_user(), [_Tenant("home", "home", TenantRole.LEAD)])
    client = _build_app(auth)
    valid_non_service = client.post("/api/v1/auth/service-accounts/validate", json={"api_key": _RAW})
    assert valid_non_service.status_code == 401

    # An unknown/invalid key returns the identical status + message (no oracle).
    invalid_auth = _authenticator(None, None, [])
    invalid_client = _build_app(invalid_auth)
    invalid = invalid_client.post("/api/v1/auth/service-accounts/validate", json={"api_key": _RAW})
    assert invalid.status_code == 401
    assert valid_non_service.json()["message"] == invalid.json()["message"]


def test_validate_is_rate_limited():
    # SEC-003: the endpoint is per-IP rate limited (reuses the auth limiter).
    auth = _authenticator(_api_key(), _service_user(), [_Tenant("home", "home", TenantRole.GROWER)])
    client = _build_app(auth)
    limit = int(settings.rate_limit_auth.split("/")[0])
    statuses = [
        client.post("/api/v1/auth/service-accounts/validate", json={"api_key": _RAW}).status_code
        for _ in range(limit + 1)
    ]
    assert 429 in statuses  # the limiter kicked in within the window
