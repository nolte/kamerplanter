"""Celery-to-async bridge decorator (AP-18b / INF-D2).

``run_async_task`` registers an ``async`` function as a Celery task, running its
coroutine on the loop-isolated ``run_async`` bridge (a fresh event loop in a
short-lived worker thread — safe under the Celery prefork worker and under
pytest-asyncio, see ``app.common.async_bridge``). It also applies the shared
``try`` / log-failure / re-raise scaffold that was copied verbatim across the
retention tasks. Task-specific completion logging stays inside the wrapped
coroutine.
"""

import functools
from collections.abc import Callable, Coroutine
from typing import Any

import structlog

from app.common.async_bridge import run_async
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


def run_async_task(name: str, **task_kwargs: Any):
    """Register an async function as a Celery task using the shared async bridge.

    The coroutine returned by ``fn`` runs via ``run_async`` (loop-isolated),
    replacing the raw ``asyncio.run`` calls. Any exception is logged as
    ``<name>.failed`` and re-raised so Celery's ``autoretry_for``/retry policy
    still applies. ``task_kwargs`` are forwarded verbatim to ``celery_app.task``
    (e.g. ``autoretry_for``, ``max_retries``, ``retry_backoff``), so task names
    and retry semantics stay identical to the hand-written tasks.
    """

    def decorator[**P, R](fn: Callable[P, Coroutine[Any, Any, R]]):
        @celery_app.task(name=name, **task_kwargs)
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return run_async(fn(*args, **kwargs))
            except Exception as exc:
                logger.exception(f"{name}.failed", error=str(exc))
                raise

        return wrapper

    return decorator
