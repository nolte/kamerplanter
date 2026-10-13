"""#1816 — the verifier's order and its burst bound, below the routes.

The route suite (``tests/unit/api/test_step_up_irreversible_account_actions.py``)
drives the rule through every HTTP entry. Two properties are only observable here:

* a *concurrent* burst of wrong passwords reaches bcrypt at most threshold times —
  the reservation happens before the check, so a request racing past the lock
  check is refused on its own count;
* the lock is decided by :class:`LoginThrottleEngine` (15 minutes at the login
  threshold), not by a second constant.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.common.exceptions import (
    ForbiddenError,
    StepUpCodeRequiredError,
    StepUpLockedError,
    StepUpPasswordRequiredError,
    UnauthorizedError,
    ValidationError,
)
from app.data_access.external.step_up_code_store import MemoryStepUpCodeStore
from app.data_access.external.step_up_throttle import MemoryStepUpThrottleStore
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS
from app.domain.engines.password_engine import PasswordEngine
from app.domain.models.user import User
from app.domain.services.step_up_service import ACCOUNT_CEILING, TARGETED_ACTIONS, StepUpVerifier, echo_matches

PASSWORD = "correct horse battery staple"
HASH = PasswordEngine().hash_password(PASSWORD)


class _CountingEngine(PasswordEngine):
    def __init__(self) -> None:
        self.calls = 0
        self._mutex = threading.Lock()

    def verify_password(self, plain: str, hashed: str) -> bool:
        with self._mutex:
            self.calls += 1
        return super().verify_password(plain, hashed)


def _user(**overrides) -> User:
    return User.model_validate(
        {"_key": "u-1", "email": "u@example.org", "display_name": "U", "password_hash": HASH, **overrides}
    )


def _verify(verifier: StepUpVerifier, user: User, password: str | None, *, ip: str = "203.0.113.1", **kw):
    return verifier.verify(
        user,
        action="account_erasure",
        target=None,
        echo_ok=kw.get("echo_ok", True),
        password=password,
        code=kw.get("code"),
        reauth_token=None,
        authenticated_with_api_key=kw.get("api_key", False),
        client_ip=ip,
    )


def test_a_concurrent_burst_reaches_bcrypt_at_most_threshold_times() -> None:
    engine = _CountingEngine()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(), engine)
    user = _user()

    def attempt(_: int) -> str:
        try:
            _verify(verifier, user, "wrong")
        except UnauthorizedError:
            return "401"
        except StepUpLockedError:
            return "429"
        return "ok"

    with ThreadPoolExecutor(max_workers=12) as pool:
        outcomes = list(pool.map(attempt, range(24)))

    assert engine.calls <= MAX_ATTEMPTS
    assert outcomes.count("401") == engine.calls
    assert outcomes.count("429") == 24 - engine.calls


def test_the_first_lock_is_the_login_engines_fifteen_minutes() -> None:
    verifier = StepUpVerifier(MemoryStepUpThrottleStore())
    user = _user()
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(UnauthorizedError):
            _verify(verifier, user, "wrong")

    with pytest.raises(StepUpLockedError) as excinfo:
        _verify(verifier, user, PASSWORD)

    assert excinfo.value.retry_after_minutes == 15
    assert excinfo.value.status_code == 429


def test_the_account_ceiling_is_above_the_address_threshold() -> None:
    assert ACCOUNT_CEILING > MAX_ATTEMPTS


def test_order_api_key_before_lock_before_echo_before_password() -> None:
    store = MemoryStepUpThrottleStore()
    verifier = StepUpVerifier(store)
    user = _user()

    with pytest.raises(ForbiddenError):
        _verify(verifier, user, "wrong", api_key=True, echo_ok=False)
    with pytest.raises(ValidationError):
        _verify(verifier, user, "wrong", echo_ok=False)
    assert store.reserve_attempt("account:u-1") == 1  # neither refusal above counted


def test_a_federated_account_is_no_longer_confirmed_by_the_echo_alone() -> None:
    """#1815 — the echo tests nothing secret; a hijacked session typed it too."""
    engine = _CountingEngine()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(), engine, code_store=MemoryStepUpCodeStore())

    with pytest.raises(StepUpCodeRequiredError) as excinfo:
        _verify(verifier, _user(password_hash=None), None)

    assert excinfo.value.status_code == 401
    assert excinfo.value.error_code == "STEP_UP_CODE_REQUIRED"
    assert engine.calls == 0


