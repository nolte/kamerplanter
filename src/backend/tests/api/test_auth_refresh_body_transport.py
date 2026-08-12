"""``POST /auth/refresh`` carries two transports, and only one of them is ambient (#1118 / P6).

A device paired by QR code stores the raw refresh token in its platform keystore.
It has no cookie jar, so it can neither send ``kp_refresh`` nor read the
``csrf_token`` cookie the double-submit compares against. Shipped without a
non-cookie transport, the pair minted by ``/auth/device-pairing/redeem`` would
expire fifteen minutes later with no way to rotate — the feature would be inert
on arrival, which is the failure class this repository keeps paying for.

What this module pins, in the order the risk runs:

* **the cookie path is unchanged** — a cookie-borne refresh without a matching
  ``X-CSRF-Token`` is still 403, a missing cookie is still 401 *before* CSRF is
  considered, the rotated token still leaves as a cookie and still never appears
  in the JSON body. This is the security-critical half: the body transport is a
  relaxation, and a relaxation that leaked into the browser path would be a CSRF
  hole on the endpoint that mints access tokens;
* **precedence** — when a request carries both a cookie and a body token, the
  body wins and the cookie is ignored *entirely*. The tempting shape ("try the
  body, fall back to the cookie") is the actual vulnerability: a forged
  cross-site request with a junk body token would spend the victim's ambient
  cookie with no CSRF header anywhere. Asserted by proving the cookie token is
  still usable after such a request;
* **rotation parity** — old token dead, new token alive, replay refused, on both
  transports;
* **``is_persistent`` survives** the body path, so a paired phone does not
  silently downgrade to a session-length token on its first rotation.

The refresh-token repository is a real in-memory implementation rather than a
``MagicMock``: "the old token is dead" is only provable if ``get_by_hash`` stops
answering for a revoked document — precisely the behaviour a mock hands out for
free and therefore never proves. The app is the real ``app.main`` one, driven
through ``dependency_overrides``, so the routers, response models and exception
handlers under test are the deployed ones.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.schemas import REFRESH_TOKEN_MAX_LENGTH
from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service
from app.common.types import UserKey
from app.data_access.external.device_pairing_throttle import MemoryDevicePairingThrottleStore
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.device_pairing_store import DevicePairingRecord, IDevicePairingCodeStore
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.models.auth import RefreshToken
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_REFRESH_PATH = "/api/v1/auth/refresh"
_LOGIN_PATH = "/api/v1/auth/login"
_ISSUE_PATH = "/api/v1/auth/device-pairing"
_REDEEM_PATH = "/api/v1/auth/device-pairing/redeem"
_SESSIONS_PATH = "/api/v1/users/me/sessions"

_USER_KEY = "8271634"
_EMAIL = "owner@example.org"
_PASSWORD = "device-pairing-password-2024"
_SECRET = "test-secret-key-for-unit-tests-32chars!"

_PHONE_USER_AGENT = "Kamerplanter/1.0 (Android 15)"
_CSRF_VALUE = "csrf-double-submit-value"

#: The browser response shape (AP-7 / FE-S1). The refresh token is **not** in it;
#: it leaves as an HttpOnly cookie. Pinned as a set so that "the body transport
#: also returns the raw token" can never bleed into the cookie transport.
_COOKIE_PATH_FIELDS = frozenset({"access_token", "token_type", "expires_in"})

# One bcrypt round costs ~100 ms and every login needs the same hash, so it is
# computed once for the module.
_PASSWORD_HASH = PasswordEngine().hash_password(_PASSWORD)


class _FakeCodeStore(IDevicePairingCodeStore):
    """In-memory pairing-code store: single use, expiry handed back from ``issue``."""

    def __init__(self, ttl_seconds: int = 90) -> None:
        self._ttl_seconds = ttl_seconds
        self._records: dict[str, DevicePairingRecord] = {}

    def issue(self, code: str, user_key: str) -> datetime:
        issued_at = datetime.now(UTC)
        self._records[code] = DevicePairingRecord(user_key=user_key, issued_at=issued_at)
        return issued_at + timedelta(seconds=self._ttl_seconds)

    def consume(self, code: str) -> DevicePairingRecord | None:
        return self._records.pop(code, None)


class _MemoryRefreshTokenRepository(IRefreshTokenRepository):
    """A session store that actually forgets a revoked token.

    ``get_by_hash`` filtering out revoked documents mirrors the AQL filter in
    ``ArangoRefreshTokenRepository`` and is the single behaviour that turns
    "rotated" into "the old token is dead".
    """

    def __init__(self) -> None:
        self._docs: dict[str, RefreshToken] = {}
        self._keys = itertools.count(1)

    def create(self, token: RefreshToken) -> RefreshToken:
        key = f"sess-{next(self._keys)}"
        stored = token.model_copy(update={"key": key})
        self._docs[key] = stored
        return stored

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next(
            (doc for doc in self._docs.values() if doc.token_hash == token_hash and not doc.revoked),
            None,
        )

    def revoke(self, key: str) -> bool:
        doc = self._docs.get(key)
        if doc is None:
            return False
        self._docs[key] = doc.model_copy(update={"revoked": True})
        return True

    def revoke_all_for_user(self, user_key: UserKey) -> int:
        revoked = 0
        for key, doc in list(self._docs.items()):
            if doc.user_key == user_key and not doc.revoked:
                self._docs[key] = doc.model_copy(update={"revoked": True})
                revoked += 1
        return revoked

    def cleanup_expired(self) -> int:
        return 0

    def list_active_for_user(self, user_key: UserKey) -> list[RefreshToken]:
        now = datetime.now(UTC)
        return [
            doc for doc in self._docs.values() if doc.user_key == user_key and not doc.revoked and doc.expires_at > now
        ]


@dataclass
class _Harness:
    client: TestClient
    sessions: _MemoryRefreshTokenRepository

    # ── obtaining real refresh tokens ───────────────────────────────

    def login(self, remember_me: bool = False) -> str:
        """Log in through the browser flow and read the raw token off the cookie.

        The login response deliberately does not contain the refresh token, so
        the cookie jar is where a test gets hold of it — which also means every
        token used below was minted by the production path, not fabricated.
        """
        self.client.cookies.clear()
        response = self.client.post(
            _LOGIN_PATH,
            json={"email": _EMAIL, "password": _PASSWORD, "remember_me": remember_me},
        )
        assert response.status_code == 200, response.text
        raw = self.client.cookies["kp_refresh"]
        self.client.cookies.clear()
        return raw

    def pair_device(self) -> str:
        """Run the QR flow a phone runs and return the token it must rotate with."""
        self.client.cookies.clear()
        issued = self.client.post(_ISSUE_PATH)
        assert issued.status_code == 201, issued.text
        redeemed = self.client.post(
            _REDEEM_PATH,
            json={"code": issued.json()["code"], "device_name": "Pixel 8"},
            headers={"user-agent": _PHONE_USER_AGENT},
        )
        assert redeemed.status_code == 200, redeemed.text
        self.client.cookies.clear()
        return redeemed.json()["refresh_token"]

    # ── the two transports under test ───────────────────────────────

    def refresh_via_body(
        self,
        raw_refresh_token: str | None,
        cookie_token: str | None = None,
        csrf: bool = False,
        body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Rotate the way a paired device does: token in the JSON body.

        ``cookie_token``/``csrf`` exist only for the precedence tests, where the
        point is that adding an ambient credential changes nothing.
        """
        self.client.cookies.clear()
        headers = {"user-agent": _PHONE_USER_AGENT}
        if cookie_token is not None:
            self.client.cookies.set("kp_refresh", cookie_token)
        if csrf:
            self.client.cookies.set("csrf_token", _CSRF_VALUE)
            headers["x-csrf-token"] = _CSRF_VALUE
        payload = body if body is not None else {"refresh_token": raw_refresh_token}
        return self.client.post(_REFRESH_PATH, json=payload, headers=headers)

    def refresh_via_cookie(
        self,
        raw_refresh_token: str | None,
        csrf_cookie: str | None = _CSRF_VALUE,
        csrf_header: str | None = _CSRF_VALUE,
        body: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Rotate the way a browser does: HttpOnly cookie + CSRF double-submit."""
        self.client.cookies.clear()
        if raw_refresh_token is not None:
            self.client.cookies.set("kp_refresh", raw_refresh_token)
        if csrf_cookie is not None:
            self.client.cookies.set("csrf_token", csrf_cookie)
        headers = {"x-csrf-token": csrf_header} if csrf_header is not None else {}
        kwargs: dict[str, Any] = {"headers": headers}
        if body is not None:
            kwargs["json"] = body
        return self.client.post(_REFRESH_PATH, **kwargs)

    def list_sessions(self) -> list[dict[str, Any]]:
        self.client.cookies.clear()
        response = self.client.get(_SESSIONS_PATH)
        assert response.status_code == 200, response.text
        return response.json()


@contextmanager
def _harness() -> Iterator[_Harness]:
    user = User(
        _key=_USER_KEY,
        email=_EMAIL,
        display_name="Code Owner",
        password_hash=_PASSWORD_HASH,
        email_verified=True,
        is_active=True,
    )
    user_repo = MagicMock()
    user_repo.get_by_key.side_effect = lambda key: user if key == _USER_KEY else None
    user_repo.get_by_email.side_effect = lambda email: user if email == _EMAIL else None
    sessions = _MemoryRefreshTokenRepository()

    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=sessions,
        password_engine=PasswordEngine(),
        token_engine=TokenEngine(_SECRET, "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        device_pairing_code_store=_FakeCodeStore(),
        device_pairing_throttle_store=MemoryDevicePairingThrottleStore(),
    )

    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            yield _Harness(client=TestClient(app, raise_server_exceptions=False), sessions=sessions)
        finally:
            app.dependency_overrides.pop(get_auth_service, None)
            app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def harness() -> Iterator[_Harness]:
    with _harness() as built:
        yield built


def _set_cookie_names(response: httpx.Response) -> set[str]:
    """Names of every cookie the response sets — read off the raw header.

    ``response.cookies`` only exposes what the jar accepted; the header is what
    the server actually sent, and "sets no cookie" is a statement about the
    server.
    """
    return {header.split("=", 1)[0].strip() for header in response.headers.get_list("set-cookie")}


class TestBodyTransport:
    """The paired device can rotate at all — R3, the reason this package exists."""

    def test_a_paired_device_rotates_with_neither_cookie_nor_csrf_header(self, harness: _Harness) -> None:
        """The full chain: redeem a QR code, then rotate the token it returned
        using nothing but the token itself. If this 401s or 403s, every paired
        phone is logged out fifteen minutes after pairing."""
        paired_token = harness.pair_device()

        rotated = harness.refresh_via_body(paired_token)

        assert rotated.status_code == 200, rotated.text
        assert rotated.json()["refresh_token"] != paired_token
        assert rotated.json()["access_token"]

    def test_the_body_path_sets_no_cookie_at_all(self, harness: _Harness) -> None:
        """One credential on two transports doubles its exposure and leaves no
        single place that revokes it. A native client has no jar to put a cookie
        in, so a ``Set-Cookie`` here would be pure leakage into proxies and
        logs — including the ``csrf_token`` cookie, which would be equally
        pointless."""
        rotated = harness.refresh_via_body(harness.pair_device())

        assert rotated.status_code == 200, rotated.text
        assert _set_cookie_names(rotated) == set()

    def test_the_returned_token_is_a_working_token_and_not_an_echo(self, harness: _Harness) -> None:
        """Rotating twice in a row proves the body actually carries the *new*
        credential. A handler that echoed the input would pass the first test
        and strand the device on its second rotation."""
        first = harness.refresh_via_body(harness.pair_device())

        second = harness.refresh_via_body(first.json()["refresh_token"])

        assert second.status_code == 200, second.text
        assert second.json()["refresh_token"] != first.json()["refresh_token"]

    def test_a_browser_minted_token_also_works_on_the_body_path(self, harness: _Harness) -> None:
        """The transport is a property of the request, not of how the token was
        minted: one rotation implementation, as the operator decided."""
        assert harness.refresh_via_body(harness.login()).status_code == 200

    def test_an_unknown_body_token_is_refused_with_401(self, harness: _Harness) -> None:
        assert harness.refresh_via_body("not-a-token-anybody-ever-issued").status_code == 401

    def test_a_body_token_over_the_cap_is_refused_at_the_boundary(self, harness: _Harness) -> None:
        """Unauthenticated free text is bounded where it enters, so it answers
        422 rather than being hashed first and 500-ing somewhere later."""
        refused = harness.refresh_via_body("x" * (REFRESH_TOKEN_MAX_LENGTH + 1))

        assert refused.status_code == 422, refused.text


class TestPersistenceIsPreserved:
    """``is_persistent`` decides whether the phone stays logged in for 30 days."""

    def test_a_persistent_session_stays_persistent_across_a_body_refresh(self, harness: _Harness) -> None:
        """Redemption mints a persistent session. Rotation replaces the session
        document, so a flag that is not carried over silently downgrades the
        phone to a session-length token on its very first refresh."""
        assert harness.refresh_via_body(harness.pair_device()).status_code == 200

        (session,) = harness.list_sessions()

        assert session["is_persistent"] is True

    def test_a_non_persistent_session_is_not_upgraded_by_a_body_refresh(self, harness: _Harness) -> None:
        """The mirror image, and the one that matters for a shared machine: a
        login without ``remember_me`` must not become a 30-day token because it
        was rotated over the body transport."""
        assert harness.refresh_via_body(harness.login(remember_me=False)).status_code == 200

        (session,) = harness.list_sessions()

        assert session["is_persistent"] is False


class TestCookiePathUnchanged:
    """The security-critical regression: the browser transport did not move."""

    def test_a_missing_csrf_header_is_still_refused_with_403(self, harness: _Harness) -> None:
        """The double-submit still guards the ambient credential. If the body
        extension had relaxed this, ``/auth/refresh`` — the endpoint that mints
        access tokens — would be forgeable from any site the user visits."""
        refused = harness.refresh_via_cookie(harness.login(), csrf_header=None)

        assert refused.status_code == 403, refused.text

    def test_a_mismatched_csrf_header_is_still_refused_with_403(self, harness: _Harness) -> None:
        refused = harness.refresh_via_cookie(harness.login(), csrf_header="a-different-value")

        assert refused.status_code == 403, refused.text

    def test_a_missing_csrf_cookie_is_still_refused_with_403(self, harness: _Harness) -> None:
        refused = harness.refresh_via_cookie(harness.login(), csrf_cookie=None)

        assert refused.status_code == 403, refused.text

    def test_a_request_with_no_credential_at_all_is_still_401_not_403(self, harness: _Harness) -> None:
        """Order of refusal, pinned: the cookie used to be extracted by a
        dependency and therefore ran *before* ``verify_csrf``. Moving it into
        the handler keeps that order — a client that lost its session gets 401
        ("log in again"), not 403 ("your CSRF token is wrong")."""
        refused = harness.refresh_via_cookie(None, csrf_cookie=None, csrf_header=None)

        assert refused.status_code == 401, refused.text

    def test_a_valid_cookie_refresh_rotates_the_cookie_and_hides_the_token(self, harness: _Harness) -> None:
        """Everything the browser flow relies on, in one assertion block: the
        rotated token comes back as a cookie, a fresh CSRF cookie comes with it,
        and the raw token is nowhere in the JSON (AP-7 / FE-S1)."""
        old_token = harness.login()

        rotated = harness.refresh_via_cookie(old_token)

        assert rotated.status_code == 200, rotated.text
        assert _set_cookie_names(rotated) == {"kp_refresh", "csrf_token"}
        assert rotated.cookies["kp_refresh"] != old_token
        assert set(rotated.json()) == _COOKIE_PATH_FIELDS

    def test_an_explicit_null_body_token_takes_the_cookie_path(self, harness: _Harness) -> None:
        """``{"refresh_token": null}`` names no token, so it is the cookie path —
        CSRF and all. Anything else would make a one-word body a CSRF bypass."""
        token = harness.login()

        refused = harness.refresh_via_cookie(token, csrf_header=None, body={"refresh_token": None})
        accepted = harness.refresh_via_cookie(token, body={"refresh_token": None})

        assert refused.status_code == 403, refused.text
        assert accepted.status_code == 200, accepted.text
        assert set(accepted.json()) == _COOKIE_PATH_FIELDS

    @pytest.mark.parametrize(
        ("content", "content_type"),
        [
            pytest.param(b"", None, id="no-body-no-content-type"),
            pytest.param(b"", "application/json", id="empty-body-json-content-type"),
            pytest.param(b"null", "application/json", id="literal-json-null"),
        ],
    )
    def test_the_shapes_the_browser_actually_sends_are_still_accepted(
        self,
        harness: _Harness,
        content: bytes,
        content_type: str | None,
    ) -> None:
        """The frontend calls ``client.post('/auth/refresh', null, …)``, and what
        axios puts on the wire for a ``null`` payload is a version-dependent
        detail — an empty body, an empty body with a JSON content type, or the
        four bytes ``null``. Declaring an optional body model means the request
        is now *parsed* where it used to be ignored, so all three shapes are
        pinned here rather than discovered by a logged-out user after deploy."""
        token = harness.login()
        harness.client.cookies.clear()
        harness.client.cookies.set("kp_refresh", token)
        harness.client.cookies.set("csrf_token", _CSRF_VALUE)
        headers = {"x-csrf-token": _CSRF_VALUE}
        if content_type is not None:
            headers["content-type"] = content_type

        rotated = harness.client.post(_REFRESH_PATH, content=content, headers=headers)

        assert rotated.status_code == 200, rotated.text
        assert set(rotated.json()) == _COOKIE_PATH_FIELDS

    def test_an_empty_body_token_is_refused_rather_than_falling_back(self, harness: _Harness) -> None:
        """An empty string is a client bug, not a request for the cookie path.
        It is refused at the boundary (422) and — the part that matters — the
        ambient cookie is not spent by it."""
        token = harness.login()

        refused = harness.refresh_via_body("", cookie_token=token)

        assert refused.status_code == 422, refused.text
        assert harness.refresh_via_cookie(token).status_code == 200


class TestPrecedenceBodyWins:
    """Both credentials present: the ambient one is never spent without CSRF."""

    def test_an_invalid_body_token_never_spends_the_cookie(self, harness: _Harness) -> None:
        """The forged-request shape: a cross-site page cannot read the victim's
        refresh cookie but the browser attaches it anyway, so a handler that fell
        back to the cookie when the body token failed would rotate the victim's
        session with no CSRF header in sight. The answer must be 401 *and* the
        cookie must still be alive afterwards — the second assertion is the one
        that catches a fallback, because a fallback would have consumed it."""
        cookie_token = harness.login()

        refused = harness.refresh_via_body("not-a-token-anybody-ever-issued", cookie_token=cookie_token)

        assert refused.status_code == 401, refused.text
        assert _set_cookie_names(refused) == set()
        assert harness.refresh_via_cookie(cookie_token).status_code == 200

    def test_a_valid_body_token_wins_and_leaves_the_cookie_untouched(self, harness: _Harness) -> None:
        """Two live sessions of the same user, one named in the body and one
        riding along in the cookie. Exactly the named one is rotated: the body
        token dies, the cookie token still works. A cookie-first precedence
        would fail both halves."""
        cookie_token = harness.login()
        body_token = harness.pair_device()

        rotated = harness.refresh_via_body(body_token, cookie_token=cookie_token)

        assert rotated.status_code == 200, rotated.text
        assert rotated.json()["refresh_token"] != cookie_token
        assert harness.refresh_via_body(body_token).status_code == 401
        assert harness.refresh_via_cookie(cookie_token).status_code == 200

    def test_the_body_path_ignores_a_csrf_header_it_does_not_need(self, harness: _Harness) -> None:
        """A client that sends a double-submit pair anyway is not punished for
        it — the body path neither requires nor rejects the header."""
        assert harness.refresh_via_body(harness.pair_device(), csrf=True).status_code == 200


class TestRotationSemanticsAreIdentical:
    """Old token revoked, new token usable once — whichever transport carried it."""

    def test_a_replayed_body_token_is_refused_with_401(self, harness: _Harness) -> None:
        token = harness.pair_device()
        assert harness.refresh_via_body(token).status_code == 200

        assert harness.refresh_via_body(token).status_code == 401

    def test_a_replayed_cookie_token_is_refused_with_401(self, harness: _Harness) -> None:
        token = harness.login()
        assert harness.refresh_via_cookie(token).status_code == 200

        assert harness.refresh_via_cookie(token).status_code == 401

    def test_a_token_rotated_over_the_body_is_dead_on_the_cookie_path_too(self, harness: _Harness) -> None:
        """Revocation is a property of the token, not of the transport that
        retired it. Otherwise a stolen token could be resurrected by switching
        transport — the same object, two answers."""
        token = harness.pair_device()
        assert harness.refresh_via_body(token).status_code == 200

        assert harness.refresh_via_cookie(token).status_code == 401

    def test_a_token_rotated_over_the_cookie_is_dead_on_the_body_path_too(self, harness: _Harness) -> None:
        token = harness.login()
        assert harness.refresh_via_cookie(token).status_code == 200

        assert harness.refresh_via_body(token).status_code == 401

    def test_each_rotation_leaves_exactly_one_live_session(self, harness: _Harness) -> None:
        """The session list is where an owner sees their devices. A rotation that
        left the old document active would grow the list on every refresh and
        make revocation meaningless."""
        token = harness.pair_device()

        for _ in range(3):
            response = harness.refresh_via_body(token)
            assert response.status_code == 200, response.text
            token = response.json()["refresh_token"]

        assert len(harness.list_sessions()) == 1
