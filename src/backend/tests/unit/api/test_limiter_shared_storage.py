"""The IP rate limits count per deployment, not per process (#2045).

slowapi's ``Limiter`` stores its counters in ``memory://`` unless told otherwise,
so every backend replica — and every worker process inside one — kept its own
count. ``N`` processes multiplied each documented limit by ``N``.

These tests pin the properties the fix is made of:

* two limiters built by the production factory against one shared storage
  spend **one** budget (the "two replicas" case);
* an unreachable, failing or hanging storage degrades to a **per-process**
  count — the limit still applies, the route neither fails open nor answers
  500, also not for requests that are already in flight when the storage goes
  away;
* a hanging storage costs a request at most one socket timeout, and only the
  request that meets the failure or carries a recovery probe pays it;
* once the storage answers again, the shared count resumes;
* with ``redis_url`` configured and no explicit override, the production
  limiter does not quietly land on ``memory://`` again.

No live Valkey is needed: the shared storage is an in-process ``limits`` storage
registered under its own scheme, the "unreachable" case points at a port nothing
listens on, and the "hanging" case at a loopback socket that accepts
connections and never answers.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from limits.storage import MemoryStorage
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from structlog.testing import capture_logs

from app.api.v1.auth.router import _rate_limit_key
from app.common import rate_limit
from app.config.settings import settings

_PROBE_LIMIT = "2/minute"

#: Budget for the concurrency case — above the number of concurrent requests, so
#: every one of them is expected to be admitted.
_WIDE_LIMIT = "10/minute"

#: One socket timeout plus scheduling slack. The pre-fix limiter spent two
#: timeouts on the first request against a hanging storage (the failing
#: ``INCR`` and an immediate ``PING`` probe), measured at 1.01 s.
_ONE_TIMEOUT_BOUND_S = rate_limit._REDIS_SOCKET_TIMEOUT_S + 0.3

#: A request served from the in-process count touches no socket at all.
_NO_TIMEOUT_BOUND_S = 0.2

#: One backing store both "replicas" talk to — what Valkey is in production.
_SHARED_BACKING = MemoryStorage()

_BACKEND_ROOT = Path(__file__).resolve().parents[3]


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

    Every call the fixed-window strategy makes raises the exception redis-py
    raises on a dropped socket, so the limiter sees the same failure it would
    see when Valkey goes away between two requests.
    """

    STORAGE_SCHEME = ["kp-dropping-test"]
    down = False

    @property
    def base_exceptions(self) -> type[Exception]:
        # What ``limits``' RedisStorage declares for the redis-py client: the
        # error family a storage outage raises. ``MemoryStorage`` declares
        # ``ValueError``, which would let this double fail in a way the real
        # storage never does.
        return RedisError

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


