"""#1815 — the e-mailed step-up code is stored hashed, lives ten minutes and is spent once.

What is asserted, for the in-process and the shared tier:

* a right code is consumed exactly once — a second presentation fails, also when
  two requests present it at the same moment (only the caller whose delete removed
  the entry wins);
* a wrong code does not spend the stored one (the step-up throttle bounds guesses);
* issuing replaces the previous code;
* an expired code is refused;
* neither the subject nor the code reaches the store in the clear (NFR-011);
* a Valkey outage degrades to the in-process tier instead of failing open or
  losing the code, and a code issued during the outage is still redeemable after it;
* the in-process tier is bounded.
"""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from app.data_access.external.step_up_code_store import (
    MemoryStepUpCodeStore,
    RedisStepUpCodeStore,
)

SUBJECT = "user-1"


def _digest(code: str) -> str:
    # Shaped like the verifier's digest; assembled at runtime (#1838).
    return hashlib.sha256(f"{SUBJECT}:{code}".encode()).hexdigest()


RAW_RIGHT = "".join(str(n) for n in range(1, 9))
RIGHT = _digest(RAW_RIGHT)
WRONG = _digest(RAW_RIGHT[::-1])


class _Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


class _FakeRedis:
    """``set ex`` / ``get`` / ``delete`` with Redis semantics (atomic under a lock)."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self._mutex = threading.Lock()

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> bool | None:
        with self._mutex:
            if nx and name in self.values:
                return None
            self.values[name] = value
            if ex is not None:
                self.ttls[name] = ex
            return True

    def incr(self, name: str, amount: int = 1) -> int:
        with self._mutex:
            value = int(self.values.get(name, "0")) + amount
            self.values[name] = str(value)
            return value

    def decr(self, name: str, amount: int = 1) -> int:
        return self.incr(name, -amount)

    def ttl(self, name: str) -> int:
        with self._mutex:
            if name not in self.values:
                return -2
            return self.ttls.get(name, -1)

    def pipeline(self, transaction: bool = True):
        outer = self

        class _Pipe:
            def __init__(self) -> None:
                self.ops: list[tuple[str, tuple, dict]] = []

            def __getattr__(self, op: str):
                def add(*args, **kwargs):
                    self.ops.append((op, args, kwargs))
                    return self

                return add

            def execute(self):
                return [getattr(outer, op)(*args, **kwargs) for op, args, kwargs in self.ops]

        return _Pipe()

    def get(self, name: str) -> str | None:
        with self._mutex:
            return self.values.get(name)

    def delete(self, *names: str) -> int:
        with self._mutex:
            removed = 0
            for name in names:
                if self.values.pop(name, None) is not None:
                    removed += 1
                self.ttls.pop(name, None)
            return removed


class _BrokenRedis:
    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> bool:
        raise ConnectionError("valkey is down")

    def ttl(self, name: str) -> int:
        raise ConnectionError("valkey is down")

    def pipeline(self, transaction: bool = True):
        raise ConnectionError("valkey is down")

    def get(self, name: str) -> str | None:
        raise ConnectionError("valkey is down")

    def delete(self, *names: str) -> int:
        raise ConnectionError("valkey is down")

    def decr(self, name: str, amount: int = 1) -> int:
        raise ConnectionError("valkey is down")


def _stores():
    return (
        MemoryStepUpCodeStore(),
        RedisStepUpCodeStore(_FakeRedis(), fallback=MemoryStepUpCodeStore()),
    )


def test_a_right_code_is_consumed_once() -> None:
    for store in _stores():
        store.issue(SUBJECT, RIGHT, 600)

        assert store.consume(SUBJECT, RIGHT) is True
        assert store.consume(SUBJECT, RIGHT) is False


def test_a_wrong_code_does_not_spend_the_stored_one() -> None:
    for store in _stores():
        store.issue(SUBJECT, RIGHT, 600)

        assert store.consume(SUBJECT, WRONG) is False
        assert store.consume(SUBJECT, RIGHT) is True


def test_issuing_replaces_the_previous_code() -> None:
    for store in _stores():
        store.issue(SUBJECT, WRONG, 600)
        store.issue(SUBJECT, RIGHT, 600)

        assert store.consume(SUBJECT, WRONG) is False
        assert store.consume(SUBJECT, RIGHT) is True


def test_a_code_of_another_subject_does_not_match() -> None:
    for store in _stores():
        store.issue("user-2", RIGHT, 600)

        assert store.consume(SUBJECT, RIGHT) is False


def test_concurrent_presentations_of_the_right_code_win_once() -> None:
    for store in _stores():
        store.issue(SUBJECT, RIGHT, 600)

        with ThreadPoolExecutor(max_workers=16) as pool:
            outcomes = list(pool.map(lambda _, s=store: s.consume(SUBJECT, RIGHT), range(32)))

        assert outcomes.count(True) == 1, type(store).__name__


def test_a_redis_consume_counts_only_the_delete_that_removed_the_entry() -> None:
    """GET matched, but another request's DEL got there first: this one must lose."""

    class _RacedRedis(_FakeRedis):
        def get(self, name: str) -> str | None:
            value = super().get(name)
            super().delete(name)  # the concurrent winner deletes between our GET and DEL
            return value

    store = RedisStepUpCodeStore(_RacedRedis(), fallback=MemoryStepUpCodeStore())
    store.issue(SUBJECT, RIGHT, 600)

    assert store.consume(SUBJECT, RIGHT) is False


