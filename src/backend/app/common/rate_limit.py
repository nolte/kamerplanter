"""Build the IP rate limiter against a storage every process shares (#2045).

slowapi's ``Limiter`` keeps its counters in ``memory://`` unless it is handed a
storage, and the backend's one shared ``limiter`` was built without one. Each
replica — and each worker process inside a replica — therefore counted on its
own, and ``N`` processes multiplied every ``@limiter.limit`` by ``N``: the login,
registration, password-reset and pairing-redemption bounds among them.

**Where the count lives.** :func:`resolve_rate_limit_storage_url` reads
``settings.rate_limit_storage_url`` and, when it is empty, the Valkey in
``settings.redis_url`` the backend already depends on. A shared count is the
default, not an opt-in a deployment has to remember.

**What happens when that storage is gone.** A shared storage is wrapped in
:class:`FailoverStorage`. Every storage call that fails with the storage's own
error family (``RedisError`` for Redis) is answered from an in-process
``MemoryStorage`` instead — per call, so a request that is already inside the
storage when it goes away falls back on its own failure and never depends on
which request noticed first. The earlier design relied on slowapi's
``in_memory_fallback_enabled``: only the request that flipped slowapi's
``_storage_dead`` flag fell back, and every request whose storage call failed
after that re-raised and answered 500 — measured ``[200, 500, 500, 500]`` for
four concurrent requests against a hanging Valkey. slowapi's fallback is
therefore not enabled any more; the wrapper never lets a storage error reach it.
An error outside that family is a defect and surfaces (a 500), it is not
swallowed. During an outage the bound is the per-process one this module
replaces — weaker than intended, but never open. A process's in-memory count
starts at zero if the process has not counted itself in the current window;
those counts are kept across a recovery until their own window expires, so a
flapping storage does not hand out a fresh per-process window per outage.

**Signals (#2049).** The first failure logs ``rate_limit_storage_unavailable``
— or, when the storage has never answered since the process started (a wrong
credential or host looks exactly like that), ``rate_limit_storage_never_reached``
at error level. While it stays down, every tenth failed probe — past the
back-off about every five minutes — logs ``rate_limit_storage_still_unavailable``.
Readiness is deliberately untouched: an unready pod would turn a Valkey outage
into a full outage.

**Recovery, per process.** While the storage is down, requests in this process
do not touch it. One request at a time carries a probe, at intervals of 1, 2,
4, 8, 16 and 32 s after the failure, and every 32 s from there on; a probe that
meets a defect instead of an outage moves the plan on as well. A probe is that
request's own storage call; when it succeeds, *this* process counts in the
shared storage again from that request on. Every other process returns with its
own next probe — up to about 32 s after the storage is back, and only when
requests reach it.

**Bounded waits.** Each check is one round trip (``INCR`` + ``EXPIRE`` in one
script) on the request path, so the Redis client gets explicit socket timeouts
and no retries: a Valkey that hangs instead of refusing costs the request that
meets the failure, and each probe request, one socket timeout (0.5 s) per
connection attempt and address. Not covered by that bound: DNS resolution,
several addresses for one name, connect and handshake together, and reloading
the script after ``NOSCRIPT``. Requests already in flight at that moment wait
out their own timeout alongside it, not after it. Every other request during
the outage is answered from memory without waiting — this applies to the
limiter. The mail-budget stores of the sign-in routes use the same client
options (:func:`bounded_redis_client_options`) and, since #2062, the same probe
plan (``app.data_access.external.latched_redis.LatchedRedis``).

**Off the event loop (#2048).** slowapi runs the limit check synchronously,
also inside the wrapper of an ``async def`` route — there it is a storage round
trip on the event loop, and every other request of the process waits behind it
(measured: 0.007 s → 0.935 s for an unrelated async route while three limited
async requests met a storage answering in 0.3 s). :class:`OffLoopLimiter` runs
the check of an ``async`` route through ``run_in_threadpool``, where the check
of every ``def`` route already runs. ``GET /api/health`` does not use the shared
storage at all: :func:`build_process_memory_rate_limiter`.
"""

from __future__ import annotations

