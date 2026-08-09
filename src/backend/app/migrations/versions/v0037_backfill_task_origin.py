"""v0037 — backfill origin='user' on tasks predating the FreeStyle field (#1082).

``Task`` grew four orthogonal FreeStyle-provenance fields (REQ-006, #1082):
``origin`` (``user`` | ``system`` | ``pipeline``), ``source``, ``source_run_ref``
and ``external_ref``. ``origin`` is the only one that needs a backfill.

Why ``origin`` needs one and the other three do not
---------------------------------------------------
The machine-generated **filter** on the task list selects on ``doc.origin`` in
AQL (and the badge switches on it in the UI). A row created before the field
existed has **no** ``origin`` attribute, so ``doc.origin == 'user'`` would not
match it and ``doc.origin != 'user'`` would — a legacy hand-authored task would
be mislabelled machine-generated, or fall out of a "user tasks only" filter.
Stamping ``origin = 'user'`` on every attribute-less task makes the additive
default (``TaskOrigin.USER``) explicit in the store, so the filter is correct for
history as well as for new rows. ``source`` defaults to ``""`` and
``source_run_ref`` / ``external_ref`` default to ``null``; none is ever filtered
for equality against a *non-empty* sentinel, so their Pydantic read-time default
is sufficient and writing them would only churn every row.

Idempotency (M-3) — keyed on the attribute being absent
-------------------------------------------------------
Like ``v0035``, this keys idempotency on ``doc.origin == null`` (the attribute is
missing) rather than on a value, because ``'user'`` is a legitimate final value: a
row already backfilled has the attribute present and is skipped on a re-run, which
then finds nothing and writes nothing (``changed == 0``). Dry-run (M-5) computes
the full plan and writes nothing. Irreversible (M-6): the pre-fix absent attribute
is not recoverable once written, so there is no honest inverse.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.common.enums import TaskOrigin
from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()


class BackfillTaskOriginMigration(Migration):
    version = "0037"
    name = "backfill_task_origin"
    description = "Stamp origin='user' on tasks created before the FreeStyle provenance field existed (#1082)."
    reversible = False

    def _origin_less_keys(self, db: StandardDatabase) -> list[str]:
        """Keys of every task whose ``origin`` attribute is absent (read-only).

        The filter is ``== null`` on purpose, not ``== ''``: only rows predating
        the field — where the attribute is missing entirely — are candidates. A
        row already carrying any ``origin`` value is left untouched.
        """
        if not db.has_collection(col.TASKS):
            return []
        rows: list[dict[str, Any]] = list(
            db.aql.execute(
                "FOR doc IN @@collection FILTER doc.origin == null RETURN {key: doc._key}",
                bind_vars={"@collection": col.TASKS},
            )
        )
        return [row["key"] for row in rows]

    @staticmethod
    def _apply(db: StandardDatabase, keys: list[str]) -> None:
        if not keys:
            return
        db.aql.execute(
            "FOR key IN @keys UPDATE {_key: key, origin: @origin} IN @@collection",
            bind_vars={"keys": keys, "origin": TaskOrigin.USER.value, "@collection": col.TASKS},
        )

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        keys = self._origin_less_keys(db)
        if not dry_run:
            self._apply(db, keys)

        changed = len(keys)
        logger.info(
            "backfill_task_origin_dry_run" if dry_run else "backfill_task_origin_applied",
            scanned=changed,
            changed=0 if dry_run else changed,
            to_update=changed,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=changed,
            changed=0 if dry_run else changed,
            dry_run=dry_run,
            details={"to_update": changed} if dry_run else {"tasks": changed},
        )


migration = BackfillTaskOriginMigration()