def test_a_service_account_is_refused() -> None:
    verifier = StepUpVerifier(MemoryStepUpThrottleStore())

    with pytest.raises(ForbiddenError):
        _verify(verifier, _user(password_hash=None, account_type="service"), None)


@pytest.mark.parametrize(
    ("given", "expected", "ci", "result"),
    [
        (" A@Example.org ", "a@example.org", True, True),
        ("a@example.org", "b@example.org", True, False),
        ("Garden", "garden", False, False),
        (" garden ", "garden", False, True),
    ],
)
def test_echo_matches(given: str, expected: str, ci: bool, result: bool) -> None:
    assert echo_matches(given, expected, case_insensitive=ci) is result


# ── security review SEC-001 / SEC-007: the lock ends, and the next try is tested ──


class _Clock:
    def __init__(self) -> None:
        from datetime import UTC, datetime

        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, minutes: int) -> None:
        from datetime import timedelta

        self.now += timedelta(minutes=minutes)


def _fail_until_locked(verifier: StepUpVerifier, user: User, *, ip: str = "203.0.113.1") -> None:
    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(UnauthorizedError):
            _verify(verifier, user, "wrong", ip=ip)


def test_after_the_lock_ends_the_correct_password_is_accepted_again() -> None:
    """Review SEC-001: the sixth reservation used to be refused forever, without bcrypt."""
    clock = _Clock()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(clock=clock))
    user = _user()
    _fail_until_locked(verifier, user)

    clock.advance(16)

    assert _verify(verifier, user, PASSWORD) == "password"


def test_after_the_lock_ends_one_wrong_try_locks_again_for_twice_as_long() -> None:
    """The login curve: after a lock, each further failure locks at once, doubling."""
    clock = _Clock()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(clock=clock))
    user = _user()
    _fail_until_locked(verifier, user)
    clock.advance(16)

    with pytest.raises(UnauthorizedError):
        _verify(verifier, user, "wrong")
    with pytest.raises(StepUpLockedError) as excinfo:
        _verify(verifier, user, PASSWORD)

    assert excinfo.value.retry_after_minutes == 30


def test_after_the_lock_ends_a_burst_still_reaches_bcrypt_only_once() -> None:
    clock = _Clock()
    engine = _CountingEngine()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(clock=clock), engine)
    user = _user()
    _fail_until_locked(verifier, user)
    clock.advance(16)
    before = engine.calls

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: _safe_verify(verifier, user), range(16)))

    assert engine.calls - before == 1


def _safe_verify(verifier: StepUpVerifier, user: User) -> str:
    try:
        return _verify(verifier, user, "wrong")
    except (UnauthorizedError, StepUpLockedError) as exc:
        return type(exc).__name__


def test_an_account_wide_lock_reports_its_own_wait() -> None:
    """Review SEC-007: the refusal named the address bucket's wait (or a flat minute)."""
    clock = _Clock()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(clock=clock))
    user = _user()
    for n in range(3):
        _fail_until_locked(verifier, user, ip=f"192.0.2.{n + 1}")

    with pytest.raises(StepUpLockedError) as excinfo:
        _verify(verifier, user, PASSWORD, ip="192.0.2.99")

    assert excinfo.value.retry_after_minutes >= 15


# ── /code-review finding: a refused reservation must not undercount after a strike ──


