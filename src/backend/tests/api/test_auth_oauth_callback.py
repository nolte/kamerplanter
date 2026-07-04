"""AP-7 (FE-S1/S3): OAuth callback delivers the token only via the HttpOnly
refresh cookie and maps failures to whitelisted error-code redirects — never a
token in the URL and never a raw provider error string or a JSON 500.
"""

from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.common.dependencies import get_auth_service
from app.common.exceptions import (
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

FRONTEND_URL = "http://frontend.test"


class _FakeAuthService:
    """Minimal stand-in for AuthService.complete_oauth used by the callback."""

    _frontend_url = FRONTEND_URL

    def __init__(self, exc: Exception | None = None) -> None:
        self._exc = exc

    def complete_oauth(self, slug, code, state, user_agent, ip_address):  # noqa: ANN001, ANN201
        if self._exc is not None:
            raise self._exc
        token_pair = SimpleNamespace(access_token="access-token-xyz", expires_in=900)
        return token_pair, "raw-refresh-token", True


def _client_with(service: _FakeAuthService) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = lambda: service
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)


def _callback(service: _FakeAuthService, query: str) -> object:
    for client in _client_with(service):
        return client.get(
            f"/api/v1/auth/oauth/google/callback{query}",
            follow_redirects=False,
        )
    raise AssertionError("client generator did not yield")


def test_successful_callback_redirects_without_token_and_sets_refresh_cookie():
    resp = _callback(_FakeAuthService(), "?code=abc&state=xyz")

    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location == f"{FRONTEND_URL}/auth/callback"
    # No access token anywhere in the redirect URL (neither query nor fragment).
    assert "access_token" not in location
    assert "#" not in location

    set_cookie = resp.headers.get("set-cookie", "")
    assert "kp_refresh=" in set_cookie
    assert "HttpOnly" in set_cookie


def test_invalid_state_redirects_to_whitelisted_error_code():
    resp = _callback(_FakeAuthService(InvalidTokenError("OAuth state")), "?code=abc&state=bad")

    assert resp.status_code == 302
    assert resp.headers["location"] == f"{FRONTEND_URL}/auth/callback?error=invalid_state"
    # A failed exchange must not set a refresh cookie.
    assert "kp_refresh=" not in resp.headers.get("set-cookie", "")


def test_disabled_account_redirects_to_account_disabled():
    resp = _callback(_FakeAuthService(UnauthorizedError("inactive")), "?code=abc&state=xyz")

    assert resp.headers["location"] == f"{FRONTEND_URL}/auth/callback?error=account_disabled"


@pytest.mark.parametrize("exc", [NotFoundError("Oidc", "google"), ValidationError("nope")])
def test_provider_errors_redirect_to_provider_error(exc):
    resp = _callback(_FakeAuthService(exc), "?code=abc&state=xyz")

    assert resp.headers["location"] == f"{FRONTEND_URL}/auth/callback?error=provider_error"


def test_provider_denial_error_param_redirects_to_access_denied():
    # Provider redirects back with ?error=access_denied and no code.
    resp = _callback(_FakeAuthService(), "?error=access_denied")

    assert resp.status_code == 302
    assert resp.headers["location"] == f"{FRONTEND_URL}/auth/callback?error=access_denied"


def test_missing_code_redirects_to_provider_error_without_500():
    resp = _callback(_FakeAuthService(), "?state=xyz")

    assert resp.status_code == 302
    assert resp.headers["location"] == f"{FRONTEND_URL}/auth/callback?error=provider_error"


def test_unexpected_exception_redirects_instead_of_json_500():
    resp = _callback(_FakeAuthService(RuntimeError("boom")), "?code=abc&state=xyz")

    assert resp.status_code == 302
    assert resp.headers["location"] == f"{FRONTEND_URL}/auth/callback?error=provider_error"