def test_an_expired_code_is_refused_in_the_local_tier() -> None:
    clock = _Clock()
    store = MemoryStepUpCodeStore(clock=clock)
    store.issue(SUBJECT, RIGHT, 600)

    clock.advance(601)

    assert store.consume(SUBJECT, RIGHT) is False


def test_the_shared_tier_writes_the_code_with_its_expiry() -> None:
    redis = _FakeRedis()
    store = RedisStepUpCodeStore(redis, fallback=MemoryStepUpCodeStore())

    store.issue(SUBJECT, RIGHT, 600)

    assert list(redis.ttls.values()) == [600]


def test_neither_subject_nor_code_reaches_the_store_in_the_clear() -> None:
    redis = _FakeRedis()
    store = RedisStepUpCodeStore(redis, fallback=MemoryStepUpCodeStore())

    store.issue(SUBJECT, RIGHT, 600)

    ((key, value),) = redis.values.items()
    assert key.startswith("kp:auth:stepup:code:")
    assert SUBJECT not in key
    assert value == RIGHT  # only the digest the verifier handed over
    assert RAW_RIGHT not in key + value


def test_the_code_namespace_is_not_the_throttle_one() -> None:
    redis = _FakeRedis()
    RedisStepUpCodeStore(redis, fallback=MemoryStepUpCodeStore()).issue(SUBJECT, RIGHT, 600)

    assert all(
        not key.startswith(("kp:auth:stepup:count:", "kp:auth:stepup:lock:", "kp:auth:stepup:strikes:"))
        for key in redis.values
    )


def test_an_outage_degrades_to_the_local_tier() -> None:
    fallback = MemoryStepUpCodeStore()
    store = RedisStepUpCodeStore(_BrokenRedis(), fallback=fallback)

    store.issue(SUBJECT, RIGHT, 600)

    assert store.consume(SUBJECT, WRONG) is False
    assert store.consume(SUBJECT, RIGHT) is True
    assert store.consume(SUBJECT, RIGHT) is False


def test_a_code_issued_during_an_outage_is_redeemable_after_recovery() -> None:
    fallback = MemoryStepUpCodeStore()
    RedisStepUpCodeStore(_BrokenRedis(), fallback=fallback).issue(SUBJECT, RIGHT, 600)

    recovered = RedisStepUpCodeStore(_FakeRedis(), fallback=fallback)

    assert recovered.consume(SUBJECT, RIGHT) is True
    assert recovered.consume(SUBJECT, RIGHT) is False


