"""v0056 — mark every pre-#1669 harvest, inspection and treatment row as unattributed.

#1669 introduced a server-set account key on the three legally-retained records:
``harvest_batches.harvested_by_key``, ``inspections.inspected_by_key`` and
``treatment_applications.applied_by_key``. Every create path writes it from the
resolved caller. The Art. 15 walk (``DataExportEngine.USER_DATA_MANIFEST``) and the
Art. 17 rules (``ErasureEngine.ANONYMIZE_COLLECTIONS``) key on it.

Rows written before that field existed have no such attribute. This migration writes
an explicit ``null`` into it — and **nothing else**.

**Why write a ``null`` at all.** A row that lacks the attribute and a row that carries
``null`` read the same through the Pydantic model, so the application does not need
this. The stored document does: after this migration, "attribute absent" no longer
occurs, so a document seen later *without* it can only have been written by a path
that bypassed the model — which is exactly the writer class #1669's fixture guard
exists to find. The ``null`` is a measured statement ("this row predates
attribution") rather than an accident of age.

**No backfill from the free text — by decision, not by omission.** ``harvester``,
``inspector`` and ``applied_by`` are typed-in display names (``"Maren"``,
``"E2E-Tester"``, ``"mcp:<account>"``). A name is not a key, a key typed into the
name field is not evidence that that account acted, and ``mcp:<key>`` records the
integration's *service account*, which the operator explicitly does not want mapped
to a person after the fact. Guessing here would attribute retained CanG / PflSchG
records to the wrong data subject and then disclose or pseudonymise them for that
subject — the opposite of what REQ-025 owes. The integration test seeds a legacy row
whose free text is *literally an existing user key* and pins that it still gets
``null``.

**Idempotent (M-3).** The scan selects only documents that still lack the attribute
(``!HAS(doc, @field)``); a second run finds none. A row that already carries a key —
written by a #1669 path in the window between the deploy and the migration run — is
never touched, because it has the attribute.

**Not reversible (M-6).** Removing the attribute again would erase the distinction
between "pre-attribution" and "written past the model" that the ``null`` records.

**Dry run (M-5).** The scan is the plan; ``dry_run`` reports its numbers and writes
nothing.

**On the version number.** ``versions/`` held ``v0001`` … ``v0054`` on ``develop``
when this was written and no open pull request carried a ``v0055``; the module was
first written as ``0055``. The parallel strand for #1620
(``v0055_rename_account_type_user_to_human``) keeps that number by operator decision
on 2026-09-23, and this branch is stacked on #1662 and lands after it — so it takes
``0056`` **now**, not at rebase time, so there is no moment in which two modules
carry the same number. ``discovery.validate_sequence`` demands gapless numbering on
the startup path, which is why a number cannot be reserved and why this module
cannot land before ``0055`` does; should the order flip after all, the rename goes
the way ``app/migrations/README.md`` prescribes (file, ``version`` string, both test
modules and their ``_DB_NAME``).
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: ``(collection, attribution key field)`` — the three #1669 fields. The free-text
#: companions (``harvester``, ``inspector``, ``applied_by``) are deliberately not
#: listed: nothing here reads them.
ATTRIBUTION_KEY_FIELDS: tuple[tuple[str, str], ...] = (
    (col.HARVEST_BATCHES, "harvested_by_key"),
    (col.INSPECTIONS, "inspected_by_key"),
    (col.TREATMENT_APPLICATIONS, "applied_by_key"),
)


class StampAttributionUserKeysMigration(Migration):
    version = "0056"
    name = "stamp_attribution_user_keys"
    description = "Write an explicit null attribution key on harvest/inspection/treatment rows that predate #1669."
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
                    # ``keep_none=True`` is what makes the ``null`` land: the default of
                    # python-arango's ``update`` would drop the attribute again and
                    # the scan above would rediscover the row on every run.
                    target.update({"_key": key, field: None}, keep_none=True, silent=True)

        scanned = sum(item[2] for item in plan)
        stamped = {f"{collection}.{field}": len(keys) for collection, field, _s, keys in plan}
        changed = sum(stamped.values())
        logger.info(
            "stamp_attribution_user_keys",
            scanned=scanned,
            stamped=stamped,
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            # Counts only. The keys of harvest, inspection and treatment rows are
            # not personal data, but a report is logged and stored and there is
            # nothing a reader would do with the list.
            details={"stamped": stamped},
        )


migration = StampAttributionUserKeysMigration()
