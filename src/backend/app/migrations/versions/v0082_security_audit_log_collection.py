"""v0082 - MT-014 (#2111): the persistent ``security_audit_log`` collection.

Creates the append-only collection that records every change of a tenant
membership, role or scope (who, whom, which tenant, when) on *existing* volumes
and adds its persistent indexes: ``(tenant_key, created_at)`` (a tenant's own
history), ``target_user_key`` and ``actor_user_key`` (the two account lookups the
erasure pseudonymisation and the admin read use) and ``created_at`` (the NFR-011
R-38 retention sweep).

Fresh databases already get all of this from the idempotent startup
``ensure_collections`` (``collections.py``), which the app lifespan runs *before*
migrations; this migration brings existing volumes - and the standalone
``python -m app.migrations`` path, which does not call ``ensure_collections`` - to
the same shape.

Purely additive and idempotent (M-3): every step checks for existence first, so a
re-run is a no-op (``changed == 0``). No data is read or rewritten. Irreversible
(M-6): dropping a collection that holds the audit record would destroy it, so no
inverse is offered.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import is_index_on

logger = structlog.get_logger()

#: ``(fields, unique)`` index specifications of the collection.
_INDEXES: list[tuple[list[str], bool]] = [
    (["tenant_key", "created_at"], False),
    (["target_user_key"], False),
    (["actor_user_key"], False),
    (["created_at"], False),
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(isinstance(idx, dict) and is_index_on(idx, fields) for idx in indexes)


class SecurityAuditLogCollectionMigration(Migration):
    version = "0082"
    name = "security_audit_log_collection"
    description = "Create the MT-014 security_audit_log collection and its indexes on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        collection_missing = not db.has_collection(col.SECURITY_AUDIT_LOG)
        present = [] if collection_missing else db.collection(col.SECURITY_AUDIT_LOG).indexes()
        index_missing = [(fields, unique) for fields, unique in _INDEXES if not _has_index(present, fields)]

        pending = {
            "document_collections": [col.SECURITY_AUDIT_LOG] if collection_missing else [],
            "indexes": [f"{col.SECURITY_AUDIT_LOG}:{fields}" for fields, _ in index_missing],
        }
        changes = int(collection_missing) + len(index_missing)
        scanned = 1 + len(_INDEXES)

        if dry_run:
            logger.info("security_audit_log_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=pending
            )

        if collection_missing:
            db.create_collection(col.SECURITY_AUDIT_LOG)
        collection = db.collection(col.SECURITY_AUDIT_LOG)
        for fields, unique in index_missing:
            if not _has_index(collection.indexes(), fields):
                collection.add_persistent_index(fields=fields, unique=unique)

        logger.info("security_audit_log_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=pending
        )


migration = SecurityAuditLogCollectionMigration()
