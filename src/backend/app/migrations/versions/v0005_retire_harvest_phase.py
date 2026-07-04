"""v0005_retire_harvest_phase — reclassify the abolished ``harvest`` phase (#306).

Thin version wrapper: the transformation logic lives in
:mod:`app.migrations.migrate_nutrient_phase_harvest` and is reused verbatim.

This is the migration that satisfies NFR-016 M-9 / AC-6: it MUST run before any
plan seed reads phase entries, because a pre-#306 volume still holds documents
with ``phase_name == "harvest"`` whose strict Pydantic read would otherwise crash
the seed.  The framework guarantees this: migrations run before seeds (O-1), and
this is the last migration in the pending set.  Idempotent, dry-run-aware,
irreversible.
"""

from __future__ import annotations

from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.migrate_nutrient_phase_harvest import migrate_nutrient_phase_harvest


class RetireHarvestPhaseMigration(Migration):
    version = "0005"
    name = "retire_harvest_phase"
    description = "Reclassify retired 'harvest' phase entries to 'ripening'/'flushing' (#306)."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        result = migrate_nutrient_phase_harvest(db, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=result.scanned,
            changed=result.reclassified,
            dry_run=dry_run,
            details={
                "to_ripening": result.to_ripening,
                "to_flushing": result.to_flushing,
                "changed_keys": result.changed_keys,
            },
        )


migration = RetireHarvestPhaseMigration()
