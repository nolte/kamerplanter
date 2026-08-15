"""v0043 — give every substrate batch an owner, via the plants that use it (#1195).

``SubstrateBatch`` carried no ``tenant_key``. A batch is a physical thing one
tenant mixed — a volume, a mix date, its own pH/EC history, its reuse cycles —
and without an owner every authenticated caller could read, edit and delete
every tenant's batches through ``/api/v1/substrates/batches/…``.

**Attribution rule (operator decision, 2026-08-15).** A batch inherits the tenant
of the plants that point at it through ``plant_instance.substrate_batch_key``.
That is the only evidence of ownership that exists: nothing else in the data model
records who mixed a batch.

**An ambiguous batch is left unstamped and counted.** Where plants of *several*
tenants point at one batch, there is no owner to derive — only a choice to invent
one. The two alternatives were both worse: picking the majority tenant hands
somebody else's batch to a stranger, and stamping it globally would make it
readable by everyone, which is the state this migration exists to end.

**Consequence, stated rather than discovered.** An unstamped batch
(``tenant_key == ""``) is invisible to every tenant in ``full`` mode, because a
real tenant key is never empty. That is the fail-safe direction — shown to nobody
rather than to everybody — but it does mean such a batch disappears from the UI
until an administrator attributes it. This is why ``details`` reports the count
and the keys: the number is the operator's work list, not decoration. In ``light``
mode the sole operator resolves to ``""`` and still sees them, which is correct
for a single-operator install.

**Orphans are not the same case.** A batch no plant references at all is also left
unstamped, and counted separately: it may be freshly mixed and not yet used, so it
is not evidence of a data problem the way an ambiguous one is.

Idempotent (M-3): only batches whose stored ``tenant_key`` differs from the
derived one are written, so a re-run reports ``changed == 0``.

Not reversible (M-6): the pre-migration state is "no attribute at all", which
cannot be told apart afterwards from a deliberate empty stamp — and removing the
field again would silently disarm every filter that now depends on it.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


class AttributeSubstrateBatchesMigration(Migration):
    version = "0043"
    name = "attribute_substrate_batches"
    description = "Derive each substrate batch's tenant from the plants that reference it (#1195)."
    reversible = False

    #: One statement, so the read and the write cannot disagree about which
    #: batches are in scope. ``COLLECT`` over the referencing plants' tenants
    #: yields the *distinct* set, which is what makes "ambiguous" a fact rather
    #: than an interpretation: more than one entry means more than one owner.
    _PLAN_QUERY = f"""
    FOR batch IN {col.SUBSTRATE_BATCHES}
      LET tenants = UNIQUE(
        FOR p IN {col.PLANT_INSTANCES}
          FILTER p.substrate_batch_key == batch._key
          RETURN p.tenant_key
      )
      RETURN {{
        key: batch._key,
        stored: batch.tenant_key,
        tenants: tenants
      }}
    """

    def _plan(self, db: StandardDatabase) -> tuple[list[dict[str, str]], int, list[str], int]:
        """Return ``(writes, scanned, ambiguous_keys, orphaned)`` without writing.

        Pure, so a dry run reports the numbers the real run would produce. A dry
        run that took a different path would describe a plan nobody executes.
        """
        if not db.has_collection(col.SUBSTRATE_BATCHES) or not db.has_collection(col.PLANT_INSTANCES):
            return [], 0, [], 0

        rows = list(db.aql.execute(self._PLAN_QUERY))
        writes: list[dict[str, str]] = []
        ambiguous: list[str] = []
        orphaned = 0

        for row in rows:
            # A referencing plant that is itself unstamped contributes no evidence
            # of ownership, so it is dropped rather than treated as "the global
            # tenant" — otherwise one un-migrated plant would make every batch it
            # touches look ambiguous.
            owners = sorted({t for t in (row.get("tenants") or []) if t})
            if not owners:
                orphaned += 1
                continue
            if len(owners) > 1:
                ambiguous.append(row["key"])
                continue
            if (row.get("stored") or "") != owners[0]:
                writes.append({"key": row["key"], "tenant_key": owners[0]})

        return writes, len(rows), ambiguous, orphaned

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        writes, scanned, ambiguous, orphaned = self._plan(db)

        if not dry_run and writes:
            batches = db.collection(col.SUBSTRATE_BATCHES)
            for write in writes:
                batches.update({"_key": write["key"], "tenant_key": write["tenant_key"]})

        logger.info(
            "attribute_substrate_batches",
            scanned=scanned,
            attributed=len(writes),
            ambiguous=len(ambiguous),
            orphaned=orphaned,
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(writes),
            dry_run=dry_run,
            details={
                "attributed": len(writes),
                # The keys, not just the count: an operator cannot attribute a
                # batch they cannot name, and these rows are invisible in the UI
                # until somebody does.
                "ambiguous_left_unstamped": ambiguous,
                "orphaned_left_unstamped": orphaned,
            },
        )


#: Module-level instance the discovery loader binds (framework contract).
migration = AttributeSubstrateBatchesMigration()
