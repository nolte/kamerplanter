"""A tenant-scoped API key is refused on another tenant's routes — #1817, through real HTTP.

The unit module next to the resolvers pins the decision; this file pins the
*premise*: that a raw ``kp_`` bearer really arrives at a ``/t/{slug}/`` route and
at an ``X-Active-Tenant`` route carrying its key's ``tenant_scope``. Nothing here
overrides ``get_current_user`` — the principal comes out of the real
``FullAuthProvider`` → ``AuthService.authenticate_api_key`` chain, from a raw key
string, exactly as in production. Overriding it would assert the gate against a
caller this test *declared*, which is the shape the defect hid behind.

The probe routes depend on the production resolvers (``get_current_tenant``,
``get_active_tenant_context``) and nothing else, so what answers is the resolver.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.common.auth import (
    ACTIVE_TENANT_HEADER,
    get_active_tenant_context,
    get_current_tenant,
    require_platform_admin,
)
from app.common.dependencies import get_auth_provider, get_tenant_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_SECRET = "test-secret-key-for-unit-tests-32chars!"
# Assembled at runtime: a credential-shaped literal would be a secret-scanner hit.
_SCOPED_KEY = "kp_" + "a" * 32
_UNSCOPED_KEY = "kp_" + "u" * 32


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class _ApiKeyRepo:
    _keys = {
        _hash(_SCOPED_KEY): ApiKey(
            _key="ak-scoped",
            user_key="owner",
            label="ha-club-a",
            key_hash=_hash(_SCOPED_KEY),
            key_prefix=_SCOPED_KEY[:8],
            tenant_scope="tenant_a",
        ),
        _hash(_UNSCOPED_KEY): ApiKey(
            _key="ak-unscoped",
            user_key="owner",
            label="everything",
            key_hash=_hash(_UNSCOPED_KEY),
            key_prefix=_UNSCOPED_KEY[:8],
        ),
    }

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return self._keys.get(key_hash)

    def update_last_used(self, key: str) -> None:
        return None


class _UserRepo:
    def __init__(self) -> None:
        self.user = User(_key="owner", email="owner@example.org", display_name="Owner")

    def get_by_key(self, key: str) -> User | None:
        return self.user if key == "owner" else None


class _TenantService:
    """The key's owner is an active lead in both clubs — the defect's precondition."""

    _tenants = {
        "club-a": SimpleNamespace(key="tenant_a", slug="club-a"),
        "club-b": SimpleNamespace(key="tenant_b", slug="club-b"),
    }

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        if slug not in self._tenants:
            raise NotFoundError("Tenant", slug)
        return self._tenants[slug]

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        if user_key == "owner":
            return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True)
        return None

    def get_personal_tenant(self, user_key: str) -> None:
        return None


def _client() -> TestClient:
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
    )

    router = APIRouter()

    @router.get("/t/{tenant_slug}/probe")
    def path_probe(ctx: TenantContext = Depends(get_current_tenant)) -> dict[str, str]:
        return {"tenant_key": ctx.tenant_key}

    @router.get("/catalogue-probe")
    def header_probe(ctx: TenantContext = Depends(get_active_tenant_context)) -> dict[str, str]:
        return {"tenant_key": ctx.tenant_key}

    @router.get("/admin-probe")
    def admin_probe(user: User = Depends(require_platform_admin)) -> dict[str, str]:
        return {"user": user.key or ""}

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_tenant_service] = lambda: _TenantService()
    app.dependency_overrides[get_auth_provider] = lambda: FullAuthProvider(
        TokenEngine(_SECRET, "HS256"),
        user_repo,  # type: ignore[arg-type]
        auth_service,
    )
    return TestClient(app)


def _bearer(raw: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw}"}


def test_a_key_scoped_to_a_is_refused_on_a_path_route_of_b():
    response = _client().get("/api/v1/t/club-b/probe", headers=_bearer(_SCOPED_KEY))

    assert response.status_code == 403


def test_a_key_scoped_to_a_is_refused_on_a_header_route_of_b():
    response = _client().get(
        "/api/v1/catalogue-probe", headers={**_bearer(_SCOPED_KEY), ACTIVE_TENANT_HEADER: "club-b"}
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("key", "path", "headers", "expected"),
    [
        (_SCOPED_KEY, "/api/v1/t/club-a/probe", {}, "tenant_a"),
        (_SCOPED_KEY, "/api/v1/catalogue-probe", {ACTIVE_TENANT_HEADER: "club-a"}, "tenant_a"),
        (_UNSCOPED_KEY, "/api/v1/t/club-b/probe", {}, "tenant_b"),
        (_UNSCOPED_KEY, "/api/v1/catalogue-probe", {ACTIVE_TENANT_HEADER: "club-b"}, "tenant_b"),
    ],
    ids=["scoped-own-path", "scoped-own-header", "unscoped-path", "unscoped-header"],
)
def test_the_control_the_same_chain_admits_what_the_scope_allows(
    key: str, path: str, headers: dict[str, str], expected: str
):
    """Without this, the 403s above are equally consistent with a chain that refuses every key."""
    response = _client().get(path, headers={**_bearer(key), **headers})

    assert response.status_code == 200, response.text
    assert response.json() == {"tenant_key": expected}


def test_a_scoped_key_of_a_platform_admin_is_not_a_platform_admin():
    """/code-review of #1854: platform rights are a membership in the ``platform`` tenant.

    The owner here is a lead everywhere, including ``platform``. A key restricted
    to ``club-a`` must not carry the cross-tenant admin surface with it.
    """
    client = _client()

    assert client.get("/api/v1/admin-probe", headers=_bearer(_SCOPED_KEY)).status_code == 403
    # Control: the same owner's unscoped key is a platform admin.
    assert client.get("/api/v1/admin-probe", headers=_bearer(_UNSCOPED_KEY)).status_code == 200
