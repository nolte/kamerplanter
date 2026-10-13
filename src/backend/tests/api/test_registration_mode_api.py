"""#2132 (MT-036, REQ-023 AK-56): the registration mode on the wire.

The service decision is pinned in ``tests/unit/domain/services/test_registration_mode.py``; this module holds
what the client sees: the 403 envelope of a refused ``POST /auth/register`` (the same for a taken and a free
address), the invitation token travelling in the request body, the OIDC callback's whitelisted redirect code,
and ``GET /mode`` telling the frontend which entry to offer.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.common.enums import InvitationType, RegistrationMode, TenantRole
from app.common.exceptions import RegistrationNotAllowedError
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.registration_engine import RegistrationPolicy
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.invitation import Invitation
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

TAKEN = "taken@example.com"
FREE = "newcomer@example.com"
PASSWORD = "a-long-enough-password-2026"
TOKEN = "the-newcomers-invitation-token"


def _auth_service(mode: RegistrationMode) -> AuthService:
    users = MagicMock()
    users.get_by_email.side_effect = lambda email: (
        User(_key="1234567", email=TAKEN, display_name="Taken") if email.lower() == TAKEN else None
    )
    users.create.side_effect = lambda user: user.model_copy(update={"key": "7654321", "created_at": datetime.now(UTC)})
    tenant_service = MagicMock()
    invitation = Invitation(
        _key="i1",
        tenant_key="t1",
        invited_by_user_key="u-lead",
        invitation_type=InvitationType.EMAIL,
        email=FREE,
        role=TenantRole.GROWER,
        token_hash=InvitationEngine.hash_token(TOKEN),
        expires_at=datetime.now(UTC) + timedelta(days=2),
    )
    tenant_service.email_invitation_admits.side_effect = lambda *, email, token: (
        token == TOKEN and email.lower() == (invitation.email or "")
    )
    return AuthService(
        user_repo=users,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=tenant_service,
        require_email_verification=False,
        registration_policy=RegistrationPolicy(mode=mode),
    )


@pytest.fixture
def app_under_test():
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        yield app
        app.dependency_overrides.pop(get_auth_service, None)


def _client(app, mode: RegistrationMode) -> TestClient:
    app.dependency_overrides[get_auth_service] = lambda: _auth_service(mode)
    return TestClient(app, raise_server_exceptions=False)


def _register(client: TestClient, email: str, token: str | None = None):
    body: dict[str, object] = {"email": email, "password": PASSWORD, "display_name": "Newcomer"}
    if token is not None:
        body["invitation_token"] = token
    return client.post("/api/v1/auth/register", json=body)


def test_invite_only_refuses_without_an_invitation_with_the_same_envelope_for_taken_and_free(app_under_test) -> None:
    client = _client(app_under_test, RegistrationMode.INVITE_ONLY)

    free = _register(client, FREE)
    taken = _register(client, TAKEN)

    assert free.status_code == taken.status_code == 403, free.text
    assert free.json()["error_code"] == taken.json()["error_code"] == "REGISTRATION_NOT_ALLOWED"
    assert free.json()["message"] == taken.json()["message"]
    assert TAKEN not in taken.text


def test_invite_only_registers_the_holder_of_the_invitation_token(app_under_test) -> None:
    client = _client(app_under_test, RegistrationMode.INVITE_ONLY)

    response = _register(client, FREE, TOKEN)

    assert response.status_code == 201, response.text
    assert response.json()["email"] == FREE


def test_closed_refuses_the_holder_of_the_invitation_token(app_under_test) -> None:
    client = _client(app_under_test, RegistrationMode.CLOSED)

    response = _register(client, FREE, TOKEN)

    assert response.status_code == 403
    assert response.json()["error_code"] == "REGISTRATION_NOT_ALLOWED"


def test_an_overlong_invitation_token_is_refused_at_the_boundary(app_under_test) -> None:
    client = _client(app_under_test, RegistrationMode.INVITE_ONLY)

    response = _register(client, FREE, "x" * 513)

    assert response.status_code == 422


def test_a_refused_first_oidc_sign_in_redirects_with_its_own_whitelisted_code(app_under_test) -> None:
    service = MagicMock()
    service._frontend_url = "https://app.example"
    service.handle_oauth_callback.side_effect = RegistrationNotAllowedError()
    app_under_test.dependency_overrides[get_auth_service] = lambda: service
    client = TestClient(app_under_test, raise_server_exceptions=False, follow_redirects=False)

    response = client.get("/api/v1/auth/oauth/acme/callback", params={"code": "c", "state": "s"})

    assert response.status_code == 302
    assert response.headers["location"] == "https://app.example/auth/callback?error=registration_not_allowed"


@pytest.mark.parametrize("mode", ["open", "invite_only", "closed"])
def test_mode_tells_the_frontend_which_registration_entry_to_offer(app_under_test, mode: str) -> None:
    client = TestClient(app_under_test)

    with (
        patch("app.api.v1.router.settings.registration_mode", mode),
        patch("app.api.v1.router.settings.registration_allowed_domains", "club.example"),
    ):
        body = client.get("/api/v1/mode").json()

    assert body["registration"] == {"mode": mode, "domain_restricted": True}
    assert "club.example" not in str(body)  # the list itself is not published


def test_mode_reports_open_and_unrestricted_by_default(app_under_test) -> None:
    body = TestClient(app_under_test).get("/api/v1/mode").json()

    assert body["registration"] == {"mode": "open", "domain_restricted": False}


def test_light_mode_reports_no_registration(app_under_test) -> None:
    """Light mode has one seeded system account and mounts no /auth routes; the configured mode is moot there."""
    with (
        patch("app.api.v1.router.settings.kamerplanter_mode", "light"),
        patch("app.api.v1.router.settings.registration_mode", "open"),
    ):
        body = TestClient(app_under_test).get("/api/v1/mode").json()

    assert body["registration"] == {"mode": "closed", "domain_restricted": False}
