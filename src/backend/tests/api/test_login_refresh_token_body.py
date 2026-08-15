"""`POST /auth/login` can hand a native client its refresh token (#1134).

Before this, a password sign-in gave a mobile app a 15-minute access token and a
refresh token it could never read — the cookie is HttpOnly and the app has no
cookie jar. The session died unrotatable, which is why the Android client dropped
the password path (`nolte/kamerplanter-android#8`).

The decision recorded on the issue: **yes, but only on explicit request.** Three
properties follow, and each is the kind that is easy to get subtly wrong:

* the browser shape is **unchanged** — cookie set, no token in the JSON;
* the body shape sets **no** cookie, because one credential on two transports
  doubles its exposure and leaves no single place that revokes it;
* the body shape is reachable **only** by asking for it — never inferred from a
  user agent, a header or the absence of a cookie, because those are all
  caller-controlled and inferring would make the weaker transport the *fallback*.

That last one is what the tests here spend most of their assertions on. A feature
like this passes a happy-path test just as well when the flag is ignored and the
token is always in the body — which would be the actual security regression.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth.router import router as auth_router
from app.common.dependencies import get_auth_service
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError

_RAW_REFRESH = "raw-refresh-token-for-a-native-client"
_ACCESS = "eyJhbGciOiJIUzI1NiJ9.access"


class _AuthService:
    """Returns a fixed pair and records what it was asked for."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def login_local(self, email, password, user_agent, ip_address, *, remember_me=False):
        self.calls.append({"email": email, "remember_me": remember_me})
        pair = SimpleNamespace(access_token=_ACCESS, token_type="bearer", expires_in=900)
        return pair, _RAW_REFRESH, remember_me


@pytest.fixture
def service() -> _AuthService:
    return _AuthService()


@pytest.fixture
def client(service: _AuthService) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(auth_router, prefix="/api/v1")
    app.dependency_overrides[get_auth_service] = lambda: service
    # The route is rate-limited; slowapi resolves the limiter from app state.
    from app.api.v1.auth.router import limiter

    app.state.limiter = limiter
    return TestClient(app)


def _login(client: TestClient, **extra) -> object:
    return client.post("/api/v1/auth/login", json={"email": "a@b.example", "password": "pw", **extra})


# ── the browser shape must not move ──────────────────────────────────────────


def test_the_default_login_still_sets_the_cookie_and_hides_the_token(client: TestClient) -> None:
    """No flag: byte-for-byte the pre-#1134 shape.

    This is the assertion that stops the change from being "the token is now
    always in the body", which would hand every web session a 30-day credential
    that XSS can read.
    """
    response = _login(client)

    assert response.status_code == 200, response.text
    assert "refresh_token" not in response.json()
    assert "kp_refresh" in response.cookies


def test_explicitly_declining_the_body_transport_is_the_browser_shape(client: TestClient) -> None:
    """``false`` must behave exactly like absent, not like a third state."""
    response = _login(client, refresh_token_in_body=False)

    assert "refresh_token" not in response.json()
    assert "kp_refresh" in response.cookies


# ── the native shape ─────────────────────────────────────────────────────────


def test_asking_for_the_body_transport_returns_the_refresh_token(client: TestClient) -> None:
    response = _login(client, refresh_token_in_body=True)

    assert response.status_code == 200, response.text
    assert response.json()["refresh_token"] == _RAW_REFRESH


def test_the_body_transport_sets_no_refresh_cookie(client: TestClient) -> None:
    """One credential, one transport.

    Setting the cookie *as well* would be the easy mistake — the cookie line is
    already there and returning early is what avoids it. Two transports double the
    credential's exposure and leave no single place that revokes it.
    """
    response = _login(client, refresh_token_in_body=True)

    assert "kp_refresh" not in response.cookies


def test_the_body_transport_sets_no_csrf_cookie_either(client: TestClient) -> None:
    """The double-submit protects an *ambient* credential. There is none here: the
    native client sends its token deliberately, so a CSRF cookie would be
    ceremony with nothing behind it."""
    response = _login(client, refresh_token_in_body=True)

    assert "csrf_token" not in response.cookies


def test_the_access_token_is_the_same_in_both_shapes(client: TestClient) -> None:
    """Only the refresh transport differs. If the two branches drifted on the
    access token or its lifetime, a native client would be renewing against a
    different session than a browser."""
    browser = _login(client).json()
    native = _login(client, refresh_token_in_body=True).json()

    assert browser["access_token"] == native["access_token"]
    assert browser["expires_in"] == native["expires_in"]
    assert browser["token_type"] == native["token_type"]


# ── the transport must not be inferable ──────────────────────────────────────


@pytest.mark.parametrize(
    "headers",
    [
        {"User-Agent": "okhttp/4.12.0"},
        {"User-Agent": "Dart/3.2 (dart:io)"},
        {"X-Requested-With": "com.example.app"},
        {"Accept": "application/json"},
    ],
)
def test_no_header_can_obtain_the_token_without_asking(client: TestClient, headers: dict) -> None:
    """The transport is chosen by the *body flag* and by nothing else.

    Every header here is caller-controlled and every one of them looks like "a
    native client". Sniffing any of them would decide a security property from an
    attacker-writable string — and, worse, would make the readable-token shape the
    fallback for anything the sniff failed to recognise as a browser.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "a@b.example", "password": "pw"},
        headers=headers,
    )

    assert "refresh_token" not in response.json()
    assert "kp_refresh" in response.cookies


def test_remember_me_stays_orthogonal_to_the_transport(service: _AuthService, client: TestClient) -> None:
    """``remember_me`` decides the refresh token's *lifetime*; the flag decides
    its *delivery*. Folding one into the other would make a native client's
    session length depend on how it receives the token."""
    _login(client, refresh_token_in_body=True, remember_me=True)
    _login(client, refresh_token_in_body=False, remember_me=True)

    assert [call["remember_me"] for call in service.calls] == [True, True]
