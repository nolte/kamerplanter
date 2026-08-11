"""QR device pairing must mint an ordinary session and guess like an ordinary lock (#1118).

``AuthService.create_device_pairing`` / ``redeem_device_pairing`` (REQ-023) turn
a 90-second QR code into the *existing* token pair. The properties worth pinning
are the ones a later refactor could remove without any endpoint changing shape:

* the code is a **credential**, not an identifier — drawn from ``secrets`` with a
  256-bit budget and no monotonic component, so it cannot be derived;
* redemption goes through the **existing** ``_create_tokens``: no new token
  type, no new claim, and therefore nothing that needs its own revocation path;
* the redeemed session resolves the **same** tenant memberships a normal login
  resolves (REQ-024) — nothing added, nothing dropped;
* every miss answers **identically**: used, expired and never-existed are one
  error, or the endpoint becomes an oracle that confirms a guessed code was real;
* the code is bound to its **issuer**, and redemption has no parameter through
  which a caller could name a different account;
* the lockout is **not decorative** — past the threshold the code store is never
  reached at all;
* the **raw code never reaches a log record**, on any of the three audit events.

**Delegated from P2.** ``test_locked_out_ip_never_reaches_the_code_store`` lives
here because the ordering it asserts — throttle before store — exists only in
``redeem_device_pairing``. The store-level precondition (past the threshold,
engine + store answer "not allowed") is proven in
``tests/unit/data_access/external/test_device_pairing_throttle.py``, whose module
docstring points here.

The code store under test is the **real** ``RedisDevicePairingCodeStore`` driven
by a fake Redis that honours ``ex`` against a virtual clock, so single-use and
expiry are proven through production code rather than through a dict that a test
author decided behaves like Redis.
"""

from __future__ import annotations

import base64
import inspect
import json
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest
import structlog

from app.common.enums import TenantRole
from app.common.exceptions import (
    AccountLockedError,
    InvalidTokenError,
    UnauthorizedError,
    ValidationError,
)
from app.data_access.external.device_pairing_throttle import (
    DEFAULT_DEVICE_PAIRING_THROTTLE_STORE,
    MemoryDevicePairingThrottleStore,
)
from app.data_access.external.redis_device_pairing import RedisDevicePairingCodeStore
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import RefreshToken, TokenPair
from app.domain.models.user import User
from app.domain.services import auth_service as auth_service_module
from app.domain.services.auth_service import AuthService

USER_KEY = "u-pairing-owner"
USER_EMAIL = "owner@example.com"
PASSWORD = "device-pairing-password-2024"
IP = "203.0.113.7"
OTHER_IP = "198.51.100.9"
USER_AGENT = "Kamerplanter/1.0 (Android 15)"
SECRET_KEY = "test-secret-key-for-unit-tests-32chars!"

# One bcrypt round costs ~100 ms; the password-carrying tests only need *a*
# valid hash, so it is computed once for the module rather than per fixture.
_PASSWORD_HASH = PasswordEngine().hash_password(PASSWORD)


# ── Fake Redis (honours ``ex`` against a virtual clock) ──────────────────


