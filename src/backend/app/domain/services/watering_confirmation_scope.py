"""The run and task a watering confirmation names must be the confirming tenant's (#1864 sweep, L8).

``POST /t/{slug}/watering-events/confirm`` / ``quick-confirm`` and their
watering-log twins take ``run_key`` and ``task_key`` from the body. Neither was
resolved under the tenant: the task was loaded with an unscoped ``get_by_key``
and then marked ``COMPLETED`` — any tenant's task — and ``task_key`` and the
run's nutrient plan were stored on the new event or log.

One predicate for both services, so the two confirmation paths cannot drift
(the watering-event path was once missed when the log path was repaired, #951).

* The **run** must be the tenant's: a foreign or unknown run answers 404 before
  anything is read through it or written.
* The **task** is optional by contract: the run's watering schedule confirms by
  *date* (``PlantingRunDetailPage`` sends the schedule date as ``task_key``), so
  most confirmations name no task at all. A task is completed only when it
  exists **and** is the tenant's; a foreign task is treated exactly like a
  missing one — nothing is completed and the answer is the same — so it can
  neither be changed nor probed.
"""

from __future__ import annotations

from typing import Any

from app.common.exceptions import NotFoundError


def require_confirmable_run(run_repo: Any, run_key: str, *, tenant_key: str) -> None:
    """Refuse a run that is not the tenant's.

    Raises:
        NotFoundError: the run does not exist or is another tenant's.
    """
    run = run_repo.get_by_key(run_key) if run_key else None
    if run is None or getattr(run, "tenant_key", None) != tenant_key:
        raise NotFoundError("PlantingRun", run_key)


def own_task_or_none(task_repo: Any, task_key: str, *, tenant_key: str) -> Any:
    """The task ``task_key`` if it is the tenant's, else ``None`` — foreign and missing alike."""
    task = task_repo.get_by_key(task_key) if task_key else None
    if task is None or getattr(task, "tenant_key", None) != tenant_key:
        return None
    return task
