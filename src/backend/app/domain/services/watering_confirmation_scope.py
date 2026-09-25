"""The run and task a watering confirmation names must be the confirming tenant's (#1864 sweep, L8).

``POST /t/{slug}/watering-events/confirm`` / ``quick-confirm`` and their
watering-log twins take ``run_key`` and ``task_key`` from the body. Neither was
resolved under the tenant: the task was loaded with an unscoped ``get_by_key``
and then marked ``COMPLETED`` — any tenant's task — and ``task_key`` and the
run's nutrient plan were stored on the new event or log.

One predicate for both services, so the two confirmation paths cannot drift
(the watering-event path was once missed when the log path was repaired, #951).
Both keys are resolved **before** anything is read through them or written; a
foreign and an unknown key give the same 404.
"""

from __future__ import annotations

from typing import Any

from app.common.exceptions import NotFoundError


def require_confirmable_run_and_task(
    run_repo: Any,
    task_repo: Any,
    run_key: str,
    task_key: str,
    *,
    tenant_key: str,
) -> Any:
    """Return the task after proving run and task belong to ``tenant_key``.

    Raises:
        NotFoundError: the run or the task does not exist or is another tenant's.
    """
    run = run_repo.get_by_key(run_key) if run_key else None
    if run is None or getattr(run, "tenant_key", None) != tenant_key:
        raise NotFoundError("PlantingRun", run_key)
    task = task_repo.get_by_key(task_key) if task_key else None
    if task is None or getattr(task, "tenant_key", None) != tenant_key:
        raise NotFoundError("Task", task_key)
    return task
