"""#1883 — creating, repointing and deleting an OIDC provider configuration passes the admin's step-up.

A provider under an attacker's control asserts ``email=<victim>`` with
``email_verified=true`` and the OAuth auto-link signs that person in as the victim.
Until #1883 ``POST``/``PUT``/``DELETE /admin/oidc-providers`` depended on
``require_platform_admin`` alone — passed by a hijacked admin session and by an
admin's leaked ``kp_`` key. The routes now go through ``OidcProviderAdminService``,
which runs the shared ``StepUpVerifier`` (act ``oidc_provider_change``, bound to the
configuration — #1884). Operator decision D6, corrected after security review
SEC-001: only ``display_name`` and ``icon_url`` need no step-up; everything else —
switching a provider on *or off* included — does.

Real routers, the real service and verifier; the repository is an in-memory double.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.admin.oidc_providers.router import router as oidc_router
from app.api.v1.auth.router import limiter
from app.api.v1.users.router import router as users_router
from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_auth_service, get_oidc_config_repo, get_oidc_provider_admin_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.external.step_up_code_store import MemoryStepUpCodeStore
from app.data_access.external.step_up_throttle import MemoryStepUpThrottleStore
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.membership import Membership
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.oidc_provider_admin_service import OidcProviderAdminService
from app.domain.services.step_up_service import StepUpVerifier
from app.domain.services.step_up_targets import StepUpTargetAuthorizer

PASSWORD = "correct horse battery staple"
PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)
ROUTE = "/api/v1/admin/oidc-providers"


def _error_handler(_request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error_code": exc.error_code, "message": exc.message})


@pytest.fixture(autouse=True)
def _full_rate_limit_budget():
    limiter.reset()
    yield
    limiter.reset()


class _Configs:
    """``IOidcConfigRepository`` over a dict; records every write."""

    def __init__(self) -> None:
        self.rows: dict[str, OidcProviderConfig] = {}
        self.writes: list[str] = []

    def get_by_key(self, key: str) -> OidcProviderConfig | None:
        row = self.rows.get(key)
        return row.model_copy(deep=True) if row else None

    def get_by_slug(self, slug: str) -> OidcProviderConfig | None:
        return next((r.model_copy(deep=True) for r in self.rows.values() if r.slug == slug), None)

    def create(self, config: OidcProviderConfig) -> OidcProviderConfig:
        key = f"cfg-{len(self.rows) + 1}"
        self.rows[key] = config.model_copy(update={"key": key})
        self.writes.append(f"create:{key}")
        return self.rows[key]

    def update_fields(self, key: str, fields: dict[str, Any]) -> OidcProviderConfig:
        """Merge, not replace — the Arango repository's partial write."""
        merged = OidcProviderConfig.model_validate({**self.rows[key].model_dump(by_alias=True), **fields})
        self.rows[key] = self.rows[key].model_copy(update=merged.model_dump(include=set(fields)))
        self.writes.append(f"update:{key}")
        return self.rows[key]

    def delete(self, key: str) -> bool:
        self.writes.append(f"delete:{key}")
        return self.rows.pop(key, None) is not None

    def list_all(self) -> list[OidcProviderConfig]:
        return list(self.rows.values())

    def list_enabled(self) -> list[OidcProviderConfig]:
        return [r for r in self.rows.values() if r.enabled]


