"""Bridge for running an async coroutine from synchronous code.

Some synchronous call sites (FastAPI sync route handlers running in the
threadpool, the tenant-deletion path) must invoke ``async`` adapter methods.
Plain ``asyncio.run`` is unsafe there: it creates and then *closes* the
thread's event loop, which breaks any caller that still relies on that loop
(notably the test process, where pytest-asyncio owns the main-thread loop).

``run_async`` sidesteps this by executing the coroutine on a fresh event loop
inside a short-lived worker thread, leaving the caller's loop untouched. When
no loop is running in the current thread it still works — it is loop-isolated
either way.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor


def run_async[T](coro: Coroutine[object, object, T]) -> T:
    """Run ``coro`` to completion on an isolated event loop and return its result.

    Safe to call from synchronous code regardless of whether the current thread
    already owns an event loop — the coroutine runs on a brand-new loop in a
    dedicated worker thread, so the caller's loop is never created, mutated or
    closed.
    """

    def _runner() -> T:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_runner).result()