import functools
import inspect
import threading
import time
from collections.abc import Callable
from typing import Any, Final, Literal, TypeVar

import structlog
from limits.storage import MemoryStorage, Storage, storage_from_string
from redis.backoff import NoBackoff
from redis.retry import Retry
from slowapi import Limiter
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

from app.config.settings import (
    RATE_LIMIT_STORAGE_SCHEMES,
    rate_limit_storage_scheme_is_usable,
    settings,
    storage_url_authority_is_well_formed,
)

logger = structlog.get_logger(__name__)

_T = TypeVar("_T")

#: Seconds to wait for the rate-limit storage — and the mail-budget stores of
#: the sign-in routes, see :func:`bounded_redis_client_options` — to accept a
#: connection / answer a command, per connection attempt and address. The
#: counters are a single round trip on an in-cluster Valkey, sub-millisecond when
#: healthy; half a second is far beyond a healthy answer and short enough that a
#: hung store degrades to the in-process tier instead of stalling logins. Not
#: covered: DNS resolution, several addresses for one name, connect and handshake
#: together, the script reload after ``NOSCRIPT``.
_REDIS_SOCKET_TIMEOUT_S = 0.5

#: Seconds after a storage failure before the first recovery probe; doubled after
#: every failed probe up to :data:`_PROBE_MAX_DELAY_S`, where it stays.
_PROBE_INITIAL_DELAY_S = 1.0
_PROBE_MAX_DELAY_S = 32.0

#: A process that still cannot reach the storage logs
#: ``rate_limit_storage_still_unavailable`` on every this-many failed probes —
#: past the back-off about every five minutes (10 × 32 s), #2049.
_REMINDER_EVERY_FAILED_PROBES = 10

#: Schemes whose ``limits`` storage hands its options straight to
#: ``redis.from_url``, so the socket timeouts and the retry policy are understood.
_REDIS_SCHEMES = frozenset({"redis", "rediss", "redis+unix"})

#: How slowapi names a route inside a bucket key (#2052). ``"endpoint"`` is the
#: route function (``module.function``); slowapi's default ``"url"`` is the
#: request **path**, so on a route with a path parameter every value the caller
#: chose was its own bucket — the limit bypassed by varying the value, and one
#: storage key written per value. Measured on ``/public/glossary/term/{slug}``
#: (30/minute): 31 distinct slugs → 31 × 200 and 31 keys. A route function
#: mounted under two prefixes now shares one bucket as well.
LIMITER_KEY_STYLE: Final[Literal["endpoint"]] = "endpoint"

#: The scheme the failover wrapper registers under with ``limits``. Never
#: configured by an operator: :func:`build_rate_limiter` builds it around the
#: configured storage.
_FAILOVER_SCHEME = "kamerplanter-failover"

_ALLOWED_TEXT = ", ".join(f"{scheme}://" for scheme in RATE_LIMIT_STORAGE_SCHEMES)


class RateLimitStorageConfigError(RuntimeError):
    """The rate-limit storage URI cannot be used — raised without the URI (#2045)."""


def _unusable_storage_error() -> RateLimitStorageConfigError:
    return RateLimitStorageConfigError(
        "the rate-limit storage (RATE_LIMIT_STORAGE_URL, or REDIS_URL when that is empty) "
        f"is not a usable storage URI (value withheld); allowed schemes: {_ALLOWED_TEXT}; "
        "percent-encode '/', '#', '?' and '@' inside the password"
    )


def _build_primary(uri: str, options: dict[str, object]) -> Storage:
    primary: object = None
    try:
        primary = storage_from_string(uri, **options)  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001 — every failure here may quote the URI
        # ``limits``' ConfigurationError is the whole URI; redis-py's
        # ``ValueError("Port could not be cast to integer value as '<…>'")``
        # quotes a password whose unencoded ``/``, ``#`` or ``?`` ended the
        # authority early. Neither message may reach stderr.
        primary = None
    # Raised outside the ``except`` block, so the original is not even the
    # context of what reaches the interpreter's hook (#1877).
    if not isinstance(primary, Storage):
        # Unknown scheme, malformed URI, missing client package, or an
        # ``async+…`` storage that would hand the synchronous limiter coroutines.
        raise _unusable_storage_error()
    return primary


