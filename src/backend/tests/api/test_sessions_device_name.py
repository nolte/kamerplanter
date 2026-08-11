"""A paired device is visible in — and revocable from — the session list (#1118 / P5).

The pairing flow deliberately mints the *ordinary* REQ-023 token pair, so the
session it creates is the ordinary session document. That is what makes it
listable and revocable at all; what this module pins is that the extra bit of
metadata which tells a phone apart from a browser survives the whole way out to
the HTTP response, and that the revocation actually kills the credential:

* ``GET /api/v1/users/me/sessions`` shows the paired device's ``device_name``
  next to the app's user agent;
* ``DELETE /api/v1/users/me/sessions/{key}`` removes it from the list **and**
  the refresh token it was minted with is dead afterwards (401) — a revocation
  that only hid the row would be the "guard implemented but inert" failure
  class, and the list would look right while the phone kept working;
* a session document written **before** this field existed still deserialises
  and lists (ArangoDB is schemaless: the key is simply absent);
* the browser login path is untouched — its sessions carry no label and the
  response field set is unchanged apart from the one added key;
* an over-long label is refused at the boundary with **422**, never 500, and
  costs neither a code nor a session.

The refresh-token repository here is a real in-memory implementation of
``IRefreshTokenRepository`` rather than a ``MagicMock``: revocation is only
meaningful if ``get_by_hash`` stops answering for a revoked document, which is
exactly the behaviour a mock would hand out for free and therefore never prove.

The app is the real ``app.main`` one, driven through ``dependency_overrides``,
so the routers, the response models and the exception handlers under test are
the deployed ones.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service
from app.common.types import UserKey
from app.data_access.external.device_pairing_throttle import MemoryDevicePairingThrottleStore
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.device_pairing_store import DevicePairingRecord, IDevicePairingCodeStore
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.models.auth import DEVICE_NAME_MAX_LENGTH, RefreshToken
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_ISSUE_PATH = "/api/v1/auth/device-pairing"
_REDEEM_PATH = "/api/v1/auth/device-pairing/redeem"
_SESSIONS_PATH = "/api/v1/users/me/sessions"
_REFRESH_PATH = "/api/v1/auth/refresh"
_LOGIN_PATH = "/api/v1/auth/login"

_USER_KEY = "8271634"
_EMAIL = "owner@example.org"
_PASSWORD = "device-pairing-password-2024"
_SECRET = "test-secret-key-for-unit-tests-32chars!"

_PHONE_USER_AGENT = "Kamerplanter/1.0 (Android 15)"
_BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Firefox/141.0"
_DEVICE_NAME = "Pixel 8 (Gewächshaus)"

#: The field set ``SessionResponse`` served before #1118. Pinned so that adding
#: ``device_name`` stays the *only* change the browser flow sees: a renamed or
#: dropped key here would break the account page without any other test noticing.
_LEGACY_SESSION_FIELDS = frozenset(
    {"key", "user_agent", "ip_address", "created_at", "expires_at", "is_current", "is_persistent"}
)

# One bcrypt round costs ~100 ms, and every test that logs in needs the same
# hash, so it is computed once for the module.
_PASSWORD_HASH = PasswordEngine().hash_password(_PASSWORD)


class _FakeCodeStore(IDevicePairingCodeStore):
    """In-memory pairing-code store: single use, and an expiry from ``issue``.

    Keyed by the raw code — the pseudonymisation property belongs to the Redis
    store and is asserted there. What this flow needs is that a code is
    redeemable exactly once.
    """

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

    ``get_by_hash`` filtering out revoked documents is the single behaviour that
    turns "the row is gone from the list" into "the credential is dead", and it
    mirrors the AQL filter in ``ArangoRefreshTokenRepository``. A ``MagicMock``
    would answer every lookup with a truthy stub, so the 401 this module asserts
    after a revocation would be unprovable.
    """

    def __init__(self) -> None:
        self._docs: dict[str, RefreshToken] = {}
        self._keys = itertools.count(1)

    def create(self, token: RefreshToken) -> RefreshToken:
        key = f"sess-{next(self._keys)}"
        stored = token.model_copy(update={"key": key})
        self._docs[key] = stored
        return stored

    def seed_document(self, document: dict[str, Any]) -> RefreshToken:
        """Insert a raw document the way the Arango repository reads one back.

        Constructed through ``RefreshToken(**document)`` on purpose: that is the
        production deserialisation path, so a document lacking a field this
        model gained fails here if — and only if — it would fail in production.
        """
        stored = RefreshToken(**document)
        self._docs[stored.key or ""] = stored
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
    service: AuthService
    sessions: _MemoryRefreshTokenRepository
    user: User

    def pair_device(
        self,
        device_name: str | None = _DEVICE_NAME,
        user_agent: str = _PHONE_USER_AGENT,
    ):  # noqa: ANN201 - httpx Response
        """Run the full issue-then-redeem flow the phone runs."""
        issued = self.client.post(_ISSUE_PATH)
        assert issued.status_code == 201, issued.text
        body: dict[str, Any] = {"code": issued.json()["code"]}
        if device_name is not None:
            body["device_name"] = device_name
        return self.client.post(_REDEEM_PATH, json=body, headers={"user-agent": user_agent})

    def list_sessions(self) -> list[dict[str, Any]]:
        response = self.client.get(_SESSIONS_PATH)
        assert response.status_code == 200, response.text
        return response.json()

    def refresh_with(
        self,
        raw_refresh_token: str,
        user_agent: str | None = None,
    ):  # noqa: ANN201 - httpx Response
        """Rotate through the cookie transport, CSRF double-submit included.

        P6 adds a body-borne transport for native clients; until then the cookie
        path is the only way to exercise "this refresh token still works", and
        it exercises the same ``AuthService.refresh_tokens`` either way.
        """
        self.client.cookies.set("kp_refresh", raw_refresh_token)
        self.client.cookies.set("csrf_token", "csrf-value")
        headers = {"x-csrf-token": "csrf-value"}
        if user_agent is not None:
            headers["user-agent"] = user_agent
        return self.client.post(_REFRESH_PATH, headers=headers)


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
            yield _Harness(
                client=TestClient(app, raise_server_exceptions=False),
                service=service,
                sessions=sessions,
                user=user,
            )
        finally:
            app.dependency_overrides.pop(get_auth_service, None)
            app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def harness() -> Iterator[_Harness]:
    with _harness() as built:
        yield built