class _Clock:
    """Virtual seconds, so expiry is tested without sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _FakePipeline:
    """Queues commands and applies them only in :meth:`execute`, like redis-py."""

    def __init__(self, redis: _FakeRedis) -> None:
        self._redis = redis
        self._commands: list[tuple[str, str]] = []

    def get(self, name: str) -> _FakePipeline:
        self._commands.append(("get", name))
        return self

    def delete(self, *names: str) -> _FakePipeline:
        self._commands.extend(("delete", name) for name in names)
        return self

    def execute(self) -> list[Any]:
        results: list[Any] = []
        for operation, name in self._commands:
            if operation == "get":
                results.append(self._redis.read(name))
            else:
                results.append(1 if self._redis.drop(name) else 0)
        self._commands = []
        return results


class _FakeRedis:
    """The three behaviours the store depends on: ``SET`` with a TTL, and a
    pipelined ``GET``+``DEL``. A key past its TTL reads as missing, exactly as
    Redis answers — which is what makes the expiry test say something."""

    def __init__(self, clock: _Clock) -> None:
        self._clock = clock
        self._values: dict[str, tuple[str, float | None]] = {}

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        expires_at = None if ex is None else self._clock.now + ex
        self._values[name] = (value, expires_at)

    def read(self, name: str) -> str | None:
        entry = self._values.get(name)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at <= self._clock.now:
            del self._values[name]
            return None
        return value

    def drop(self, name: str) -> bool:
        return self._values.pop(name, None) is not None

    def pipeline(self) -> _FakePipeline:
        return _FakePipeline(self)


# ── Harness ─────────────────────────────────────────────────────────────


def _make_user(key: str = USER_KEY, is_active: bool = True) -> User:
    return User(
        _key=key,
        email=USER_EMAIL,
        display_name="Pairing Owner",
        password_hash=_PASSWORD_HASH,
        email_verified=True,
        is_active=is_active,
    )


@dataclass
class _Harness:
    service: AuthService
    clock: _Clock
    code_store: Any
    throttle_store: Any
    user_repo: MagicMock
    refresh_token_repo: MagicMock
    tenant_service: MagicMock | None
    token_engine: TokenEngine
    created_tokens: list[RefreshToken] = field(default_factory=list)


def _make_harness(
    *,
    user: User | None = None,
    code_store: Any = None,
    throttle_store: Any = None,
    tenant_service: MagicMock | None = None,
    ttl_seconds: int = 90,
) -> _Harness:
    resolved_user = _make_user() if user is None else user
    clock = _Clock()
    store = code_store
    if store is None:
        store = RedisDevicePairingCodeStore(_FakeRedis(clock), ttl_seconds=ttl_seconds)
    throttle = MemoryDevicePairingThrottleStore() if throttle_store is None else throttle_store

    user_repo = MagicMock()
    user_repo.get_by_key.return_value = resolved_user
    user_repo.get_by_email.return_value = resolved_user

    created: list[RefreshToken] = []

    def _capture(token: RefreshToken) -> RefreshToken:
        created.append(token)
        return token

    refresh_token_repo = MagicMock()
    refresh_token_repo.create.side_effect = _capture

    token_engine = TokenEngine(SECRET_KEY, "HS256")
    service = AuthService(
        user_repo=user_repo,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=refresh_token_repo,
        password_engine=PasswordEngine(),
        token_engine=token_engine,
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=tenant_service,
        device_pairing_code_store=store,
        device_pairing_throttle_store=throttle,
    )
    return _Harness(
        service=service,
        clock=clock,
        code_store=store,
        throttle_store=throttle,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        tenant_service=tenant_service,
        token_engine=token_engine,
        created_tokens=created,
    )


def _fail_redemptions(harness: _Harness, times: int, ip_address: str = IP) -> None:
    for _ in range(times):
        with pytest.raises(InvalidTokenError):
            harness.service.redeem_device_pairing("never-issued-code", ip_address=ip_address)


# ── Issuance ────────────────────────────────────────────────────────────


class TestCreateDevicePairing:
    def test_code_is_drawn_from_secrets_with_a_256_bit_budget(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``random`` here would make the code derivable from other draws."""
        requested: list[int | None] = []

        def _fake_token_urlsafe(nbytes: int | None = None) -> str:
            requested.append(nbytes)
            return "patched-pairing-code"

        monkeypatch.setattr(auth_service_module.secrets, "token_urlsafe", _fake_token_urlsafe)
        harness = _make_harness()

        code, _ = harness.service.create_device_pairing(USER_KEY)

        assert code == "patched-pairing-code"
        assert requested == [32]

    def test_a_thousand_draws_are_unique_and_carry_no_monotonic_component(self) -> None:
        """A counter or a timestamp in the code would let one draw predict the next."""
        harness = _make_harness()

        codes = [harness.service.create_device_pairing(USER_KEY)[0] for _ in range(1000)]

        assert len(set(codes)) == 1000
        # Constant length: a growing counter or an encoded ordinal would not be.
        assert len({len(code) for code in codes}) == 1
        # Not in generation order: a time- or counter-derived code sorts as it
        # was drawn. This is the assertion that "unique" alone does not make.
        assert codes != sorted(codes)
        # A shared time prefix would collapse the leading characters into a
        # handful of buckets; independent draws keep them all distinct.
        assert len({code[:6] for code in codes}) == 1000

    def test_returns_the_expiry_the_store_computed(self) -> None:
        harness = _make_harness(ttl_seconds=90)

        code, expires_at = harness.service.create_device_pairing(USER_KEY)

        record = harness.code_store.consume(code)
        assert record is not None
        assert (expires_at - record.issued_at).total_seconds() == pytest.approx(90, abs=1)

    def test_code_is_bound_to_the_issuing_user_in_the_store(self) -> None:
        harness = _make_harness()

        code, _ = harness.service.create_device_pairing("u-someone-else")

        record = harness.code_store.consume(code)
        assert record is not None
        assert record.user_key == "u-someone-else"

    def test_a_store_failure_is_not_swallowed(self) -> None:
        """Swallowing it would show the user a QR code that can never redeem."""
        broken = MagicMock()
        broken.issue.side_effect = ConnectionError("redis is down")
        harness = _make_harness(code_store=broken)

        with pytest.raises(ConnectionError):
            harness.service.create_device_pairing(USER_KEY)

    def test_refuses_when_no_store_is_configured(self) -> None:
        service = AuthService(
            user_repo=MagicMock(),
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine(SECRET_KEY, "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="http://localhost:5173",
        )

        with pytest.raises(ValidationError) as excinfo:
            service.create_device_pairing(USER_KEY)

        assert excinfo.value.status_code == 422


# ── Redemption yields the ordinary session ──────────────────────────────


def _decode(harness: _Harness, pair: TokenPair) -> dict[str, Any]:
    """Return the token's **raw** claims, not the ``TokenPayload`` projection.

    ``decode_access_token`` builds a fixed-field model, so an extra claim minted
    into the token would be silently dropped on the way out and a comparison of
    projected fields would pass no matter what was added. Reading the payload
    segment is what makes "no new claim" an assertion rather than a wish; the
    projected decode still runs first, so an unverifiable token fails here too.
    """
    harness.token_engine.decode_access_token(pair.access_token)
    segment = pair.access_token.split(".")[1]
    padded = segment + "=" * (-len(segment) % 4)
    claims: dict[str, Any] = json.loads(base64.urlsafe_b64decode(padded))
    return claims


class TestRedeemedPairIsTheLoginPair:
    def test_shape_is_identical_to_a_login_local_pair(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        login_pair, login_raw, login_persistent = harness.service.login_local(
            USER_EMAIL, PASSWORD, USER_AGENT, IP, remember_me=True
        )
        redeem_pair, redeem_raw, redeem_persistent = harness.service.redeem_device_pairing(
            code, user_agent=USER_AGENT, ip_address=IP
        )

        assert isinstance(redeem_pair, TokenPair)
        assert redeem_pair.token_type == login_pair.token_type
        assert redeem_pair.expires_in == login_pair.expires_in
        assert redeem_persistent == login_persistent is True
        assert isinstance(redeem_raw, str) and len(redeem_raw) == len(login_raw)

    def test_no_new_token_type_and_no_new_claim(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        login_claims = _decode(harness, harness.service.login_local(USER_EMAIL, PASSWORD)[0])
        redeem_claims = _decode(harness, harness.service.redeem_device_pairing(code)[0])

        assert set(redeem_claims) == set(login_claims)
        assert redeem_claims["type"] == login_claims["type"] == "access"
        assert redeem_claims["sub"] == login_claims["sub"] == USER_KEY
        assert redeem_claims["is_platform_admin"] == login_claims["is_platform_admin"]

    def test_session_document_has_the_same_fields_a_login_session_has(self) -> None:
        """A paired device must be an ordinary row in ``list_sessions``."""
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        harness.service.login_local(USER_EMAIL, PASSWORD, USER_AGENT, IP, remember_me=True)
        harness.service.redeem_device_pairing(code, user_agent=USER_AGENT, ip_address=IP)

        login_token, redeem_token = harness.created_tokens
        assert set(redeem_token.model_dump()) == set(login_token.model_dump())
        assert redeem_token.user_key == login_token.user_key == USER_KEY
        assert redeem_token.user_agent == USER_AGENT
        assert redeem_token.ip_address == IP
        assert redeem_token.is_persistent is True

    def test_redeemed_session_resolves_the_same_tenant_memberships(self) -> None:
        """REQ-024 — nothing added, nothing dropped relative to a normal login."""
        membership = MagicMock(is_active=True, role=TenantRole.LEAD)
        tenant_service = MagicMock()
        tenant_service.get_membership.return_value = membership
        harness = _make_harness(tenant_service=tenant_service)
        code, _ = harness.service.create_device_pairing(USER_KEY)

        login_claims = _decode(harness, harness.service.login_local(USER_EMAIL, PASSWORD)[0])
        login_lookups = list(tenant_service.get_membership.call_args_list)
        tenant_service.get_membership.reset_mock()

        redeem_claims = _decode(harness, harness.service.redeem_device_pairing(code)[0])
        redeem_lookups = list(tenant_service.get_membership.call_args_list)

        assert redeem_lookups == login_lookups
        assert redeem_claims["tenant_roles"] == login_claims["tenant_roles"]
        assert redeem_claims["is_platform_admin"] == login_claims["is_platform_admin"] is True

    def test_an_inactive_account_gets_no_session(self) -> None:
        harness = _make_harness(user=_make_user(is_active=False))
        code, _ = harness.service.create_device_pairing(USER_KEY)

        with pytest.raises(UnauthorizedError):
            harness.service.redeem_device_pairing(code, ip_address=IP)

        assert harness.refresh_token_repo.create.call_count == 0


# ── One error for every miss ────────────────────────────────────────────


def _error_signature(excinfo: pytest.ExceptionInfo[Any]) -> tuple[Any, ...]:
    error = excinfo.value
    return (type(error), error.status_code, error.error_code, error.message)


class TestNoOracleOnAMiss:
    def test_second_redemption_answers_exactly_like_an_unknown_code(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)
        harness.service.redeem_device_pairing(code, ip_address=IP)

        with pytest.raises(InvalidTokenError) as replayed:
            harness.service.redeem_device_pairing(code, ip_address=IP)
        with pytest.raises(InvalidTokenError) as unknown:
            harness.service.redeem_device_pairing("never-issued-code", ip_address=IP)

        assert _error_signature(replayed) == _error_signature(unknown)

    def test_expired_code_answers_exactly_like_an_unknown_code(self) -> None:
        harness = _make_harness(ttl_seconds=90)
        code, _ = harness.service.create_device_pairing(USER_KEY)

        harness.clock.advance(91)

        with pytest.raises(InvalidTokenError) as expired:
            harness.service.redeem_device_pairing(code, ip_address=IP)
        with pytest.raises(InvalidTokenError) as unknown:
            harness.service.redeem_device_pairing("never-issued-code", ip_address=IP)

        assert _error_signature(expired) == _error_signature(unknown)

    def test_a_code_still_inside_its_ttl_does_redeem(self) -> None:
        """Guards the expiry test above: without this, a store that expired
        everything immediately would make it pass for the wrong reason."""
        harness = _make_harness(ttl_seconds=90)
        code, _ = harness.service.create_device_pairing(USER_KEY)

        harness.clock.advance(89)

        pair, _, _ = harness.service.redeem_device_pairing(code, ip_address=IP)
        assert pair.access_token

    def test_a_missed_redemption_mints_nothing(self) -> None:
        harness = _make_harness()

        with pytest.raises(InvalidTokenError):
            harness.service.redeem_device_pairing("never-issued-code", ip_address=IP)

        assert harness.refresh_token_repo.create.call_count == 0


# ── The code carries the identity ───────────────────────────────────────


class TestCodeIsBoundToItsIssuer:
    def test_redemption_has_no_caller_supplied_identity_parameter(self) -> None:
        """An absence check: an ``email``/``user_key`` argument here would be a
        second, weaker path to an account, and no behavioural test can see a
        parameter that a future edit adds but nothing yet passes."""
        parameters = set(inspect.signature(AuthService.redeem_device_pairing).parameters)

        assert parameters == {"self", "code", "user_agent", "ip_address", "device_name"}

    def test_the_account_is_read_from_the_stored_record(self) -> None:
        harness = _make_harness(user=_make_user(key="u-issuer"))
        code, _ = harness.service.create_device_pairing("u-issuer")

        harness.service.redeem_device_pairing(code, ip_address=IP)

        harness.user_repo.get_by_key.assert_called_once_with("u-issuer")
        assert harness.user_repo.get_by_email.call_count == 0


# ── The lockout is not decorative ───────────────────────────────────────


class TestRedemptionLockout:
    def test_threshold_reached_raises_account_locked_with_remaining_minutes(self) -> None:
        harness = _make_harness()
        _fail_redemptions(harness, MAX_ATTEMPTS)

        with pytest.raises(AccountLockedError) as excinfo:
            harness.service.redeem_device_pairing("another-guess", ip_address=IP)

        # Mirrors what ``login_local`` answers under the same conditions.
        assert excinfo.value.status_code == 423
        assert excinfo.value.error_code == "ACCOUNT_LOCKED"
        assert excinfo.value.message == "Account temporarily locked. Try again in 15 minutes."

    def test_locked_out_ip_never_reaches_the_code_store(self) -> None:
        """Delegated from P2. Without the ordering, a lockout costs an attacker a
        status code and nothing else — the code would still be tested, and a
        correct guess would still be burned."""
        throttle = MemoryDevicePairingThrottleStore()
        counting = _make_harness(throttle_store=throttle)
        _fail_redemptions(counting, MAX_ATTEMPTS)

        code_store = MagicMock()
        locked = _make_harness(code_store=code_store, throttle_store=throttle)

        with pytest.raises(AccountLockedError):
            locked.service.redeem_device_pairing("a-guess", ip_address=IP)

        assert code_store.mock_calls == []
        assert code_store.consume.call_count == 0

    def test_a_valid_code_is_refused_while_the_address_is_locked(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)
        _fail_redemptions(harness, MAX_ATTEMPTS)

        with pytest.raises(AccountLockedError):
            harness.service.redeem_device_pairing(code, ip_address=IP)

        assert harness.refresh_token_repo.create.call_count == 0
        # And the code was not consumed while locked, so it still works after.
        assert harness.code_store.consume(code) is not None

    def test_a_successful_redemption_clears_the_counter(self) -> None:
        harness = _make_harness()
        _fail_redemptions(harness, MAX_ATTEMPTS - 1)
        code, _ = harness.service.create_device_pairing(USER_KEY)

        harness.service.redeem_device_pairing(code, ip_address=IP)

        assert harness.throttle_store.get_failure_state(IP) == (0, None)

    def test_counters_are_per_address(self) -> None:
        """One attacker must not be able to lock out a bystander."""
        harness = _make_harness()
        _fail_redemptions(harness, MAX_ATTEMPTS, ip_address=OTHER_IP)
        code, _ = harness.service.create_device_pairing(USER_KEY)

        pair, _, _ = harness.service.redeem_device_pairing(code, ip_address=IP)

        assert pair.access_token

    def test_counter_survives_across_service_instances(self) -> None:
        """Production rebuilds ``AuthService`` per request; the count must not restart."""
        throttle = MemoryDevicePairingThrottleStore()
        for _ in range(MAX_ATTEMPTS):
            _fail_redemptions(_make_harness(throttle_store=throttle), 1)

        with pytest.raises(AccountLockedError):
            _make_harness(throttle_store=throttle).service.redeem_device_pairing("a-guess", ip_address=IP)

    def test_throttle_store_defaults_to_the_process_wide_instance(self) -> None:
        """``None`` here would not disable the feature, only its guard."""
        service = AuthService(
            user_repo=MagicMock(),
            auth_provider_repo=MagicMock(),
            refresh_token_repo=MagicMock(),
            password_engine=PasswordEngine(),
            token_engine=TokenEngine(SECRET_KEY, "HS256"),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="http://localhost:5173",
        )

        assert service._device_pairing_throttle_store is DEFAULT_DEVICE_PAIRING_THROTTLE_STORE


# ── Audit events ────────────────────────────────────────────────────────


def _events(logs: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [entry for entry in logs if entry["event"] == name]


class TestAuditEvents:
    def test_created_event_carries_who_where_and_when(self) -> None:
        harness = _make_harness()

        with structlog.testing.capture_logs() as logs:
            _, expires_at = harness.service.create_device_pairing(USER_KEY, ip_address=IP)

        created = _events(logs, "device_pairing_created")
        assert len(created) == 1
        assert created[0]["user_key"] == USER_KEY
        assert created[0]["ip_address"] == IP
        assert created[0]["expires_at"] == expires_at.isoformat()
        assert created[0]["code_sha256"]

    def test_redeemed_event_carries_who_where_and_when(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        with structlog.testing.capture_logs() as logs:
            harness.service.redeem_device_pairing(code, ip_address=IP)

        redeemed = _events(logs, "device_pairing_redeemed")
        assert len(redeemed) == 1
        assert redeemed[0]["user_key"] == USER_KEY
        assert redeemed[0]["ip_address"] == IP
        assert redeemed[0]["issued_at"]

    def test_failed_event_names_the_address_but_no_account(self) -> None:
        """A miss has no account — inventing one would attribute a stranger's
        guess to whoever the code *would* have belonged to."""
        harness = _make_harness()

        with structlog.testing.capture_logs() as logs, pytest.raises(InvalidTokenError):
            harness.service.redeem_device_pairing("never-issued-code", ip_address=IP)

        failed = _events(logs, "device_pairing_redeem_failed")
        assert len(failed) == 1
        assert failed[0]["ip_address"] == IP
        assert failed[0]["reason"] == "not_redeemable"
        assert failed[0]["failed_attempts"] == 1
        assert "user_key" not in failed[0]

    def test_lockout_emits_the_failed_event_with_its_own_reason(self) -> None:
        harness = _make_harness()
        _fail_redemptions(harness, MAX_ATTEMPTS)

        with structlog.testing.capture_logs() as logs, pytest.raises(AccountLockedError):
            harness.service.redeem_device_pairing("a-guess", ip_address=IP)

        failed = _events(logs, "device_pairing_redeem_failed")
        assert len(failed) == 1
        assert failed[0]["reason"] == "locked_out"
        assert failed[0]["retry_after_minutes"] >= 1

    @pytest.mark.parametrize("outcome", ["issued", "redeemed", "replayed"])
    def test_the_raw_code_never_reaches_a_log_record(self, outcome: str) -> None:
        """The line outlives the 90-second code in whatever sink collects it."""
        harness = _make_harness()

        with structlog.testing.capture_logs() as logs:
            code, _ = harness.service.create_device_pairing(USER_KEY, ip_address=IP)
            if outcome in {"redeemed", "replayed"}:
                harness.service.redeem_device_pairing(code, ip_address=IP)
            if outcome == "replayed":
                with pytest.raises(InvalidTokenError):
                    harness.service.redeem_device_pairing(code, ip_address=IP)

        assert logs, "no log records captured — the assertion below would be vacuous"
        rendered = str(logs)
        assert code not in rendered
        # Not even a prefix of it: an 8-character head would shrink the search
        # space of the credential the line is about.
        assert code[:8] not in rendered

    def test_the_raw_refresh_token_never_reaches_a_log_record(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        with structlog.testing.capture_logs() as logs:
            _, raw_refresh, _ = harness.service.redeem_device_pairing(code, ip_address=IP)

        assert raw_refresh not in str(logs)


# ── Client-supplied device label (P5 wires persistence) ─────────────────


class TestDeviceName:
    def test_a_label_is_accepted_and_normalised(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        with structlog.testing.capture_logs() as logs:
            harness.service.redeem_device_pairing(code, ip_address=IP, device_name="  Pixel 9  ")

        assert _events(logs, "device_pairing_redeemed")[0]["device_name_supplied"] is True

    def test_a_blank_label_is_the_same_as_none(self) -> None:
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        with structlog.testing.capture_logs() as logs:
            harness.service.redeem_device_pairing(code, ip_address=IP, device_name="   ")

        assert _events(logs, "device_pairing_redeemed")[0]["device_name_supplied"] is False

    def test_an_over_long_label_is_refused_at_the_service_boundary(self) -> None:
        """The caller is unauthenticated; P4's schema bounds it too, but a
        service reachable from a task must not rely on that."""
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        with pytest.raises(ValidationError) as excinfo:
            harness.service.redeem_device_pairing(code, ip_address=IP, device_name="x" * 65)

        assert excinfo.value.status_code == 422
        # Refused before the code was spent, so a typo does not cost the code.
        assert harness.code_store.consume(code) is not None

    def test_the_label_is_not_persisted_yet(self) -> None:
        """P5 adds ``RefreshToken.device_name`` and wires it through
        ``_create_tokens``. Until then the parameter is accepted and validated
        but stored nowhere — asserted, so "P5 is done" is a fact this test
        reports rather than an assumption."""
        harness = _make_harness()
        code, _ = harness.service.create_device_pairing(USER_KEY)

        harness.service.redeem_device_pairing(code, ip_address=IP, device_name="Pixel 9")

        (token,) = harness.created_tokens
        assert "device_name" not in token.model_dump()
