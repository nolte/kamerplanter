"""REQ-016 §3.6 — Celery tasks for the optional InvenTree sync.

Two periodic tasks drive the bidirectional sync across every tenant that has an
active InvenTree connection:

* ``sync_stock_levels`` (hourly) pulls current stock into the local cache (READ).
* ``push_pending_transactions`` (every 5 min) drains pending consumption
  bookings to InvenTree (WRITE).

Both are no-ops when the integration kill-switch is off, and each connection is
processed independently so one unreachable InvenTree instance never aborts the
run (graceful degradation). The per-tenant read/write path stays tenant-scoped:
the sync engine is built for one connection's ``tenant_key`` at a time (SEC-B4).
"""

from __future__ import annotations

import asyncio

import structlog

from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


def _active_connections():
    """Yield ``(tenant_key, connection)`` for every active connection, cross-tenant."""
    from app.common.dependencies import get_inventree_repo
    from app.data_access.arango.collections import INVENTREE_CONNECTIONS
    from app.domain.models.inventree import InvenTreeConnection

    repo = get_inventree_repo()
    db = repo._db  # noqa: SLF001 — direct AQL for cross-tenant iteration (mirrors frost task)
    cursor = db.aql.execute(
        "FOR c IN @@col FILTER c.is_active == true RETURN c",
        bind_vars={"@col": INVENTREE_CONNECTIONS},
    )
    for doc in cursor:
        connection = InvenTreeConnection(**repo._from_doc(doc))  # noqa: SLF001
        if connection.tenant_key:
            yield connection.tenant_key, connection


def _run_per_connection(operation: str) -> dict:
    from app.common.dependencies import _get_redis_client, get_encryption_engine, get_inventree_repo
    from app.domain.services.inventree_service import InvenTreeService

    repo = get_inventree_repo()
    # Inject the shared Valkey/Redis client (same factory as the HTTP path in
    # ``dependencies.get_inventree_service``) so the adapter's persistent
    # per-connection outbound rate-limit window (IT-005) also applies on the
    # Celery path. Without it the service degrades to a best-effort in-memory
    # window that resets on every task run — leaving the 60/min cap ineffective
    # for the scheduler-driven sync/push.
    service = InvenTreeService(repo, get_encryption_engine(), redis_client=_get_redis_client())

    totals = {"connections": 0, "ok": 0, "errors": 0}
    for tenant_key, connection in _active_connections():
        totals["connections"] += 1
        try:
            engine = service._sync_engine_for(connection, tenant_key)  # noqa: SLF001
            if operation == "sync":
                asyncio.run(engine.sync_stock_levels())
            else:
                asyncio.run(engine.push_pending_transactions())
            totals["ok"] += 1
        except Exception as exc:  # noqa: BLE001 — one bad connection must not abort the run
            totals["errors"] += 1
            logger.warning(
                "inventree_task_connection_failed",
                operation=operation,
                connection_key=connection.key,
                error=type(exc).__name__,
            )
    return totals


@celery_app.task(name="inventree.sync_stock_levels", bind=True, max_retries=3, default_retry_delay=300)
def sync_stock_levels(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Periodic READ: pull current InvenTree stock into the local cache."""
    if not settings.inventree_enabled:
        return {"status": "skipped", "reason": "inventree_disabled"}
    result = _run_per_connection("sync")
    logger.info("inventree_stock_sync_complete", **result)
    return {"status": "ok", **result}


@celery_app.task(name="inventree.push_pending_transactions", bind=True, max_retries=2, default_retry_delay=60)
def push_pending_transactions(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Periodic WRITE: drain pending consumption bookings to InvenTree."""
    if not settings.inventree_enabled:
        return {"status": "skipped", "reason": "inventree_disabled"}
    result = _run_per_connection("push")
    logger.info("inventree_push_complete", **result)
    return {"status": "ok", **result}
