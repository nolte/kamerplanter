"""v0009_notification_group_key_index — add the persistent ``group_key`` index to
the ``notifications`` collection on existing volumes (Issue #409, F2).

The proactive frost-forecast producer deduplicates and tops up recipients per
``(group_key, tenant_key)`` (``exists_by_group_key`` / ``find_notified_user_keys``).
Before this change ``notifications`` carried no index on ``group_key``, so a
growing collection was full-scanned on every frost-predicted site per day.

Fresh databases get the index from ``ensure_collections`` bootstrap
(``collections.py``); this migration brings *existing* volumes to the same shape.
It creates the identical non-unique persistent index on
``["group_key", "tenant_key"]`` (non-unique: many users share one ``group_key``).

Idempotent (M-3): the target index is looked up first — when a persistent index on
``["group_key", "tenant_key"]`` already exists (bootstrapped fresh DB or a prior
run) the migration is a no-op (``changed == 0``). ArangoDB persistent-index
creation is itself idempotent by field-set, so a re-run never duplicates it. Dry-run
(M-5): existence is inspected without creating anything. Irreversible (M-6):
dropping an index that may predate this migration (bootstrap also creates it) would
not honestly restore the pre-migration state, so no inverse is offered.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

_TARGET_FIELDS: list[str] = ["group_key", "tenant_key"]


def _has_group_key_index(indexes: object) -> bool:
    """True when a persistent index on ``_TARGET_FIELDS`` already exists.

    ``collection.indexes()`` returns a list of index dicts (``type``/``fields``);
    a match on both the type and the exact field ordering means the dedup read is
    already backed and the migration has nothing to do.
    """
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _TARGET_FIELDS
        for idx in indexes
    )


class NotificationGroupKeyIndexMigration(Migration):
    version = "0009"
    name = "notification_group_key_index"
    description = "Add the persistent (group_key, tenant_key) index to notifications on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        collection = db.collection(col.NOTIFICATIONS)
        already_present = _has_group_key_index(collection.indexes())

        # ``scanned`` counts the one target index definition inspected; ``changed``
        # is 1 only when this run actually creates it.
        details = {"index_fields": _TARGET_FIELDS, "already_present": already_present}

        if dry_run:
            logger.info("notification_group_key_index_dry_run", already_present=already_present)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=1,
                changed=0,
                dry_run=True,
                details=details,
            )

        changed = 0
        if not already_present:
            collection.add_persistent_index(fields=_TARGET_FIELDS, unique=False)
            changed = 1

        logger.info("notification_group_key_index_applied", changed=changed, already_present=already_present)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=1,
            changed=changed,
            dry_run=False,
            details={**details, "created": bool(changed)},
        )


migration = NotificationGroupKeyIndexMigration()
