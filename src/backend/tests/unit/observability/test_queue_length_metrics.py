"""Celery queue lengths on ``/metrics`` — the series a worker autoscaler reads (#2128, #2127).

Asserted here:

1. **The keys are kombu's.** The broker lists read are exactly the ones kombu's
   Redis transport writes a queue to (one per priority step), computed by
   kombu's own ``Channel._q_for_pri`` — not a re-statement of it.
2. **One series per declared queue, one label.** ``celery_queue_length`` carries
   ``queue`` only, with the values of ``app.tasks.routing.QUEUES``; whatever else
   the reader returns is dropped.
3. **A broken broker never breaks the scrape.** A reader that raises, a port that
   refuses and a Valkey that accepts and never answers all yield a scrape
   without the queue series and with ``celery_broker_up 0`` — within the client
   bound, not after redis-py's default 5 s per operation.
4. **Cheap.** A read answers every scrape for ``CACHE_SECONDS``; registering
   does not touch the broker.
5. **The reach probe.** ``start_configured_metrics_server`` — the path the API's
   lifespan takes — serves the series on the metrics listener.
"""

from __future__ import annotations

import socket
import threading
import time
import urllib.request
from collections.abc import Iterator, Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import pytest
import structlog
from kombu.transport.redis import PRIORITY_STEPS, Channel
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.parser import text_string_to_metric_families

from app.observability import metrics
from app.observability.queue_metrics import (
    BROKER_UP_METRIC,
    CACHE_SECONDS,
    KOMBU_PRIORITY_SEPARATOR,
    KOMBU_PRIORITY_STEPS,
    QUEUE_LENGTH_METRIC,
    BrokerQueueLengths,
    QueueLengthCollector,
    broker_list_keys,
    configured_broker_keys,
    install_queue_length_collector,
)
from app.tasks.routing import QUEUES


def _samples(text: str, name: str) -> list[tuple[dict[str, str], float]]:
    return [
        (dict(sample.labels), sample.value)
        for family in text_string_to_metric_families(text)
        for sample in family.samples
        if sample.name == name
    ]


def _scrape(registry: CollectorRegistry) -> str:
    return generate_latest(registry).decode()


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class _Reader:
    def __init__(self, *answers: Mapping[str, int] | Exception) -> None:
        self._answers = list(answers)
        self.calls = 0

    def __call__(self) -> Mapping[str, int]:
        self.calls += 1
        answer = self._answers[min(self.calls, len(self._answers)) - 1]
        if isinstance(answer, Exception):
            raise answer
        return answer


def _registry_with(collector: QueueLengthCollector) -> CollectorRegistry:
    registry = CollectorRegistry(auto_describe=True)
    registry.register(collector)
    return registry


# ---------------------------------------------------------------------------
# 1. The keys are kombu's.
# ---------------------------------------------------------------------------


def _kombu_keys(queue: str, steps: Sequence[int], prefix: str = "") -> list[str]:
    """What kombu's transport itself computes (``_q_for_pri``), plus the prefix its client applies."""
    channel: Any = SimpleNamespace(priority_steps=list(steps), sep=Channel.sep)
    channel.priority = lambda n: Channel.priority(channel, n)
    return [prefix + Channel._q_for_pri(channel, queue, step) for step in steps]


def test_the_restated_transport_defaults_are_kombus() -> None:
    assert list(KOMBU_PRIORITY_STEPS) == PRIORITY_STEPS
    assert Channel.sep == KOMBU_PRIORITY_SEPARATOR


@pytest.mark.parametrize("queue", QUEUES)
def test_the_keys_read_are_the_lists_kombu_writes_the_queue_to(queue: str) -> None:
    assert list(broker_list_keys(queue, priority_steps=PRIORITY_STEPS, separator=Channel.sep)) == _kombu_keys(
        queue, PRIORITY_STEPS
    )


def test_custom_priority_steps_and_a_key_prefix_are_followed() -> None:
    keys = broker_list_keys("bulk", priority_steps=[0, 5], separator=Channel.sep, key_prefix="kp:")

    assert list(keys) == _kombu_keys("bulk", [0, 5], prefix="kp:")


def test_the_configured_keys_cover_every_declared_queue_and_every_priority_step() -> None:
    keys = configured_broker_keys()

    assert set(keys) == set(QUEUES)
    for queue in QUEUES:
        assert list(keys[queue]) == _kombu_keys(queue, PRIORITY_STEPS)


