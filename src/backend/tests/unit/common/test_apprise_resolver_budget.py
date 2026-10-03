"""#1995 — the Apprise host resolver: per-owner share, separate lanes, host cache.

The DNS seam ``url_safety.resolve_host_addresses`` is replaced by a double whose
``stuck*`` names block until released (a nameserver that never answers) and
whose ``boom*`` names raise once released. Every other name answers at once.
"""

import threading
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog.testing

from app.common import url_safety
from app.common.exceptions import ValidationError
from app.common.url_safety import _HostCache, _ResolverLane
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import ChannelPreference, ChannelResult, Notification, NotificationPreferences

PUBLIC = "93.184.216.34"
DEADLINE = 0.3
TIMEOUT_REASON = "An Apprise URL host did not resolve in time."


class _Resolver:
    def __init__(self) -> None:
        self.release = threading.Event()
        self.calls: list[str] = []
        self._lock = threading.Lock()
        self.inside = 0

    def __call__(self, host: str) -> list[str]:
        self.calls.append(host)
        if host.startswith("nx"):
            raise OSError("Name or service not known")
        if host.startswith("loop"):
            return ["127.0.0.1"]
        if not host.startswith(("stuck", "boom")):
            return [PUBLIC]
        with self._lock:
            self.inside += 1
        try:
            self.release.wait(30)
            if host.startswith("boom"):
                raise RuntimeError("resolver crashed")
            return [PUBLIC]
        finally:
            with self._lock:
                self.inside -= 1

    def drain(self) -> None:
        self.release.set()
        end = time.monotonic() + 10
        while self.inside and time.monotonic() < end:
            time.sleep(0.01)


@pytest.fixture
def resolver(monkeypatch):
    double = _Resolver()
    monkeypatch.setattr(url_safety, "APPRISE_RESOLVE_TIMEOUT_SECONDS", DEADLINE)
    monkeypatch.setattr(url_safety, "resolve_host_addresses", double)
    yield double
    double.drain()


def _wait_until(predicate, seconds: float = 5.0) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def _urls(*hosts: str) -> list[str]:
    return [f"gotify://{h}/t" for h in hosts]


# ── The lane: per-owner cap, no queue, slot released when the lookup ends ──


def test_the_owner_cap_is_enforced_per_owner_and_released_when_a_resolution_ends(resolver):
    lane = _ResolverLane("t", workers=8, per_owner=3, trusts_cache=True)
    held = [lane.try_submit("a", resolver, f"stuck{i}") for i in range(3)]
    assert all(f is not None for f in held)
    assert lane.try_submit("a", resolver, "stuck3") is None
    assert lane.try_submit("b", resolver, "fast.example") is not None  # another owner is unaffected
    resolver.release.set()
    assert _wait_until(lambda: lane.outstanding("a") == 0), lane.outstanding("a")
    assert lane.try_submit("a", resolver, "fast.example") is not None


def test_a_full_lane_refuses_instead_of_queueing(resolver):
    lane = _ResolverLane("t", workers=2, per_owner=3, trusts_cache=True)
    assert lane.try_submit("a", resolver, "stuck-a") is not None
    assert lane.try_submit("b", resolver, "stuck-b") is not None
    assert lane.try_submit("c", resolver, "fast.example") is None
    assert lane.outstanding() == 2


def test_a_resolution_that_raises_frees_its_slot(resolver):
    lane = _ResolverLane("t", workers=8, per_owner=1, trusts_cache=True)
    future = lane.try_submit("a", resolver, "boom.example")
    assert future is not None
    assert lane.try_submit("a", resolver, "fast.example") is None
    resolver.release.set()
    assert _wait_until(future.done)
    assert isinstance(future.exception(), RuntimeError)
    assert _wait_until(lambda: lane.outstanding("a") == 0)
    assert lane.try_submit("a", resolver, "fast.example") is not None


def test_a_timed_out_resolution_keeps_its_slot_until_its_thread_returns(resolver):
    """The deadline ends the wait, not the lookup: the slot follows the thread (#1995)."""
    lane = _ResolverLane("t", workers=8, per_owner=3, trusts_cache=True)
    refusals = url_safety._apprise_resolution_refusals(_urls("stuck1.example"), owner_key="a", lane=lane)
    assert refusals == {0: TIMEOUT_REASON}
    assert lane.outstanding("a") == 1
    resolver.release.set()
    assert _wait_until(lambda: lane.outstanding("a") == 0)


# ── Refusal at once, same wording as a timeout, owner never logged ─────


