"""HTTP surface of QR device pairing (REQ-023, #1118 / P4).

Two endpoints with deliberately different authentication postures:

* ``POST /api/v1/auth/device-pairing`` — Bearer-authenticated, mints one
  short-lived code plus the base URL a scanner needs;
* ``POST /api/v1/auth/device-pairing/redeem`` — **public**, exchanges a scanned
  code for the standard token pair, with the refresh token in the JSON body
  because the client is a native app with no cookie jar.

What this module pins is the *boundary*, not the domain logic (that is covered
by the ``AuthService`` unit tests) and not the adversarial behaviour (P8): the
payload's source of truth, the response's field set, the absence of a cookie and
of an identity field, the rate limits, the CSRF posture and the OpenAPI security
marking. Every one of those is a property that a plausible edit would break
silently while every other test stayed green.

The app is the real ``app.main`` one — the security marking is produced by
``main.py::_openapi_postprocessed``, so a hand-built ``FastAPI()`` would assert
against a document the deployment never serves.
"""

from __future__ import annotations

import base64
import json
import math
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth.schemas import DEVICE_NAME_MAX_LENGTH, DevicePairingRedeemRequest
from app.common.auth import get_current_user
from app.common.dependencies import get_auth_service
from app.config.settings import settings
from app.data_access.external.device_pairing_throttle import MemoryDevicePairingThrottleStore
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.device_pairing_store import DevicePairingRecord, IDevicePairingCodeStore
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_ISSUE_PATH = "/api/v1/auth/device-pairing"
_REDEEM_PATH = "/api/v1/auth/device-pairing/redeem"

_USER_KEY = "8271634"
_SECRET = "test-secret-key-for-unit-tests-32chars!"

#: A TTL no ``settings.device_pairing_ttl_seconds`` could ever hold (the setting
#: is bounded to 60–120). Used to tell "derived from ``expires_at``" apart from
#: "read the setting back out", which look identical at the default.
_UNSETTABLE_TTL = 42

#: Response fields that differ between any two requests and therefore carry no
#: information about the code that was sent.
_VOLATILE_BODY_FIELDS = frozenset({"error_id", "timestamp"})


class _FakeCodeStore(IDevicePairingCodeStore):
    """In-memory stand-in for the Redis code store.

    Keyed by the raw code rather than its digest: the pseudonymisation property
    belongs to the real store and is asserted there. What this fake has to be
    faithful about is what the *router* depends on — single use, and an expiry
    it returns from ``issue`` — so a redemption is answered exactly once and the
    TTL is observable independently of the settings module.
    """

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._records: dict[str, DevicePairingRecord] = {}

    def issue(self, code: str, user_key: str) -> datetime:
        issued_at = datetime.now(UTC)
        self._records[code] = DevicePairingRecord(user_key=user_key, issued_at=issued_at)
        return issued_at + timedelta(seconds=self._ttl_seconds)

    def consume(self, code: str) -> DevicePairingRecord | None:
        return self._records.pop(code, None)