def test_a_shared_issue_retires_a_code_left_in_the_local_tier() -> None:
    """Issuing replaces *any* previous code — also the one an outage parked locally."""
    fallback = MemoryStepUpCodeStore()
    RedisStepUpCodeStore(_BrokenRedis(), fallback=fallback).issue(SUBJECT, WRONG, 600)
    recovered = RedisStepUpCodeStore(_FakeRedis(), fallback=fallback)

    recovered.issue(SUBJECT, RIGHT, 600)

    assert recovered.consume(SUBJECT, WRONG) is False
    assert recovered.consume(SUBJECT, RIGHT) is True


def test_the_local_tier_is_bounded() -> None:
    store = MemoryStepUpCodeStore(capacity=8)

    for n in range(50):
        store.issue(f"user-{n}", RIGHT, 600)

    assert len(store._entries) == 8


# ── review SEC-002: issuance budget per subject ──────────────────────────────

_POLICY = {"cooldown_seconds": 60, "max_issues": 5, "window_seconds": 3600}


def test_a_reservation_inside_the_cooldown_waits_and_the_code_stays() -> None:
    for store in _stores():
        assert store.reserve_issue(SUBJECT, **_POLICY) == 0
        store.issue(SUBJECT, RIGHT, 600)

        wait = store.reserve_issue(SUBJECT, **_POLICY)

        assert 0 < wait <= 60, type(store).__name__
        assert store.consume(SUBJECT, RIGHT) is True


def test_a_spent_code_ends_the_cooldown() -> None:
    for store in _stores():
        store.reserve_issue(SUBJECT, **_POLICY)
        store.issue(SUBJECT, RIGHT, 600)
        store.consume(SUBJECT, RIGHT)

        assert store.reserve_issue(SUBJECT, **_POLICY) == 0, type(store).__name__


def test_the_sixth_reservation_in_the_window_waits() -> None:
    for store in _stores():
        for _ in range(5):
            assert store.reserve_issue(SUBJECT, **_POLICY) == 0
            store.issue(SUBJECT, RIGHT, 600)
            assert store.consume(SUBJECT, RIGHT)

        wait = store.reserve_issue(SUBJECT, **_POLICY)

        assert 0 < wait <= 3600, type(store).__name__


def test_the_window_ends_in_the_local_tier() -> None:
    clock = _Clock()
    store = MemoryStepUpCodeStore(clock=clock)
    for _ in range(5):
        store.reserve_issue(SUBJECT, **_POLICY)
        store.issue(SUBJECT, RIGHT, 600)
        store.consume(SUBJECT, RIGHT)
    clock.advance(3601)

    assert store.reserve_issue(SUBJECT, **_POLICY) == 0


def test_concurrent_reservations_never_exceed_the_budget() -> None:
    for store in _stores():
        policy = {**_POLICY, "cooldown_seconds": 0}
        with ThreadPoolExecutor(max_workers=16) as pool:
            waits = list(pool.map(lambda _, s=store, p=policy: s.reserve_issue(SUBJECT, **p), range(32)))

        assert waits.count(0) == 5, type(store).__name__


def test_the_issuance_counter_has_its_own_namespace_and_no_plain_subject() -> None:
    redis = _FakeRedis()
    store = RedisStepUpCodeStore(redis, fallback=MemoryStepUpCodeStore())

    store.reserve_issue(SUBJECT, **_POLICY)

    assert redis.values
    assert all(k.startswith("kp:auth:stepup:code") and SUBJECT not in k for k in redis.values)
    assert all(not k.startswith("kp:auth:stepup:code:") for k in redis.values)


def test_an_outage_counts_issuance_in_the_local_tier() -> None:
    fallback = MemoryStepUpCodeStore()
    store = RedisStepUpCodeStore(_BrokenRedis(), fallback=fallback)
    for _ in range(5):
        assert store.reserve_issue(SUBJECT, **{**_POLICY, "cooldown_seconds": 0}) == 0

    assert store.reserve_issue(SUBJECT, **{**_POLICY, "cooldown_seconds": 0}) > 0