def test_excess_is_refused_at_once_without_reaching_the_resolver(resolver):
    lane = _ResolverLane("t", workers=8, per_owner=3, trusts_cache=True)
    url_safety._apprise_resolution_refusals(_urls("stuck1", "stuck2", "stuck3"), owner_key="user-7f3a", lane=lane)
    assert lane.outstanding("user-7f3a") == 3
    calls_before = len(resolver.calls)
    with structlog.testing.capture_logs() as logs:
        started = time.monotonic()
        refusals = url_safety._apprise_resolution_refusals(_urls("fast.example"), owner_key="user-7f3a", lane=lane)
        elapsed = time.monotonic() - started
    assert refusals == {0: TIMEOUT_REASON}  # no new oracle: reads like a timeout
    assert elapsed < DEADLINE / 3, elapsed
    assert len(resolver.calls) == calls_before
    capped = [e for e in logs if e["event"] == "apprise_resolution_capped"]
    assert capped and "user-7f3a" not in repr(logs)


def test_a_call_with_more_hosts_than_its_share_resolves_them_in_turn(resolver):
    """A legitimate list of more distinct names than the share still resolves within the deadline."""
    lane = _ResolverLane("t", workers=8, per_owner=3, trusts_cache=True)
    hosts = [f"h{i}.example" for i in range(7)]
    assert url_safety._apprise_resolution_refusals(_urls(*hosts), owner_key="a", lane=lane) == {}
    assert sorted(resolver.calls) == sorted(hosts)


# ── Save and send use separate lanes ────────────────────────────────


def test_save_and_send_do_not_share_a_pool(resolver):
    assert url_safety._save_lane is not url_safety._send_lane
    assert url_safety._save_lane._pool is not url_safety._send_lane._pool
    with pytest.raises(ValidationError):
        url_safety.validate_apprise_urls(_urls("stuck1", "stuck2", "stuck3"), owner_key="owner-x")
    assert url_safety._save_lane.outstanding("owner-x") == 3
    # The same owner's delivery still resolves: its save share is spent, its send share is not.
    allowed, refused = url_safety.partition_apprise_urls(_urls("fast.example"), owner_key="owner-x")
    assert (allowed, refused) == (_urls("fast.example"), 0)
    assert url_safety._send_lane.outstanding("owner-x") == 0


# ── The host cache ──────────────────────────────────────────────────


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_cache_hit_miss_and_expiry_with_a_fake_clock():
    clock = _Clock()
    cache = _HostCache(ttl=60, negative_ttl=10, max_entries=8, clock=clock)
    assert cache.lookup("gotify.example") == (False, None)
    cache.store("Gotify.Example", (PUBLIC,))
    assert cache.lookup("gotify.example") == (True, (PUBLIC,))  # names are case-insensitive
    clock.now += 59.9
    assert cache.lookup("gotify.example") == (True, (PUBLIC,))
    clock.now += 0.1
    assert cache.lookup("gotify.example") == (False, None)
    assert len(cache) == 0


def test_negative_cache_uses_the_short_ttl():
    clock = _Clock()
    cache = _HostCache(ttl=60, negative_ttl=10, max_entries=8, clock=clock)
    cache.store("nx.example", None)
    assert cache.lookup("nx.example") == (True, None)
    clock.now += 10
    assert cache.lookup("nx.example") == (False, None)


def test_cache_size_is_bounded_and_drops_the_oldest():
    cache = _HostCache(ttl=60, negative_ttl=10, max_entries=2, clock=_Clock())
    cache.store("a.example", (PUBLIC,))
    cache.store("b.example", (PUBLIC,))
    cache.store("c.example", None)
    assert len(cache) == 2
    assert cache.lookup("a.example") == (False, None)
    assert cache.lookup("c.example") == (True, None)


def test_the_resolver_is_consulted_once_per_ttl(resolver, monkeypatch):
    clock = _Clock()
    monkeypatch.setattr(url_safety, "_resolution_cache", _HostCache(ttl=60, negative_ttl=10, clock=clock))
    lane = _ResolverLane("t", trusts_cache=True)
    for _ in range(2):
        assert url_safety._apprise_resolution_refusals(
            _urls("fast.example", "loop.example"), owner_key="a", lane=lane
        ) == {1: "An Apprise URL host resolves to a loopback, link-local or reserved address."}
    assert sorted(resolver.calls) == ["fast.example", "loop.example"]  # the blocked answer is cached too
    clock.now += 60
    url_safety._apprise_resolution_refusals(_urls("fast.example"), owner_key="a", lane=lane)
    assert resolver.calls.count("fast.example") == 2