def test_the_metrics_read_the_broker_the_application_publishes_to() -> None:
    from app.config.settings import settings
    from app.tasks import celery_app

    assert celery_app.conf.broker_url == settings.redis_url


# ---------------------------------------------------------------------------
# The reader: one pipelined round trip, summed per queue.
# ---------------------------------------------------------------------------


class _FakePipeline:
    def __init__(self, sizes: Mapping[str, int | None]) -> None:
        self._sizes = sizes
        self.keys: list[str] = []

    def llen(self, key: str) -> _FakePipeline:
        self.keys.append(key)
        return self

    def execute(self) -> list[int | None]:
        return [self._sizes.get(key) for key in self.keys]


class _FakeClient:
    def __init__(self, sizes: Mapping[str, int | None]) -> None:
        self.pipeline_obj = _FakePipeline(sizes)
        self.pipelines = 0

    def pipeline(self, *, transaction: bool) -> _FakePipeline:
        assert transaction is False
        self.pipelines += 1
        return self.pipeline_obj


def test_the_reader_sums_every_priority_list_of_a_queue_in_one_round_trip() -> None:
    keys = configured_broker_keys()
    sizes: dict[str, int | None] = {
        keys["critical"][0]: 4,
        keys["critical"][2]: 3,
        keys["bulk"][0]: 7,
        keys["celery"][1]: None,  # a non-integer reply is not counted
    }
    client = _FakeClient(sizes)

    lengths = BrokerQueueLengths(client, keys)()  # type: ignore[arg-type]

    assert lengths == {"critical": 7, "celery": 0, "bulk": 7}
    assert client.pipelines == 1
    assert sorted(client.pipeline_obj.keys) == sorted(key for queue in QUEUES for key in keys[queue])


# ---------------------------------------------------------------------------
# 2. One series per declared queue, one label.
# ---------------------------------------------------------------------------


def test_every_declared_queue_is_one_series_labelled_by_queue_only() -> None:
    reader = _Reader({"critical": 2, "celery": 0, "bulk": 41, "someone-elses-queue": 9})

    text = _scrape(_registry_with(QueueLengthCollector(reader)))

    assert _samples(text, QUEUE_LENGTH_METRIC) == [
        ({"queue": "critical"}, 2.0),
        ({"queue": "celery"}, 0.0),
        ({"queue": "bulk"}, 41.0),
    ]
    assert _samples(text, BROKER_UP_METRIC) == [({}, 1.0)]
    assert "someone-elses-queue" not in text


def test_a_queue_the_reader_does_not_answer_for_is_zero_and_a_negative_is_clamped() -> None:
    text = _scrape(_registry_with(QueueLengthCollector(_Reader({"critical": -3}))))

    assert dict((labels["queue"], value) for labels, value in _samples(text, QUEUE_LENGTH_METRIC)) == {
        "critical": 0.0,
        "celery": 0.0,
        "bulk": 0.0,
    }


# ---------------------------------------------------------------------------
# 3. A broken broker never breaks the scrape.
# ---------------------------------------------------------------------------


def test_a_failed_read_drops_the_queue_series_and_reports_the_broker_down() -> None:
    clock = _Clock()
    reader = _Reader({"critical": 5, "celery": 1, "bulk": 0}, ConnectionError("valkey gone"))
    registry = _registry_with(QueueLengthCollector(reader, clock=clock))

    first = _scrape(registry)
    clock.now += CACHE_SECONDS + 1
    second = _scrape(registry)

    assert _samples(first, QUEUE_LENGTH_METRIC)
    # Absent, not the last value: a stale number would steer the autoscaler.
    assert _samples(second, QUEUE_LENGTH_METRIC) == []
    assert _samples(second, BROKER_UP_METRIC) == [({}, 0.0)]


def test_the_outage_is_logged_once_and_the_recovery_once() -> None:
    clock = _Clock()
    down = ConnectionError("valkey gone")
    reader = _Reader(down, down, down, {"critical": 1})
    registry = _registry_with(QueueLengthCollector(reader, clock=clock))

    with structlog.testing.capture_logs() as logs:
        for _ in range(4):
            _scrape(registry)
            clock.now += CACHE_SECONDS + 1

    events = [entry["event"] for entry in logs]
    assert events == ["celery_queue_length_unavailable", "celery_queue_length_available"]
    assert logs[0]["error_type"] == "ConnectionError"
    assert "valkey gone" not in str(logs)


