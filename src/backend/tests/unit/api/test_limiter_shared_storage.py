"""The IP rate limits count per deployment, not per process (#2045).

slowapi's ``Limiter`` stores its counters in ``memory://`` unless told otherwise,
so every backend replica — and every worker process inside one — kept its own
count. ``N`` processes multiplied each documented limit by ``N``, including the
mail bound on ``/auth/resend-verification``.

These tests pin the three properties the fix is made of:

* two limiters built by the production factory against one shared storage
  spend **one** budget (the "two replicas" case);
* an unreachable or failing storage degrades to a **per-process** count — the
  limit still applies, the route neither fails open nor answers 500;
* with ``redis_url`` configured and no explicit override, the factory does not
  quietly land on ``memory://`` again.

No live Valkey is needed: the shared storage is an in-process ``limits`` storage
registered under its own scheme, and the "unreachable" case points at a port
nothing listens on.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from limits.storage import MemoryStorage
from redis.exceptions import ConnectionError as RedisConnectionError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import _rate_limit_key
from app.config.settings import settings

_PROBE_LIMIT = "2/minute"

#: One backing store both "replicas" talk to — what Valkey is in production.
_SHARED_BACKING = MemoryStorage()


class _SharedProcessStorage(MemoryStorage):
    """A ``limits`` storage whose every instance reads and writes one backing store.

    Each ``Limiter`` builds its own storage object from the URI, exactly as two
    replicas each open their own Redis connection; what makes the count shared
    is that the objects point at the same data. Plain ``memory://`` gives each
    instance private counters — which is the defect.
    """

    STORAGE_SCHEME = ["kp-shared-test"]

    def __init__(self, uri: str | None = None, wrap_exceptions: bool = False, **options: str) -> None:
        super().__init__(uri, wrap_exceptions=wrap_exceptions, **options)
        self.storage = _SHARED_BACKING.storage
        self.expirations = _SHARED_BACKING.expirations
        self.events = _SHARED_BACKING.events
        self.locks = _SHARED_BACKING.locks


class _DroppingStorage(MemoryStorage):
    """A storage that works until ``down`` is set, then fails like a lost Redis connection.

    Every call the fixed-window strategy and slowapi's recovery probe make raises
    the exception redis-py raises on a dropped socket, so the limiter sees the
    same failure it would see when Valkey goes away between two requests.
    """

    STORAGE_SCHEME = ["kp-dropping-test"]
    down = False

    def _fail_if_down(self) -> None:
        if type(self).down:
            raise RedisConnectionError("Connection closed by server.")

    def incr(self, key: str, expiry: int, amount: int = 1) -> int:
        self._fail_if_down()
        return super().incr(key, expiry, amount)

    def get(self, key: str) -> int:
        self._fail_if_down()
        return super().get(key)

    def get_expiry(self, key: str) -> float:
        self._fail_if_down()
        return super().get_expiry(key)

    def check(self) -> bool:
        return not type(self).down


@pytest.fixture(autouse=True)
def _clean_test_storages() -> Iterator[None]:
    _SHARED_BACKING.reset()
    _DroppingStorage.down = False
    yield
    _SHARED_BACKING.reset()
    _DroppingStorage.down = False


def _make_app(limiter: Limiter) -> FastAPI:
    """One "replica": its own app and its own limiter instance, same route."""
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    @app.get("/probe")
    @limiter.limit(_PROBE_LIMIT)
    async def probe(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    return app


def _client(limiter: Limiter) -> TestClient:
    # A server exception must surface as a 500 status the assertions can see,
    # not as an exception that ends the test with a different message.
    return TestClient(_make_app(limiter), raise_server_exceptions=False)


def _build(storage_url: str) -> Limiter:
    from app.common.rate_limit import build_rate_limiter

    return build_rate_limiter(_rate_limit_key, storage_url=storage_url)


class TestSharedCount:
    def test_two_limiters_on_one_storage_spend_one_budget(self) -> None:
        first = _client(_build("kp-shared-test://"))
        second = _client(_build("kp-shared-test://"))

        assert first.get("/probe").status_code == 200
        assert second.get("/probe").status_code == 200
        # The budget is spent across both "replicas": the third request is over
        # the limit regardless of which one receives it.
        assert first.get("/probe").status_code == 429
        assert second.get("/probe").status_code == 429

    def test_control_memory_storage_counts_per_instance(self) -> None:
        """The defect itself: two ``memory://`` limiters each grant the full budget.

        Kept as a control so the shared-count test above is known to measure the
        storage and not something else that would make the third request 429.
        """
        first = _client(Limiter(key_func=_rate_limit_key, storage_uri="memory://"))
        second = _client(Limiter(key_func=_rate_limit_key, storage_uri="memory://"))

        assert [first.get("/probe").status_code for _ in range(2)] == [200, 200]
        assert [second.get("/probe").status_code for _ in range(2)] == [200, 200]


class TestStorageOutage:
    @pytest.mark.allow_db_connection(
        "connects to 127.0.0.1:1 — nothing listens there; the test needs redis-py's real refused-connect error"
    )
    def test_unreachable_storage_still_limits_per_process(self) -> None:
        # Port 1 on loopback: nothing listens, the connect is refused at once.
        client = _client(_build("redis://127.0.0.1:1/0"))

        statuses = [client.get("/probe").status_code for _ in range(3)]

        assert statuses == [200, 200, 429]

    def test_storage_dropping_between_requests_keeps_limiting(self) -> None:
        client = _client(_build("kp-dropping-test://"))

        assert client.get("/probe").status_code == 200
        _DroppingStorage.down = True

        # The shared count is gone with the storage; the fallback starts a fresh
        # per-process count. Within one limit's worth of requests the route must
        # be refusing again — never a 500, never unbounded.
        statuses = [client.get("/probe").status_code for _ in range(3)]

        assert 500 not in statuses
        assert statuses == [200, 200, 429]


class TestStorageSelection:
    def test_redis_url_without_override_does_not_select_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.common.rate_limit import build_rate_limiter, resolve_rate_limit_storage_url

        monkeypatch.setattr(settings, "rate_limit_storage_url", "")
        monkeypatch.setattr(settings, "redis_url", "redis://valkey.invalid:6379/0")

        assert resolve_rate_limit_storage_url() == "redis://valkey.invalid:6379/0"
        # Construction is lazy — no connection is attempted here.
        limiter = build_rate_limiter(_rate_limit_key)
        assert not isinstance(limiter.limiter.storage, MemoryStorage)

    def test_explicit_override_wins_over_redis_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.common.rate_limit import resolve_rate_limit_storage_url

        monkeypatch.setattr(settings, "rate_limit_storage_url", "redis://limits.invalid:6379/3")
        monkeypatch.setattr(settings, "redis_url", "redis://valkey.invalid:6379/0")

        assert resolve_rate_limit_storage_url() == "redis://limits.invalid:6379/3"

    def test_production_limiter_uses_the_resolved_storage_with_fallback(self) -> None:
        """The module-level ``limiter`` is built through the factory, not beside it."""
        from app.api.v1.auth.router import limiter
        from app.common.rate_limit import resolve_rate_limit_storage_url

        assert limiter._storage_uri == resolve_rate_limit_storage_url()
        assert limiter._in_memory_fallback_enabled is True
