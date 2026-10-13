"""Celery queue lengths on the backend's ``/metrics`` — the signal a worker autoscaler reads (#2128, #2127).

**What is exported.** ``celery_queue_length{queue="critical"|"celery"|"bulk"}`` —
the messages waiting in the broker for each queue the application routes to
(:data:`app.tasks.routing.QUEUES`), and ``celery_broker_up`` — ``1`` when the last
read of the broker succeeded, ``0`` when it did not. A message a worker has
already reserved is not waiting and is not counted (kombu keeps it in its
``unacked`` hash, not in the queue's list).

**How it is read.** One ``LLEN`` per broker list, all in one pipelined round
trip, at scrape time — never on an API request. kombu's Redis transport keeps a
queue in one list per priority step (``<queue>`` for step 0,
``<queue>\\x06\\x16<step>`` for the others, behind the transport's
``global_keyprefix``); the length of a queue is the sum over its lists, which is
what kombu's own ``Channel._size`` computes. A result is reused for
:data:`CACHE_SECONDS`, so several scrapers (an HA Prometheus pair) cost one round
trip between them.

**What a broken broker does.** The client is bounded like every Valkey client of
the backend (``bounded_redis_client_options``: 0.5 s per socket operation, no
retry), so a Valkey that hangs delays a scrape by about a second, once per
:data:`CACHE_SECONDS`. A failed read never raises into the scrape: the queue
series are then ABSENT for that scrape (``celery_broker_up`` is ``0``), never a
stale number. Absent is the safe answer for an autoscaler — the HPA holds its
current replica count when its External metric has no value, whereas a stale
high value would hold workers it no longer needs and a stale ``0`` would scale
them down under load. The warning is logged on the change from readable to
unreadable (and back), not on every scrape.

**Cardinality.** One label, ``queue``, whose values are the three names the
application declares — a key in the broker that is not one of them is never
read, so nothing in Valkey can grow the series set. No tenant, no task name.

**Where it runs.** Registered on the metrics listener's registry by
:func:`app.observability.metrics.start_configured_metrics_server`, i.e. only
in a process that serves ``/metrics``. Every backend replica exports the same
broker-wide numbers; the Prometheus Adapter rule therefore aggregates with
``max``, not ``sum`` (``docs/de/deployment/helm.md#worker-autoscaling-nach-queue-laenge``).
"""

from __future__ import annotations

import threading
import time
import weakref
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Final

import redis
import structlog
from prometheus_client import CollectorRegistry
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector

from app.common.rate_limit import bounded_redis_client_options
from app.tasks.routing import QUEUES, celery_queue_config

logger = structlog.get_logger(__name__)

#: The series an External-metric HPA scales the workers on (``helm/kamerplanter/values.yaml``,
#: ``celeryWorkers.queueAutoscaling.metricName``).
QUEUE_LENGTH_METRIC: Final = "celery_queue_length"
#: ``1`` when the last broker read succeeded, ``0`` when the queue series are absent.
BROKER_UP_METRIC: Final = "celery_broker_up"
#: How long one broker read answers every scrape.
CACHE_SECONDS: Final = 5.0
#: kombu's Redis transport defaults (``kombu.transport.redis.PRIORITY_STEPS`` and
#: ``Channel.sep``). Restated because kombu ships no type information; the test
#: holds them to kombu's own values and to its own ``_q_for_pri``.
KOMBU_PRIORITY_STEPS: Final[tuple[int, ...]] = (0, 3, 6, 9)
KOMBU_PRIORITY_SEPARATOR: Final = "\x06\x16"

_QUEUE_LENGTH_HELP: Final = "Messages waiting in the Celery broker per queue (not yet reserved by a worker)."
_BROKER_UP_HELP: Final = f"1 if the last read of the Celery broker succeeded, 0 if {QUEUE_LENGTH_METRIC} is absent."

type LengthReader = Callable[[], Mapping[str, int]]


def broker_list_keys(
    queue: str,
    *,
    priority_steps: Sequence[int],
    separator: str,
    key_prefix: str = "",
) -> tuple[str, ...]:
    """The broker lists kombu's Redis transport keeps *queue* in — one per priority step.

    Mirrors ``kombu.transport.redis.Channel._q_for_pri``: step ``0`` is the bare
    queue name, every other step is ``<queue><separator><step>``; the transport
    prefixes every key with its ``global_keyprefix``.
    """
    keys: list[str] = []
    for step in sorted(set(priority_steps)):
        key = f"{key_prefix}{queue}" if step == 0 else f"{key_prefix}{queue}{separator}{step}"
        keys.append(key)
    return tuple(keys)


