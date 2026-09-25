"""#1816 — the step-up throttle store counts atomically, is bounded and never fails open.

What is asserted:

* a reservation returns the new count, so the n-th of n *concurrent* attempts sees
  ``n`` — the property that keeps a burst from testing more passwords than the
  threshold allows (the read-then-write counters of the login path do not have it);
* a lock holds for its window and ``clear`` drops counter and lock;
* a Valkey outage degrades to the in-process tier instead of resetting to zero;
* subjects never reach the store in the clear (NFR-011);
* the in-process tier is bounded.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from app.data_access.external.step_up_throttle import (
    MemoryStepUpThrottleStore,
    RedisStepUpThrottleStore,
)

SUBJECT = "pair:user-1:203.0.113.7"


class _FakeRedis:
    """``incr`` / ``expire`` / ``set ex`` / ``ttl`` / ``delete`` with Redis semantics (atomic under a lock)."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.transactions: list[list[str]] = []
        self._mutex = threading.Lock()

    def incr(self, name: str, amount: int = 1) -> int:
        with self._mutex:
            value = int(self.values.get(name, "0")) + amount
            self.values[name] = str(value)
            return value

    def pipeline(self, transaction: bool = True):
        outer = self

        class _Pipe:
            def __init__(self) -> None:
                self.ops: list[tuple[str, tuple]] = []

            def incr(self, name: str, amount: int = 1):
                self.ops.append(("incr", (name, amount)))
                return self

            def expire(self, name: str, time: int):
                self.ops.append(("expire", (name, time)))
                return self

            def set(self, name: str, value: str, ex: int | None = None):
                self.ops.append(("set", (name, value, ex)))
                return self

            def execute(self):
                outer.transactions.append([op for op, _ in self.ops])
                return [getattr(outer, op)(*args) for op, args in self.ops]

        return _Pipe()

    def expire(self, name: str, time: int) -> bool:
        self.ttls[name] = time
        return True

    def set(self, name: str, value: str, ex: int | None = None) -> bool:
        self.values[name] = value
        if ex is not None:
            self.ttls[name] = ex
        return True

    def get(self, name: str) -> str | None:
        return self.values.get(name)

    def ttl(self, name: str) -> int:
        if name not in self.values:
            return -2
        return self.ttls.get(name, -1)

    def delete(self, *names: str) -> int:
        for name in names:
            self.values.pop(name, None)
            self.ttls.pop(name, None)
        return len(names)


class _BrokenRedis:
    def get(self, name: str) -> str | None:
        raise ConnectionError("valkey is down")

    def pipeline(self, transaction: bool = True):
        raise ConnectionError("valkey is down")

    def incr(self, name: str) -> int:
        raise ConnectionError("valkey is down")

    def expire(self, name: str, time: int) -> bool:
        raise ConnectionError("valkey is down")

    def set(self, name: str, value: str, ex: int | None = None) -> bool:
        raise ConnectionError("valkey is down")

    def ttl(self, name: str) -> int:
        raise ConnectionError("valkey is down")

    def delete(self, *names: str) -> int:
        raise ConnectionError("valkey is down")


def test_memory_reservations_are_atomic_under_concurrency() -> None:
    store = MemoryStepUpThrottleStore()

    with ThreadPoolExecutor(max_workers=16) as pool:
        counts = sorted(pool.map(lambda _: store.reserve_attempt(SUBJECT), range(64)))

    assert counts == list(range(1, 65))


def test_redis_reservations_count_in_the_shared_tier() -> None:
    redis = _FakeRedis()
    store = RedisStepUpThrottleStore(redis, fallback=MemoryStepUpThrottleStore())

    assert [store.reserve_attempt(SUBJECT) for _ in range(3)] == [1, 2, 3]
    assert any(ttl == 86_400 for ttl in redis.ttls.values())


def test_a_lock_holds_and_clear_drops_it_with_the_counter() -> None:
    for store in (
        MemoryStepUpThrottleStore(),
        RedisStepUpThrottleStore(_FakeRedis(), fallback=MemoryStepUpThrottleStore()),
    ):
        store.reserve_attempt(SUBJECT)
        store.lock(SUBJECT, 900)
        assert 0 < store.lock_remaining_seconds(SUBJECT) <= 900

        store.clear(SUBJECT)

        assert store.lock_remaining_seconds(SUBJECT) == 0
        assert store.reserve_attempt(SUBJECT) == 1