class _RecordingAuthService(AuthService):
    """Real service, plus a record of *how the router called it*.

    The arguments the handler forwards — the resolved client IP, the User-Agent,
    the device label — leave no trace in the response, so without this they
    would be untested and a handler that dropped them would look perfectly
    healthy. Both overrides delegate to ``super()``, so the behaviour under test
    stays the production one.
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.create_calls: list[tuple[str, str | None]] = []
        self.redeem_calls: list[tuple[str, str | None, str | None, str | None]] = []

    def create_device_pairing(self, user_key: str, ip_address: str | None = None) -> tuple[str, datetime]:
        self.create_calls.append((user_key, ip_address))
        return super().create_device_pairing(user_key, ip_address)

    def redeem_device_pairing(
        self,
        code: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
        device_name: str | None = None,
    ):  # noqa: ANN201 - tuple[TokenPair, str, bool], inherited
        self.redeem_calls.append((code, user_agent, ip_address, device_name))
        return super().redeem_device_pairing(code, user_agent, ip_address, device_name)


@dataclass
class _Harness:
    client: TestClient
    service: _RecordingAuthService
    code_store: _FakeCodeStore
    user: User
    created_refresh_tokens: list[object] = field(default_factory=list)

    def issue(self, **kwargs: object):  # noqa: ANN201 - httpx Response
        return self.client.post(_ISSUE_PATH, **kwargs)  # type: ignore[arg-type]

    def redeem(self, code: str, **body: object):  # noqa: ANN201 - httpx Response
        return self.client.post(_REDEEM_PATH, json={"code": code, **body})

    def issue_code(self) -> str:
        response = self.issue()
        assert response.status_code == 201, response.text
        return response.json()["code"]


@contextmanager
def _harness(ttl_seconds: int = 90) -> Iterator[_Harness]:
    user = User(
        _key=_USER_KEY,
        email="owner@example.org",
        display_name="Code Owner",
        is_active=True,
    )
    code_store = _FakeCodeStore(ttl_seconds)
    user_repo = MagicMock()
    user_repo.get_by_key.side_effect = lambda key: user if key == _USER_KEY else None
    refresh_token_repo = MagicMock()
    created: list[object] = []
    refresh_token_repo.create.side_effect = created.append

    service = _RecordingAuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=refresh_token_repo,
        password_engine=PasswordEngine(),
        token_engine=TokenEngine(_SECRET, "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        device_pairing_code_store=code_store,
        # Fresh per harness: the lockout counter is process state, and a shared
        # one would let a lockout driven by one test decide another's answer.
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
                code_store=code_store,
                user=user,
                created_refresh_tokens=created,
            )
        finally:
            app.dependency_overrides.pop(get_auth_service, None)
            app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def harness() -> Iterator[_Harness]:
    with _harness() as built:
        yield built


def _jwt_claims(access_token: str) -> dict:
    """Read the claims straight out of the token's payload segment.

    Decoded here rather than via ``TokenEngine``: comparing a token to something
    the same engine produced can pass while both sides are wrong about which
    account was signed in.
    """
    payload = access_token.split(".")[1]
    padded = payload + "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _observable(response) -> tuple[int, dict]:  # noqa: ANN001 - httpx Response
    body = {k: v for k, v in response.json().items() if k not in _VOLATILE_BODY_FIELDS}
    return response.status_code, body


# ── Issuance ───────────────────────────────────────────────────────


class TestIssuance:
    def test_returns_the_full_qr_payload_and_nothing_else(self, harness: _Harness) -> None:
        response = harness.issue()

        assert response.status_code == 201
        body = response.json()
        assert set(body) == {"payload_version", "server_url", "code", "expires_at", "expires_in"}
        assert body["payload_version"] == 1
        assert body["code"], "an empty code would render an unscannable QR"

    def test_server_url_comes_from_the_setting_never_from_the_request(
        self,
        harness: _Harness,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The one property that only fails in production if it is wrong.

        ``request.base_url`` is the obvious source and is what a request from
        inside the cluster reports — behind the Traefik ingress that is a
        service address the scanning phone cannot resolve. The failure is
        invisible locally (there the two agree) and total in a deployment, so it
        is pinned by making the two disagree.
        """
        monkeypatch.setattr(settings, "app_base_url", "https://garten.example.org")

        body = harness.issue().json()

        assert body["server_url"] == "https://garten.example.org"
        # The base URL TestClient sends, i.e. what request.base_url would yield.
        assert "testserver" not in body["server_url"]

    def test_expires_in_is_derived_from_expires_at_not_read_off_the_setting(self) -> None:
        """A store TTL the setting could not hold tells the two apart.

        At the default they agree, so a handler that returns
        ``settings.device_pairing_ttl_seconds`` passes the equality check below
        and is still wrong: it would report 90 for a code the store expires in
        42 seconds, and the client would keep showing a dead QR.
        """
        with _harness(ttl_seconds=_UNSETTABLE_TTL) as built:
            body = built.issue().json()

        assert body["expires_in"] == _UNSETTABLE_TTL

        expires_at = datetime.fromisoformat(body["expires_at"])
        assert expires_at.tzinfo is not None, "a naive expiry cannot be compared by a client in another zone"
        assert body["expires_in"] == max(0, math.ceil((expires_at - datetime.now(UTC)).total_seconds()))

    def test_expires_in_matches_the_configured_ttl_at_the_default(self, harness: _Harness) -> None:
        assert harness.issue().json()["expires_in"] == settings.device_pairing_ttl_seconds

    def test_the_code_is_bound_to_the_authenticated_caller(self, harness: _Harness) -> None:
        harness.issue()

        assert harness.service.create_calls[0][0] == _USER_KEY

    def test_the_forwarded_client_address_reaches_the_audit_event(self, harness: _Harness) -> None:
        """Not ``request.client.host``: behind the ingress that is the proxy.

        The same value buckets the redemption throttle, so recording the peer
        address would put every caller in the world into one bucket — turning a
        per-IP lockout into a global one.
        """
        harness.issue(headers={"X-Forwarded-For": "203.0.113.9, 10.42.0.1"})

        assert harness.service.create_calls[0][1] == "203.0.113.9"

    def test_two_issuances_never_return_the_same_code(self, harness: _Harness) -> None:
        assert harness.issue_code() != harness.issue_code()

    def test_is_rate_limited(self, harness: _Harness) -> None:
        limit = int(settings.rate_limit_auth.split("/")[0])

        statuses = [harness.issue().status_code for _ in range(limit + 1)]

        assert statuses[:limit] == [201] * limit
        assert statuses[-1] == 429


