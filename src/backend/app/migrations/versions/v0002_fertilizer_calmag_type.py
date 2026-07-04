"""v0002_fertilizer_calmag_type — reclassify legacy CalMag products (DOM-6).

Thin version wrapper: the transformation logic lives in
:mod:`app.migrations.migrate_fertilizer_calmag_type` and is reused verbatim.
Idempotent and dry-run-aware; irreversible (a reclassified type cannot be
restored to its unknown prior value).
"""

from __future__ import annotations

from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.migrate_fertilizer_calmag_type import migrate_fertilizer_calmag_type


class FertilizerCalmagTypeMigration(Migration):
    version = "0002"
    name = "fertilizer_calmag_type"
    description = "Set fertilizer_type='calmag' on name-matched legacy CalMag products."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        result = migrate_fertilizer_calmag_type(db, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=result.scanned,
            changed=result.reclassified,
            dry_run=dry_run,
            details={"changed_keys": result.changed_keys},
        )


migration = FertilizerCalmagTypeMigration()
