"""v0001_baseline — the No-op baseline marking pre-framework databases.

Applying this migration records the ``0001`` marker in ``schema_migrations``
without touching any data.  It exists so that a database predating the framework
has an explicit, inspectable "version 0001" floor and so that ``current`` never
returns ``None`` on a migrated database.  It is the only reversible migration —
its ``down`` is likewise a No-op.
"""

from __future__ import annotations

from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport


class BaselineMigration(Migration):
    version = "0001"
    name = "baseline"
    description = "No-op baseline marking the pre-framework database state."
    reversible = True

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)

    def down(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)


migration = BaselineMigration()
