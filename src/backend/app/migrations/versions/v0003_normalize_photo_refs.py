"""v0003_normalize_photo_refs — normalise legacy photo_refs to attachment ids.

Thin version wrapper: the transformation logic lives in
:mod:`app.migrations.migrate_photo_refs` and is reused verbatim.  Idempotent and
dry-run-aware; irreversible (the original raw reference is not retained).
"""

from __future__ import annotations

from arango.database import StandardDatabase

from app.migrations import migrate_photo_refs
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport


class NormalizePhotoRefsMigration(Migration):
    version = "0003"
    name = "normalize_photo_refs"
    description = "Rewrite legacy photo_refs entries to NFR-013 attachment ids."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        result = migrate_photo_refs.run(db, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=result.scanned_documents,
            changed=result.changed_documents,
            dry_run=dry_run,
            details=result.as_dict(),
        )


migration = NormalizePhotoRefsMigration()