class _LateReleaseStore(MemoryStepUpThrottleStore):
    """Delivers every given-back reservation only after the next strike.

    Models the interleaving the review found: burst requests refused while the
    one tested attempt runs bcrypt give their reservation back *after* that
    attempt failed and re-armed the counter — which then undercounts.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._late: list[str] = []

    def release_attempt(self, subject: str) -> None:
        self._late.append(subject)

    def strike(self, subject: str, **kwargs):  # type: ignore[override]
        strikes = super().strike(subject, **kwargs)
        late, self._late = self._late, []
        release = getattr(super(), "release_attempt", None)
        for pending in late:
            if release is not None:
                release(pending)
        return strikes


def test_a_burst_during_the_tested_attempt_does_not_buy_extra_tries_after_the_lock() -> None:
    clock = _Clock()
    store = _LateReleaseStore(clock=clock)
    user = _user()
    burst: list[str] = []

    class _BurstDuringBcrypt(_CountingEngine):
        def verify_password(self, plain: str, hashed: str) -> bool:
            if self.calls == MAX_ATTEMPTS - 1 and not burst:  # the attempt that reaches the threshold
                for _ in range(3):
                    burst.append(_safe_verify(verifier, user))
            return super().verify_password(plain, hashed)

    engine = _BurstDuringBcrypt()
    verifier = StepUpVerifier(store, engine)
    _fail_until_locked(verifier, user)
    assert burst == ["StepUpLockedError"] * 3
    clock.advance(16)
    before = engine.calls

    outcomes = [_safe_verify(verifier, user) for _ in range(4)]

    assert engine.calls - before == 1, outcomes


# ── #1815: an account without a local password confirms with an e-mailed code ──


def _federated(**overrides) -> User:
    return _user(password_hash=None, **overrides)


def _code_verifier(clock: _Clock | None = None) -> tuple[StepUpVerifier, MemoryStepUpCodeStore]:
    codes = MemoryStepUpCodeStore(clock=clock) if clock else MemoryStepUpCodeStore()
    throttle = MemoryStepUpThrottleStore(clock=clock) if clock else MemoryStepUpThrottleStore()
    return StepUpVerifier(throttle, code_store=codes, target_policy=_AnyTarget()), codes


def _issue(
    verifier: StepUpVerifier,
    user: User,
    *,
    api_key: bool = False,
    ip: str = "203.0.113.1",
    action: str = "account_erasure",
) -> str:
    code, _expires_at = verifier.issue_code(
        user, action=action, target=_target_of(action), authenticated_with_api_key=api_key, client_ip=ip
    )
    return code


class _AnyTarget:
    """A target policy that admits every target — the rules themselves are pinned in test_step_up_target_binding.py."""

    def authorize(self, requester: User, *, action: str, target: str) -> None:
        return None


def _target_of(action: str) -> str | None:
    """The target a test names for *action*: one for an act on something else (#1884), none otherwise."""
    return "target-1" if action in TARGETED_ACTIONS else None


def _other_code(code: str) -> str:
    return f"{(int(code) + 1) % 10**8:08d}"


def test_an_issued_code_is_eight_digits_and_expires_in_ten_minutes() -> None:
    from datetime import UTC, datetime, timedelta

    verifier, _codes = _code_verifier()
    before = datetime.now(UTC)

    code, expires_at = verifier.issue_code(
        _federated(), action="account_erasure", target=None, authenticated_with_api_key=False, client_ip="203.0.113.1"
    )

    assert len(code) == 8 and code.isdigit()
    assert before + timedelta(seconds=590) <= expires_at <= datetime.now(UTC) + timedelta(seconds=600)


def test_the_right_code_confirms_once() -> None:
    verifier, _codes = _code_verifier()
    user = _federated()
    code = _issue(verifier, user)

    assert _verify(verifier, user, None, code=code) == "email_code"
    with pytest.raises(UnauthorizedError):
        _verify(verifier, user, None, code=code)


def test_the_code_is_stored_only_as_a_digest() -> None:
    verifier, codes = _code_verifier()
    code = _issue(verifier, _federated())

    stored = repr(codes._entries)
    assert code not in stored
    assert "u-1" not in stored


def test_a_code_confirms_the_password_change_of_a_federated_account() -> None:
    """The act that set a first password on nothing at all ("no_local_password")."""
    verifier, _codes = _code_verifier()
    user = _federated()
    code = _issue(verifier, user, action="password_change")

    method = verifier.verify(
        user,
        action="password_change",
        target=None,
        echo_ok=None,
        password=None,
        code=code,
        reauth_token=None,
        authenticated_with_api_key=False,
        client_ip="203.0.113.1",
    )

    assert method == "email_code"


def test_the_password_change_of_a_federated_account_without_a_code_is_refused() -> None:
    verifier, _codes = _code_verifier()

    with pytest.raises(StepUpCodeRequiredError):
        verifier.verify(
            _federated(),
            action="password_change",
            target=None,
            echo_ok=None,
            password=None,
            code=None,
            reauth_token=None,
            authenticated_with_api_key=False,
            client_ip="203.0.113.1",
        )


def test_a_wrong_code_is_counted_and_locks_at_the_address_threshold() -> None:
    verifier, _codes = _code_verifier()
    user = _federated()
    code = _issue(verifier, user)

    for _ in range(MAX_ATTEMPTS):
        with pytest.raises(UnauthorizedError):
            _verify(verifier, user, None, code=_other_code(code))

    with pytest.raises(StepUpLockedError) as excinfo:
        _verify(verifier, user, None, code=code)
    assert excinfo.value.status_code == 429


def test_a_code_is_refused_after_its_ten_minutes() -> None:
    clock = _Clock()
    verifier, _codes = _code_verifier(clock)
    user = _federated()
    code = _issue(verifier, user)

    clock.advance(11)

    with pytest.raises(UnauthorizedError):
        _verify(verifier, user, None, code=code)


def test_the_lock_is_checked_before_the_code() -> None:
    """A locked step-up does not spend (or test) the code."""
    verifier, codes = _code_verifier()
    user = _federated()
    code = _issue(verifier, user)
    verifier._store.lock("account:u-1", 900)

    with pytest.raises(StepUpLockedError):
        _verify(verifier, user, None, code=code)
    verifier._store.clear("account:u-1")

    assert _verify(verifier, user, None, code=code) == "email_code"


def test_a_wrong_echo_is_refused_before_the_code_is_spent() -> None:
    verifier, _codes = _code_verifier()
    user = _federated()
    code = _issue(verifier, user)

    with pytest.raises(ValidationError):
        _verify(verifier, user, None, code=code, echo_ok=False)

    assert _verify(verifier, user, None, code=code) == "email_code"


def test_a_password_account_cannot_substitute_a_code_for_its_password() -> None:
    verifier, _codes = _code_verifier()

    with pytest.raises(UnauthorizedError):
        _verify(verifier, _user(), None, code="".join(["0"] * 8))


@pytest.mark.parametrize(
    ("user_of", "api_key"),
    [
        pytest.param(lambda: _federated(), True, id="api key"),
        pytest.param(lambda: _federated(account_type="service"), False, id="service account"),
    ],
)
def test_no_code_is_issued_to_an_api_key_or_a_service_account(user_of, api_key) -> None:
    verifier, codes = _code_verifier()

    with pytest.raises(ForbiddenError):
        _issue(verifier, user_of(), api_key=api_key)

    assert not codes._entries


def test_no_code_is_issued_to_an_account_with_a_password() -> None:
    verifier, codes = _code_verifier()

    with pytest.raises(StepUpPasswordRequiredError):
        _issue(verifier, _user())

    assert not codes._entries


def test_no_code_is_issued_while_the_step_up_is_locked() -> None:
    verifier, codes = _code_verifier()
    verifier._store.lock("pair:u-1:203.0.113.1", 900)

    with pytest.raises(StepUpLockedError):
        _issue(verifier, _federated())

    assert not codes._entries


def test_the_code_attempts_share_the_budget_with_the_password_attempts() -> None:
    """One budget per account: a wrong code and a wrong password fill the same counter."""
    store = MemoryStepUpThrottleStore()
    verifier = StepUpVerifier(store, code_store=MemoryStepUpCodeStore())
    user = _federated()
    _issue(verifier, user)

    with pytest.raises(UnauthorizedError):
        _verify(verifier, user, None, code="".join(["9"] * 8))

    assert store.reserve_attempt("account:u-1") == 2


# ── the persisted step-up literals: the new method is storable, the old ones stay readable ──


@pytest.mark.parametrize("value", ["oidc_reauth", "email_code", "echo", "password"])
def test_an_erasure_record_reads_every_step_up_it_was_ever_written_with(value: str) -> None:
    """``email_code`` is what #1815 writes; ``echo`` is on records from before it."""
    from app.domain.models.privacy import ErasureRequest

    record = ErasureRequest.model_validate({"user_key": "u", "status": "scheduled", "step_up": value})

    assert record.step_up == value


@pytest.mark.parametrize("value", ["oidc_reauth", "email_code", "slug_confirmation", "password"])
def test_a_tenant_deletion_record_reads_every_step_up_it_was_ever_written_with(value: str) -> None:
    from datetime import UTC, datetime

    from app.domain.models.tenant_erasure import TenantErasureRecord

    record = TenantErasureRecord.model_validate(
        {
            "tenant_key": "t",
            "tenant_type": "organization",
            "origin": "tenant_management",
            "step_up": value,
            "requested_at": datetime.now(UTC),
        }
    )

    assert record.step_up == value


# ── the stored digest is bound to a server secret (a leaked store is no offline oracle) ──


def test_the_stored_digest_is_not_a_bare_hash_of_key_and_code() -> None:
    import hashlib

    codes = MemoryStepUpCodeStore()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(), code_store=codes, code_secret="server-" + "s" * 32)
    user = _federated()
    code = _issue(verifier, user)

    ((stored, _expires_at),) = codes._entries.values()
    assert stored != hashlib.sha256(f"u-1:{code}".encode()).hexdigest()
    assert stored != hashlib.sha256(code.encode()).hexdigest()


