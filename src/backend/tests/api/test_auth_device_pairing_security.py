"""Adversarial properties of the QR pairing surface, end to end (REQ-023/REQ-024, #1118 / P8).

The issue states its security properties as behaviour ("the code is single-use",
"brute force is locked out", "the session belongs to the account that issued the
code"). None of them is a statement about one function: each spans the router,
the service, the throttle, the code store and — for the tenant property — the
authorisation chain that runs on the *next* request the minted token makes. The
unit suites pin the parts, ``test_auth_device_pairing_api.py`` pins the shape of
the two endpoints, and ``test_auth_refresh_body_transport.py`` pins the two
refresh transports. This module attacks the assembled thing.

Deliberately **not** repeated here (already pinned elsewhere, and a second copy
would only make the two drift): the response field sets, ``server_url``'s source,
the CSRF posture, the OpenAPI ``security: []`` marking and the plain
"consumed code answers like an unknown one" comparison (P4); the cookie-path CSRF
regression, precedence between cookie and body, and rotation parity (P6); the
light-mode 404 on both routes, which ``test_device_pairing_router_mounting.py``
proves at import time under a real ``KAMERPLANTER_MODE=light`` re-import — a
behavioural repetition here would add a slower copy of the same fact.

Real vs doubled
---------------
Per ``spec/project/test-tier-integration/`` §"Isolation level", stated so a
reviewer can confirm the test is narrow. **Real** (the seam under test): the
deployed ``app.main`` application with its middleware, exception handlers and
rate limiter; both pairing routes and ``/auth/refresh``; ``AuthService`` with the
real ``LoginThrottleEngine``, ``TokenEngine`` and ``PasswordEngine``; the real
``FullAuthProvider``, so every token minted here is verified by production code
before it is honoured; the real ``get_current_tenant`` membership gate; and the
real ``MemoryDevicePairingThrottleStore`` (the in-process tier of the production
store, not a mock). **Doubled** at the boundary: the pairing-code store (Redis),
the refresh-token repository, the user repository, ``TenantService`` and
``SiteService`` — i.e. exactly the collaborators that would otherwise be
ArangoDB or Valkey.

The two doubles that carry behaviour are written to be faithful about the one
thing each is asked here: :class:`_ClockedCodeStore` consumes atomically and
expires at the instant it reported from ``issue`` (so "expired" is driven by a
clock, never by ``sleep``), and :class:`_MemoryRefreshTokenRepository` stops
answering for a revoked document, which is what makes "no second session" and
"the old token is dead" provable at all — a ``MagicMock`` hands both out for
free and therefore proves neither.

Falsifiability — which mutation kills which test
------------------------------------------------
Per ``spec/project/test-falsifiability/`` §"Negative verification". The feature
was already implemented when this module was written, so the evidence is
mutation-based rather than a revert; each was applied, observed red, and undone
(see the P8 dispatch-log entry for the commands):

* **M1** ``redeem_device_pairing``: re-``issue`` the code after consuming it,
  i.e. read without delete → ``…replayed_code_mints_no_second_session…``.
* **M2** ``create_device_pairing`` handler: advertise ``now + 300 s`` instead of
  the store's expiry → ``…still_redeemable_one_second_before_its_advertised_expiry``
  (the code is dead long before the client's countdown says so).
* **M3** ``redeem_device_pairing``: move ``store.consume`` *above* the lockout
  check → ``…locked_address_cannot_burn_the_valid_code_it_holds`` (the refused
  attempt eats the code, so the clean address then gets 401).
* **M4** redeem handler: bucket on ``request.client.host`` instead of
  ``resolve_client_ip`` → the same test **and** the rate-limit one (every caller
  lands in one bucket, so the clean address is locked too).
* **M5** router: drop ``@limiter.limit`` from the redeem route →
  ``…submitted_while_rate_limited_is_refused_and_not_consumed``.
* **M6** ``_membership_for_slug``: synthesise a viewer membership instead of
  refusing → ``…refused_by_a_tenant_its_user_is_no_member_of``,
  ``…resolved_per_request_not_frozen_into_the_paired_token`` (the same defect a
  token with baked-in memberships would produce) and the cross-user test.
* **M7** schema + service + handler: accept a ``user_key`` in the redeem body and
  resolve the account from it → ``…stranger_redeeming_a_code_gets_a_session_on_the_issuers_account_only``.
* **M8** ``create_device_pairing``: add ``code=code`` to the audit event →
  ``…no_log_record_carries_the_pairing_code_or_a_raw_token``.
* **M9** ``/auth/refresh``: remove the body parameter (the pre-P6 shape, where a
  body was accepted and ignored) → all four
  ``…non_json_body_is_refused_at_the_boundary_without_spending_the_cookie`` cases,
  which then answer 403 from ``verify_csrf`` instead of 422 at the boundary.
* **M10** ``_membership_for_slug``: refuse every slug →
  ``…paired_token_reaches_the_issuing_users_own_tenant`` (the positive anchor).
* **M11/M12** ``_create_tokens``: hard-code ``is_platform_admin`` to ``True`` /
  ``False`` → the two ``…platform_admin…`` tests respectively; neither can be
  satisfied by a constant, which is why both directions are here.
* **M13** ``redeem_device_pairing``: fabricate a record when the store misses →
  the replay, the expiry-refusal, the brute-force and the log-hygiene tests.

Traceability: REQ-023 (device pairing, #1118) and REQ-024 §tenant isolation. No
derived TC-ID exists for this strand — the ``TC-023-NNN`` cases added by P11
cover the browser dialog, not these boundary properties — so none is claimed
here rather than a plausible-looking one being invented.
"""