class FailoverStorage(Storage):
    """A ``limits`` storage that answers from process memory while the shared one fails.

    Wraps the storage the deployment counts in (*primary*). Each call goes to
    the primary unless it is known to be down; a call that fails with the
    primary's ``base_exceptions`` marks it down and is answered from the
    in-process fallback instead. See the module docstring for the probe
    schedule and the bounds this gives.
    """

    STORAGE_SCHEME = [_FAILOVER_SCHEME]

    def __init__(
        self,
        uri: str | None = None,
        wrap_exceptions: bool = False,
        *,
        primary_uri: str,
        **options: object,
    ) -> None:
        super().__init__(uri, wrap_exceptions=wrap_exceptions)
        self.primary: Storage = _build_primary(primary_uri, options)
        self.fallback = MemoryStorage()
        self._lock = threading.Lock()
        self._down = False
        self._probe_in_flight = False
        self._probe_delay_s = _PROBE_INITIAL_DELAY_S
        self._next_probe_at = 0.0
        #: Whether the primary has answered once since this process started:
        #: a failure before that is a misconfiguration as often as an outage
        #: (a wrong credential in ``REDIS_URL`` is a ``RedisError`` too), #2049.
        self._ever_answered = False
        self._down_since = 0.0
        self._failed_probes = 0

    @property
    def base_exceptions(self) -> type[Exception] | tuple[type[Exception], ...]:
        # Only the fallback's errors can leave this storage.
        return self.fallback.base_exceptions

    def _claim_primary(self) -> tuple[bool, bool]:
        """Return ``(use_primary, is_probe)`` for the call about to be made."""
        with self._lock:
            if not self._down:
                return True, False
            if not self._probe_in_flight and time.monotonic() >= self._next_probe_at:
                self._probe_in_flight = True
                return True, True
            return False, False

    def _probe_failed_locked(self) -> None:
        """Release the probe slot and schedule the next probe; the caller holds ``_lock``."""
        self._probe_in_flight = False
        self._probe_delay_s = min(self._probe_delay_s * 2, _PROBE_MAX_DELAY_S)
        self._next_probe_at = time.monotonic() + self._probe_delay_s

    def _primary_failed(self, error: Exception, *, probe: bool) -> None:
        with self._lock:
            if probe:
                self._probe_failed_locked()
                self._failed_probes += 1
                remind = self._failed_probes % _REMINDER_EVERY_FAILED_PROBES == 0
                down_for_s = time.monotonic() - self._down_since
                never_answered = not self._ever_answered
            else:
                if self._down:
                    # A concurrent call already recorded this outage and set the schedule.
                    return
                self._down = True
                self._down_since = time.monotonic()
                self._failed_probes = 0
                self._probe_delay_s = _PROBE_INITIAL_DELAY_S
                self._next_probe_at = time.monotonic() + self._probe_delay_s
                never_answered = not self._ever_answered
        # Only the type: a redis-py message names host and port.
        if probe:
            if remind:
                # #2049: one warning per outage was the only signal, and a process
                # that counted for itself for days said so once, at the start.
                logger.warning(
                    "rate_limit_storage_still_unavailable",
                    error_type=type(error).__name__,
                    down_for_s=int(down_for_s),
                    never_answered=never_answered,
                    detail="IP rate limits count per process; every replica and worker grants the full budget",
                )
            return
        if never_answered:
            # #2049: never reached since start — a wrong REDIS_URL credential or
            # host looks exactly like this, and it reproduces the per-process
            # counting #2045 removed. Error level, not a readiness failure: an
            # unready pod would turn a Valkey outage into a full outage.
            logger.error(
                "rate_limit_storage_never_reached",
                error_type=type(error).__name__,
                detail=(
                    "IP rate limits count per process until the storage answers; "
                    "check RATE_LIMIT_STORAGE_URL / REDIS_URL"
                ),
            )
            return
        logger.warning("rate_limit_storage_unavailable", error_type=type(error).__name__)

    def _primary_answered(self, *, probe: bool) -> None:
        if not probe:
            return
        with self._lock:
            self._probe_in_flight = False
            self._down = False
            self._probe_delay_s = _PROBE_INITIAL_DELAY_S
        # The per-process counts are deliberately kept: they expire with their
        # own window. Clearing them here gave every outage/recovery cycle of a
        # flapping storage — about one a second — a fresh per-process budget.
        logger.info("rate_limit_storage_recovered")

    def _call(self, operation: Callable[[Storage], _T]) -> _T:
        use_primary, probe = self._claim_primary()
        if use_primary:
            try:
                result = operation(self.primary)
            except self.primary.base_exceptions as error:
                self._primary_failed(error, probe=probe)
            except BaseException:
                # Not an outage (a defect): surface it. A probe still releases
                # its slot — or the storage is never probed again — and moves
                # the plan on like a failed probe, so the next request does not
                # walk into the same defect at once.
                if probe:
                    with self._lock:
                        self._probe_failed_locked()
                raise
            else:
                self._ever_answered = True
                self._primary_answered(probe=probe)
                return result
        return operation(self.fallback)

    def incr(self, key: str, expiry: int, amount: int = 1) -> int:
        return self._call(lambda storage: storage.incr(key, expiry, amount))

    def get(self, key: str) -> int:
        return self._call(lambda storage: storage.get(key))

    def get_expiry(self, key: str) -> float:
        return self._call(lambda storage: storage.get_expiry(key))

    def check(self) -> bool:
        """Report the primary's health; the fallback is always available."""
        return bool(self.primary.check())

    def reset(self) -> int | None:
        self.fallback.reset()
        try:
            return self.primary.reset()
        except self.primary.base_exceptions:
            return None

    def clear(self, key: str) -> None:
        self.fallback.clear(key)
        try:
            self.primary.clear(key)
        except self.primary.base_exceptions:
            return