@pytest.fixture
def blackhole_port() -> Iterator[int]:
    """A loopback port that accepts TCP connections and never sends a byte back.

    The shape of a Valkey that hangs instead of refusing (a stopped process
    behind a live socket, a stalled node): ``connect`` succeeds, every command
    waits for a reply that never comes. The accepted sockets are held open so
    the peer never sees a close either.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(64)
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept_and_hold() -> None:
        server.settimeout(0.05)
        while not stop.is_set():
            try:
                connection, _ = server.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            held.append(connection)

    acceptor = threading.Thread(target=accept_and_hold, daemon=True)
    acceptor.start()
    try:
        yield server.getsockname()[1]
    finally:
        stop.set()
        acceptor.join(timeout=1)
        for connection in held:
            connection.close()
        server.close()


def _make_app(limiter: Limiter) -> FastAPI:
    """One "replica": its own app and its own limiter instance, same routes.

    ``/probe`` is an ``async def`` route, ``/probe-sync`` a plain ``def`` one —
    the shape of the auth routes, which FastAPI runs on its thread pool, so
    several of them can be inside the limiter at the same moment.
    """
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    @app.get("/probe")
    @limiter.limit(_PROBE_LIMIT)
    async def probe(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/probe-sync")
    @limiter.limit(_WIDE_LIMIT)
    def probe_sync(request: Request) -> dict[str, str]:
        return {"status": "ok"}

    return app


def _client(limiter: Limiter) -> TestClient:
    # A server exception must surface as a 500 status the assertions can see,
    # not as an exception that ends the test with a different message.
    return TestClient(_make_app(limiter), raise_server_exceptions=False)


def _build(storage_url: str) -> Limiter:
    return rate_limit.build_rate_limiter(_rate_limit_key, storage_url=storage_url)


def _timed_get(client: TestClient, path: str = "/probe") -> tuple[int, float]:
    started = time.monotonic()
    status = client.get(path).status_code
    return status, time.monotonic() - started


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

    def test_shared_count_resumes_once_the_storage_answers_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Probe on the very next request instead of after one second.
        monkeypatch.setattr(rate_limit, "_PROBE_INITIAL_DELAY_S", 0.0)
        client = _client(_build("kp-dropping-test://"))

        assert client.get("/probe").status_code == 200  # shared count: 1
        _DroppingStorage.down = True
        # Two requests in the per-process count — its budget is now spent.
        assert [client.get("/probe").status_code for _ in range(2)] == [200, 200]
        _DroppingStorage.down = False

        # Recovered: the request counts in the shared storage again (2 of 2),
        # not in the exhausted per-process count, where it would be a 429.
        assert client.get("/probe").status_code == 200
        assert client.get("/probe").status_code == 429


@pytest.mark.allow_db_connection(
    "connects to a loopback socket this test opens itself, which accepts and never answers — "
    "the hanging-Valkey case needs redis-py's real socket timeout"
)
class TestHangingStorage:
    """A storage that accepts the connection and never answers (#2045 review, SEC-001/SEC-002)."""

    def test_first_request_waits_at_most_one_socket_timeout(self, blackhole_port: int) -> None:
        client = _client(_build(f"redis://127.0.0.1:{blackhole_port}/0"))
        # The production limiter is built at import, long before an outage —
        # far past the first recovery-probe interval.
        time.sleep(1.1)

        first_status, first_elapsed = _timed_get(client)
        second_status, second_elapsed = _timed_get(client)

        assert first_status == 200
        assert first_elapsed < _ONE_TIMEOUT_BOUND_S, f"first request took {first_elapsed:.2f}s"
        assert second_status == 200
        assert second_elapsed < _NO_TIMEOUT_BOUND_S, f"second request took {second_elapsed:.2f}s"

    def test_a_recovery_probe_costs_one_request_one_timeout(self, blackhole_port: int) -> None:
        client = _client(_build(f"redis://127.0.0.1:{blackhole_port}/0"))

        assert _timed_get(client)[0] == 200  # meets the failure, falls back
        time.sleep(rate_limit._PROBE_INITIAL_DELAY_S + 0.1)

        probe_status, probe_elapsed = _timed_get(client)  # carries the probe
        after_status, after_elapsed = _timed_get(client)  # next probe is 2 s away

        # The probe fails against the hanging storage and the request is
        # counted per process: 2 of 2, then over the limit.
        assert probe_status == 200
        assert probe_elapsed < _ONE_TIMEOUT_BOUND_S, f"probe request took {probe_elapsed:.2f}s"
        assert after_status == 429
        assert after_elapsed < _NO_TIMEOUT_BOUND_S, f"request after the probe took {after_elapsed:.2f}s"

    def test_requests_in_flight_when_the_storage_hangs_never_answer_500(self, blackhole_port: int) -> None:
        client = _client(_build(f"redis://127.0.0.1:{blackhole_port}/0"))
        concurrent = 4
        start = threading.Barrier(concurrent)
        results: list[tuple[int, float]] = []
        lock = threading.Lock()

        def one_request() -> None:
            start.wait()
            result = _timed_get(client, "/probe-sync")
            with lock:
                results.append(result)

        threads = [threading.Thread(target=one_request) for _ in range(concurrent)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        statuses = sorted(status for status, _ in results)
        slowest = max(elapsed for _, elapsed in results)
        # All four are inside the storage call when it times out. Each falls
        # back on its own failure — none depends on which request flipped the
        # state first — and the per-process budget of 10 admits all of them.
        assert statuses == [200] * concurrent
        assert slowest < _ONE_TIMEOUT_BOUND_S, f"slowest request took {slowest:.2f}s"


class TestPerProcessWarning:
    """``memory://`` outside debug mode is said out loud once, when the limiter is built (SEC-005)."""

    _EVENT = "rate_limit_storage_counts_per_process"

    def test_memory_storage_without_debug_warns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "debug", False)

        with capture_logs() as logs:
            _build("memory://")

        warnings = [entry for entry in logs if entry.get("event") == self._EVENT]
        assert len(warnings) == 1
        assert warnings[0]["log_level"] == "warning"
        assert "memory://" not in repr(warnings[0])

    def test_memory_storage_in_debug_stays_silent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "debug", True)

        with capture_logs() as logs:
            _build("memory://")

        assert [entry for entry in logs if entry.get("event") == self._EVENT] == []

    def test_shared_storage_stays_silent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "debug", False)

        with capture_logs() as logs:
            _build("redis://valkey.invalid:6379/0")

        assert [entry for entry in logs if entry.get("event") == self._EVENT] == []


