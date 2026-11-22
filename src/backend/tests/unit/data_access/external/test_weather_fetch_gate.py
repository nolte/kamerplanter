"""REQ-046 §3.6a (#2934) — the Valkey running lock and manual-fetch cooldown.

The fake below implements the four Redis calls the gate makes with their NX/EX
and compare-and-delete semantics, so the test fails if the gate stops using them
(e.g. a get-then-set that two racing callers could both pass).
"""

from __future__ import annotations

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.data_access.external.weather_fetch_gate import (
    _RELEASE_SCRIPT,
    MANUAL_COOLDOWN_KEY,
    RUN_LOCK_KEY,
    RedisWeatherFetchGate,
)
from app.domain.interfaces.weather_fetch import WeatherFetchGateUnavailableError


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> bool | None:
        if nx and name in self.values:
            return None
        self.values[name] = value
        if ex is not None:
            self.ttls[name] = ex
        return True

    def exists(self, *names: str) -> int:
        return sum(1 for n in names if n in self.values)

    def ttl(self, name: str) -> int:
        if name not in self.values:
            return -2
        return self.ttls.get(name, -1)

    def delete(self, *names: str) -> int:
        removed = 0
        for n in names:
            removed += int(self.values.pop(n, None) is not None)
            self.ttls.pop(n, None)
        return removed

    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> int:
        assert script == _RELEASE_SCRIPT and numkeys == 1
        key, token = keys_and_args
        if self.values.get(key) == token:
            return self.delete(key)
        return 0


class _DownRedis:
    def __getattr__(self, name: str):  # noqa: ANN204
        def _fail(*_args: object, **_kwargs: object) -> None:
            raise RedisConnectionError("valkey down")

        return _fail


def test_the_lock_is_exclusive_and_expires() -> None:
    redis = _FakeRedis()
    gate = RedisWeatherFetchGate(redis)

    token = gate.acquire_run_lock(3300)

    assert token
    assert gate.is_running()
    assert redis.ttls[RUN_LOCK_KEY] == 3300
    assert gate.acquire_run_lock(3300) is None


def test_release_frees_only_the_own_lock() -> None:
    redis = _FakeRedis()
    gate = RedisWeatherFetchGate(redis)
    first = gate.acquire_run_lock(60)
    assert first is not None
    # The first lock expired and another run took over.
    redis.delete(RUN_LOCK_KEY)
    second = gate.acquire_run_lock(60)

    gate.release_run_lock(first)

    assert gate.is_running()
    assert redis.values[RUN_LOCK_KEY] == second
    assert second is not None
    gate.release_run_lock(second)
    assert not gate.is_running()


def test_the_cooldown_is_claimed_once_and_reports_the_seconds_left() -> None:
    redis = _FakeRedis()
    gate = RedisWeatherFetchGate(redis)

    assert gate.manual_cooldown_remaining() == 0
    assert gate.claim_manual_cooldown(600) == 0
    assert redis.ttls[MANUAL_COOLDOWN_KEY] == 600
    assert gate.claim_manual_cooldown(600) == 600
    assert gate.manual_cooldown_remaining() == 600

    gate.release_manual_cooldown()

    assert gate.manual_cooldown_remaining() == 0


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.acquire_run_lock(60),
        lambda g: g.is_running(),
        lambda g: g.claim_manual_cooldown(600),
        lambda g: g.manual_cooldown_remaining(),
    ],
)
def test_an_unreachable_valkey_is_reported_not_guessed(call) -> None:  # noqa: ANN001
    with pytest.raises(WeatherFetchGateUnavailableError):
        call(RedisWeatherFetchGate(_DownRedis()))


def test_releases_tolerate_an_unreachable_valkey() -> None:
    gate = RedisWeatherFetchGate(_DownRedis())

    gate.release_run_lock("token")
    gate.release_manual_cooldown()
