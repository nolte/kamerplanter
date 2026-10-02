"""v0067 — clean the references written through the #1871 holes before the fixes (#1878).

Before #1876 several tenant routes stored a caller-supplied reference unchecked.
The fixes stop new rows; this migration repairs the rows the holes already
produced, in seven classes (the predicate of each lives in
:mod:`app.migrations.support.legacy_foreign_references`, shared with the
operator's pre-deploy count queries):

* **Shared workflow templates of a private species** (B10) — a generated plan with
  ``tenant_key == ""`` whose species belongs to one tenant is *re-owned* to that
  tenant. Re-owning rather than deleting keeps the row (nothing is lost), removes it
  from every other tenant's union read, and gives the species owner the plan they
  were always meant to have.
* **Slot field / ``has_slot`` edge disagreement** (B1) — the edge follows the
  ``location_key`` **field** (the field is what the ownership anchor reads and what a
  user set explicitly; the edge was written once at create), but only when the field's
  location and the edge's current location belong to the same tenant. A field that
  points into another tenant's location, a slot with no edge or with several, is
  ambiguous and left.
* **Foreign edges** — ``equipment_at`` (B2), ``assigned_to_location`` (B3),
  ``log_slot`` (B4), ``feeds_from`` (B5) and ``entry_for_species`` (B11) are dropped
  where both endpoint tenants are known and differ. A global-catalogue endpoint
  (``tenant_key == ""`` — a species), a granted species, and any row with an
  endpoint whose tenant cannot be established are left and counted.

**Counts only.** The log and the report carry per-class counts; never a key, a name
or a tenant.

**Idempotent (M-3).** Every repair removes the row from its own predicate (a
re-owned template is no longer shared, a moved edge agrees with the field, a dropped
edge is gone), so a second run finds nothing to change; the left-alone counts are
stable.

**Dry run (M-5).** Computes every class and writes nothing.

**Not reversible (M-6).** A dropped edge and the previous owner of a re-owned
template are not recoverable from the migrated state; back up before running
(``arangodump`` of the seven collections named above is enough).
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_foreign_references import CLASSES, REQUIRED_COLLECTIONS, LegacyClass

logger = structlog.get_logger(__name__)

_BATCH = 500


class CleanLegacyForeignReferencesMigration(Migration):
    version = "0067"
    name = "clean_legacy_foreign_references"
    description = (
        "Re-own shared workflow templates of private species, move has_slot edges to the slot's "
        "location field, and drop cross-tenant equipment/assignment/log-slot/feed/entry-species edges "
        "written before #1871 (#1878)."
    )
    reversible = False

    @staticmethod
    def _rows(db: StandardDatabase, cls: LegacyClass) -> list[dict[str, Any]]:
        if not all(db.has_collection(name) for name in REQUIRED_COLLECTIONS[cls.name]):
            return []
        return list(db.aql.execute(cls.rows_query))

    @staticmethod
    def _apply(db: StandardDatabase, cls: LegacyClass, rows: list[dict[str, Any]]) -> None:
        for start in range(0, len(rows), _BATCH):
            batch = rows[start : start + _BATCH]
            if cls.repair_verdict == "reown":
                db.aql.execute(
                    "FOR r IN @rows UPDATE {_key: r.key, tenant_key: r.owner} IN @@c",
                    bind_vars={"rows": batch, "@c": cls.target_collection},
                )
            elif cls.repair_verdict == "move_edge":
                db.aql.execute(
                    "FOR r IN @rows UPDATE {_key: r.edge_key, _from: CONCAT(@loc, r.location_key)} IN @@c",
                    bind_vars={"rows": batch, "@c": cls.target_collection, "loc": f"{col.LOCATIONS}/"},
                )
            else:
                db.aql.execute(
                    "FOR r IN @rows REMOVE r.key IN @@c",
                    bind_vars={"rows": batch, "@c": cls.target_collection},
                )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        details: dict[str, int] = {}
        repaired_total = 0
        for cls in CLASSES:
            rows = self._rows(db, cls)
            to_repair = [r for r in rows if r["verdict"] == cls.repair_verdict]
            left = len(rows) - len(to_repair)
            if to_repair and not dry_run:
                self._apply(db, cls, to_repair)
            details[f"{cls.name}__{cls.repair_verdict}"] = len(to_repair)
            details[f"{cls.name}__left_unclassified"] = left
            repaired_total += len(to_repair)
        logger.info("clean_legacy_foreign_references", dry_run=dry_run, **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=repaired_total + sum(v for k, v in details.items() if k.endswith("__left_unclassified")),
            changed=0 if dry_run else repaired_total,
            dry_run=dry_run,
            details=details,
        )


migration = CleanLegacyForeignReferencesMigration()