def test_a_code_issued_under_one_server_secret_is_refused_under_another() -> None:
    codes = MemoryStepUpCodeStore()
    user = _federated()
    code = _issue(StepUpVerifier(MemoryStepUpThrottleStore(), code_store=codes, code_secret="a" * 32), user)
    other = StepUpVerifier(MemoryStepUpThrottleStore(), code_store=codes, code_secret="b" * 32)

    with pytest.raises(UnauthorizedError):
        _verify(other, user, None, code=code)


# ── review SEC-003: the code is bound to the act it was requested for ──


@pytest.mark.parametrize(
    ("issued_for", "presented_to"),
    [
        ("password_change", "account_erasure"),
        ("email_change", "tenant_deletion"),
        ("account_erasure", "admin_account_erasure"),
    ],
)
def test_a_code_confirms_only_the_act_it_was_issued_for(issued_for: str, presented_to: str) -> None:
    verifier, _codes = _code_verifier()
    user = _federated()
    code = _issue(verifier, user, action=issued_for)

    with pytest.raises(UnauthorizedError):
        verifier.verify(
            user,
            action=presented_to,
            target=_target_of(presented_to),
            echo_ok=None,
            password=None,
            code=code,
            reauth_token=None,
            authenticated_with_api_key=False,
            client_ip="203.0.113.1",
        )
    # Not spent by the mismatch: the owner can still use it for what they asked it for.
    assert (
        verifier.verify(
            user,
            action=issued_for,
            target=_target_of(issued_for),
            echo_ok=None,
            password=None,
            code=code,
            reauth_token=None,
            authenticated_with_api_key=False,
            client_ip="203.0.113.1",
        )
        == "email_code"
    )