class TestStorageSelection:
    def test_redis_url_without_override_does_not_select_memory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "rate_limit_storage_url", "")
        monkeypatch.setattr(settings, "redis_url", "redis://valkey.invalid:6379/0")

        assert rate_limit.resolve_rate_limit_storage_url() == "redis://valkey.invalid:6379/0"
        # Construction is lazy — no connection is attempted here.
        limiter = rate_limit.build_rate_limiter(_rate_limit_key)
        assert not isinstance(limiter.limiter.storage, MemoryStorage)

    def test_explicit_override_wins_over_redis_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "rate_limit_storage_url", "redis://limits.invalid:6379/3")
        monkeypatch.setattr(settings, "redis_url", "redis://valkey.invalid:6379/0")

        assert rate_limit.resolve_rate_limit_storage_url() == "redis://limits.invalid:6379/3"

    def test_a_storage_url_limits_cannot_use_is_refused_without_echoing_it(self) -> None:
        """``REDIS_URL`` is not checked against the limiter's schemes when it loads.

        An empty ``RATE_LIMIT_STORAGE_URL`` hands it to the limiter, and an
        unknown scheme used to surface as ``limits``' ``ConfigurationError``,
        whose text is the whole URL — password included — printed at import,
        before the redacting log setup runs.
        """
        with pytest.raises(rate_limit.RateLimitStorageConfigError) as raised:
            _build("unix://:hunter2-secret@valkey/0")

        assert "hunter2-secret" not in str(raised.value)
        assert "valkey" not in str(raised.value)

    def test_production_limiter_counts_in_redis_url_when_no_override_is_set(self) -> None:
        """The module-level ``limiter`` is built through the factory, from the settings it loads with.

        Asserted in a fresh interpreter: the suite's ``conftest.py`` points this
        process's limiter at ``memory://`` before ``app`` is imported, so any
        comparison inside this process would compare that override with itself.
        """
        env = {
            **os.environ,
            "RATE_LIMIT_STORAGE_URL": "",
            "REDIS_URL": "redis://valkey-for-limits.invalid:6390/4",
            "PYTHONPATH": str(_BACKEND_ROOT),
        }
        script = (
            "from app.api.v1.auth.router import limiter\n"
            "storage = limiter.limiter.storage\n"
            "pool = storage.primary.storage.connection_pool\n"
            "print(type(storage).__name__, type(storage.primary).__name__,"
            " pool.connection_kwargs['host'], pool.connection_kwargs['port'],"
            " pool.connection_kwargs['db'])\n"
        )
        completed = subprocess.run(  # noqa: S603 — fixed interpreter and script, no shell
            [sys.executable, "-c", script],
            cwd=_BACKEND_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr[-2000:]
        assert completed.stdout.split()[-5:] == [
            "FailoverStorage",
            "RedisStorage",
            "valkey-for-limits.invalid",
            "6390",
            "4",
        ]