def _refusing_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
    return port


@pytest.fixture
def silent_valkey() -> Iterator[int]:
    """A TCP listener that accepts connections and never answers — a hung Valkey."""
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(8)
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept() -> None:
        server.settimeout(0.1)
        while not stop.is_set():
            try:
                connection, _ = server.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            held.append(connection)

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    try:
        yield server.getsockname()[1]
    finally:
        stop.set()
        thread.join(timeout=2)
        for connection in held:
            connection.close()
        server.close()


#: The loopback tests open a real Valkey client against a port that is no datastore.
_LOOPBACK = pytest.mark.allow_db_connection("a Valkey client against a loopback port that refuses or never answers")


@_LOOPBACK
@pytest.mark.parametrize("broker", ["refused", "silent"])
def test_an_unreachable_valkey_costs_the_scrape_one_bounded_wait_and_no_exception(
    broker: str, request: pytest.FixtureRequest
) -> None:
    port = _refusing_port() if broker == "refused" else request.getfixturevalue("silent_valkey")
    registry = CollectorRegistry(auto_describe=True)
    install_queue_length_collector(registry, f"redis://127.0.0.1:{port}/0")

    started = time.monotonic()
    text = _scrape(registry)
    elapsed = time.monotonic() - started

    assert _samples(text, QUEUE_LENGTH_METRIC) == []
    assert _samples(text, BROKER_UP_METRIC) == [({}, 0.0)]
    # 0.5 s per socket operation, no retry (bounded_redis_client_options); redis-py's
    # unbounded default would wait 5 s here.
    assert elapsed < 2.0


# ---------------------------------------------------------------------------
# 4. Cheap.
# ---------------------------------------------------------------------------


def test_one_read_answers_every_scrape_within_the_cache_window() -> None:
    clock = _Clock()
    reader = _Reader({"critical": 1}, {"critical": 2})
    registry = _registry_with(QueueLengthCollector(reader, clock=clock))

    _scrape(registry)
    clock.now += CACHE_SECONDS / 2
    within = _scrape(registry)
    clock.now += CACHE_SECONDS
    after = _scrape(registry)

    assert reader.calls == 2
    assert ({"queue": "critical"}, 1.0) in _samples(within, QUEUE_LENGTH_METRIC)
    assert ({"queue": "critical"}, 2.0) in _samples(after, QUEUE_LENGTH_METRIC)


def test_registering_does_not_read_the_broker() -> None:
    reader = _Reader(AssertionError("read at registration"))

    _registry_with(QueueLengthCollector(reader))

    assert reader.calls == 0


def test_installing_twice_on_one_registry_registers_once() -> None:
    registry = CollectorRegistry(auto_describe=True)
    url = f"redis://127.0.0.1:{_refusing_port()}/0"

    first = install_queue_length_collector(registry, url)
    second = install_queue_length_collector(registry, url)

    # A second registration of the same names would have raised ValueError.
    assert first is second


# ---------------------------------------------------------------------------
# 5. The reach probe: the lifespan's start path serves the series.
# ---------------------------------------------------------------------------


@_LOOPBACK
def test_the_configured_metrics_listener_serves_the_queue_series(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings

    registry = CollectorRegistry(auto_describe=True)
    monkeypatch.setattr(metrics, "REGISTRY", registry)
    monkeypatch.setattr(settings, "metrics_port", _refusing_port())
    monkeypatch.setattr(settings, "metrics_bind_address", "127.0.0.1")
    monkeypatch.setattr(settings, "redis_url", f"redis://127.0.0.1:{_refusing_port()}/0")

    server = metrics.start_configured_metrics_server()
    assert server is not None
    try:
        url = f"http://127.0.0.1:{server.server_port}/metrics"
        with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310 — loopback test listener
            body = response.read().decode()
    finally:
        metrics.stop_metrics_server(server)

    # The broker refuses here, so the queue series are absent and the up-gauge says why.
    assert _samples(body, BROKER_UP_METRIC) == [({}, 0.0)]
    assert _samples(body, QUEUE_LENGTH_METRIC) == []