# ── /code-review of #1862: an undeliverable code gives its issuance back ────────


def test_release_drops_the_code_the_cooldown_and_one_issue() -> None:
    for store in _stores():
        for _ in range(4):
            assert store.reserve_issue(SUBJECT, **_POLICY) == 0
            store.issue(SUBJECT, RIGHT, 600)
            assert store.consume(SUBJECT, RIGHT)
        assert store.reserve_issue(SUBJECT, **_POLICY) == 0  # the 5th, about to fail delivery
        store.issue(SUBJECT, RIGHT, 600)

        store.release_issue(SUBJECT)

        assert store.consume(SUBJECT, RIGHT) is False, type(store).__name__  # the undelivered code is gone
        assert store.reserve_issue(SUBJECT, **_POLICY) == 0, type(store).__name__  # no cooldown, budget back
        store.issue(SUBJECT, RIGHT, 600)
        assert store.consume(SUBJECT, RIGHT)
        assert store.reserve_issue(SUBJECT, **_POLICY) > 0  # and now the budget is spent


def test_release_never_drives_the_budget_negative() -> None:
    for store in _stores():
        store.release_issue(SUBJECT)
        store.release_issue(SUBJECT)

        for _ in range(5):
            assert store.reserve_issue(SUBJECT, **{**_POLICY, "cooldown_seconds": 0}) == 0
        assert store.reserve_issue(SUBJECT, **{**_POLICY, "cooldown_seconds": 0}) > 0, type(store).__name__


def test_release_degrades_to_the_local_tier() -> None:
    fallback = MemoryStepUpCodeStore()
    store = RedisStepUpCodeStore(_BrokenRedis(), fallback=fallback)
    store.reserve_issue(SUBJECT, **_POLICY)
    store.issue(SUBJECT, RIGHT, 600)

    store.release_issue(SUBJECT)

    assert fallback.consume(SUBJECT, RIGHT) is False
    assert store.reserve_issue(SUBJECT, **_POLICY) == 0


# ── /code-review of #1862: the replacement wait is claimed atomically ───────────


class _InterleavingRedis(_FakeRedis):
    """Runs a second reservation between the first one's read of the wait and its claim.

    Models the race the review found: two requests both read "no wait" (TTL -2)
    and both went on to issue.
    """

    def __init__(self) -> None:
        super().__init__()
        self.store: RedisStepUpCodeStore | None = None
        self.results: list[int] = []
        self._inside = False

    def ttl(self, name: str) -> int:
        value = super().ttl(name)
        if not self._inside and "codecooldown" in name and self.store is not None:
            self._inside = True
            self.results.append(self.store.reserve_issue(SUBJECT, **_POLICY))
        return value

    def set(self, name, value, ex=None, nx=False):  # noqa: ANN001, ANN201 - fake
        if not self._inside and nx and "codecooldown" in name and self.store is not None:
            self._inside = True
            self.results.append(self.store.reserve_issue(SUBJECT, **_POLICY))
        return super().set(name, value, ex=ex, nx=nx)


def test_two_racing_reservations_admit_exactly_one() -> None:
    redis = _InterleavingRedis()
    store = RedisStepUpCodeStore(redis, fallback=MemoryStepUpCodeStore())
    redis.store = store

    first = store.reserve_issue(SUBJECT, **_POLICY)

    assert [first, *redis.results].count(0) == 1, (first, redis.results)


def test_an_over_budget_reservation_leaves_no_wait_behind() -> None:
    """A refused issue did not send a code, so it must not hold the next one back for a minute."""
    redis = _FakeRedis()
    store = RedisStepUpCodeStore(redis, fallback=MemoryStepUpCodeStore())
    for _ in range(5):
        store.reserve_issue(SUBJECT, **_POLICY)
        store.issue(SUBJECT, RIGHT, 600)
        store.consume(SUBJECT, RIGHT)

    assert store.reserve_issue(SUBJECT, **_POLICY) > 0

    assert not any("codecooldown" in key for key in redis.values)