def resolve_rate_limit_storage_url() -> str:
    """Return the storage URI the IP rate limiter counts in.

    Returns:
        ``settings.rate_limit_storage_url`` when set, otherwise
        ``settings.redis_url`` — the shared Valkey every replica reaches.
    """
    return settings.rate_limit_storage_url or settings.redis_url


def _scheme(uri: str) -> str:
    return uri.partition("://")[0]


def bounded_redis_client_options() -> dict[str, object]:
    """Keyword arguments for ``redis.from_url`` that bound one socket operation to 0.5 s, no retry.

    Shared by this limiter's storage and by the mail-budget stores of the
    sign-in routes (``app.common.dependencies._get_throttle_redis_client``),
    which sit on the same request paths and degrade the same way.
    """
    return {
        "socket_connect_timeout": _REDIS_SOCKET_TIMEOUT_S,
        "socket_timeout": _REDIS_SOCKET_TIMEOUT_S,
        # redis-py 8.1 gives a connection built through ``from_url`` (the path
        # ``limits`` takes) no retries already — measured — but a client built
        # directly retries ten times with back-off. Pinned, so the one-timeout
        # bound does not hang on which path a future ``limits`` takes.
        "retry": Retry(NoBackoff(), 0),
    }


#: Set on the wrapper :class:`OffLoopLimiter` puts around an ``async`` route, so a
#: guard can tell a route whose check runs in the threadpool from one whose check
#: runs on the event loop (``tests/unit/guards/test_async_limited_routes_check_off_the_loop.py``).
LIMIT_CHECK_OFF_LOOP_ATTRIBUTE = "_kp_limit_check_off_loop"


