"""The SEC-H-010 lockout store must stay bounded and must not fail open.

``AuthService`` asks this store whether an address that owns no account is
already locked out. Two properties matter beyond "it stores things":

* it is **bounded** — an unauthenticated caller decides which keys go in, so an
  unbounded map would trade an enumeration oracle for a memory-growth vector;
* a Redis outage degrades to the in-process tier rather than fail-open. Failing
  open here does not skip a rate limit, it reopens the disclosure.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.data_access.external.unknown_account_store import (
    MemoryUnknownAccountStore,
    RedisUnknownAccountStore,
)

EMAIL = "ghost@example.com"


class _BrokenRedis:
    """Every call raises, like a client whose server is gone."""

    def get(self, key: str) -> str | None:
        raise ConnectionError("redis is down")

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis is down")


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int | None] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value
        self.expiries[key] = ex


class TestMemoryTier:
    def test_unseen_address_starts_at_zero(self) -> None:
        assert MemoryUnknownAccountStore().get_failure_state(EMAIL) == (0, None)

    def test_roundtrips_attempts_and_lockout(self) -> None:
        store = MemoryUnknownAccountStore()
        locked_until = datetime.now(UTC) + timedelta(minutes=15)
        store.record_failure(EMAIL, 5, locked_until)

        assert store.get_failure_state(EMAIL) == (5, locked_until)

    def test_addresses_do_not_share_a_counter(self) -> None:
        store = MemoryUnknownAccountStore()
        store.record_failure(EMAIL, 5, None)

        assert store.get_failure_state("other@example.com") == (0, None)

    def test_normalises_case_and_surrounding_whitespace(self) -> None:
        """``get_by_email`` matches case-insensitively; the counter must too.

        Otherwise ``Ghost@example.com`` gets a fresh counter while the account
        lookup treats it as the same address — the oracle back through the door.
        """
        store = MemoryUnknownAccountStore()
        store.record_failure(EMAIL, 3, None)

        assert store.get_failure_state("  Ghost@Example.COM ") == (3, None)

    def test_entry_expires_after_its_ttl(self) -> None:
        store = MemoryUnknownAccountStore(ttl_seconds=0)
        store.record_failure(EMAIL, 5, datetime.now(UTC) + timedelta(minutes=15))

        assert store.get_failure_state(EMAIL) == (0, None)

    def test_capacity_evicts_oldest_first(self) -> None:
        store = MemoryUnknownAccountStore(capacity=2)
        store.record_failure("a@example.com", 1, None)
        store.record_failure("b@example.com", 2, None)
        store.record_failure("c@example.com", 3, None)

        assert store.get_failure_state("a@example.com") == (0, None)
        assert store.get_failure_state("b@example.com") == (2, None)
        assert store.get_failure_state("c@example.com") == (3, None)


class TestRedisTier:
    def test_roundtrips_through_redis_with_a_ttl(self) -> None:
        redis = _FakeRedis()
        store = RedisUnknownAccountStore(redis, ttl_seconds=1234)
        locked_until = datetime.now(UTC) + timedelta(minutes=30)
        store.record_failure(EMAIL, 6, locked_until)

        assert store.get_failure_state(EMAIL) == (6, locked_until)
        assert set(redis.expiries.values()) == {1234}

    def test_never_writes_the_address_in_the_clear(self) -> None:
        redis = _FakeRedis()
        RedisUnknownAccountStore(redis).record_failure(EMAIL, 1, None)

        stored = "".join(redis.values) + "".join(redis.values.values())
        assert EMAIL not in stored
        assert "ghost" not in stored

    def test_outage_falls_back_to_the_local_tier_instead_of_resetting(self) -> None:
        fallback = MemoryUnknownAccountStore()
        store = RedisUnknownAccountStore(_BrokenRedis(), fallback=fallback)
        store.record_failure(EMAIL, 5, None)

        assert store.get_failure_state(EMAIL) == (5, None)
        assert fallback.get_failure_state(EMAIL) == (5, None)

    def test_fallback_defaults_to_the_process_wide_instance(self) -> None:
        """A per-instance fallback would be empty on every request and count nothing."""
        from app.data_access.external.unknown_account_store import DEFAULT_UNKNOWN_ACCOUNT_STORE

        assert RedisUnknownAccountStore(_FakeRedis())._fallback is DEFAULT_UNKNOWN_ACCOUNT_STORE

    @pytest.mark.parametrize("corrupt", ["not-json", '{"failed_attempts": "many"}'])
    def test_corrupt_entry_reads_as_no_record(self, corrupt: str) -> None:
        redis = _FakeRedis()
        store = RedisUnknownAccountStore(redis)
        store.record_failure(EMAIL, 5, None)
        redis.values[next(iter(redis.values))] = corrupt

        assert store.get_failure_state(EMAIL) == (0, None)
