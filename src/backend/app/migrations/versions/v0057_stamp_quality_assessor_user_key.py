"""v0057 — mark every pre-#1663 quality assessment as unattributed.

#1663 adds the server-set account key ``quality_assessments.assessed_by_key``
beside the free-text ``assessed_by``, exactly as #1669 did for harvests,
inspections and treatments (v0056). The one create path
(``POST /t/{slug}/harvest/batches/{batch_key}/quality``) writes it from the
resolved caller; the Art. 15 walk (``DataExportEngine.USER_DATA_MANIFEST``) and
the Art. 17 rule (``ErasureEngine.ANONYMIZE_COLLECTIONS``) key on it. NFR-011
R-16 retains quality assessments for five years with the harvest record, so the
rule pseudonymises the key and clears the name rather than deleting the row.

Rows written before that field existed have no such attribute. This migration
writes an explicit ``null`` into it — and **nothing else**. It is v0056's scan
over one more pair, and every property holds for the reasons stated there in
full:

* **Why a ``null`` at all:** after this migration "attribute absent" no longer
  occurs, so a document seen without it was written past the model.
* **No backfill from the free text — by operator decision (2026-09-23):**
  ``assessed_by`` is a typed-in name; a name is not a key, and a key typed into
  the name field is not evidence that that account acted.
* **Idempotent (M-3):** the scan selects ``!HAS(doc, @field)`` only; a row a
  #1663 path wrote between deploy and migration run is never touched.
* **Not reversible (M-6)**, **dry run (M-5)**: as v0056.

``yield_metrics`` — the third R-16 collection — carries no user reference at all
(``domain/models/harvest.py::YieldMetric``), so there is nothing to stamp there.

**Why the scan is written out again rather than inherited from v0056.**
``Migration.checksum()`` hashes the class source, and v0056 is shipped: editing
its class to share the loop would make every installation that applied it log
``migration_checksum_drift`` for good (``test_applied_migration_sources_are_frozen``).
Subclassing it unchanged is no better — its ``_plan`` reads v0056's own module
constant. The loop is short; a copy that cannot drift the shipped one is cheaper
than either.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: ``(collection, attribution key field)`` — the #1663 field. ``assessed_by``, the
#: free-text companion, is deliberately not listed: nothing here reads it.
ATTRIBUTION_KEY_FIELDS: tuple[tuple[str, str], ...] = ((col.QUALITY_ASSESSMENTS, "assessed_by_key"),)


class StampQualityAssessorUserKeyMigration(Migration):
    version = "0057"
    name = "stamp_quality_assessor_user_key"
    description = "Write an explicit null assessed_by_key on quality assessments that predate #1663."
    reversible = False

    #: Only documents that do not carry the attribute at all. A document that
    #: carries it — with a key or with ``null`` — is already in its final shape.
    _SCAN_QUERY = """
    FOR doc IN @@collection
      FILTER !HAS(doc, @field)
      RETURN doc._key
    """

    _TOTAL_QUERY = "RETURN LENGTH(@@collection)"

    def _plan(self, db: StandardDatabase) -> list[tuple[str, str, int, list[str]]]:
        """Return ``(collection, field, scanned, keys to stamp)`` per collection, without writing."""
        plan: list[tuple[str, str, int, list[str]]] = []
        for collection, field in ATTRIBUTION_KEY_FIELDS:
            if not db.has_collection(collection):
                plan.append((collection, field, 0, []))
                continue
            scanned = int(next(iter(db.aql.execute(self._TOTAL_QUERY, bind_vars={"@collection": collection})), 0))
            keys = [
                str(k) for k in db.aql.execute(self._SCAN_QUERY, bind_vars={"@collection": collection, "field": field})
            ]
            plan.append((collection, field, scanned, keys))
        return plan

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        plan = self._plan(db)

        if not dry_run:
            for collection, field, _scanned, keys in plan:
                if not keys:
                    continue
                target = db.collection(collection)
                for key in keys:
                    # ``keep_none=True`` makes the ``null`` land; the default would
                    # drop the attribute and the scan would rediscover the row.
                    target.update({"_key": key, field: None}, keep_none=True, silent=True)

        scanned = sum(item[2] for item in plan)
        stamped = {f"{collection}.{field}": len(keys) for collection, field, _s, keys in plan}
        changed = sum(stamped.values())
        logger.info("stamp_quality_assessor_user_key", scanned=scanned, stamped=stamped, dry_run=dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            # Counts only, as v0056.
            details={"stamped": stamped},
        )


migration = StampQualityAssessorUserKeyMigration()
