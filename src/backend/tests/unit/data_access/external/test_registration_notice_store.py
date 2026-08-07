"""The REQ-023 §3.2 suppression window must actually suppress, and stay bounded.

``/auth/register`` is anonymous, so an attacker picks both the recipient of the
duplicate-registration notice and how often it fires. The window is the only
thing between that and an unauthenticated mail-bombing primitive, so three
properties are asserted rather than assumed:

* a claim is granted **once** per address per window and refused afterwards;
* the map is **bounded** — the caller decides which keys go in;
* a Redis outage degrades to the in-process tier instead of defaulting to
  "yes", which during an outage would be the unbounded send itself.
"""

from app.data_access.external.registration_notice_store import (
    MemoryRegistrationNoticeStore,
    RedisRegistrationNoticeStore,
)

EMAIL = "victim@example.com"


class _BrokenRedis:
    """Every call raises, like a client whose server is gone."""

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> object:
        raise ConnectionError("redis is down")


class _FakeRedis:
    """Enough of ``SET key value NX EX`` to exercise the claim."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int | None] = {}

    def set(self, name: str, value: str, ex: int | None = None, nx: bool = False) -> object:
        if nx and name in self.values:
            return None
        self.values[name] = value
        self.expiries[name] = ex
        return True


class TestMemoryTier:
    def test_first_claim_is_granted(self) -> None:
        assert MemoryRegistrationNoticeStore().claim(EMAIL) is True

    def test_second_claim_inside_the_window_is_refused(self) -> None:
        store = MemoryRegistrationNoticeStore()
        store.claim(EMAIL)

        assert store.claim(EMAIL) is False

    def test_claim_is_granted_again_once_the_window_expired(self) -> None:
        store = MemoryRegistrationNoticeStore(ttl_seconds=0)
        store.claim(EMAIL)

        assert store.claim(EMAIL) is True

    def test_addresses_do_not_share_a_window(self) -> None:
        store = MemoryRegistrationNoticeStore()
        store.claim(EMAIL)

        assert store.claim("someone-else@example.com") is True

    def test_normalises_case_and_surrounding_whitespace(self) -> None:
        """``get_by_email`` matches case-insensitively; the window must too.

        Otherwise ``Victim@Example.com`` opens a second window for the same
        inbox, and the bound is only as tight as the attacker's imagination
        about capitalisation.
        """
        store = MemoryRegistrationNoticeStore()
        store.claim(EMAIL)

        assert store.claim("  Victim@Example.COM ") is False

    def test_capacity_evicts_oldest_first(self) -> None:
        """The bound is real, and eviction reopens exactly the oldest window.

        That reopening is the residual this tier trades for a fixed memory
        ceiling: at ``_FALLBACK_CAPACITY`` distinct addresses in one window, the
        oldest recipient can be notified a second time. It costs one extra mail
        to a real account, against an unbounded map an anonymous caller fills.
        A refused claim writes nothing, so the two checks below do not disturb
        the order they are inspecting.
        """
        store = MemoryRegistrationNoticeStore(capacity=2)
        store.claim("a@example.com")
        store.claim("b@example.com")
        store.claim("c@example.com")

        assert store.claim("c@example.com") is False
        assert store.claim("b@example.com") is False
        assert store.claim("a@example.com") is True


class TestRedisTier:
    def test_claim_is_granted_once_and_carries_the_ttl(self) -> None:
        redis = _FakeRedis()
        store = RedisRegistrationNoticeStore(redis, ttl_seconds=1234)

        assert store.claim(EMAIL) is True
        assert store.claim(EMAIL) is False
        assert set(redis.expiries.values()) == {1234}

    def test_never_writes_the_address_in_the_clear(self) -> None:
        redis = _FakeRedis()
        RedisRegistrationNoticeStore(redis).claim(EMAIL)

        stored = "".join(redis.values) + "".join(redis.values.values())
        assert EMAIL not in stored
        assert "victim" not in stored

    def test_outage_falls_back_to_the_local_tier_instead_of_granting(self) -> None:
        fallback = MemoryRegistrationNoticeStore()
        store = RedisRegistrationNoticeStore(_BrokenRedis(), fallback=fallback)

        assert store.claim(EMAIL) is True
        assert store.claim(EMAIL) is False

    def test_fallback_defaults_to_the_process_wide_instance(self) -> None:
        """A per-instance fallback would be empty every time and suppress nothing."""
        from app.data_access.external.registration_notice_store import (
            DEFAULT_REGISTRATION_NOTICE_STORE,
        )

        store = RedisRegistrationNoticeStore(_FakeRedis())

        assert store._fallback is DEFAULT_REGISTRATION_NOTICE_STORE
