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
from dataclasses import dataclass
from typing import Any

import structlog

from app.common.async_bridge import run_async
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class TaskAttempt:
    """Where a bound task stands in its retry chain, captured in the worker thread.

    Celery's ``task.request`` is a **thread-local** stack. The coroutine runs on
    the ``run_async`` bridge's own thread, where ``self.request`` is an empty
    context and ``retries`` always reads as ``0`` — so a coroutine that asked the
    task itself would believe every attempt is the first (#1666). The snapshot
    is taken in the Celery thread, before the coroutine starts.
    """

    retries: int
    max_retries: int | None

    @property
    def number(self) -> int:
        """1-based number of this attempt."""
        return self.retries + 1

    @property
    def is_retry(self) -> bool:
        return self.retries > 0

    @property
    def is_final(self) -> bool:
        """No further retry follows this attempt."""
        return self.max_retries is not None and self.retries >= self.max_retries


def run_async_task(name: str, **task_kwargs: Any):
    """Register an async function as a Celery task using the shared async bridge.

    The coroutine returned by ``fn`` runs via ``run_async`` (loop-isolated),
    replacing the raw ``asyncio.run`` calls. Any exception is logged as
    ``<name>.failed`` and re-raised so Celery's ``autoretry_for``/retry policy
    still applies. ``task_kwargs`` are forwarded verbatim to ``celery_app.task``
    (e.g. ``autoretry_for``, ``max_retries``, ``retry_backoff``), so task names
    and retry semantics stay identical to the hand-written tasks.

    With ``bind=True`` the coroutine's first argument is a :class:`TaskAttempt`
    snapshot, **not** the task instance: the task's ``request`` is thread-local
    and reads empty on the bridge thread the coroutine runs on.
    """
    bind = bool(task_kwargs.get("bind"))

    def decorator[**P, R](fn: Callable[P, Coroutine[Any, Any, R]]):
        @celery_app.task(name=name, **task_kwargs)
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            attempt: TaskAttempt | None = None
            retried_on: tuple[type[BaseException], ...] = ()
            if bind:
                task, *rest = args
                attempt = TaskAttempt(retries=task.request.retries or 0, max_retries=task.max_retries)
                retried_on = tuple(getattr(task, "autoretry_for", ()) or ())
                args = (attempt, *rest)
            try:
                return run_async(fn(*args, **kwargs))
            except Exception as exc:
                if attempt is not None and not attempt.is_final and isinstance(exc, retried_on):
                    # Celery retries this one; "<name>.failed" at error level
                    # would announce a failure that has not happened (#1666).
                    logger.warning(
                        f"{name}.attempt_failed",
                        attempt=attempt.number,
                        error_type=type(exc).__name__,
                        error=str(exc),
                    )
                else:
                    logger.exception(f"{name}.failed", error=str(exc))
                raise

        return wrapper

    return decorator