from __future__ import annotations

import base64
import itertools
import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
import structlog
from fastapi.testclient import TestClient

from app.api.v1.auth.router import limiter
from app.common.dependencies import get_auth_provider, get_auth_service, get_site_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.common.types import UserKey
from app.config.settings import settings
from app.data_access.external.device_pairing_throttle import MemoryDevicePairingThrottleStore
from app.domain.engines.full_auth_provider import FullAuthProvider
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.device_pairing_store import DevicePairingRecord, IDevicePairingCodeStore
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.models.auth import RefreshToken
from app.domain.models.membership import Membership
from app.domain.models.site import Site
from app.domain.models.tenant import Tenant
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService

_ISSUE_PATH = "/api/v1/auth/device-pairing"
_REDEEM_PATH = "/api/v1/auth/device-pairing/redeem"
_REFRESH_PATH = "/api/v1/auth/refresh"
_SESSIONS_PATH = "/api/v1/users/me/sessions"

_SECRET = "test-secret-key-for-unit-tests-32chars!"
_CSRF_VALUE = "csrf-double-submit-value"

#: The two accounts. ``_OWNER`` issues the pairing codes; ``_STRANGER`` is the
#: attacker holding a valid session of their own — the interesting adversary,
#: because an unauthenticated one has strictly fewer options.
_OWNER = "user-owner"
_STRANGER = "user-stranger"

#: One tenant each, so "the token reaches its own tenant" and "the token is
#: refused by the other" are answered by the same route with the same double.
_OWNER_TENANT = Tenant(_key="tenant-owner", name="Owner Garden", slug="owner-garden", owner_user_key=_OWNER)
_STRANGER_TENANT = Tenant(
    _key="tenant-stranger",
    name="Stranger Garden",
    slug="stranger-garden",
    owner_user_key=_STRANGER,
)

#: Readable identity of the row only the owner's tenant holds, so the positive
#: half of the tenant assertions names *what* was read, not merely that a status
#: code was 200.
_OWNER_SITE_NAME = "Owner Greenhouse"

#: Two source addresses. The throttle buckets per address, so a lockout driven
#: from one must leave the other able to redeem.
_ATTACKER_IP = "203.0.113.9"
_CLEAN_IP = "198.51.100.7"