def _row_for(sessions: list[dict[str, Any]], device_name: str | None) -> dict[str, Any]:
    matches = [row for row in sessions if row["device_name"] == device_name]
    assert len(matches) == 1, f"expected exactly one session labelled {device_name!r}, got {sessions}"
    return matches[0]


class TestPairedDeviceVisibility:
    def test_a_paired_device_is_listed_with_its_label_and_user_agent(self, harness: _Harness) -> None:
        """Both fields, not either: the label is what the owner recognises, the
        user agent is what tells them it is the app and not a browser."""
        redeemed = harness.pair_device()
        assert redeemed.status_code == 200, redeemed.text

        row = _row_for(harness.list_sessions(), _DEVICE_NAME)

        assert row["user_agent"] == _PHONE_USER_AGENT
        assert row["is_persistent"] is True

    def test_a_pairing_without_a_label_lists_with_a_null_one(self, harness: _Harness) -> None:
        """The label is optional in the request, so the response must carry the
        key with ``null`` rather than omit it — the frontend falls back to the
        user agent on ``null``, and cannot fall back on a missing key it never
        typed."""
        assert harness.pair_device(device_name=None).status_code == 200

        (row,) = harness.list_sessions()

        assert row["device_name"] is None
        assert row["user_agent"] == _PHONE_USER_AGENT

    def test_the_label_survives_a_refresh_rotation(self, harness: _Harness) -> None:
        """Rotation writes a new session document every 15 minutes. Without the
        label being carried over, the paired phone would appear correctly
        exactly once and turn into an anonymous row afterwards."""
        raw_refresh = harness.pair_device().json()["refresh_token"]

        # The phone sends its own user agent when it rotates; the rotated
        # document takes that from the request, as it always has.
        rotated = harness.refresh_with(raw_refresh, user_agent=_PHONE_USER_AGENT)

        assert rotated.status_code == 200, rotated.text
        row = _row_for(harness.list_sessions(), _DEVICE_NAME)
        assert row["user_agent"] == _PHONE_USER_AGENT


class TestPairedDeviceRevocation:
    def test_revoking_the_session_kills_the_refresh_token(self, harness: _Harness) -> None:
        """The point of listing the phone is being able to take it away. A
        revocation that only removed the row would leave the phone able to
        rotate its token forever, and the session list would say otherwise."""
        raw_refresh = harness.pair_device().json()["refresh_token"]
        session_key = _row_for(harness.list_sessions(), _DEVICE_NAME)["key"]

        revoked = harness.client.delete(f"{_SESSIONS_PATH}/{session_key}")

        assert revoked.status_code == 200, revoked.text
        assert harness.list_sessions() == []
        assert harness.refresh_with(raw_refresh).status_code == 401

    def test_revoking_one_session_leaves_the_others_alone(self, harness: _Harness) -> None:
        """A per-session revoke that behaved like ``logout-all`` would pass the
        test above and lock the owner out of their own browser."""
        phone_refresh = harness.pair_device().json()["refresh_token"]
        other_refresh = harness.pair_device(device_name="Tablet", user_agent=_PHONE_USER_AGENT).json()["refresh_token"]
        phone_key = _row_for(harness.list_sessions(), _DEVICE_NAME)["key"]

        assert harness.client.delete(f"{_SESSIONS_PATH}/{phone_key}").status_code == 200

        assert harness.refresh_with(phone_refresh).status_code == 401
        assert harness.refresh_with(other_refresh).status_code == 200