# ── Redemption ─────────────────────────────────────────────────────


class TestRedemption:
    def test_returns_exactly_the_two_tokens_and_no_other_credential(self, harness: _Harness) -> None:
        code = harness.issue_code()

        response = harness.redeem(code)

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"access_token", "token_type", "expires_in", "refresh_token"}
        assert body["token_type"] == "bearer"
        assert body["access_token"] and body["refresh_token"]
        # The body is the transport for the refresh token here (native clients
        # have no cookie jar) — but for that token only. No password hash, no
        # API key, no session id, no user record rides along.
        serialised = json.dumps(body)
        for leaked in ("password", "api_key", "kp_", "csrf"):
            assert leaked not in serialised.lower()

    def test_the_access_token_names_the_account_the_code_was_issued_for(self, harness: _Harness) -> None:
        code = harness.issue_code()

        claims = _jwt_claims(harness.redeem(code).json()["access_token"])

        assert claims["sub"] == _USER_KEY
        assert claims["type"] == "access"

    def test_no_refresh_cookie_is_set(self, harness: _Harness) -> None:
        """One credential, one transport.

        Setting ``kp_refresh`` as well would double the token's exposure for a
        client that cannot read cookies anyway, and leave two places to revoke.
        """
        code = harness.issue_code()

        response = harness.redeem(code)

        assert "kp_refresh" not in response.cookies
        assert "set-cookie" not in {k.lower() for k in response.headers}

    def test_the_request_schema_carries_no_identity_field(self) -> None:
        """The absent field is the contract (mirrors the P3 service-level test).

        A ``user_key``/``email`` on an unauthenticated route is a caller-supplied
        claim, and the first handler edit that reads it hands out a session for
        an account of the caller's choosing. Asserted as an exact field set, so
        adding one fails here rather than in a review.
        """
        assert set(DevicePairingRedeemRequest.model_fields) == {"code", "device_name"}

    def test_an_identity_field_smuggled_into_the_body_changes_nothing(self, harness: _Harness) -> None:
        code = harness.issue_code()

        response = harness.redeem(code, user_key="99999", email="attacker@example.org")

        claims = _jwt_claims(response.json()["access_token"])

        assert claims["sub"] == _USER_KEY

    def test_the_user_agent_and_device_label_reach_the_service(self, harness: _Harness) -> None:
        code = harness.issue_code()

        harness.client.post(
            _REDEEM_PATH,
            json={"code": code, "device_name": "Pixel 8"},
            headers={"User-Agent": "Kamerplanter/1.0 (Android 15)", "X-Forwarded-For": "198.51.100.7"},
        )

        assert harness.service.redeem_calls[0] == (code, "Kamerplanter/1.0 (Android 15)", "198.51.100.7", "Pixel 8")

    @pytest.mark.parametrize("length", [1, DEVICE_NAME_MAX_LENGTH])
    def test_a_device_label_up_to_the_cap_is_accepted(self, harness: _Harness, length: int) -> None:
        code = harness.issue_code()

        response = harness.redeem(code, device_name="x" * length)

        assert response.status_code == 200

    def test_an_over_long_device_label_is_rejected_at_the_boundary(self, harness: _Harness) -> None:
        """BACKEND.md §5.4 — the boundary rejects what the domain rejects.

        Asserting only ``422`` would not test this endpoint's schema at all: the
        service caps the label too and answers 422 by itself, so a request model
        with no ``max_length`` passes that check. The discriminator is *which*
        layer refused — a boundary rejection is FastAPI's
        ``RequestValidationError``, and it names the offending field, where the
        service's ``ValidationError`` carries no details at all.
        """
        code = harness.issue_code()

        response = harness.redeem(code, device_name="x" * (DEVICE_NAME_MAX_LENGTH + 1))

        assert response.status_code == 422
        details = response.json()["details"] or []
        assert [d["field"] for d in details] == ["body.device_name"], (
            f"expected a boundary rejection naming the field, got {response.json()}"
        )
        # Nothing was spent on the way in: the code is still redeemable.
        assert harness.redeem(code).status_code == 200

    def test_a_consumed_code_answers_like_one_that_never_existed(self, harness: _Harness) -> None:
        code = harness.issue_code()
        assert harness.redeem(code).status_code == 200

        replayed = _observable(harness.redeem(code))
        unknown = _observable(harness.redeem("a-code-nobody-ever-issued"))

        assert replayed[0] == 401
        assert replayed == unknown, f"replay is distinguishable from an unknown code: {replayed} vs {unknown}"
        assert "Invalid or expired pairing code." in json.dumps(replayed[1])

    def test_a_locked_out_source_address_is_answered_with_423(self, harness: _Harness) -> None:
        statuses = [harness.redeem("wrong-code").status_code for _ in range(MAX_ATTEMPTS + 1)]

        assert statuses == [401] * MAX_ATTEMPTS + [423]
        # And a *valid* code is refused while the lockout holds — otherwise the
        # lockout costs an attacker a status code and nothing else.
        assert harness.redeem(harness.issue_code()).status_code == 423

    def test_is_rate_limited_by_its_own_dedicated_budget(self, harness: _Harness) -> None:
        limit = int(settings.rate_limit_device_pairing_redeem.split("/")[0])

        statuses = [harness.redeem("wrong-code").status_code for _ in range(limit + 1)]

        assert 429 not in statuses[:limit]
        assert statuses[-1] == 429

    def test_the_redemption_budget_is_below_the_interactive_auth_budget(self) -> None:
        """A scanned code is submitted once; there is no typo to retry."""
        redeem_limit, redeem_window = settings.rate_limit_device_pairing_redeem.split("/")
        auth_limit, auth_window = settings.rate_limit_auth.split("/")

        assert redeem_window == auth_window
        assert int(redeem_limit) < int(auth_limit)


