"""Celery tasks of the tenant export and import (REQ-056 §8, #2138) — both on the ``bulk`` queue.

Long, resumable-by-request work: an archive of a large tenant reads every row of it
and its objects. Neither task retries on its own: a failed run is recorded on its
request (``failed`` with a reason) and the requester asks again; a run that died
without recording anything is ended by ``retention.expire_data_exports`` once its
heartbeat is older than six hours, so the one-running-export rule does not block
the tenant for ever.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any, cast

import structlog

from app.tasks.task_bridge import TaskAttempt, run_async_task

logger = structlog.get_logger(__name__)


type _TaskBody = Callable[[TaskAttempt, str], Coroutine[Any, Any, dict[str, str]]]

#: ``run_async_task`` with its return type spelled out: Celery ships no types, and an untyped
#: decorator would make the coroutines below untyped as well (mypy strict, #2169). Both tasks are
#: started by name (``celery_app.send_task`` in ``dependencies.get_tenant_export_service``).
_task = cast(Callable[..., Callable[[_TaskBody], object]], run_async_task)


@_task(name="app.tasks.tenant_export_tasks.run_tenant_export", bind=True, max_retries=0)
async def run_tenant_export(attempt: TaskAttempt, export_key: str) -> dict[str, str]:
    """Write and store the archive of one requested tenant export (dispatched by the request)."""
    del attempt
    from app.common.dependencies import get_tenant_export_service

    result = await get_tenant_export_service().run_export(export_key)
    status = result.status if result else "unknown"
    logger.info("tenant_export.task_finished", export_key=export_key, status=status)
    return {"export_key": export_key, "status": status}


@_task(name="app.tasks.tenant_export_tasks.run_tenant_import", bind=True, max_retries=0)
async def run_tenant_import(attempt: TaskAttempt, import_key: str) -> dict[str, str]:
    """Import one verified, stored tenant archive into a new tenant (dispatched by the request)."""
    del attempt
    from app.common.dependencies import get_tenant_export_service

    result = await get_tenant_export_service().run_import(import_key)
    status = result.status if result else "unknown"
    logger.info("tenant_import.task_finished", import_key=import_key, status=status)
    return {"import_key": import_key, "status": status}