class TestBackwardsCompatibility:
    def test_a_session_stored_before_this_field_existed_still_lists(self, harness: _Harness) -> None:
        """ArangoDB is schemaless, so no migration ran: documents written before
        #1118 have no ``device_name`` key at all. If deserialising one raised,
        every account with an open session would get a 500 on the account page
        the moment this shipped — which is why it is asserted, not assumed."""
        harness.sessions.seed_document(
            {
                "_key": "sess-legacy",
                "user_key": _USER_KEY,
                "token_hash": "hash-of-a-pre-existing-session",
                "user_agent": _BROWSER_USER_AGENT,
                "ip_address": "198.51.100.4",
                "expires_at": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
                "is_persistent": True,
                "revoked": False,
            }
        )

        response = harness.client.get(_SESSIONS_PATH)

        assert response.status_code == 200, response.text
        (row,) = response.json()
        assert row["key"] == "sess-legacy"
        assert row["device_name"] is None
        assert row["user_agent"] == _BROWSER_USER_AGENT

    def test_the_response_gained_exactly_one_field(self, harness: _Harness) -> None:
        """Pins the contract the account page and any API client already had:
        ``device_name`` is additive, and nothing was renamed or dropped
        alongside it."""
        assert harness.pair_device().status_code == 200

        (row,) = harness.list_sessions()

        assert set(row) == _LEGACY_SESSION_FIELDS | {"device_name"}


class TestBrowserPathsUnaffected:
    def test_a_password_login_session_carries_no_label(self, harness: _Harness) -> None:
        """The web and OAuth flows pass no device metadata, so their sessions
        must render exactly as before — ``device_name`` null, everything else
        untouched. Driven through the real login endpoint rather than the
        service, because "unaffected" is a statement about the response."""
        logged_in = harness.client.post(
            _LOGIN_PATH,
            json={"email": _EMAIL, "password": _PASSWORD, "remember_me": False},
            headers={"user-agent": _BROWSER_USER_AGENT},
        )
        assert logged_in.status_code == 200, logged_in.text

        (row,) = harness.list_sessions()

        assert row["device_name"] is None
        assert row["user_agent"] == _BROWSER_USER_AGENT
        assert row["is_persistent"] is False

    def test_a_browser_and_a_paired_device_are_distinguishable_in_one_list(self, harness: _Harness) -> None:
        """The whole point of the field: two sessions of the same account, and
        the owner can tell which one is the phone."""
        assert (
            harness.client.post(
                _LOGIN_PATH,
                json={"email": _EMAIL, "password": _PASSWORD},
                headers={"user-agent": _BROWSER_USER_AGENT},
            ).status_code
            == 200
        )
        assert harness.pair_device().status_code == 200

        sessions = harness.list_sessions()

        assert _row_for(sessions, _DEVICE_NAME)["user_agent"] == _PHONE_USER_AGENT
        assert _row_for(sessions, None)["user_agent"] == _BROWSER_USER_AGENT


class TestLabelBoundary:
    def test_an_over_long_label_is_refused_with_422_and_creates_no_session(self, harness: _Harness) -> None:
        """Client-supplied free text on an unauthenticated route: it is bounded
        at the boundary, so it answers 422 and never reaches a 500 — and the
        refusal costs neither a session nor the code's single use."""
        issued = harness.client.post(_ISSUE_PATH)
        code = issued.json()["code"]

        refused = harness.client.post(
            _REDEEM_PATH,
            json={"code": code, "device_name": "x" * (DEVICE_NAME_MAX_LENGTH + 1)},
        )

        assert refused.status_code == 422, refused.text
        assert harness.list_sessions() == []
        # The code was not spent by the rejected attempt.
        assert harness.client.post(_REDEEM_PATH, json={"code": code}).status_code == 200

    def test_a_label_at_the_cap_is_stored_whole(self, harness: _Harness) -> None:
        """Off-by-one guard: the cap is inclusive, and the stored value is not
        silently truncated to something the owner would not recognise."""
        label = "x" * DEVICE_NAME_MAX_LENGTH

        assert harness.pair_device(device_name=label).status_code == 200

        assert _row_for(harness.list_sessions(), label)["device_name"] == label
