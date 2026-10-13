"""A Valkey client that stops calling a failed Valkey until a probe answers (#2062).

The mail budgets of the sign-in routes (``RedisStepUpThrottleStore`` for the
reset and the two resend budgets) and the unknown-account counter
(``RedisUnknownAccountStore``) fall back to an in-process tier on every Valkey
error. Their shared client has bounded socket timeouts (0.5 s,
``app.common.rate_limit.bounded_redis_client_options``) but no probe plan: while
Valkey hangs, **every** store call waits one timeout. Measured through the real
routes against a socket that accepts and never answers: a reset request
(two reservations since #2059) took 1.0 s, a failed login for an unknown
address 1.3 s — on a threadpool thread each, for as long as the outage lasts.

:class:`LatchedRedis` gives these stores the schedule the IP limiter's
``FailoverStorage`` already has: after a Valkey error it answers every call at
once with a ``ConnectionError`` (the stores treat it like any outage and count
in process), and lets one call at a time through as a probe — 1, 2, 4, 8, 16
and 32 s after the failure, then every 32 s. The probe that succeeds reopens the
client for this process. Errors outside redis-py's ``RedisError`` family are
defects, not outages: they pass through and do not latch.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

import structlog
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

logger = structlog.get_logger(__name__)

_T = TypeVar("_T")

#: Seconds after a failure before the first probe; doubled after every failed
#: probe up to :data:`PROBE_MAX_DELAY_S`. The IP limiter's schedule.
PROBE_INITIAL_DELAY_S = 1.0
PROBE_MAX_DELAY_S = 32.0


class LatchedRedis:
    """Wraps a redis-py client; after a ``RedisError`` it fails fast until a probe answers.

    Exposes the calls the throttle stores make — ``get``, ``set``, ``ttl``,
    ``delete`` and ``pipeline(...)....execute()`` — and nothing else, so a store
    that starts using another command fails loudly in its tests instead of
    bypassing the latch.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self._lock = threading.Lock()
        self._down = False
        self._probe_in_flight = False
        self._probe_delay_s = PROBE_INITIAL_DELAY_S
        self._next_probe_at = 0.0

    @property
    def is_down(self) -> bool:
        """Whether this process currently treats Valkey as unavailable."""
        with self._lock:
            return self._down

    def _claim(self) -> bool:
        """Return whether the call about to be made is a probe; raise if it may not be made."""
        with self._lock:
            if not self._down:
                return False
            if not self._probe_in_flight and time.monotonic() >= self._next_probe_at:
                self._probe_in_flight = True
                return True
        raise RedisConnectionError("Valkey is marked unavailable in this process; the next probe is pending")

    def _schedule_next_probe_locked(self) -> None:
        self._probe_in_flight = False
        self._probe_delay_s = min(self._probe_delay_s * 2, PROBE_MAX_DELAY_S)
        self._next_probe_at = time.monotonic() + self._probe_delay_s

    def _call(self, operation: Callable[[], _T]) -> _T:
        probe = self._claim()
        try:
            result = operation()
        except RedisError as error:
            with self._lock:
                if probe:
                    self._schedule_next_probe_locked()
                    already_recorded = True
                elif self._down:
                    already_recorded = True  # a concurrent call recorded this outage first
                else:
                    self._down = True
                    self._probe_delay_s = PROBE_INITIAL_DELAY_S
                    self._next_probe_at = time.monotonic() + self._probe_delay_s
                    already_recorded = False
            if not already_recorded:
                # Only the type: a redis-py message names host and port.
                logger.warning("throttle_store_unavailable", error_type=type(error).__name__)
            raise
        except BaseException:
            if probe:
                with self._lock:
                    self._schedule_next_probe_locked()
            raise
        if probe:
            with self._lock:
                self._down = False
                self._probe_in_flight = False
                self._probe_delay_s = PROBE_INITIAL_DELAY_S
            logger.info("throttle_store_recovered")
        return result

    def get(self, name: str) -> Any:
        return self._call(lambda: self._client.get(name))

    def set(self, name: str, value: Any, ex: int | None = None) -> Any:
        return self._call(lambda: self._client.set(name, value, ex=ex))

    def ttl(self, name: str) -> Any:
        return self._call(lambda: self._client.ttl(name))

    def delete(self, *names: str) -> Any:
        return self._call(lambda: self._client.delete(*names))

    def pipeline(self, transaction: bool = True) -> _LatchedPipeline:
        return _LatchedPipeline(self, self._client.pipeline(transaction=transaction))


class _LatchedPipeline:
    """Queues commands on the real pipeline; only ``execute`` reaches Valkey, through the latch."""

    def __init__(self, owner: LatchedRedis, pipeline: Any) -> None:
        self._owner = owner
        self._pipeline = pipeline

    def __getattr__(self, name: str) -> Callable[..., _LatchedPipeline]:
        command = getattr(self._pipeline, name)

        def queue(*args: Any, **kwargs: Any) -> _LatchedPipeline:
            command(*args, **kwargs)
            return self

        return queue

    def execute(self) -> Any:
        return self._owner._call(self._pipeline.execute)