def configured_broker_keys(queues: Sequence[str] = QUEUES) -> dict[str, tuple[str, ...]]:
    """``queue -> broker list keys`` under the transport options the application configures."""
    options = celery_queue_config().get("broker_transport_options")
    transport: Mapping[str, object] = options if isinstance(options, Mapping) else {}
    raw_steps = transport.get("priority_steps", KOMBU_PRIORITY_STEPS)
    steps = [int(step) for step in raw_steps] if isinstance(raw_steps, Sequence) else list(KOMBU_PRIORITY_STEPS)
    prefix = str(transport.get("global_keyprefix", "") or "")
    return {
        queue: broker_list_keys(queue, priority_steps=steps, separator=KOMBU_PRIORITY_SEPARATOR, key_prefix=prefix)
        for queue in queues
    }


class BrokerQueueLengths:
    """Reads the waiting messages per queue with one pipelined ``LLEN`` round trip."""

    def __init__(self, client: redis.Redis, keys_by_queue: Mapping[str, Sequence[str]]) -> None:
        self._client = client
        self._keys_by_queue: dict[str, tuple[str, ...]] = {queue: tuple(keys) for queue, keys in keys_by_queue.items()}

    def __call__(self) -> dict[str, int]:
        pipeline = self._client.pipeline(transaction=False)
        order: list[str] = []
        for queue, keys in self._keys_by_queue.items():
            for key in keys:
                pipeline.llen(key)
                order.append(queue)
        results = pipeline.execute()
        lengths: dict[str, int] = {queue: 0 for queue in self._keys_by_queue}
        for queue, size in zip(order, results, strict=True):
            if isinstance(size, int):
                lengths[queue] += size
        return lengths


class QueueLengthCollector(Collector):
    """Exports :data:`QUEUE_LENGTH_METRIC` per queue and :data:`BROKER_UP_METRIC` at scrape time."""

    def __init__(
        self,
        read: LengthReader,
        *,
        queues: Sequence[str] = QUEUES,
        cache_seconds: float = CACHE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._read: LengthReader = read
        self._queues = tuple(queues)
        self._cache_seconds = cache_seconds
        self._clock: Callable[[], float] = clock
        self._lock = threading.Lock()
        self._read_at: float | None = None
        self._lengths: dict[str, int] | None = None
        self._reachable = True

    def describe(self) -> Iterable[GaugeMetricFamily]:
        """The families without samples — registering must not touch the broker."""
        return [
            GaugeMetricFamily(QUEUE_LENGTH_METRIC, _QUEUE_LENGTH_HELP, labels=["queue"]),
            GaugeMetricFamily(BROKER_UP_METRIC, _BROKER_UP_HELP),
        ]

    def collect(self) -> Iterable[GaugeMetricFamily]:
        lengths = self._current()
        if lengths is not None:
            family = GaugeMetricFamily(QUEUE_LENGTH_METRIC, _QUEUE_LENGTH_HELP, labels=["queue"])
            for queue in self._queues:
                family.add_metric([queue], float(lengths.get(queue, 0)))
            yield family
        yield GaugeMetricFamily(BROKER_UP_METRIC, _BROKER_UP_HELP, value=1.0 if lengths is not None else 0.0)

    def _current(self) -> dict[str, int] | None:
        # Plain callables, not methods: bound to typed locals so the call is on a
        # name with a declared type (tests/unit/api/_write_call_graph.py counts an
        # attribute call it cannot resolve as an annotation gap).
        clock: Callable[[], float] = self._clock
        read: LengthReader = self._read
        with self._lock:
            now = clock()
            if self._read_at is not None and now - self._read_at < self._cache_seconds:
                return self._lengths
            self._read_at = now
            try:
                raw = read()
                self._lengths = {queue: max(0, int(raw.get(queue, 0))) for queue in self._queues}
            except Exception as exc:  # noqa: BLE001 — any failure to read the broker means "no value", never a failed scrape
                self._lengths = None
                if self._reachable:
                    logger.warning("celery_queue_length_unavailable", error_type=type(exc).__name__)
                self._reachable = False
            else:
                if not self._reachable:
                    logger.info("celery_queue_length_available")
                self._reachable = True
            return self._lengths


_INSTALLED: weakref.WeakKeyDictionary[CollectorRegistry, QueueLengthCollector] = weakref.WeakKeyDictionary()


def install_queue_length_collector(registry: CollectorRegistry, broker_url: str) -> QueueLengthCollector:
    """Register a :class:`QueueLengthCollector` for *broker_url* on *registry* — once per registry.

    Building the client opens no connection; the first scrape does.
    """
    installed = _INSTALLED.get(registry)
    if installed is not None:
        return installed
    client = redis.Redis.from_url(broker_url, **bounded_redis_client_options())
    collector = QueueLengthCollector(BrokerQueueLengths(client, configured_broker_keys()))
    registry.register(collector)
    _INSTALLED[registry] = collector
    return collector
