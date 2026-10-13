"""v0092 — add the persistent ``(tenant_key, status)`` index to ``tasks`` on existing volumes (#1534).

The tenant's task queue (``GET /t/{slug}/tasks/queue``), the overdue list and the
status-filtered task list read ``FILTER doc.tenant_key == @t AND doc.status == @s``.
``tasks`` carried a single-field ``status`` index and no index with ``tenant_key``,
so the optimizer took ``status`` and filtered the tenant afterwards: every tenant's
queue read every pending task of the installation. Measured on ArangoDB 3.12.12
(``spec/analysis/task-queue-index-measurement-2026-10.md``): at 970 426 tasks across
3 406 tenants a 277-task tenant scanned 533 680 index entries and took ~1.4 s per
query, two queries per queue call; with this index it reads 149 entries in ~2 ms.

``due_date`` is deliberately **not** a third field: the queries sort and filter on
``DATE_TIMESTAMP(doc.due_date)`` with a ``_key`` tie-breaker and the orphan guard sits
between the index scan and the ``SORT``, so a third field changed no plan (identical
scan counts, the ``SortNode`` stays). The single-field ``status`` index stays as well.

Fresh databases get the identical index from ``ensure_collections``
(:data:`~app.data_access.arango.collections.TASK_TENANT_STATUS_INDEX_FIELDS`); this
migration brings a volume that predates it to the same shape. Structural only — **no
document is read or written**. Built ``in_background`` like the bootstrap does, so a
large ``tasks`` collection stays writable while it is built (1.97 s at 970 k tasks).

Idempotent (M-3): a persistent-family index on exactly ``(tenant_key, status)`` —
``persistent`` or a pre-June ``hash`` one, selected through
:func:`~app.migrations.support.legacy_indexes.indexes_on` — makes the run a no-op
(``changed == 0``). Dry-run (M-5) inspects without creating. Irreversible (M-6): the
bootstrap creates the same index on every boot, so dropping it would not restore the
pre-migration state.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import indexes_on

logger = structlog.get_logger(__name__)

#: The target field list, frozen here so a later change of the bootstrap constant does
#: not change what this applied version did. Order is significant: ``tenant_key`` leads,
#: so a tenant-only filter (``get_all_tasks`` without a status) uses it as a prefix.
#: Equal to ``collections.TASK_TENANT_STATUS_INDEX_FIELDS`` (asserted by its unit test).
TARGET_FIELDS: tuple[str, ...] = ("tenant_key", "status")


class TaskTenantStatusIndexMigration(Migration):
    version = "0092"
    name = "task_tenant_status_index"
    description = (
        "Add the persistent (tenant_key, status) index to tasks on existing volumes so a "
        "tenant's task queue reads its own pending tasks, not the installation's (#1534)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        fields = list(TARGET_FIELDS)
        if not db.has_collection(col.TASKS):
            # Nothing to index; bootstrap creates collection and index together.
            logger.info("task_tenant_status_index_skipped", reason="collection_absent")
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=0,
                changed=0,
                dry_run=dry_run,
                details={"index_fields": fields, "collection_absent": True},
            )

        tasks = db.collection(col.TASKS)
        already_present = bool(indexes_on(tasks, fields))
        details: dict[str, object] = {"index_fields": fields, "already_present": already_present}

        if dry_run:
            logger.info("task_tenant_status_index_dry_run", already_present=already_present)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=1,
                changed=0,
                dry_run=True,
                details={**details, "will_create": not already_present},
            )

        changed = 0
        if not already_present:
            tasks.add_persistent_index(fields=fields, unique=False, in_background=True)
            changed = 1

        logger.info("task_tenant_status_index_applied", changed=changed, already_present=already_present)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=1,
            changed=changed,
            dry_run=False,
            details={**details, "created": bool(changed)},
        )


migration = TaskTenantStatusIndexMigration()
