"""Celery task ``adjacency_recompute`` (REQ-053 GP-NFR-016, GP-FR-130).

Derives the ``adjacent_to`` edges of one bed after its slots changed (``PATCH /slots``, ``slots/batch``,
run creation, reservations, clearing). It is dispatched **after** the write committed and decoupled from the
request, so a slow derivation never holds the editor, and it is idempotent: the derivation is a pure
function of the stored slots and the reconcile only writes the difference, so a redelivered or overlapping
run changes nothing (the task is listed in ``ACKS_LATE_TASKS`` for that reason).

The message carries **only** ``location_key``. The task resolves the site and the tenant from the stored
documents itself — nothing in the message could be trusted to name them — and leaves a bed whose tenant is
not ``active`` alone (REQ-056 §5.2).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import structlog

from app.common.exceptions import NotFoundError
from app.tasks import celery_app

logger = structlog.get_logger(__name__)

TASK_NAME = "app.tasks.adjacency.adjacency_recompute"

#: ``celery_app.task`` with its return type spelled out: Celery ships no types, and an untyped decorator would
#: make the function below untyped as well (mypy strict, #2169).
_task = cast(Callable[..., Callable[[Callable[..., dict[str, Any]]], Any]], celery_app.task)


@_task(name=TASK_NAME, bind=True, max_retries=3, default_retry_delay=30)
def adjacency_recompute(self: Any, location_key: str) -> dict[str, Any]:
    """Re-derive the neighbourhood of the slots of bed ``location_key``."""
    from app.common.dependencies import get_adjacency_service, get_site_repo, get_tenant_repo
    from app.tasks.tenant_gate import ActiveTenants

    sites = get_site_repo()
    location = sites.get_location_by_key(location_key) if location_key else None
    site = sites.get_site_by_key(location.site_key) if location is not None and location.site_key else None
    if location is None or site is None or not site.tenant_key:
        # The bed is gone (deleted between the write and the run): nothing to derive, nothing to retry.
        return {"status": "skipped", "reason": "location_not_found", "location_key": location_key}
    if not ActiveTenants(get_tenant_repo())(site.tenant_key):
        return {"status": "skipped", "reason": "tenant_not_active", "location_key": location_key}
    try:
        result = get_adjacency_service().recompute(location_key, tenant_key=site.tenant_key)
    except NotFoundError:
        # The bed vanished between the lookup and the call: permanent, not worth three retries.
        return {"status": "skipped", "reason": "location_not_found", "location_key": location_key}
    except Exception as exc:
        logger.warning("adjacency.recompute_failed", location_key=location_key, error_type=type(exc).__name__)
        raise self.retry(exc=exc) from exc
    return {
        "status": "ok",
        "location_key": location_key,
        "pairs": result.pairs,
        "created": result.sync.created,
        "updated": result.sync.updated,
        "removed": result.sync.removed,
    }
