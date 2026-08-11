"""The redemption lockout must count, must be bounded, and must not fail open.

``RedisDevicePairingThrottleStore`` (#1118) is the counter under the
unauthenticated pairing-redemption endpoint. The route's per-minute rate limit
refuses a burst and then lets the next minute through, forever; only this
counter turns repeated failures into a lockout that grows.

What is asserted here:

* the threshold is the *login* one — the decision is read out of
  :class:`~app.domain.engines.login_throttle_engine.LoginThrottleEngine`, so a
  second constant introduced later fails these tests instead of drifting;
* a Redis outage degrades to the in-process tier instead of resetting the
  counter to zero, because failing open on this store reopens unbounded
  guessing against an endpoint that mints sessions;
* the map is bounded — an unauthenticated caller decides which addresses become
  keys;
* counters are per address, so one attacker cannot lock out a bystander;
* a successful redemption clears the address.

**Deferred to P3, deliberately.** The plan's criterion "past the threshold the
next attempt is refused *before* the code store is consulted (the store mock
records zero calls)" is an assertion about an *ordering*, and the only place
that ordering exists is ``AuthService.redeem_device_pairing`` — which P3 adds.
Writing it here would mean composing store, engine and a mock code store in the
test itself and asserting against that test-local composition: a green test that
certifies nothing about production code. P3 must add it to
``tests/unit/domain/services/test_auth_service_device_pairing.py`` as
``test_locked_out_ip_never_reaches_the_code_store``. What this file establishes
is its precondition: past the threshold, engine + store answer "not allowed".
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.data_access.external.device_pairing_throttle import (
    DEFAULT_TTL_SECONDS,
    MemoryDevicePairingThrottleStore,
    RedisDevicePairingThrottleStore,
)
from app.domain.engines.login_throttle_engine import MAX_ATTEMPTS, LoginThrottleEngine
from app.domain.interfaces.device_pairing_throttle import IDevicePairingThrottleStore

IP = "203.0.113.7"
OTHER_IP = "198.51.100.9"


class _BrokenRedis:
    """Every call raises, like a client whose server is gone."""

    def get(self, name: str) -> str | None:
        raise ConnectionError("redis is down")

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis is down")

    def delete(self, *names: str) -> None:
        raise ConnectionError("redis is down")


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int | None] = {}

    def get(self, name: str) -> str | None:
        return self.values.get(name)

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        self.values[name] = value
        self.expiries[name] = ex

    def delete(self, *names: str) -> None:
        for name in names:
            self.values.pop(name, None)
            self.expiries.pop(name, None)


def _fail_once(store: IDevicePairingThrottleStore, engine: LoginThrottleEngine, ip_address: str) -> None:
    """Record one failed redemption exactly the way the service will.

    Read-increment-write through the engine — no arithmetic of its own, so the
    tests below cannot pass against a threshold this file invented.
    """
    failed_attempts, _ = store.get_failure_state(ip_address)
    failed_attempts += 1
    store.record_failure(ip_address, failed_attempts, engine.calculate_lockout(failed_attempts))


class TestMemoryTier:
    def test_unseen_address_starts_at_zero(self) -> None:
        assert MemoryDevicePairingThrottleStore().get_failure_state(IP) == (0, None)

    def test_roundtrips_attempts_and_lockout(self) -> None:
        store = MemoryDevicePairingThrottleStore()
        locked_until = datetime.now(UTC) + timedelta(minutes=15)
        store.record_failure(IP, 5, locked_until)

        assert store.get_failure_state(IP) == (5, locked_until)

    def test_addresses_do_not_share_a_counter(self) -> None:
        store = MemoryDevicePairingThrottleStore()
        store.record_failure(IP, MAX_ATTEMPTS, datetime.now(UTC) + timedelta(minutes=15))

        assert store.get_failure_state(OTHER_IP) == (0, None)

    def test_ipv6_spellings_share_one_counter(self) -> None:
        """Two spellings of one host must not be two guessing budgets."""
        store = MemoryDevicePairingThrottleStore()
        store.record_failure("2001:DB8::1", 3, None)

        assert store.get_failure_state(" 2001:db8::1 ") == (3, None)

    def test_clear_drops_the_counter(self) -> None:
        store = MemoryDevicePairingThrottleStore()
        store.record_failure(IP, MAX_ATTEMPTS, datetime.now(UTC) + timedelta(minutes=15))

        store.clear(IP)

        assert store.get_failure_state(IP) == (0, None)

    def test_entry_expires_after_its_ttl(self) -> None:
        store = MemoryDevicePairingThrottleStore(ttl_seconds=0)
        store.record_failure(IP, MAX_ATTEMPTS, datetime.now(UTC) + timedelta(minutes=15))

        assert store.get_failure_state(IP) == (0, None)

    def test_capacity_evicts_oldest_first(self) -> None:
        store = MemoryDevicePairingThrottleStore(capacity=2)
        store.record_failure("192.0.2.1", 1, None)
        store.record_failure("192.0.2.2", 2, None)
        store.record_failure("192.0.2.3", 3, None)

        assert store.get_failure_state("192.0.2.1") == (0, None)
        assert store.get_failure_state("192.0.2.2") == (2, None)
        assert store.get_failure_state("192.0.2.3") == (3, None)

    def test_counter_outlives_the_longest_lockout(self) -> None:
        """A counter that expires under an active lockout would cut it short."""
        from app.domain.engines.login_throttle_engine import MAX_LOCKOUT_MINUTES

        assert DEFAULT_TTL_SECONDS > MAX_LOCKOUT_MINUTES * 60


class TestRedisTier:
    def test_roundtrips_through_redis_with_a_ttl(self) -> None:
        redis = _FakeRedis()
        store = RedisDevicePairingThrottleStore(redis, ttl_seconds=1234)
        locked_until = datetime.now(UTC) + timedelta(minutes=30)
        store.record_failure(IP, 6, locked_until)

        assert store.get_failure_state(IP) == (6, locked_until)
        assert set(redis.expiries.values()) == {1234}

    def test_never_writes_the_address_in_the_clear(self) -> None:
        """The source IP is personal data and its owner is unauthenticated (NFR-011)."""
        redis = _FakeRedis()
        RedisDevicePairingThrottleStore(redis).record_failure(IP, 1, None)

        stored = "".join(redis.values) + "".join(redis.values.values())
        assert IP not in stored
        assert "203.0.113" not in stored

    def test_outage_falls_back_to_the_local_tier_instead_of_resetting(self) -> None:
        fallback = MemoryDevicePairingThrottleStore()
        store = RedisDevicePairingThrottleStore(_BrokenRedis(), fallback=fallback)
        store.record_failure(IP, MAX_ATTEMPTS, None)

        assert store.get_failure_state(IP) == (MAX_ATTEMPTS, None)
        assert fallback.get_failure_state(IP) == (MAX_ATTEMPTS, None)

    def test_fallback_defaults_to_the_process_wide_instance(self) -> None:
        """A per-instance fallback would be empty on every request and count nothing."""
        from app.data_access.external.device_pairing_throttle import (
            DEFAULT_DEVICE_PAIRING_THROTTLE_STORE,
        )

        store = RedisDevicePairingThrottleStore(_FakeRedis())
        assert store._fallback is DEFAULT_DEVICE_PAIRING_THROTTLE_STORE

    @pytest.mark.parametrize("corrupt", ["not-json", '{"failed_attempts": "many"}'])
    def test_corrupt_entry_reads_as_no_record(self, corrupt: str) -> None:
        redis = _FakeRedis()
        store = RedisDevicePairingThrottleStore(redis)
        store.record_failure(IP, MAX_ATTEMPTS, None)
        redis.values[next(iter(redis.values))] = corrupt

        assert store.get_failure_state(IP) == (0, None)

    def test_clear_reaches_the_local_tier_too(self) -> None:
        """Failures recorded during an outage must not resurrect after a success.

        ``get_failure_state`` consults the fallback only while Redis is down, so
        a local entry left behind would come back on the next outage — a lockout
        the user had already cleared by pairing successfully.
        """
        fallback = MemoryDevicePairingThrottleStore()
        outage_store = RedisDevicePairingThrottleStore(_BrokenRedis(), fallback=fallback)
        outage_store.record_failure(IP, MAX_ATTEMPTS, datetime.now(UTC) + timedelta(minutes=15))

        RedisDevicePairingThrottleStore(_FakeRedis(), fallback=fallback).clear(IP)

        assert fallback.get_failure_state(IP) == (0, None)

    def test_clear_survives_a_redis_outage(self) -> None:
        fallback = MemoryDevicePairingThrottleStore()
        store = RedisDevicePairingThrottleStore(_BrokenRedis(), fallback=fallback)
        store.record_failure(IP, MAX_ATTEMPTS, None)

        store.clear(IP)

        assert store.get_failure_state(IP) == (0, None)


class TestLockoutDecisionReusesTheLoginEngine:
    """No second threshold: the decision is the one ``login_local`` already makes."""

    @pytest.fixture
    def engine(self) -> LoginThrottleEngine:
        return LoginThrottleEngine()

    @pytest.fixture(params=["memory", "redis"])
    def store(self, request: pytest.FixtureRequest) -> IDevicePairingThrottleStore:
        if request.param == "memory":
            return MemoryDevicePairingThrottleStore()
        return RedisDevicePairingThrottleStore(_FakeRedis(), fallback=MemoryDevicePairingThrottleStore())

    def test_attempts_below_the_threshold_stay_allowed(
        self, store: IDevicePairingThrottleStore, engine: LoginThrottleEngine
    ) -> None:
        for _ in range(MAX_ATTEMPTS - 1):
            _fail_once(store, engine, IP)

        assert engine.check_allowed(*store.get_failure_state(IP)) is True

    def test_the_threshold_attempt_locks_the_address_out(
        self, store: IDevicePairingThrottleStore, engine: LoginThrottleEngine
    ) -> None:
        """The precondition of P3's 'refused before the code store is consulted'."""
        for _ in range(MAX_ATTEMPTS):
            _fail_once(store, engine, IP)

        failed_attempts, locked_until = store.get_failure_state(IP)
        assert failed_attempts == MAX_ATTEMPTS
        assert engine.check_allowed(failed_attempts, locked_until) is False
        assert engine.get_lockout_minutes(locked_until) > 0

    def test_lockout_does_not_spill_onto_another_address(
        self, store: IDevicePairingThrottleStore, engine: LoginThrottleEngine
    ) -> None:
        for _ in range(MAX_ATTEMPTS * 2):
            _fail_once(store, engine, IP)

        assert engine.check_allowed(*store.get_failure_state(OTHER_IP)) is True

    def test_a_successful_redemption_clears_the_lockout(
        self, store: IDevicePairingThrottleStore, engine: LoginThrottleEngine
    ) -> None:
        for _ in range(MAX_ATTEMPTS):
            _fail_once(store, engine, IP)
        assert engine.check_allowed(*store.get_failure_state(IP)) is False

        store.clear(IP)

        assert store.get_failure_state(IP) == (0, None)
        assert engine.check_allowed(*store.get_failure_state(IP)) is True
