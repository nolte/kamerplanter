"""v0080 — clear the foreign reference fields v0067 left behind (#1963).

v0067 (#1878) drops a cross-tenant edge and leaves the source document untouched,
because the document mirrors the same key in a field of its own. After it the edge
and the field disagree. Four classes (the predicate of each lives in
:mod:`app.migrations.support.legacy_foreign_fields`, shared with the operator's
pre-deploy count queries):

* **``equipment.location_key``** naming a location of another tenant is set to
  ``null`` — the field is optional and the edge is already gone.
* **``watering_logs.slot_keys``** naming a slot of another tenant loses those keys.
  A log that would be left with neither a slot nor a plant stays as it is (the model
  refuses such a log on read) and is counted.
* **``location_assignments.location_key``** and **``planting_run_entries.species_key``**
  are required on their model, so nothing can replace the foreign key. They are only
  *counted*; the entry's readers resolve its species under the tenant instead
  (``PlantingRunService``, the irrigation task), so a legacy entry no longer reaches the
  foreign species.

A field is touched only when both tenants are known and differ; a dangling target or an
unstamped row is left and counted.

**Counts only.** The log and the report carry per-class counts; never a key, a name or a
tenant.

**Idempotent (M-3).** A repaired row no longer matches its own predicate, so a second run
changes nothing; the left-alone counts are stable.

**Dry run (M-5).** Computes every class and writes nothing.

**Not reversible (M-6).** The foreign key a field held is not recoverable from the
migrated state; back up ``equipment`` and ``watering_logs`` before running.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

import structlog
from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_foreign_fields import CLASSES, REQUIRED_COLLECTIONS, LegacyFieldClass

logger = structlog.get_logger(__name__)

_BATCH = 500


class NullForeignReferenceFieldsMigration(Migration):
    version = "0080"
    name = "null_foreign_reference_fields"
    description = (
        "Null equipment.location_key and drop watering_logs.slot_keys entries that name another tenant's "
        "row (the fields v0067 left behind after dropping their edges); count the required fields (#1963)."
    )
    reversible = False

    @staticmethod
    def _rows(db: StandardDatabase, cls: LegacyFieldClass) -> list[dict[str, Any]]:
        if not all(db.has_collection(name) for name in REQUIRED_COLLECTIONS[cls.name]):
            return []
        return list(cast("Iterable[dict[str, Any]]", db.aql.execute(cls.rows_query)))

    @staticmethod
    def _apply(db: StandardDatabase, cls: LegacyFieldClass, rows: list[dict[str, Any]]) -> None:
        for start in range(0, len(rows), _BATCH):
            batch = rows[start : start + _BATCH]
            if cls.repair_verdict == "null_field":
                query = "FOR r IN @rows UPDATE {_key: r.key, location_key: null} IN @@c OPTIONS {keepNull: true}"
            else:
                query = "FOR r IN @rows UPDATE {_key: r.key, slot_keys: r.kept} IN @@c"
            db.aql.execute(query, bind_vars={"rows": batch, "@c": cls.target_collection})

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        details: dict[str, int] = {}
        repaired_total = 0
        left_total = 0
        for cls in CLASSES:
            rows = self._rows(db, cls)
            to_repair = [r for r in rows if cls.repair_verdict is not None and r["verdict"] == cls.repair_verdict]
            left = len(rows) - len(to_repair)
            if to_repair and not dry_run:
                self._apply(db, cls, to_repair)
            if cls.repair_verdict is not None:
                details[f"{cls.name}__{cls.repair_verdict}"] = len(to_repair)
            details[f"{cls.name}__left"] = left
            repaired_total += len(to_repair)
            left_total += left
        logger.info("null_foreign_reference_fields", dry_run=dry_run, **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=repaired_total + left_total,
            changed=0 if dry_run else repaired_total,
            dry_run=dry_run,
            details=details,
        )


migration = NullForeignReferenceFieldsMigration()