class _World:
    def __init__(self, *, password_hash: str | None = PASSWORD_HASH) -> None:
        self.admin = User.model_validate(
            {
                "_key": f"admin-{uuid.uuid4().hex[:10]}",
                "email": "admin@example.org",
                "display_name": "Admin",
                "password_hash": password_hash,
            }
        )
        self.configs = _Configs()
        for slug, enabled in (("corp", True), ("lab", False)):
            self.configs.rows[f"key-{slug}"] = OidcProviderConfig.model_validate(
                {
                    "_key": f"key-{slug}",
                    "slug": slug,
                    "display_name": slug.title(),
                    "issuer_url": f"https://{slug}.example.org",
                    "client_id": f"{slug}-client",
                    "enabled": enabled,
                }
            )
        memberships = MagicMock(
            **{
                "get_by_user_and_tenant.side_effect": lambda user_key, tenant_key: (
                    Membership(user_key=user_key, tenant_key="platform", role=TenantRole.LEAD)
                    if tenant_key == "platform"
                    else None
                )
            }
        )
        users = MagicMock(**{"get_by_key.return_value": self.admin, "get_or_raise.return_value": self.admin})
        self.verifier = StepUpVerifier(
            MemoryStepUpThrottleStore(),
            code_store=MemoryStepUpCodeStore(),
            reauth_store=MemoryStepUpCodeStore(),
            code_secret="s" * 32,
            target_policy=StepUpTargetAuthorizer(
                user_repo=users,
                membership_repo=memberships,
                tenant_repo=MagicMock(),
                tenant_erasure_repo=None,
                auth_provider_repo=MagicMock(**{"list_by_user.return_value": []}),
                oidc_config_repo=self.configs,
            ),
        )
        self.service = OidcProviderAdminService(
            self.configs, EncryptionEngine(Fernet.generate_key().decode()), OAuthEngine(), self.verifier
        )
        self.mail = MagicMock()
        self.auth = AuthService(
            user_repo=users,
            auth_provider_repo=MagicMock(**{"list_by_user.return_value": []}),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=self.mail,
            frontend_url="http://localhost:5173",
            step_up_verifier=self.verifier,
        )

    def call(self, method: str, path: str, body: dict[str, Any] | None = None, *, bearer: str | None = None) -> Any:
        app = FastAPI()
        app.include_router(oidc_router, prefix="/api/v1")
        app.include_router(users_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_user] = lambda: self.admin
        app.dependency_overrides[get_is_platform_admin] = lambda: True
        app.dependency_overrides[get_oidc_provider_admin_service] = lambda: self.service
        app.dependency_overrides[get_oidc_config_repo] = lambda: self.configs
        app.dependency_overrides[get_auth_service] = lambda: self.auth
        headers = {"X-Forwarded-For": "198.51.100.9"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        client = TestClient(app, raise_server_exceptions=False)
        return client.request(method, path, json=body, headers=headers)

    def code_for(self, target: str) -> str:
        resp = self.call("POST", "/api/v1/users/me/step-up-code", {"action": "oidc_provider_change", "target": target})
        assert resp.status_code == 202, resp.text
        return self.mail.send_step_up_code_email.call_args.kwargs["code"]


NEW_PROVIDER = {
    "slug": "evil",
    "display_name": "Evil",
    "issuer_url": "https://idp.attacker.example",
    "client_id": "c",
    "client_secret": "s",
    "enabled": True,
}

WRITES = [
    pytest.param("POST", ROUTE, NEW_PROVIDER, id="create"),
    pytest.param("PUT", f"{ROUTE}/key-corp", {"issuer_url": "https://idp.attacker.example"}, id="repoint issuer"),
    pytest.param("PUT", f"{ROUTE}/key-corp", {"token_url": "https://idp.attacker.example/t"}, id="repoint endpoint"),
    pytest.param("PUT", f"{ROUTE}/key-corp", {"client_secret": "other"}, id="client secret"),
    pytest.param("PUT", f"{ROUTE}/key-corp", {"default_tenant_key": "t-victim"}, id="default tenant"),
    pytest.param("PUT", f"{ROUTE}/key-lab", {"enabled": True}, id="switch on"),
    # Security review SEC-001 (operator decision, corrects D6): switching a provider OFF
    # empties the re-auth-capable links of every account whose only one it was, and
    # those accounts fall back to the mailed code — a step-up downgrade.
    pytest.param("PUT", f"{ROUTE}/key-corp", {"enabled": False}, id="switch off"),
    pytest.param("DELETE", f"{ROUTE}/key-corp", {}, id="delete"),
]


@pytest.mark.parametrize(("method", "path", "body"), WRITES)
def test_without_the_step_up_nothing_is_written(method: str, path: str, body: dict[str, Any]) -> None:
    world = _World()

    resp = world.call(method, path, body)

    assert resp.status_code == 401, resp.text
    assert world.configs.writes == []


@pytest.mark.parametrize(("method", "path", "body"), WRITES)
def test_a_wrong_password_writes_nothing(method: str, path: str, body: dict[str, Any]) -> None:
    world = _World()

    resp = world.call(method, path, {**body, "current_password": "wrong"})

    assert resp.status_code == 401, resp.text
    assert world.configs.writes == []


@pytest.mark.parametrize(("method", "path", "body"), WRITES)
def test_an_admins_api_key_is_refused(method: str, path: str, body: dict[str, Any]) -> None:
    world = _World()

    resp = world.call(method, path, {**body, "current_password": PASSWORD}, bearer="kp_admin-automation")

    assert resp.status_code == 403, resp.text
    assert world.configs.writes == []


@pytest.mark.parametrize(("method", "path", "body"), WRITES)
def test_the_admins_password_confirms_the_change(method: str, path: str, body: dict[str, Any]) -> None:
    world = _World()

    resp = world.call(method, path, {**body, "current_password": PASSWORD})

    assert resp.status_code in (200, 201, 204), resp.text
    assert len(world.configs.writes) == 1
    assert "current_password" not in str(world.configs.rows)


def test_repeated_failures_lock_the_step_up() -> None:
    world = _World()
    for _ in range(5):
        assert world.call("DELETE", f"{ROUTE}/key-corp", {"current_password": "wrong"}).status_code == 401

    resp = world.call("DELETE", f"{ROUTE}/key-corp", {"current_password": PASSWORD})

    assert resp.status_code == 429, resp.text
    assert resp.json()["error_code"] == "STEP_UP_LOCKED"
    assert world.configs.writes == []


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"display_name": "Corporate"}, id="display name"),
        pytest.param({"icon_url": "https://corp.example.org/icon.svg"}, id="icon"),
        pytest.param({"issuer_url": "https://corp.example.org"}, id="issuer sent unchanged"),
        pytest.param({"enabled": True}, id="enabled sent unchanged"),
    ],
)
def test_only_presentation_needs_no_step_up(body: dict[str, Any]) -> None:
    """Operator decision D6 as corrected after SEC-001 — the allow-list; a value sent unchanged is no change."""
    world = _World()

    resp = world.call("PUT", f"{ROUTE}/key-corp", body)

    assert resp.status_code == 200, resp.text
    assert world.configs.writes == ["update:key-corp"]


