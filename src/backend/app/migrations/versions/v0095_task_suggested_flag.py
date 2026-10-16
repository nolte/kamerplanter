"""v0095 — REQ-053 migration M3: ``Task.suggested`` on stored tasks (#2325).

**What (§12.1, §20.9).** M3 is mostly code: ``TaskCategory`` gains the twenty §12.1
bed-care values (``mulching`` … ``pollinating``) additively, and ``Task`` gains
``suggested: bool = False`` and ``suggestion_reason: str | None``. Neither needs a
write for a row to *read* correctly — Pydantic fills the defaults. What does need one
is the AQL side: in AQL ``null == false`` is false, so an equality filter or an index
over ``suggested`` would not see a row that predates the attribute. This version
stamps ``suggested = false`` on every stored task that carries no value for it, so the
whole pre-M3 stock carries the attribute the model declares. ``suggestion_reason`` is
left absent: ``null`` and "missing" mean the same thing for it.

**One-time, by design (M-1 — the v0093 class).** The stamp covers the rows present
when it runs. A row that arrives later without the attribute — the tenant import
accepts archives whose ``source_migration`` is *older* than this version and inserts
their documents raw (``tenant_export_store``), not through ``Task.model_dump`` — is
not covered. A reader that must see every non-suggested task therefore filters
null-safe (``FILTER t.suggested != true``), never ``== false``; the stamp makes the
stock uniform, it is not a guarantee a query may lean on.

**Side effect, measured.** ``tasks`` carries the computed value ``care_dedup_key``
(``computeOn`` insert/update/replace, ``overwrite: true``, v0045 + unique sparse
index). Every ``UPDATE`` here re-derives it. ``CARE_TASK_DEDUP_EXPRESSION`` has not
changed since v0045 introduced it (one commit in ``git log -S``), and v0045 removed
every duplicate among the open care tasks before adding the index, so the
re-derivation yields the key the index already holds — a no-op for the constraint.
The integration test runs the stamp over two open care tasks and reads the
materialised keys back.

**Idempotent (M-3).** A task with ``suggested`` set — either value — is not matched; a
second run reports ``changed == 0`` and, because ``scanned`` counts the candidate rows,
``scanned == 0``.

**Dry run (M-5).** Counts the tasks without the flag; writes nothing.

**Batched.** ``tasks`` is among the largest tenant collections; the keys are scanned
once and stamped in chunks of :data:`_BATCH_SIZE`, so one statement never spans the
whole collection (the v0093 pattern).

**Not reversible (M-6).** An older image ignores the attribute; a ``down`` would only
remove a flag that carries no information beyond the default.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: Documents per ``UPDATE`` statement.
_BATCH_SIZE = 500

# ``== null`` matches both an absent attribute and an explicit ``null``.
_SCAN = """
FOR t IN @@collection
  FILTER t.suggested == null
  RETURN t._key
"""

_APPLY = """
FOR k IN @keys
  UPDATE k WITH { suggested: false } IN @@collection
"""


def _keys_without_flag(db: StandardDatabase) -> list[str]:
    if not db.has_collection(col.TASKS):
        return []
    cursor = cast(Cursor, db.aql.execute(_SCAN, bind_vars={"@collection": col.TASKS}))
    return [str(key) for key in cursor]


def _apply(db: StandardDatabase, keys: list[str]) -> None:
    for start in range(0, len(keys), _BATCH_SIZE):
        chunk = keys[start : start + _BATCH_SIZE]
        db.aql.execute(_APPLY, bind_vars={"@collection": col.TASKS, "keys": chunk})


class TaskSuggestedFlagMigration(Migration):
    version = "0095"
    name = "task_suggested_flag"
    description = "REQ-053 M3: stamp suggested=false on every stored task without the flag (#2325)."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        keys = _keys_without_flag(db)
        details: dict[str, Any] = {"tasks_without_flag": len(keys)}
        if dry_run:
            logger.info("task_suggested_flag_dry_run", pending_changes=len(keys), details=details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=len(keys), changed=0, dry_run=True, details=details
            )
        _apply(db, keys)
        logger.info("task_suggested_flag_applied", changed=len(keys), details=details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=len(keys), changed=len(keys), dry_run=False, details=details
        )


migration = TaskSuggestedFlagMigration()
