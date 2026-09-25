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

from app.common.exceptions import ForbiddenError, StepUpLockedError, UnauthorizedError, ValidationError
from app.data_access.external.step_up_throttle import MemoryStepUpThrottleStore
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS
from app.domain.engines.password_engine import PasswordEngine
from app.domain.models.user import User
from app.domain.services.step_up_service import ACCOUNT_CEILING, StepUpVerifier, echo_matches

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
        echo_ok=kw.get("echo_ok", True),
        password=password,
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


def test_a_federated_account_is_confirmed_by_the_echo_and_never_counts() -> None:
    engine = _CountingEngine()
    verifier = StepUpVerifier(MemoryStepUpThrottleStore(), engine)

    assert _verify(verifier, _user(password_hash=None), None) == "echo"
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