# ── Authentication posture ─────────────────────────────────────────


class TestAuthenticationPosture:
    def test_the_openapi_marks_redemption_public(self, harness: _Harness) -> None:
        """``security: []`` is what tells a scanner "public on purpose".

        ``scripts/security/zap_auth_bypass.py::is_protected`` reads exactly this
        field; without the marking the nightly DAST lane reports the endpoint as
        an authentication bypass, and the finding gets suppressed rather than
        read — which is how a real bypass later hides in the noise.
        """
        operation = harness.client.app.openapi()["paths"][_REDEEM_PATH]["post"]  # type: ignore[attr-defined]

        assert operation["security"] == []

    def test_the_openapi_marks_issuance_as_authenticated(self, harness: _Harness) -> None:
        """The other half: pins that the two endpoints are not both public.

        Asserting only the empty list above would stay green if *every*
        operation lost its security requirement.
        """
        operation = harness.client.app.openapi()["paths"][_ISSUE_PATH]["post"]  # type: ignore[attr-defined]

        assert operation["security"], "issuance must carry a security requirement"
        assert "BearerAuth" in {scheme for entry in operation["security"] for scheme in entry}

    def test_the_csrf_guard_is_reachable_in_this_setup(self, harness: _Harness) -> None:
        """Makes the two tests below mean something.

        ``TestClient`` sends no ``X-CSRF-Token`` by default, so "succeeds without
        the header" is also what a request to a route that never checks would
        look like — and what *every* route would look like if ``verify_csrf``
        stopped working. This pins that the guard does fire on the routes that
        carry it, from this very client.
        """
        assert harness.client.post("/api/v1/auth/logout").status_code == 403

    def test_issuance_needs_no_csrf_header(self, harness: _Harness) -> None:
        """Bearer-authenticated, like ``create_api_key``: no ambient credential."""
        response = harness.issue()

        assert response.status_code == 201
        assert "x-csrf-token" not in {k.lower() for k in response.request.headers}

    def test_redemption_needs_no_csrf_header(self, harness: _Harness) -> None:
        """The request carries its own credential; there is nothing to ride on."""
        code = harness.issue_code()

        response = harness.redeem(code)

        assert response.status_code == 200
        assert "x-csrf-token" not in {k.lower() for k in response.request.headers}