class _Clock:
    """A movable "now", so expiry is driven by arithmetic and never by sleeping."""

    def __init__(self) -> None:
        self.now = datetime.now(UTC)

    def advance_to(self, moment: datetime) -> None:
        self.now = moment


class _ClockedCodeStore(IDevicePairingCodeStore):
    """In-memory pairing-code store with a real TTL, on a test-driven clock.

    Faithful about the two things the routes depend on: a code is redeemable
    exactly once (``consume`` deletes), and it stops being redeemable at the
    instant ``issue`` reported — which is the moment the API hands the client as
    ``expires_at``. Keyed by the raw code rather than by its digest: the
    pseudonymisation of the *keys* is a property of the Redis store and is
    asserted there.
    """

    def __init__(self, clock: _Clock, ttl_seconds: int) -> None:
        self._clock = clock
        self._ttl_seconds = ttl_seconds
        self._records: dict[str, tuple[DevicePairingRecord, datetime]] = {}

    def issue(self, code: str, user_key: str) -> datetime:
        issued_at = self._clock.now
        expires_at = issued_at + timedelta(seconds=self._ttl_seconds)
        self._records[code] = (DevicePairingRecord(user_key=user_key, issued_at=issued_at), expires_at)
        return expires_at

    def consume(self, code: str) -> DevicePairingRecord | None:
        entry = self._records.get(code)
        if entry is None:
            return None
        record, expires_at = entry
        if self._clock.now >= expires_at:
            # Redis would have dropped the key; dropping it here keeps the two
            # stores answering alike for a code that is asked for twice.
            del self._records[code]
            return None
        del self._records[code]
        return record

    def holds(self, code: str) -> bool:
        """Whether the code is still on file — used only to sharpen a message."""
        return code in self._records