def test_a_failure_is_cached_for_the_negative_ttl_only(resolver, monkeypatch):
    clock = _Clock()
    monkeypatch.setattr(url_safety, "_resolution_cache", _HostCache(ttl=60, negative_ttl=10, clock=clock))
    lane = _ResolverLane("t", trusts_cache=True)
    reason = "An Apprise URL host could not be resolved."
    for _ in range(2):
        assert url_safety._apprise_resolution_refusals(_urls("nx.example"), owner_key="a", lane=lane) == {0: reason}
    assert resolver.calls == ["nx.example"]
    clock.now += 10
    url_safety._apprise_resolution_refusals(_urls("nx.example"), owner_key="a", lane=lane)
    assert resolver.calls == ["nx.example", "nx.example"]


def test_a_timeout_is_never_cached_and_a_late_answer_is(resolver, monkeypatch):
    """A timeout says nothing about the name; the answer the stuck lookup ends with does."""
    cache = _HostCache(ttl=60, negative_ttl=10, clock=_Clock())
    monkeypatch.setattr(url_safety, "_resolution_cache", cache)
    lane = _ResolverLane("t", trusts_cache=True)
    assert url_safety._apprise_resolution_refusals(_urls("stuck.example"), owner_key="a", lane=lane) == {
        0: TIMEOUT_REASON
    }
    assert cache.lookup("stuck.example") == (False, None)
    resolver.release.set()
    assert _wait_until(lambda: cache.lookup("stuck.example")[0])
    assert cache.lookup("stuck.example") == (True, (PUBLIC,))
    assert url_safety._apprise_resolution_refusals(_urls("stuck.example"), owner_key="a", lane=lane) == {}


def test_the_send_lane_takes_only_a_blocked_verdict_from_the_cache_and_writes_nothing(resolver, monkeypatch):
    """#1995 review F1: at send, a cached ``ok`` or failure is resolved again; only ``blocked`` is reused."""
    cache = _HostCache(ttl=60, negative_ttl=10, clock=_Clock())
    monkeypatch.setattr(url_safety, "_resolution_cache", cache)
    cache.store("fast.example", (PUBLIC,))  # a cached ok: must be resolved again at send
    cache.store("nx-cached.example", None)  # stale failure
    cache.store("loop.example", ("127.0.0.1",))
    send = _ResolverLane("send-t", trusts_cache=False)
    refusals = url_safety._apprise_resolution_refusals(
        _urls("fast.example", "nx-cached.example", "loop.example", "other.example"), owner_key="a", lane=send
    )
    assert sorted(resolver.calls) == ["fast.example", "nx-cached.example", "other.example"]
    assert set(refusals) == {1, 2}  # NXDOMAIN now, loop from cache; fast/other resolve public
    assert cache.lookup("other.example") == (False, None), "the send lane wrote into the cache"


# ── The send path knows whose delivery it is ────────────────────────


@pytest.mark.asyncio
async def test_a_channel_sees_the_recipient_as_owner_before_sending():
    """The Apprise send share is keyed by ``notification.user_key``; the engine sets it before ``send``."""
    seen: list[tuple[str, str]] = []
    channel = MagicMock()
    channel.channel_key = "apprise"
    channel.supports_batching = False

    async def _send(notification, config):
        seen.append((notification.user_key, notification.tenant_key))
        return ChannelResult(channel_key="apprise", success=True)

    async def _send_batch(notifications, config):
        return await _send(notifications[0], config)

    channel.send = AsyncMock(side_effect=_send)
    channel.send_batch = AsyncMock(side_effect=_send_batch)
    prefs = MagicMock()
    prefs.get_by_user.return_value = NotificationPreferences(
        user_key="u1", channels={"apprise": ChannelPreference(enabled=True, priority=10)}
    )
    repo = MagicMock()
    repo.create.side_effect = lambda n: n
    registry = MagicMock()
    registry.get.return_value = channel
    registry.all_keys.return_value = ["apprise"]
    redis = MagicMock()
    redis.get.return_value = None
    engine = NotificationEngine(
        notification_repo=repo,
        preference_repo=prefs,
        channel_registry=registry,
        redis_client=redis,
        user_repo=MagicMock(),
    )
    engine._is_quiet_hours = MagicMock(return_value=False)  # type: ignore[method-assign]

    await engine.notify("u1", "t1", Notification(notification_type="care_watering", title="Water", body="Tomato"))
    channel.supports_batching = True
    await engine.notify_batch("u1", "t1", [Notification(notification_type="care_watering", title="W", body="T")])
    assert seen == [("u1", "t1"), ("u1", "t1")]
