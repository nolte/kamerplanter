"""A per-configuration cache of the signing keys an OIDC provider publishes (#1987).

Until #1987 every login did one or two GETs to the provider — the discovery document, then
the key set — so a provider outage, or a throttle on its key endpoint, was a login outage,
and anyone able to start logins could make this server fetch from the provider as often as
they liked.

**What it does.**

* A key set is kept for ``JWKS_TTL_SECONDS`` per configuration (and per resolved source: the
  cache key includes the issuer and the key URL the configuration points at, so repointing a
  provider never reuses the old provider's keys).
* A token whose header names a ``kid`` the cached set does not hold causes **one** refetch —
  provider key rotation — but never more than one per ``JWKS_REFETCH_MIN_INTERVAL_SECONDS``
  and configuration, successful or not. An attacker who forges key ids therefore costs the
  provider one request per interval, not one per attempt. The price is that the first login
  signed with a freshly rotated key can be refused if another fetch happened in the last ten
  seconds; the next one, ten seconds later, is not.
* A failed fetch is remembered for ``JWKS_NEGATIVE_TTL_SECONDS`` — long enough to stop an
  outage turning every login into a request to the provider, short enough that a provider
  that comes back is used again within the half minute. It is **never** cached for the
  positive TTL, and no stale key set is served after a failed refetch of an expired one:
  fail closed.

**One process, one cache.** The state is in the memory of the worker. A second worker has its
own and fetches on its own: at most one extra request per worker per TTL, and nothing is
shared that could be poisoned across processes or survive a restart. Moving it to Redis would
buy only that saving.

The clock is :func:`time.monotonic` (``_clock``, replaceable in a test); wall-clock changes do
not stretch an entry.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from typing import Any

#: How long a fetched key set is used. Providers rotate keys over days and publish the next
#: key before signing with it; ten minutes is far inside that, and bounds how long a key the
#: provider withdrew stays accepted.
JWKS_TTL_SECONDS = 600.0

#: How long a failed fetch is remembered.
JWKS_NEGATIVE_TTL_SECONDS = 30.0

#: The least time between two fetches for one configuration that an unknown ``kid`` may cause.
JWKS_REFETCH_MIN_INTERVAL_SECONDS = 10.0

#: The most one fetch may take, wall clock. httpx bounds each phase, not the request; this bounds
#: the whole of a response that arrives in dribbles.
JWKS_FETCH_DEADLINE_SECONDS = 10.0

#: The largest key set (and discovery document) read. Real ones are a few kilobytes (Google's
#: is about 1.5 KB); a response beyond this is not read to the end.
JWKS_MAX_BYTES = 256 * 1024


class JwksFetchError(Exception):
    """The key set could not be obtained (network, status, size, content or URL).

    Carries no URL or body: a caller logs the reason, not what the provider said.
    """


def _clock() -> float:
    return time.monotonic()


@dataclass
class _Entry:
    keys: Any | None
    kids: frozenset[str]
    fetched_at: float
    expires_at: float
    failed_until: float = 0.0


class JwksCache:
    """The cache itself. One module-level instance serves the process (see :func:`cached_key_set`)."""

    def __init__(self) -> None:
        self._entries: dict[Hashable, _Entry] = {}
        self._guard = threading.Lock()
        self._fetch_locks: dict[Hashable, threading.Lock] = {}

    def clear(self) -> None:
        with self._guard:
            self._entries.clear()
            self._fetch_locks.clear()

    def key_set(
        self,
        cache_key: Hashable,
        fetch: Callable[[], tuple[Any, frozenset[str]]],
        *,
        kid: str | None = None,
    ) -> Any:
        """The key set for *cache_key*: cached while fresh, fetched (once) when missing, expired or lacking *kid*.

        *fetch* returns the set and the key ids it holds. Fetches for one configuration are
        serialised, so a burst of logins after expiry is one request, not one each.

        Raises:
            JwksFetchError: the fetch failed now, or failed within the negative TTL.
        """
        with self._guard:
            lock = self._fetch_locks.setdefault(cache_key, threading.Lock())
        # A bounded wait: the fetch inside is bounded (``JWKS_FETCH_DEADLINE_SECONDS``), so a
        # login that cannot get the lock in about twice that is behind a hung one and fails
        # rather than holding a worker thread.
        if not lock.acquire(timeout=2 * JWKS_FETCH_DEADLINE_SECONDS + 5):
            raise JwksFetchError("Timed out waiting for another fetch of the key set.")
        try:
            return self._key_set_locked(cache_key, fetch, kid)
        finally:
            lock.release()

    def _key_set_locked(
        self, cache_key: Hashable, fetch: Callable[[], tuple[Any, frozenset[str]]], kid: str | None
    ) -> Any:
        now = _clock()
        entry = self._entries.get(cache_key)
        if entry is not None:
            if entry.keys is None:
                if entry.failed_until > now:
                    raise JwksFetchError("A recent fetch of the key set failed.")
            elif now < entry.expires_at:
                if kid is None or kid in entry.kids:
                    return entry.keys
                if now - entry.fetched_at < JWKS_REFETCH_MIN_INTERVAL_SECONDS:
                    return entry.keys  # unknown kid, but the set was fetched moments ago
        try:
            keys, kids = fetch()
        except JwksFetchError:
            if entry is not None and entry.keys is not None and now < entry.expires_at:
                # A refetch for an unknown ``kid`` failed: keep the fresh set, and stamp the
                # attempt so the next forged ``kid`` waits out the interval as well.
                entry.fetched_at = now
                return entry.keys
            self._entries[cache_key] = _Entry(
                keys=None,
                kids=frozenset(),
                fetched_at=now,
                expires_at=now,
                failed_until=now + JWKS_NEGATIVE_TTL_SECONDS,
            )
            raise
        self._entries[cache_key] = _Entry(keys=keys, kids=kids, fetched_at=now, expires_at=now + JWKS_TTL_SECONDS)
        return keys


_CACHE = JwksCache()


def cached_key_set(
    cache_key: Hashable, fetch: Callable[[], tuple[Any, frozenset[str]]], *, kid: str | None = None
) -> Any:
    """:meth:`JwksCache.key_set` on the process-wide cache."""
    return _CACHE.key_set(cache_key, fetch, kid=kid)


def reset_jwks_cache() -> None:
    """Forget everything — for tests, and for an operator tool that wants the next login to fetch."""
    _CACHE.clear()
