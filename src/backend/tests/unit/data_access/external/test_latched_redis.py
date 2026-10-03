"""``LatchedRedis`` — the probe plan of the throttle stores' Valkey client (#2062).

The route-level behaviour (a hanging Valkey costs one request one timeout, the
following ones nothing) is held by
``tests/api/test_auth_budget_stores_bounded_wait.py``. This file pins the
schedule and the edges: the stores keep falling back while the latch is shut,
one call probes when it is due, a success reopens the client, and an error
outside redis-py's family is a defect that neither latches nor is swallowed.
"""

from __future__ import annotations

from typing import Any

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.data_access.external import latched_redis
from app.data_access.external.latched_redis import LatchedRedis
from app.data_access.external.step_up_throttle import MemoryStepUpThrottleStore, RedisStepUpThrottleStore


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class _Pipeline:
    def __init__(self, owner: _Valkey) -> None:
        self._owner = owner
        self._ops: list[str] = []

    def incr(self, key: str) -> _Pipeline:
        self._ops.append(key)
        return self

    def expire(self, key: str, seconds: int) -> _Pipeline:
        return self

    def execute(self) -> list[Any]:
        self._owner.calls += 1
        self._owner.fail_if_down()
        results: list[Any] = []
        for key in self._ops:
            self._owner.counts[key] = self._owner.counts.get(key, 0) + 1
            results += [self._owner.counts[key], True]
        return results


class _Valkey:
    """Answers until ``error`` is set, then raises it from every call that reaches it."""

    def __init__(self) -> None:
        self.error: BaseException | None = None
        self.calls = 0
        self.counts: dict[str, int] = {}

    def fail_if_down(self) -> None:
        if self.error is not None:
            raise self.error

    def pipeline(self, transaction: bool = True) -> _Pipeline:
        return _Pipeline(self)

    def get(self, name: str) -> str | None:
        self.calls += 1
        self.fail_if_down()
        return None

    def ttl(self, name: str) -> int:
        self.calls += 1
        self.fail_if_down()
        return -2


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    fake = _Clock()
    monkeypatch.setattr(latched_redis.time, "monotonic", fake)
    return fake


def _store(valkey: _Valkey) -> tuple[RedisStepUpThrottleStore, LatchedRedis]:
    client = LatchedRedis(valkey)
    return RedisStepUpThrottleStore(client, ttl_seconds=3600, fallback=MemoryStepUpThrottleStore(3600)), client


def test_after_a_timeout_calls_fall_back_without_reaching_valkey(clock: _Clock) -> None:
    valkey = _Valkey()
    store, client = _store(valkey)
    valkey.error = RedisTimeoutError("Timeout reading from socket")

    counts = [store.reserve_attempt("password-reset:a@example.com") for _ in range(4)]

    assert counts == [1, 2, 3, 4], "the in-process tier must keep counting while the latch is shut"
    assert valkey.calls == 1, "only the call that met the failure may reach Valkey"
    assert client.is_down


def test_one_call_probes_when_due_and_a_success_reopens_the_client(clock: _Clock) -> None:
    valkey = _Valkey()
    store, client = _store(valkey)
    valkey.error = RedisConnectionError("refused")
    store.reserve_attempt("s")

    clock.now += latched_redis.PROBE_INITIAL_DELAY_S
    valkey.error = None
    store.reserve_attempt("s")

    assert valkey.calls == 2
    assert not client.is_down
    store.reserve_attempt("s")
    assert valkey.calls == 3


def test_a_failed_probe_doubles_the_wait(clock: _Clock) -> None:
    valkey = _Valkey()
    store, _ = _store(valkey)
    valkey.error = RedisConnectionError("refused")
    store.reserve_attempt("s")

    clock.now += latched_redis.PROBE_INITIAL_DELAY_S
    store.reserve_attempt("s")  # probe 1 fails
    clock.now += latched_redis.PROBE_INITIAL_DELAY_S
    store.reserve_attempt("s")  # not due yet: the delay doubled
    calls_before_second_probe = valkey.calls
    clock.now += latched_redis.PROBE_INITIAL_DELAY_S
    store.reserve_attempt("s")  # probe 2

    assert calls_before_second_probe == 2
    assert valkey.calls == 3


def test_an_error_outside_the_redis_family_passes_through_and_does_not_latch(clock: _Clock) -> None:
    valkey = _Valkey()
    client = LatchedRedis(valkey)
    valkey.error = RuntimeError("a defect, not an outage")

    with pytest.raises(RuntimeError):
        client.get("k")

    assert not client.is_down