# ── review SEC-002: issuance is bounded per account ──


def _clocked() -> tuple[StepUpVerifier, _Clock]:
    clock = _Clock()
    return (
        StepUpVerifier(MemoryStepUpThrottleStore(clock=clock), code_store=MemoryStepUpCodeStore(clock=clock)),
        clock,
    )


def test_a_second_code_within_a_minute_is_refused_and_the_first_stays_valid() -> None:
    verifier, clock = _clocked()
    user = _federated()
    code = _issue(verifier, user)

    clock.now += __import__("datetime").timedelta(seconds=30)
    with pytest.raises(StepUpLockedError) as excinfo:
        _issue(verifier, user)

    assert excinfo.value.retry_after_minutes == 1
    assert excinfo.value.error_code == "STEP_UP_LOCKED"
    assert "No new confirmation code" in excinfo.value.message
    assert _verify(verifier, user, None, code=code) == "email_code"


def test_after_the_minute_a_new_code_replaces_the_old_one() -> None:
    verifier, clock = _clocked()
    user = _federated()
    old = _issue(verifier, user)
    clock.now += __import__("datetime").timedelta(seconds=61)

    new = _issue(verifier, user)

    if new != old:
        with pytest.raises(UnauthorizedError):
            _verify(verifier, user, None, code=old)
    assert _verify(verifier, user, None, code=new) == "email_code"


def test_the_sixth_code_within_an_hour_is_refused() -> None:
    verifier, clock = _clocked()
    user = _federated()
    for _ in range(5):
        _issue(verifier, user)
        clock.now += __import__("datetime").timedelta(seconds=61)

    with pytest.raises(StepUpLockedError) as excinfo:
        _issue(verifier, user)

    assert 1 <= excinfo.value.retry_after_minutes <= 60


def test_the_hourly_budget_comes_back_after_the_hour() -> None:
    verifier, clock = _clocked()
    user = _federated()
    for _ in range(5):
        _issue(verifier, user)
        clock.now += __import__("datetime").timedelta(seconds=61)
    clock.now += __import__("datetime").timedelta(hours=1)

    assert _issue(verifier, user)


def test_a_withdrawn_code_gives_its_issuance_back() -> None:
    """/code-review of #1862: a code that could not be mailed spends neither the wait nor the budget."""
    verifier, clock = _clocked()
    user = _federated()
    for _ in range(4):
        _issue(verifier, user)
        clock.now += __import__("datetime").timedelta(seconds=61)
    failed = _issue(verifier, user)

    verifier.withdraw_code(user)

    with pytest.raises(UnauthorizedError):
        _verify(verifier, user, None, code=failed)
    assert _issue(verifier, user)  # neither the minute nor the 5th slot is taken