class OffLoopLimiter(Limiter):
    """A slowapi ``Limiter`` whose ``async`` routes run the limit check in the threadpool (#2048).

    slowapi's ``async_wrapper`` calls the synchronous ``_check_request_limit``
    directly, so against a networked storage every check of an ``async def``
    route blocks the event loop for a round trip — a socket timeout while the
    storage hangs. This limiter puts one more wrapper around such a route: it
    runs the same check through ``run_in_threadpool`` and marks the request as
    checked (``request.state._rate_limiting_complete``, slowapi's own flag), so
    slowapi's wrapper skips its own check and only adds its headers.

    ``def`` routes are unchanged: FastAPI already runs them, check included, in
    the threadpool. A call that does not pass ``request`` by keyword — FastAPI
    always does — falls through to slowapi's own (on-loop) check rather than
    going unchecked.
    """

    def limit(self, *args: Any, **kwargs: Any) -> Callable[..., Any]:
        decorate = super().limit(*args, **kwargs)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            wrapped: Callable[..., Any] = decorate(func)
            if not inspect.iscoroutinefunction(func):
                return wrapped

            @functools.wraps(func)
            async def check_off_the_loop(*call_args: Any, **call_kwargs: Any) -> Any:
                request = call_kwargs.get("request")
                if (
                    self.enabled
                    and self._auto_check
                    and isinstance(request, Request)
                    and not getattr(request.state, "_rate_limiting_complete", False)
                ):
                    await run_in_threadpool(self._check_request_limit, request, func, False)
                    request.state._rate_limiting_complete = True
                return await wrapped(*call_args, **call_kwargs)

            setattr(check_off_the_loop, LIMIT_CHECK_OFF_LOOP_ATTRIBUTE, True)
            return check_off_the_loop

        return decorator


def build_process_memory_rate_limiter(key_func: Callable[[Request], str]) -> Limiter:
    """Build a limiter that counts in this process's memory only, whatever the settings say (#2048).

    For ``GET /api/health``: an unauthenticated M2M endpoint whose limit bounds
    amplification into internal services (SEC-003), not a security budget that
    must hold across replicas. Counting it in the shared storage cost every
    health request a Valkey round trip, and a socket timeout during an outage —
    the moment an operator or a client asks whether the backend is healthy.
    Per process, the bound is ``rate_limit_health`` times the process count.
    """
    return OffLoopLimiter(key_func=key_func, storage_uri="memory://", key_style=LIMITER_KEY_STYLE)


def build_rate_limiter(key_func: Callable[[Request], str], *, storage_url: str | None = None) -> Limiter:
    """Build a slowapi ``Limiter`` that counts in a shared storage and degrades per process.

    Construction is lazy in slowapi 0.1.10 / limits 5.x: no connection is opened
    here, so an unreachable storage cannot break application start-up.

    Args:
        key_func: Maps a request to its bucket (the resolved client address).
        storage_url: A ``limits`` storage URI; ``None`` resolves it from the
            settings via :func:`resolve_rate_limit_storage_url` and holds it to
            :data:`~app.config.settings.RATE_LIMIT_STORAGE_SCHEMES`.

    Returns:
        The configured :class:`OffLoopLimiter`. ``memory://`` is used as it is;
        any other storage is wrapped in :class:`FailoverStorage`.

    Raises:
        RateLimitStorageConfigError: The URI cannot be used as a storage. The
            message never contains the URI.
    """
    uri = storage_url if storage_url is not None else resolve_rate_limit_storage_url()
    if storage_url is None and not (
        rate_limit_storage_scheme_is_usable(uri) and storage_url_authority_is_well_formed(uri)
    ):
        # Both settings are checked when they load; ``REDIS_URL`` only for its
        # shape, not for a scheme the limiter can count in.
        raise _unusable_storage_error()

    if _scheme(uri) == "memory":
        if not settings.debug:
            # One process counting for itself is right for a test run or a
            # single-process server and wrong for anything with replicas or
            # workers. Never the URI — only what it means.
            logger.warning(
                "rate_limit_storage_counts_per_process",
                detail="IP rate limits count per process; every replica and worker grants the full budget",
            )
        return OffLoopLimiter(key_func=key_func, storage_uri=uri, key_style=LIMITER_KEY_STYLE)

    options: dict[str, object] = {"primary_uri": uri}
    if _scheme(uri) in _REDIS_SCHEMES:
        options.update(bounded_redis_client_options())
    return OffLoopLimiter(
        key_func=key_func,
        key_style=LIMITER_KEY_STYLE,
        storage_uri=f"{_FAILOVER_SCHEME}://",
        # slowapi annotates ``storage_options`` as ``Dict[str, str]`` although it
        # forwards them unchanged to the storage, which needs the primary URI,
        # numbers and a ``Retry`` object.
        storage_options=options,  # type: ignore[arg-type]
    )
