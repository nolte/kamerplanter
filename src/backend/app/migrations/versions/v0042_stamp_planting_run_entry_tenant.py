"""v0042 — stamp every planting-run entry with its parent run's tenant (SEC-004, #1112).

``PlantingRunEntry.cultivar_key`` comes straight from a request body
(``EntryCreate`` / ``EntryUpdate``) and was written unverified: nothing checked
that the referenced cultivar belongs to the caller's tenant. The fix is the
repository's declared owned-reference guard — but that guard compares a reference
against **the row's own** ``tenant_key`` and *skips a row that has none*
(:meth:`BaseArangoRepository._verify_owned_references`).

Entries had no ``tenant_key``. They are tenant-verified through their parent run,
which is the right access model and is why the field was never needed before. It
is needed now, purely so the guard has something to compare against — declaring
the reference without it would have shipped a check that never runs, which the
#1112 issue text calls out by name as the trap to avoid.

**What this migration does.** For every entry, copy ``tenant_key`` from the run it
belongs to. Membership comes from the entry's own ``run_key``, not from the
``has_entry`` edge: the field is what every read already uses
(``get_entries`` is ``find_by_field("run_key", …)``), so a row whose edge and
field disagreed would be stamped consistently with how it is actually read.

**An entry whose run is missing is left alone**, and counted. It is unreachable
(every route resolves entries through a run) and stamping it would mean inventing
an owner. Left unstamped it keeps the pre-migration behaviour — the guard skips
it — which is no worse than today and does not fabricate ownership.

Idempotent (M-3): only entries whose stored ``tenant_key`` differs from their
run's are written, so a re-run reports ``changed == 0``.

Not reversible (M-6): the pre-migration state is "no attribute at all", and
distinguishing that from a legitimately-empty stamp after the fact is not
possible. Removing the field again would silently disarm the guard.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class StampPlantingRunEntryTenantMigration(Migration):
    version = "0042"
    name = "stamp_planting_run_entry_tenant"
    description = "Copy each planting-run entry's tenant_key from its parent run (SEC-004, #1112)."
    reversible = False

    #: One statement, so the read and the write cannot disagree about which
    #: entries are in scope. ``run.tenant_key`` is read through the entry's own
    #: ``run_key`` — the same field every application read uses.
    _PLAN_QUERY = f"""
    FOR entry IN {col.PLANTING_RUN_ENTRIES}
      LET run = FIRST(
        FOR r IN {col.PLANTING_RUNS}
          FILTER r._key == entry.run_key
          LIMIT 1
          RETURN r
      )
      RETURN {{
        key: entry._key,
        stored: entry.tenant_key,
        run_tenant: run ? run.tenant_key : null,
        orphaned: run == null
      }}
    """

    def _plan(self, db: StandardDatabase) -> tuple[list[dict[str, str]], int, int]:
        """Return ``(writes, scanned, orphaned)`` without touching anything.

        Pure, so :meth:`up` computes the same numbers in dry-run mode that it
        would write for real — a dry run that took a different path would report
        on a plan nobody executes.
        """
        if not db.has_collection(col.PLANTING_RUN_ENTRIES) or not db.has_collection(col.PLANTING_RUNS):
            return [], 0, 0

        rows = list(db.aql.execute(self._PLAN_QUERY))
        orphaned = sum(1 for row in rows if row["orphaned"])
        writes = [
            {"key": row["key"], "tenant_key": row["run_tenant"] or ""}
            for row in rows
            if not row["orphaned"] and (row.get("stored") or "") != (row["run_tenant"] or "")
        ]
        return writes, len(rows), orphaned

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        writes, scanned, orphaned = self._plan(db)

        if not dry_run and writes:
            entries = db.collection(col.PLANTING_RUN_ENTRIES)
            for write in writes:
                entries.update({"_key": write["key"], "tenant_key": write["tenant_key"]})

        logger.info(
            "stamp_planting_run_entry_tenant",
            scanned=scanned,
            stamped=len(writes),
            orphaned=orphaned,
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(writes),
            dry_run=dry_run,
            details={"stamped": len(writes), "orphaned_entries_left_unstamped": orphaned},
        )


#: Module-level instance the discovery loader binds (framework contract).
migration = StampPlantingRunEntryTenantMigration()