def test_an_unlocked_subject_reads_zero() -> None:
    store = RedisStepUpThrottleStore(_FakeRedis(), fallback=MemoryStepUpThrottleStore())

    assert store.lock_remaining_seconds(SUBJECT) == 0


def test_an_outage_degrades_to_the_local_tier_instead_of_failing_open() -> None:
    fallback = MemoryStepUpThrottleStore()
    store = RedisStepUpThrottleStore(_BrokenRedis(), fallback=fallback)

    assert [store.reserve_attempt(SUBJECT) for _ in range(3)] == [1, 2, 3]
    store.lock(SUBJECT, 600)

    assert store.lock_remaining_seconds(SUBJECT) > 0
    assert fallback.lock_remaining_seconds(SUBJECT) > 0


def test_clear_reaches_the_local_tier_too() -> None:
    """A lock recorded during an outage must not come back with the next one."""
    fallback = MemoryStepUpThrottleStore()
    fallback.lock(SUBJECT, 600)
    store = RedisStepUpThrottleStore(_FakeRedis(), fallback=fallback)

    store.clear(SUBJECT)

    assert fallback.lock_remaining_seconds(SUBJECT) == 0


def test_the_subject_never_reaches_the_store_in_the_clear() -> None:
    redis = _FakeRedis()
    store = RedisStepUpThrottleStore(redis, fallback=MemoryStepUpThrottleStore())

    store.reserve_attempt(SUBJECT)
    store.lock(SUBJECT, 60)

    assert redis.values
    assert all("user-1" not in key and "203.0.113.7" not in key for key in redis.values)


def test_the_local_tier_is_bounded() -> None:
    store = MemoryStepUpThrottleStore(capacity=8)

    for n in range(50):
        store.reserve_attempt(f"account:user-{n}")

    assert len(store._entries) == 8


# ── security review SEC-005 / SEC-008 ─────────────────────────────────────────


_PipelineRedis = _FakeRedis


def test_the_counter_and_its_expiry_are_written_in_one_transaction() -> None:
    """Review SEC-005: an INCR that lands without its EXPIRE would never age out."""
    redis = _PipelineRedis()
    store = RedisStepUpThrottleStore(redis, fallback=MemoryStepUpThrottleStore())

    store.reserve_attempt(SUBJECT)

    assert ["incr", "expire"] in redis.transactions


def test_a_lock_set_during_an_outage_still_holds_after_recovery() -> None:
    """Review SEC-008: the recovered tier did not know the lock the fallback recorded."""
    fallback = MemoryStepUpThrottleStore()
    RedisStepUpThrottleStore(_BrokenRedis(), fallback=fallback).lock(SUBJECT, 600)

    recovered = RedisStepUpThrottleStore(_PipelineRedis(), fallback=fallback)

    assert recovered.lock_remaining_seconds(SUBJECT) > 0


def test_strike_rearms_the_counter_and_counts_the_locks() -> None:
    for store in (
        MemoryStepUpThrottleStore(),
        RedisStepUpThrottleStore(_PipelineRedis(), fallback=MemoryStepUpThrottleStore()),
    ):
        for _ in range(5):
            store.reserve_attempt(SUBJECT)

        assert store.strike(SUBJECT, rearm_to=4, lock_seconds=lambda strikes: 900 * strikes) == 1
        assert store.reserve_attempt(SUBJECT) == 5
        assert store.strike(SUBJECT, rearm_to=4, lock_seconds=lambda strikes: 900 * strikes) == 2


def test_a_strike_locks_in_the_same_step_it_re_arms() -> None:
    """/code-review of #1846: a separate re-arm and lock left a window in which a request passed the lock check."""
    redis = _PipelineRedis()
    store = RedisStepUpThrottleStore(redis, fallback=MemoryStepUpThrottleStore())

    store.strike(SUBJECT, rearm_to=4, lock_seconds=lambda strikes: 900)

    assert ["set", "set", "set"] in redis.transactions
    assert 0 < store.lock_remaining_seconds(SUBJECT) <= 900


def test_the_lock_grows_with_the_strikes() -> None:
    for store in (
        MemoryStepUpThrottleStore(),
        RedisStepUpThrottleStore(_PipelineRedis(), fallback=MemoryStepUpThrottleStore()),
    ):
        store.strike(SUBJECT, rearm_to=4, lock_seconds=lambda strikes: 60 * strikes)
        first = store.lock_remaining_seconds(SUBJECT)
        store.strike(SUBJECT, rearm_to=4, lock_seconds=lambda strikes: 60 * strikes)

        assert store.lock_remaining_seconds(SUBJECT) > first