class _MemoryRefreshTokenRepository(IRefreshTokenRepository):
    """A session store that actually forgets a revoked token.

    ``get_by_hash`` filtering revoked documents mirrors the AQL filter in
    ``ArangoRefreshTokenRepository``; without it "the rotated token is dead" and
    "the replay minted no session" are unprovable.
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


class _FakeTenantService:
    """Slug → tenant → membership, the two lookups the tenant gate makes.

    Mutable on purpose: revoking a membership mid-test is how "authorisation is
    re-decided per request" is told apart from "authorisation was decided once,
    when the token was minted".
    """

    def __init__(self) -> None:
        self._tenants = {t.slug: t for t in (_OWNER_TENANT, _STRANGER_TENANT)}
        self._memberships: dict[tuple[str, str], Membership] = {
            (_OWNER, _OWNER_TENANT.key or ""): Membership(
                user_key=_OWNER,
                tenant_key=_OWNER_TENANT.key or "",
                role=TenantRole.LEAD,
            ),
            (_STRANGER, _STRANGER_TENANT.key or ""): Membership(
                user_key=_STRANGER,
                tenant_key=_STRANGER_TENANT.key or "",
                role=TenantRole.LEAD,
            ),
        }

    def get_tenant_by_slug(self, slug: str) -> Tenant:
        tenant = self._tenants.get(slug)
        if tenant is None:
            raise NotFoundError("Tenant", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> Membership | None:
        return self._memberships.get((user_key, tenant_key))

    def revoke_membership(self, user_key: str, tenant_key: str) -> None:
        removed = self._memberships.pop((user_key, tenant_key), None)
        assert removed is not None, f"no membership of {user_key} in {tenant_key} to revoke — the setup is wrong"


@dataclass
class _World:
    """The application under test plus handles on everything it was given."""

    client: TestClient
    clock: _Clock
    code_store: _ClockedCodeStore
    sessions: _MemoryRefreshTokenRepository
    tenants: _FakeTenantService
    sites: MagicMock
    token_engine: TokenEngine

    # ── talking to the surface ──────────────────────────────────────

    def bearer(self, user_key: str) -> dict[str, str]:
        """A freshly minted access token for ``user_key``, as a header.

        Setup only — the tokens the *assertions* are about are the ones the
        redeem endpoint returns.
        """
        pair = self.token_engine.create_access_token(user_key=user_key)
        return {"authorization": f"Bearer {pair.access_token}"}

    def issue(self, user_key: str = _OWNER) -> httpx.Response:
        self.client.cookies.clear()
        return self.client.post(_ISSUE_PATH, headers=self.bearer(user_key))

    def issue_code(self, user_key: str = _OWNER) -> tuple[str, datetime]:
        response = self.issue(user_key)
        assert response.status_code == 201, response.text
        body = response.json()
        return body["code"], datetime.fromisoformat(body["expires_at"])

    def redeem(
        self,
        code: str,
        ip: str = _ATTACKER_IP,
        headers: dict[str, str] | None = None,
        **body: object,
    ) -> httpx.Response:
        self.client.cookies.clear()
        return self.client.post(
            _REDEEM_PATH,
            json={"code": code, **body},
            headers={"x-forwarded-for": ip, **(headers or {})},
        )

    def pair(self, user_key: str = _OWNER, ip: str = _CLEAN_IP) -> dict[str, str]:
        """Run the whole flow and return the token pair a phone would hold."""
        code, _ = self.issue_code(user_key)
        response = self.redeem(code, ip=ip)
        assert response.status_code == 200, response.text
        return response.json()

    def refresh_via_body(self, raw_refresh_token: str) -> httpx.Response:
        self.client.cookies.clear()
        return self.client.post(_REFRESH_PATH, json={"refresh_token": raw_refresh_token})

    def refresh_via_cookie(self, raw_refresh_token: str) -> httpx.Response:
        self.client.cookies.clear()
        self.client.cookies.set("kp_refresh", raw_refresh_token)
        self.client.cookies.set("csrf_token", _CSRF_VALUE)
        return self.client.post(_REFRESH_PATH, headers={"x-csrf-token": _CSRF_VALUE})

    def list_sessions(self, access_token: str) -> list[dict[str, Any]]:
        self.client.cookies.clear()
        response = self.client.get(_SESSIONS_PATH, headers={"authorization": f"Bearer {access_token}"})
        assert response.status_code == 200, response.text
        return response.json()

    def read_sites(self, tenant_slug: str, access_token: str) -> httpx.Response:
        self.client.cookies.clear()
        return self.client.get(
            f"/api/v1/t/{tenant_slug}/sites",
            headers={"authorization": f"Bearer {access_token}"},
        )


@contextmanager
def _world(platform_leads: frozenset[str] = frozenset()) -> Iterator[_World]:
    """Build the app with every collaborator this module drives.

    ``platform_leads`` decides who holds a LEAD membership in the ``platform``
    tenant, which is the single input ``_create_tokens`` turns into the
    ``is_platform_admin`` claim.
    """
    users = {
        _OWNER: User(_key=_OWNER, email="owner@example.org", display_name="Code Owner", is_active=True),
        _STRANGER: User(_key=_STRANGER, email="stranger@example.org", display_name="Stranger", is_active=True),
    }
    user_repo = MagicMock()
    user_repo.get_by_key.side_effect = users.get

    clock = _Clock()
    code_store = _ClockedCodeStore(clock, settings.device_pairing_ttl_seconds)
    tenants = _FakeTenantService()
    token_engine = TokenEngine(_SECRET, "HS256")

    def _get_membership(user_key: str, tenant_key: str) -> Membership | None:
        """``platform`` is not a row in the fake — it is the ``is_platform_admin`` input."""
        if tenant_key == "platform":
            if user_key in platform_leads:
                return Membership(user_key=user_key, tenant_key="platform", role=TenantRole.LEAD)
            return None
        return _FakeTenantService.get_membership(tenants, user_key, tenant_key)

    tenants.get_membership = _get_membership  # type: ignore[method-assign]

    sessions = _MemoryRefreshTokenRepository()
    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=sessions,
        password_engine=PasswordEngine(),
        token_engine=token_engine,
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=tenants,
        device_pairing_code_store=code_store,
        # Fresh per world: the lockout counter is process state, and a shared one
        # would let a lockout driven by one test decide another test's answer.
        device_pairing_throttle_store=MemoryDevicePairingThrottleStore(),
    )

    sites = MagicMock()
    sites.list_sites.return_value = (
        [Site(_key="site-owner", tenant_key=_OWNER_TENANT.key or "", name=_OWNER_SITE_NAME)],
        1,
    )
    sites.get_water_warnings.return_value = []

    # The real provider: every token this module asserts about is verified by
    # production code (signature, expiry, ``type``) before the app honours it.
    auth_provider = FullAuthProvider(token_engine, user_repo, service)

    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_auth_service] = lambda: service
        app.dependency_overrides[get_auth_provider] = lambda: auth_provider
        app.dependency_overrides[get_tenant_service] = lambda: tenants
        app.dependency_overrides[get_site_service] = lambda: sites
        try:
            yield _World(
                client=TestClient(app, raise_server_exceptions=False),
                clock=clock,
                code_store=code_store,
                sessions=sessions,
                tenants=tenants,
                sites=sites,
                token_engine=token_engine,
            )
        finally:
            for dependency in (get_auth_service, get_auth_provider, get_tenant_service, get_site_service):
                app.dependency_overrides.pop(dependency, None)


@pytest.fixture
def world() -> Iterator[_World]:
    with _world() as built:
        yield built


def _jwt_claims(access_token: str) -> dict[str, Any]:
    """Read the claims straight out of the token's payload segment.

    Decoded here rather than through ``TokenEngine``: comparing a token against
    something the same engine produced can pass while both sides are wrong about
    which account was signed in.
    """
    payload = access_token.split(".")[1]
    padded = payload + "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _refusal(response: httpx.Response) -> tuple[int, dict[str, Any]]:
    """Status plus the part of an error body that carries information.

    ``error_id`` and ``timestamp`` differ between any two responses and say
    nothing about the request, so comparing them would make every comparison
    fail for the wrong reason.
    """
    body = {k: v for k, v in response.json().items() if k not in {"error_id", "timestamp"}}
    return response.status_code, body


# ── 1. Replay ──────────────────────────────────────────────────────


class TestReplay:
    def test_a_replayed_code_mints_no_second_session_and_answers_like_an_unknown_code(
        self,
        world: _World,
    ) -> None:
        """Single use, asserted on the *effect* rather than on the status code.

        ``test_auth_device_pairing_api.py`` already compares the replay's answer
        with an unknown code's. What it cannot see is the persisted side: a
        service that read the record without deleting it would answer 401 for
        the *second* request only because the throttle happened to fire, or
        would answer 200 and hand out a second, independently revocable session
        for one scanned QR. So the session list — the place the owner revokes
        from — is the assertion, and the answer comparison rides along.
        """
        code, _ = world.issue_code()
        first = world.redeem(code)
        assert first.status_code == 200, first.text

        replayed = world.redeem(code)
        unknown = world.redeem("a-code-nobody-ever-issued")

        assert replayed.status_code == 401, replayed.text
        assert _refusal(replayed) == _refusal(unknown), "a replay is distinguishable from an unknown code"
        assert set(replayed.json()) & {"access_token", "refresh_token"} == set()
        sessions = world.list_sessions(first.json()["access_token"])
        assert len(sessions) == 1, f"one scanned code produced {len(sessions)} sessions"


# ── 2. Expiry ──────────────────────────────────────────────────────


class TestExpiry:
    def test_a_code_is_still_redeemable_one_second_before_its_advertised_expiry(self, world: _World) -> None:
        """The client's countdown must be telling the truth.

        ``expires_at`` is what the dialog counts down and what the phone decides
        by. If the handler ever advertised a window wider than the store's TTL,
        every assertion in the module below would still pass while real codes
        died mid-countdown — so the advertised instant, not a hard-coded 90, is
        what the clock is moved against.
        """
        code, expires_at = world.issue_code()

        world.clock.advance_to(expires_at - timedelta(seconds=1))

        assert world.redeem(code).status_code == 200

    def test_a_code_past_its_advertised_expiry_is_refused_like_an_unknown_code(self, world: _World) -> None:
        """No token pair, and no oracle either — expired and never-existed are
        one answer, so a scanner cannot use the status code to learn that the
        code it guessed was real a minute ago."""
        code, expires_at = world.issue_code()

        world.clock.advance_to(expires_at + timedelta(seconds=1))
        expired = world.redeem(code)
        unknown = world.redeem("a-code-nobody-ever-issued")

        assert expired.status_code == 401, expired.text
        assert _refusal(expired) == _refusal(unknown)
        assert set(expired.json()) & {"access_token", "refresh_token"} == set()
        assert world.sessions.list_active_for_user(_OWNER) == []


# ── 3. Brute force ─────────────────────────────────────────────────


class TestBruteForce:
    def test_a_locked_address_cannot_burn_the_valid_code_it_holds(self, world: _World) -> None:
        """The lockout has to run *before* the store, not merely before the answer.

        A guard that refuses after consuming the code is the worse of both
        worlds: the attacker still gets their 423, and the owner's live code is
        gone — a denial of service on pairing that costs five wrong guesses. The
        third act is what proves the ordering: the very same code, presented
        from an address that was never locked, still works. It also pins that
        the counter is per source address, which only holds because the throttle
        buckets on ``resolve_client_ip`` rather than on the ingress peer.
        """
        code, _ = world.issue_code()

        refusals = [world.redeem("wrong-code", ip=_ATTACKER_IP).status_code for _ in range(MAX_ATTEMPTS)]
        locked_out = world.redeem(code, ip=_ATTACKER_IP)

        assert refusals == [401] * MAX_ATTEMPTS, refusals
        assert locked_out.status_code == 423, locked_out.text
        assert world.code_store.holds(code), "the locked-out attempt consumed the code it was refused for"
        survivor = world.redeem(code, ip=_CLEAN_IP)
        assert survivor.status_code == 200, survivor.text
        assert _jwt_claims(survivor.json()["access_token"])["sub"] == _OWNER


# ── 4. Rate limit ──────────────────────────────────────────────────


class TestRateLimit:
    def test_a_valid_code_submitted_while_rate_limited_is_refused_and_not_consumed(self, world: _World) -> None:
        """The per-minute budget is a shield, not just a status code.

        ``test_auth_device_pairing_api.py`` pins that the budget exists and is
        the dedicated one. What matters adversarially is that a request refused
        by it never reaches the store: otherwise a flood could burn a victim's
        live code (or, with a lucky guess, spend it) at no cost, and the limit
        would protect the server while sacrificing the feature. The 429 request
        below carries the *valid* code, and the code is still redeemable
        afterwards — from a clean address, because the flood also locked the one
        it came from.
        """
        limit = int(settings.rate_limit_device_pairing_redeem.split("/")[0])
        code, _ = world.issue_code()

        spent = [world.redeem("wrong-code", ip=_ATTACKER_IP).status_code for _ in range(limit)]
        rate_limited = world.redeem(code, ip=_ATTACKER_IP)

        assert 429 not in spent, spent
        assert rate_limited.status_code == 429, rate_limited.text
        # The minute window elapses. Resetting the counter is what its expiry
        # does; nothing else about the world changes.
        limiter.reset()
        survivor = world.redeem(code, ip=_CLEAN_IP)
        assert survivor.status_code == 200, survivor.text


# ── 5. Tenant integrity (REQ-024) ──────────────────────────────────


class TestTenantIntegrity:
    def test_a_paired_token_reaches_the_issuing_users_own_tenant(self, world: _World) -> None:
        """The positive half, without which the refusals below prove nothing: a
        token that reached *no* tenant would satisfy every negative assertion in
        this class."""
        pair = world.pair(_OWNER)

        response = world.read_sites(_OWNER_TENANT.slug, pair["access_token"])

        assert response.status_code == 200, response.text
        assert [site["name"] for site in response.json()] == [_OWNER_SITE_NAME]
        assert world.sites.list_sites.call_args.kwargs["tenant_key"] == _OWNER_TENANT.key

    def test_a_paired_token_is_refused_by_a_tenant_its_user_is_no_member_of(self, world: _World) -> None:
        """The scope a paired phone carries is the issuing account's, and nothing
        else. Asserted together with the service never being reached, so a
        refusal that happened only inside the repository — i.e. one row-level
        filter away from a leak — would not pass for a gate."""
        pair = world.pair(_OWNER)
        world.sites.list_sites.reset_mock()

        response = world.read_sites(_STRANGER_TENANT.slug, pair["access_token"])

        assert response.status_code == 403, response.text
        assert world.sites.list_sites.call_count == 0, "the tenant gate let the request through to the service"

    def test_membership_is_resolved_per_request_not_frozen_into_the_paired_token(self, world: _World) -> None:
        """A paired device holds its access token for 15 minutes and its refresh
        token for 30 days. If the token carried the memberships it was minted
        with, removing someone from a community garden would leave their phone
        reading it until the token expired — and after a rotation, indefinitely.
        The first read proves the token *did* work before the change, so the
        second one cannot pass for the wrong reason."""
        pair = world.pair(_OWNER)
        assert world.read_sites(_OWNER_TENANT.slug, pair["access_token"]).status_code == 200

        world.tenants.revoke_membership(_OWNER, _OWNER_TENANT.key or "")

        assert world.read_sites(_OWNER_TENANT.slug, pair["access_token"]).status_code == 403

    def test_a_paired_token_claims_no_platform_admin_for_an_ordinary_account(self, world: _World) -> None:
        claims = _jwt_claims(world.pair(_OWNER)["access_token"])

        assert claims["is_platform_admin"] is False
        assert claims["tenant_roles"] == {}, "memberships must not be baked into the token"

    def test_a_paired_token_carries_the_platform_admin_standing_the_account_has(self) -> None:
        """The other direction, and the reason the assertion above is not
        vacuous: the claim tracks the account's real standing, so ``False`` above
        is a fact about that account rather than a constant."""
        with _world(platform_leads=frozenset({_OWNER})) as elevated:
            claims = _jwt_claims(elevated.pair(_OWNER)["access_token"])

        assert claims["is_platform_admin"] is True


# ── 6. Log hygiene ─────────────────────────────────────────────────


class TestLogHygiene:
    def test_no_log_record_carries_the_pairing_code_or_a_raw_token(self, world: _World) -> None:
        """Captured across the whole life of the credentials, at the HTTP layer.

        The service-level version of this lives in the P3 unit tests; what it
        cannot see is anything the *rest* of the request path logs — middleware,
        the exception handlers on the refusal paths, and the rotation the phone
        performs afterwards. Every branch a code can take is walked here (issued,
        redeemed, replayed, mistyped) plus two rotations, and every secret that
        existed during the capture is searched for, prefixes included: an
        8-character head of a credential in a line that outlives it by months
        shrinks the search space of the credential itself.
        """
        with structlog.testing.capture_logs() as logs:
            code, _ = world.issue_code()
            redeemed = world.redeem(code, ip=_CLEAN_IP)
            assert redeemed.status_code == 200, redeemed.text
            assert world.redeem(code, ip=_CLEAN_IP).status_code == 401
            assert world.redeem("a-code-nobody-ever-issued", ip=_CLEAN_IP).status_code == 401
            rotated = world.refresh_via_body(redeemed.json()["refresh_token"])
            assert rotated.status_code == 200, rotated.text

        assert logs, "no log records captured — every assertion below would be vacuous"
        rendered = json.dumps(logs, default=str)
        secrets = {
            "pairing code": code,
            "redeemed refresh token": redeemed.json()["refresh_token"],
            "redeemed access token": redeemed.json()["access_token"],
            "rotated refresh token": rotated.json()["refresh_token"],
        }
        for label, secret in secrets.items():
            assert secret not in rendered, f"the {label} was written to a log record"
            assert secret[:8] not in rendered, f"a prefix of the {label} was written to a log record"


# ── 7. Cross-user containment ──────────────────────────────────────


class TestCrossUserContainment:
    def test_a_stranger_redeeming_a_code_gets_a_session_on_the_issuers_account_only(self, world: _World) -> None:
        """Whoever scans the QR gets the issuer's session — and *only* that.

        The redeem route is public, so the adversary worth modelling is not an
        anonymous one but a signed-in user who got hold of somebody else's code:
        they can present their own bearer token, name themselves in the body, and
        do both at once. The identity of the minted pair still comes from the
        record the code was stored under. ``test_auth_device_pairing_api.py``
        pins that the request *schema* has no identity field; this pins the
        token, the session and the reach of both — which is what would actually
        be lost if the handler ever consulted the caller.
        """
        code, _ = world.issue_code(_OWNER)

        response = world.redeem(
            code,
            ip=_CLEAN_IP,
            headers=world.bearer(_STRANGER),
            user_key=_STRANGER,
            email="stranger@example.org",
        )

        assert response.status_code == 200, response.text
        minted = response.json()
        assert _jwt_claims(minted["access_token"])["sub"] == _OWNER
        # The session is the owner's to see and to revoke, and the stranger's
        # own account gained nothing.
        assert len(world.list_sessions(minted["access_token"])) == 1
        assert world.list_sessions(world.bearer(_STRANGER)["authorization"].removeprefix("Bearer ")) == []
        assert world.read_sites(_OWNER_TENANT.slug, minted["access_token"]).status_code == 200
        assert world.read_sites(_STRANGER_TENANT.slug, minted["access_token"]).status_code == 403


# ── 8. The fuzz surface on /auth/refresh (P6 hand-over) ────────────


class TestRefreshBodyFuzz:
    """Non-JSON bodies on the endpoint that now parses one.

    P6 turned ``/auth/refresh`` from "body ignored" into "body parsed", and
    pinned the shapes a browser sends (absent, empty, ``null``). The shapes an
    *attacker* sends are these: a form encoding — the one content type a
    cross-site form POST can produce without a preflight — plain text, and JSON
    that does not parse. Two things must hold for each: the request is refused at
    the boundary (422, not 403 and certainly not 200), and the ambient cookie it
    rode in on is still unspent afterwards. The second assertion is the load-
    bearing one: a handler that fell back to the cookie when the body failed to
    parse would rotate the victim's session with no CSRF header in sight, and the
    422 alone would not notice.
    """

    @pytest.mark.parametrize(
        ("content", "content_type"),
        [
            pytest.param(b"refresh_token=smuggled", "application/x-www-form-urlencoded", id="form-encoded"),
            pytest.param(b"refresh_token: smuggled", "text/plain", id="text-plain"),
            pytest.param(b'{"refresh_token": ', "application/json", id="truncated-json"),
            pytest.param(b'["refresh_token"]', "application/json", id="json-array"),
        ],
    )
    def test_a_non_json_body_is_refused_at_the_boundary_without_spending_the_cookie(
        self,
        world: _World,
        content: bytes,
        content_type: str,
    ) -> None:
        cookie_token = world.pair(_OWNER)["refresh_token"]
        world.client.cookies.clear()
        world.client.cookies.set("kp_refresh", cookie_token)
        world.client.cookies.set("csrf_token", _CSRF_VALUE)

        # No ``X-CSRF-Token``: the shape a forged cross-site request has.
        refused = world.client.post(_REFRESH_PATH, content=content, headers={"content-type": content_type})

        assert refused.status_code == 422, refused.text
        assert refused.headers.get("set-cookie") is None
        assert world.refresh_via_cookie(cookie_token).status_code == 200, "the malformed request spent the cookie"
