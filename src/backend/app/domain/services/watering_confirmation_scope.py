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
* The run's **nutrient plan** is a stored reference: it is followed only when the
  tenant may read it (own or global); an unreadable one is treated as no plan, so
  neither its watering schedule nor its key reaches the event or log (#2107
  review SEC-002).
* The run's **plants** come from ``run_contains`` edges: a plant that is missing
  or another tenant's (a legacy edge) is left out of everything written (#2107
  review SEC-001 sweep).
"""

from __future__ import annotations

from typing import Any

from app.common.exceptions import NotFoundError
from app.domain.services.feeding_references import require_readable_nutrient_plan


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


def readable_run_plan(run_repo: Any, plan_repo: Any, run_key: str, *, tenant_key: str) -> tuple[str | None, Any]:
    """``(plan_key, plan)`` of the run's nutrient plan if the tenant may read it, else ``(None, None)``."""
    plan_key = run_repo.get_run_nutrient_plan_key(run_key)
    if not plan_key or plan_repo is None:
        return None, None
    try:
        return plan_key, require_readable_nutrient_plan(plan_repo, plan_key, tenant_key)
    except NotFoundError:
        return None, None


def own_run_plants(run_repo: Any, plant_repo: Any, run_key: str, *, tenant_key: str) -> list[dict[str, Any]]:
    """The run's attached plant rows whose plant is the tenant's; nothing without a plant repository."""
    rows: list[dict[str, Any]] = []
    for row in run_repo.get_run_plants(run_key, include_detached=False):
        plant_key = row.get("_key") or ""
        plant = plant_repo.get_by_key(plant_key) if plant_repo is not None and plant_key else None
        if plant is not None and tenant_key and getattr(plant, "tenant_key", None) == tenant_key:
            rows.append(row)
    return rows
