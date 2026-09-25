"""A tenant-scoped API key does not act as the whole account — #1851, through the deployed app.

A key restricted to one tenant binds on every tenant-resolving route (#1817).
The routes that resolve *no* tenant act on the owner's account; before #1851 a
scoped key reached all of them. The app here is the real ``app.main`` one; the
principal comes out of the real ``get_current_user`` → ``FullAuthProvider`` →
``AuthService.authenticate_api_key`` chain from a raw key string. Only the
stores behind it and the services the routes would call are doubled — and the
refused routes must never reach those services.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.common.auth import SCOPED_KEY_ON_ACCOUNT_ROUTE
from app.common.dependencies import (
    get_auth_provider,
    get_auth_service,
    get_privacy_service,
    get_substrate_service,
    get_tenant_service,
    get_user_service,
)
from app.common.enums import TenantRole, TenantType
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey
from app.domain.models.tenant import TenantWithRole
from app.domain.models.user import User, UserProfile
from app.domain.services.auth_service import AuthService

_SECRET = "test-secret-key-for-unit-tests-32chars!"
# Assembled at runtime: a credential-shaped literal would be a secret-scanner hit.
_SCOPED = "kp_" + "s" * 32
_UNSCOPED = "kp_" + "u" * 32


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class _ApiKeyRepo:
    _keys = {
        _hash(_SCOPED): ApiKey(
            _key="ak-s",
            user_key="owner",
            label="ha",
            key_hash=_hash(_SCOPED),
            key_prefix="kp_sssss",
            tenant_scope="t_a",
        ),
        _hash(_UNSCOPED): ApiKey(
            _key="ak-u", user_key="owner", label="all", key_hash=_hash(_UNSCOPED), key_prefix="kp_uuuuu"
        ),
    }

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return self._keys.get(key_hash)

    def update_last_used(self, key: str) -> None:
        return None


class _UserRepo:
    def get_by_key(self, key: str) -> User | None:
        return User(_key="owner", email="owner@example.org", display_name="Owner") if key == "owner" else None


def _tenant(key: str, slug: str) -> TenantWithRole:
    return TenantWithRole(
        key=key,
        name=slug,
        slug=slug,
        tenant_type=TenantType.ORGANIZATION,
        description=None,
        role=TenantRole.LEAD,
        is_active=True,
    )


class _TenantService:
    """The owner is a lead in two clubs and a platform admin."""

    def list_my_tenants(self, user_key: str) -> list[TenantWithRole]:
        return [_tenant("t_a", "club-a"), _tenant("t_b", "club-b")]

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True)


@pytest.fixture
def services() -> dict[str, MagicMock]:
    return {name: MagicMock(name=name) for name in ("auth", "privacy", "substrate", "user")}


@pytest.fixture
def client(services: dict[str, MagicMock]) -> Iterator[TestClient]:
    from app.main import app

    user_repo = _UserRepo()
    auth_service = AuthService(
        user_repo=user_repo,  # type: ignore[arg-type]
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine(_SECRET, "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        api_key_repo=_ApiKeyRepo(),  # type: ignore[arg-type]
    )
    services["user"].get_profile.return_value = UserProfile(
        key="owner",
        email="owner@example.org",
        display_name="Owner",
        email_verified=True,
        is_active=True,
        avatar_url=None,
        locale="de",
        last_login_at=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    app.dependency_overrides[get_auth_provider] = lambda: FullAuthProvider(
        TokenEngine(_SECRET, "HS256"),
        user_repo,  # type: ignore[arg-type]
        auth_service,
    )
    app.dependency_overrides[get_tenant_service] = _TenantService
    app.dependency_overrides[get_auth_service] = lambda: services["auth"]
    app.dependency_overrides[get_privacy_service] = lambda: services["privacy"]
    app.dependency_overrides[get_substrate_service] = lambda: services["substrate"]
    app.dependency_overrides[get_user_service] = lambda: services["user"]
    try:
        # The unscoped control reaches the doubled services, whose MagicMock answers
        # fail response validation; a 500 there is fine — only the gate is asserted.
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.clear()


def _bearer(raw: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw}"}


_REFUSED = [
    ("POST", "/api/v1/tenants"),
    ("POST", "/api/v1/tenants/invitations/accept"),
    ("POST", "/api/v1/auth/api-keys"),
    ("GET", "/api/v1/auth/api-keys"),
    ("POST", "/api/v1/auth/device-pairing"),
    ("POST", "/api/v1/auth/logout-all"),
    ("PATCH", "/api/v1/users/me"),
    ("DELETE", "/api/v1/users/me"),
    ("POST", "/api/v1/users/me/password"),
    ("GET", "/api/v1/users/me/sessions"),
    ("GET", "/api/v1/users/me/providers"),
    ("POST", "/api/v1/privacy/export"),
    ("POST", "/api/v1/privacy/erasure"),
    ("GET", "/api/v1/privacy/consents"),
    ("POST", "/api/v1/substrates/batches/b1/assign-slot/s1"),
]


@pytest.mark.parametrize(("method", "path"), _REFUSED, ids=[f"{m} {p}" for m, p in _REFUSED])
def test_a_scoped_key_is_refused_on_an_account_route(
    client: TestClient, services: dict[str, MagicMock], method: str, path: str
) -> None:
    response = client.request(method, path, headers=_bearer(_SCOPED), json={})

    assert response.status_code == 403, response.text
    assert response.json()["message"] == SCOPED_KEY_ON_ACCOUNT_ROUTE
    assert all(not svc.method_calls for svc in services.values()), {n: s.method_calls for n, s in services.items()}


@pytest.mark.parametrize(("method", "path"), _REFUSED, ids=[f"{m} {p}" for m, p in _REFUSED])
def test_an_unscoped_key_passes_the_same_gate(client: TestClient, method: str, path: str) -> None:
    # Control: the 403 above is the scope decision, not a route that refuses every key.
    response = client.request(method, path, headers=_bearer(_UNSCOPED), json={})

    assert response.status_code != 403 or response.json().get("message") != SCOPED_KEY_ON_ACCOUNT_ROUTE


def test_the_tenant_list_shows_a_scoped_key_only_its_tenant(client: TestClient) -> None:
    scoped = client.get("/api/v1/tenants", headers=_bearer(_SCOPED))
    unscoped = client.get("/api/v1/tenants", headers=_bearer(_UNSCOPED))

    assert scoped.status_code == 200, scoped.text
    assert [t["key"] for t in scoped.json()] == ["t_a"]
    assert [t["key"] for t in unscoped.json()] == ["t_a", "t_b"]


def test_the_identity_read_admits_a_scoped_key_without_the_platform_role(client: TestClient) -> None:
    scoped = client.get("/api/v1/users/me", headers=_bearer(_SCOPED))
    unscoped = client.get("/api/v1/users/me", headers=_bearer(_UNSCOPED))

    assert scoped.status_code == 200, scoped.text
    assert scoped.json()["is_platform_admin"] is False
    assert unscoped.json()["is_platform_admin"] is True
