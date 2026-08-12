"""A pairing code must be redeemable exactly once, and never be readable at rest.

``RedisDevicePairingCodeStore`` (#1118) is the custody layer under the QR
device-pairing flow. Three properties are load-bearing and none of them is
visible from a "it stores things" test:

* **single use** — the read and the delete travel in *one* pipeline. A
  get-then-delete pair would let two simultaneous redemptions of one code both
  observe the payload and both mint a session, and it would pass every
  sequential test.
* **no oracle** — unknown, already-used, expired and "Redis is down" all answer
  ``None``. An exception on any of them would tell a guesser which of their
  codes was real.
* **nothing readable at rest** — the raw code appears neither as a Redis key nor
  inside a value, so a dump or a slow-log line is not a bag of live credentials.

The TTL window itself is pinned on the settings model rather than here, because
that is where an operator's out-of-range value has to be refused.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from app.config.settings import Settings
from app.data_access.external.redis_device_pairing import (
    DEFAULT_TTL_SECONDS,
    RedisDevicePairingCodeStore,
)

CODE = "s3cr3t-pairing-code-value"
USER_KEY = "user-42"


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
        self._redis.batches.append(list(self._commands))
        results: list[Any] = []
        for operation, name in self._commands:
            if operation == "get":
                results.append(self._redis.values.get(name))
            else:
                results.append(1 if self._redis.values.pop(name, None) is not None else 0)
        self._commands = []
        return results


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int | None] = {}
        #: One entry per ``execute()``; each is the list of commands that were
        #: queued together. This is what makes the atomicity claim testable.
        self.batches: list[list[tuple[str, str]]] = []

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        self.values[name] = value
        self.expiries[name] = ex

    def pipeline(self) -> _FakePipeline:
        return _FakePipeline(self)


class _BrokenRedis:
    """Every call raises, like a client whose server is gone."""

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis is down")

    def pipeline(self) -> Any:
        raise ConnectionError("redis is down")


class TestSingleUse:
    def test_consume_returns_the_payload_once_and_none_afterwards(self) -> None:
        redis = _FakeRedis()
        store = RedisDevicePairingCodeStore(redis)
        store.issue(CODE, USER_KEY)

        first = store.consume(CODE)
        assert first is not None
        assert first.user_key == USER_KEY

        assert store.consume(CODE) is None
        assert store.consume(CODE) is None

    def test_read_and_delete_travel_in_one_pipeline(self) -> None:
        """The property a sequential test cannot see.

        Two redemptions racing on one code are separated only by Redis running
        the queued ``GET``+``DEL`` as one unit. Asserting on the *batch* is the
        only way this test fails if someone replaces the pipeline with a read,
        a branch and a later delete — which behaves identically here.
        """
        redis = _FakeRedis()
        store = RedisDevicePairingCodeStore(redis)
        store.issue(CODE, USER_KEY)

        store.consume(CODE)

        assert len(redis.batches) == 1, "the read and the delete were not sent together"
        batch = redis.batches[0]
        assert [operation for operation, _ in batch] == ["get", "delete"]
        assert len({name for _, name in batch}) == 1, "delete addressed a different key than get"

    def test_issued_at_survives_the_roundtrip(self) -> None:
        redis = _FakeRedis()
        store = RedisDevicePairingCodeStore(redis)
        before = datetime.now(UTC)

        store.issue(CODE, USER_KEY)
        record = store.consume(CODE)

        assert record is not None
        assert record.issued_at.tzinfo is not None
        assert before <= record.issued_at <= datetime.now(UTC)


class TestExpiry:
    def test_ttl_is_passed_through_to_redis(self) -> None:
        redis = _FakeRedis()
        RedisDevicePairingCodeStore(redis, ttl_seconds=77).issue(CODE, USER_KEY)

        assert set(redis.expiries.values()) == {77}

    def test_default_ttl_sits_inside_the_documented_window(self) -> None:
        """A store built without an explicit TTL must not be unbounded."""
        assert 60 <= DEFAULT_TTL_SECONDS <= 120

    def test_issue_returns_the_expiry_the_caller_can_advertise(self) -> None:
        store = RedisDevicePairingCodeStore(_FakeRedis(), ttl_seconds=90)

        expires_at = store.issue(CODE, USER_KEY)

        remaining = expires_at - datetime.now(UTC)
        assert timedelta(seconds=85) <= remaining <= timedelta(seconds=90)

    def test_expired_code_reads_as_unknown(self) -> None:
        """Redis drops the key on TTL; the store must answer ``None``, not raise."""
        redis = _FakeRedis()
        store = RedisDevicePairingCodeStore(redis, ttl_seconds=90)
        store.issue(CODE, USER_KEY)
        redis.values.clear()  # what Redis does when the TTL elapses

        assert store.consume(CODE) is None


class TestNoOracle:
    def test_unknown_code_yields_none_without_raising(self) -> None:
        assert RedisDevicePairingCodeStore(_FakeRedis()).consume("never-issued") is None

    def test_a_redis_outage_answers_like_an_unknown_code(self) -> None:
        """Fails closed: an outage refuses redemption instead of granting it."""
        assert RedisDevicePairingCodeStore(_BrokenRedis()).consume(CODE) is None

    def test_issue_fails_loud_when_redis_is_down(self) -> None:
        """The other direction of the same decision.

        Swallowing the write would hand the user a QR code that can never be
        redeemed — a silent failure nobody can report. See the module docstring
        of the store.
        """
        with pytest.raises(ConnectionError):
            RedisDevicePairingCodeStore(_BrokenRedis()).issue(CODE, USER_KEY)

    @pytest.mark.parametrize("corrupt", ["not-json", "{}", '{"user_key": "u", "issued_at": "nonsense"}'])
    def test_corrupt_entry_reads_as_unknown_and_is_still_consumed(self, corrupt: str) -> None:
        redis = _FakeRedis()
        store = RedisDevicePairingCodeStore(redis)
        store.issue(CODE, USER_KEY)
        redis.values[next(iter(redis.values))] = corrupt

        assert store.consume(CODE) is None
        assert redis.values == {}, "a corrupt entry must not survive its redemption"


class TestPseudonymisation:
    def test_the_raw_code_is_never_a_key_or_a_value(self) -> None:
        redis = _FakeRedis()
        RedisDevicePairingCodeStore(redis).issue(CODE, USER_KEY)

        stored = "".join(redis.values) + "".join(redis.values.values())
        assert CODE not in stored
        assert "pairing-code-value" not in stored

    def test_two_codes_do_not_share_a_slot(self) -> None:
        redis = _FakeRedis()
        store = RedisDevicePairingCodeStore(redis)
        store.issue(CODE, USER_KEY)
        store.issue("a-different-code", "user-99")

        assert store.consume(CODE) is not None
        other = store.consume("a-different-code")
        assert other is not None and other.user_key == "user-99"

    def test_the_stored_value_carries_only_user_key_and_issued_at(self) -> None:
        redis = _FakeRedis()
        RedisDevicePairingCodeStore(redis).issue(CODE, USER_KEY)

        payload = json.loads(next(iter(redis.values.values())))
        assert set(payload) == {"user_key", "issued_at"}


class TestSettingsWindow:
    """The 60–120 s window is enforced by the model, not by a comment (#1118 P1)."""

    def test_default_is_ninety_seconds(self) -> None:
        assert Settings().device_pairing_ttl_seconds == 90

    @pytest.mark.parametrize("value", [60, 90, 120])
    def test_values_inside_the_window_are_accepted(self, value: int) -> None:
        assert Settings(device_pairing_ttl_seconds=value).device_pairing_ttl_seconds == value

    @pytest.mark.parametrize("value", [-1, 0, 30, 59, 121, 3600])
    def test_values_outside_the_window_refuse_startup(self, value: int) -> None:
        with pytest.raises(ValidationError):
            Settings(device_pairing_ttl_seconds=value)
