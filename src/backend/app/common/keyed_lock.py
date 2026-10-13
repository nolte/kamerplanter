"""One in-process lock per key, created on demand and dropped when nobody holds or waits for it (#2062)."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager


class KeyedLocks:
    """``with locks.hold(key):`` serialises the threads of this process that use the same key.

    Unrelated keys never wait for each other, and the table holds an entry only
    while a thread holds or waits for it, so it is bounded by the concurrency,
    not by the number of keys ever used. It does **not** reach other processes
    or replicas: the guarantee is per process.
    """

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._entries: dict[str, tuple[threading.Lock, int]] = {}

    @contextmanager
    def hold(self, key: str) -> Iterator[None]:
        with self._guard:
            lock, users = self._entries.get(key) or (threading.Lock(), 0)
            self._entries[key] = (lock, users + 1)
        lock.acquire()
        try:
            yield
        finally:
            lock.release()
            with self._guard:
                lock, users = self._entries[key]
                if users <= 1:
                    del self._entries[key]
                else:
                    self._entries[key] = (lock, users - 1)

    def __len__(self) -> int:
        with self._guard:
            return len(self._entries)
