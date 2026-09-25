"""Light mode refuses to set a credential on the shared system account — #1844.

In light mode (REQ-027) every request resolves to the one seeded system user
without authentication (``LightAuthProvider``), and that account has no password
hash. ``POST /api/v1/users/me/password`` therefore took the step-up verifier's
``no_local_password`` branch: anyone who could reach a light instance set the
account's first password, with no current password to prove. The password is
inert while the instance stays in light mode and becomes a working sign-in the
moment it is switched to ``full`` — for whoever set it.

Nothing here overrides ``get_current_user``: the principal comes out of the real
``LightAuthProvider``, exactly as on a light instance, with no ``Authorization``
header at all.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenants.router import router as tenants_router
from app.api.v1.users.router import router as users_router
from app.common.dependencies import get_auth_provider, get_auth_service, get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.engines.light_auth_provider import LightAuthProvider
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.invitation import InvitationLink
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

# Assembled at runtime so no credential-shaped literal sits in the tree (#1838).
_NEW_PASSWORD = "-".join(["chosen", "by", "whoever", "came", "first"])


class _UserRepo:
    def __init__(self) -> None:
        # The light-mode seed (app/migrations/seed_light_mode.py): no password hash.
        self.user = User(_key="system-user", email="system@kamerplanter.example", display_name="Gaertner")
        self.writes: list[dict] = []

    def get_by_key(self, key: str) -> User | None:
        return self.user if key == self.user.key else None

    def get_or_raise(self, key: str) -> User:
        assert key == self.user.key
        return self.user

    def update_fields(self, key: str, fields: dict) -> User:
        self.writes.append(fields)
        for name, value in fields.items():
            setattr(self.user, name, value)
        return self.user


class _NoopRepo:
    def list_by_user(self, user_key: str) -> list:
        return []

    def create(self, model):  # noqa: ANN001, ANN202
        return model

    def revoke_all_for_user(self, user_key: str) -> int:
        return 0


def _client() -> tuple[TestClient, _UserRepo]:
    user_repo = _UserRepo()
    auth_service = AuthService(
        user_repo=user_repo,  # type: ignore[arg-type]
        auth_provider_repo=_NoopRepo(),  # type: ignore[arg-type]
        refresh_token_repo=_NoopRepo(),  # type: ignore[arg-type]
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=None,  # type: ignore[arg-type]
        frontend_url="http://localhost:5173",
    )
    app = FastAPI()
    app.include_router(users_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_auth_provider] = lambda: LightAuthProvider(user_repo)  # type: ignore[arg-type]
    return TestClient(app), user_repo


def test_light_mode_refuses_to_set_the_system_accounts_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    client, user_repo = _client()

    response = client.post("/api/v1/users/me/password", json={"new_password": _NEW_PASSWORD})

    assert response.status_code == 403, response.text
    assert user_repo.writes == []
    assert user_repo.user.password_hash is None


def test_the_control_in_full_mode_the_same_account_sets_its_first_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without this, the 403 above is equally consistent with a route that refuses everyone.

    A federated account without a hash sets its first password without one
    (``no_local_password``, #1815) — that path is unchanged in full mode.
    """
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    client, user_repo = _client()

    response = client.post("/api/v1/users/me/password", json={"new_password": _NEW_PASSWORD})

    assert response.status_code == 200, response.text
    assert user_repo.user.password_hash


# ── Security review of #1844 (SEC-001): invitations are the same class ──────
#
# The seeded system account is ``lead`` with the ``management`` scope in the
# light tenant, so every unauthenticated light-mode caller passes the invitation
# gate. The token it gets back outlives the mode: after the switch to full, the
# caller registers an account, redeems the token and holds a membership (up to
# ``lead``) over the operator's data.


class _InvitingTenantService:
    def __init__(self) -> None:
        self.created: list[str] = []

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        return SimpleNamespace(key="system-tenant", slug=slug)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT], is_active=True)

    def _link(self, kind: str) -> InvitationLink:
        self.created.append(kind)
        return InvitationLink(invitation_key="inv-1", token="t" * 16, expires_at=datetime.now(UTC))

    def create_link_invitation(self, **_: object) -> InvitationLink:
        return self._link("link")

    def create_email_invitation(self, **_: object) -> InvitationLink:
        return self._link("email")


def _tenants_client(tenant_service: _InvitingTenantService) -> TestClient:
    user_repo = _UserRepo()
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_tenant_service] = lambda: tenant_service
    app.dependency_overrides[get_auth_provider] = lambda: LightAuthProvider(user_repo)  # type: ignore[arg-type]
    return TestClient(app)


@pytest.mark.parametrize(
    ("path", "body"),
    [("link", {"role": "lead"}), ("email", {"email": "someone@example.org", "role": "lead"})],
    ids=["link", "email"],
)
def test_light_mode_refuses_to_issue_an_invitation(monkeypatch: pytest.MonkeyPatch, path: str, body: dict) -> None:
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    tenant_service = _InvitingTenantService()

    response = _tenants_client(tenant_service).post(f"/api/v1/tenants/mein-garten/invitations/{path}", json=body)

    assert response.status_code == 403, response.text
    assert tenant_service.created == []


def test_the_control_in_full_mode_a_lead_still_invites(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    tenant_service = _InvitingTenantService()

    response = _tenants_client(tenant_service).post("/api/v1/tenants/mein-garten/invitations/link", json={})

    assert response.status_code == 201, response.text
    assert tenant_service.created == ["link"]
