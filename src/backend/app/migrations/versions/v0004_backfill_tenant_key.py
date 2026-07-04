"""v0004_backfill_tenant_key — assign tenant_key to legacy tenant-scoped docs.

Thin version wrapper: the transformation logic lives in
:mod:`app.migrations.backfill_tenant_key` and is reused verbatim.

The underlying multi-phase backfill has no native ``dry_run`` (its phases depend
on earlier phases having written).  Rather than duplicate its collection lists or
weaken its logic, the dry-run here performs a *read-only* count of documents still
missing ``tenant_key`` across the module's own collection lists — an honest
"work remaining" estimate that writes nothing (M-5).  Irreversible.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.migrations.backfill_tenant_key import (
    CHILD_PROPAGATION,
    SLOT_PROPAGATION,
    TOP_LEVEL_COLLECTIONS,
    backfill_tenant_key,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()


def _scoped_collections() -> list[str]:
    """Every tenant-scoped collection the backfill touches (reused, not duplicated)."""
    return [*TOP_LEVEL_COLLECTIONS, *(child for child, _, _ in CHILD_PROPAGATION), SLOT_PROPAGATION[0]]


class BackfillTenantKeyMigration(Migration):
    version = "0004"
    name = "backfill_tenant_key"
    description = "Assign tenant_key to tenant-scoped documents that predate multi-tenancy."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if dry_run:
            scanned = 0
            for collection_name in _scoped_collections():
                cursor = db.aql.execute(
                    "FOR doc IN @@collection "
                    "FILTER doc.tenant_key == null OR doc.tenant_key == '' "
                    "COLLECT WITH COUNT INTO n RETURN n",
                    bind_vars={"@collection": collection_name},
                )
                scanned += next(iter(cursor), 0)
            logger.info("backfill_tenant_key_dry_run", orphaned_documents=scanned)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details={"orphaned_documents": scanned},
            )

        stats = backfill_tenant_key(db)
        total = stats.get("total_updated", 0)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=total,
            changed=total,
            dry_run=False,
            details=stats,
        )


migration = BackfillTenantKeyMigration()