def test_the_scope_check_refuses_before_the_step_up_is_spent() -> None:
    """A configuration that could never sign anyone in is refused (422, #1477) without spending an attempt."""
    world = _World()

    resp = world.call("POST", ROUTE, {**NEW_PROVIDER, "provider_type": "github", "scopes": ["read:user"]})

    assert resp.status_code == 422, resp.text
    assert world.configs.writes == []


def test_a_taken_slug_is_refused_before_the_step_up() -> None:
    resp = _World().call("POST", ROUTE, {**NEW_PROVIDER, "slug": "corp"})

    assert resp.status_code == 409, resp.text


# ── federated admin: the mailed code, bound to the configuration (#1884) ─────


def test_a_code_for_one_configuration_does_not_repoint_another() -> None:
    world = _World(password_hash=None)
    code = world.code_for("key-lab")

    refused = world.call("PUT", f"{ROUTE}/key-corp", {"issuer_url": "https://x.example", "step_up_code": code})
    assert refused.status_code == 401, refused.text
    assert world.configs.writes == []

    meant = world.call("PUT", f"{ROUTE}/key-lab", {"issuer_url": "https://x.example", "step_up_code": code})
    assert meant.status_code == 200, meant.text
    assert world.configs.writes == ["update:key-lab"]


def test_a_creation_is_confirmed_with_a_code_for_its_slug() -> None:
    world = _World(password_hash=None)
    code = world.code_for("new:evil")

    wrong_slug = world.call("POST", ROUTE, {**NEW_PROVIDER, "slug": "other", "step_up_code": code})
    assert wrong_slug.status_code == 401, wrong_slug.text

    resp = world.call("POST", ROUTE, {**NEW_PROVIDER, "step_up_code": code})
    assert resp.status_code == 201, resp.text


@pytest.mark.parametrize(
    ("target", "status"),
    [("key-missing", 404), ("new:corp", 409), ("new:Not A Slug", 422)],
)
def test_no_code_is_mailed_for_a_configuration_target_the_act_would_refuse(target: str, status: int) -> None:
    world = _World(password_hash=None)

    resp = world.call("POST", "/api/v1/users/me/step-up-code", {"action": "oidc_provider_change", "target": target})

    assert resp.status_code == status, resp.text
    world.mail.send_step_up_code_email.assert_not_called()


# ── security review SEC-002 / SEC-003: no write reverts a change made meanwhile ──


def test_an_update_writes_only_what_it_changes() -> None:
    """SEC-003: a concurrent step-up'd change landing during this update's bcrypt check is kept."""
    world = _World()
    real_verify = world.verifier.verify

    def verify_while_someone_else_writes(*args: Any, **kwargs: Any) -> str:
        # Another admin's (step-up'd) switch-off lands while this request is being confirmed.
        world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(update={"enabled": False})
        return real_verify(*args, **kwargs)

    world.verifier.verify = verify_while_someone_else_writes  # type: ignore[method-assign]

    resp = world.call("PUT", f"{ROUTE}/key-corp", {"client_id": "rotated", "current_password": PASSWORD})

    assert resp.status_code == 200, resp.text
    stored = world.configs.rows["key-corp"]
    assert stored.client_id == "rotated"
    assert stored.enabled is False, "the update wrote back its stale snapshot"


def test_the_discovery_test_writes_only_the_discovery_fields() -> None:
    """SEC-002: ``POST /{key}/test`` fetches for up to 15 s; a change made meanwhile must survive it."""
    world = _World()
    discovery = {
        "issuer": "https://corp.example.org",
        "authorization_endpoint": "https://corp.example.org/authorize",
        "token_endpoint": "https://corp.example.org/token",
    }

    def slow_fetch(_issuer_url: str) -> dict[str, Any]:
        # The admin switches the provider off while the (attacker-paced) fetch is pending.
        world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(update={"enabled": False})
        return discovery

    with patch.object(OAuthEngine, "fetch_discovery_document", side_effect=slow_fetch):
        resp = world.call("POST", f"{ROUTE}/key-corp/test")

    assert resp.status_code == 200, resp.text
    stored = world.configs.rows["key-corp"]
    assert stored.enabled is False, "the discovery test wrote back its stale snapshot"
    assert stored.discovery_document == discovery
