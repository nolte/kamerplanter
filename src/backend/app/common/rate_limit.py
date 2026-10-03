"""Build the IP rate limiter against a storage every process shares (#2045).

slowapi's ``Limiter`` keeps its counters in ``memory://`` unless it is handed a
storage, and the backend's one shared ``limiter`` was built without one. Each
replica — and each worker process inside a replica — therefore counted on its
own, and ``N`` processes multiplied every ``@limiter.limit`` by ``N``: the login
and registration bounds, the pairing redemption bound, and the mail bound on
``/auth/resend-verification`` that exists to cap outbound mail to third parties.

**Where the count lives.** :func:`resolve_rate_limit_storage_url` reads
``settings.rate_limit_storage_url`` and, when it is empty, the Valkey in
``settings.redis_url`` the backend already depends on. A shared count is the
default, not an opt-in a deployment has to remember.

**What happens when that storage is gone.** The limiter is built with
``in_memory_fallback_enabled=True``: on the first storage error slowapi marks the
storage dead and evaluates the *same* route limits against an in-process
``MemoryStorage``, probing the real storage again with exponential back-off
(1, 2, 4 … 32 s) and switching back when it answers. During an outage the bound
is therefore the per-process one this module replaces — weaker than intended,
but never open, and never a 500 on every limited route (which is what a storage
without fallback produces: measured ``[500, 500, 500]`` against an unreachable
Redis). The fixed-window count restarts in the fallback, so the request that
crosses the outage can see up to one fresh window per process.

**Bounded waits.** Each check is a round trip on the request path, so the Redis
client gets explicit socket timeouts: a Valkey that hangs instead of refusing
costs a request at most that long before the fallback takes over, rather than
the redis-py default of waiting forever.
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlsplit

from slowapi import Limiter
from starlette.requests import Request

from app.config.settings import settings

#: Seconds to wait for the rate-limit storage to accept a connection / answer a
#: command. The counters are a single ``INCR`` + ``EXPIRE`` on an in-cluster
#: Valkey, sub-millisecond when healthy; half a second is far beyond a healthy
#: answer and short enough that a hung store degrades to the fallback instead of
#: stalling logins.
_REDIS_SOCKET_TIMEOUT_S = 0.5

#: Schemes whose ``limits`` storage hands its options straight to
#: ``redis.from_url`` (or the valkey equivalent), so the socket timeouts above
#: are understood. Sentinel and cluster storages build their clients
#: differently and get no options rather than options they might reject.
_REDIS_SCHEMES = frozenset({"redis", "rediss", "redis+unix", "valkey", "valkeys", "valkey+unix"})


def resolve_rate_limit_storage_url() -> str:
    """Return the storage URI the IP rate limiter counts in.

    Returns:
        ``settings.rate_limit_storage_url`` when set, otherwise
        ``settings.redis_url`` — the shared Valkey every replica reaches.
    """
    return settings.rate_limit_storage_url or settings.redis_url


def _storage_options(storage_url: str) -> dict[str, float]:
    if urlsplit(storage_url).scheme in _REDIS_SCHEMES:
        return {
            "socket_connect_timeout": _REDIS_SOCKET_TIMEOUT_S,
            "socket_timeout": _REDIS_SOCKET_TIMEOUT_S,
        }
    return {}


def build_rate_limiter(key_func: Callable[[Request], str], *, storage_url: str | None = None) -> Limiter:
    """Build a slowapi ``Limiter`` that counts in a shared storage and degrades per process.

    Construction is lazy in slowapi 0.1.10 / limits 5.x: no connection is opened
    here, so an unreachable storage cannot break application start-up.

    Args:
        key_func: Maps a request to its bucket (the resolved client address).
        storage_url: A ``limits`` storage URI; ``None`` resolves it from the
            settings via :func:`resolve_rate_limit_storage_url`.

    Returns:
        The configured limiter, with in-memory fallback enabled.
    """
    uri = storage_url if storage_url is not None else resolve_rate_limit_storage_url()
    # slowapi annotates ``storage_options`` as ``Dict[str, str]`` although it
    # forwards them unchanged to redis-py, which needs the timeouts as numbers.
    options: dict[str, str] = _storage_options(uri)  # type: ignore[assignment]
    return Limiter(
        key_func=key_func,
        storage_uri=uri,
        storage_options=options,
        in_memory_fallback_enabled=True,
    )
