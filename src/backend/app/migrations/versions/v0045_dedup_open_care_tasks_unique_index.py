"""v0045 — collapse duplicate OPEN care tasks and enforce the dedup index (#1301).

Bug (duplicate-care-task race): ``CareReminderService.ensure_next_watering_task``
promises "exactly one pending watering task exists for this plant" and enforces it
with a read-then-create — ``find_open_care_task`` then ``create_task``, with no
lock and, until now, no uniqueness constraint on ``tasks``. The guarantee therefore
held **sequentially** and not **concurrently**: the 06:00 UTC Celery beat and a
manual ``POST /t/{slug}/tasks/generate-care-reminders`` are different processes, so
both read "none open" and both insert. The surplus task is not cosmetic —
``advance_watering_task_after_log`` completes one of them and the other stays open
forever as an orphan.

The code fix makes the storage layer reject the losing insert
(``ensure_care_task_dedup_index``): an ArangoDB **computed value**
``care_dedup_key`` that the database derives on every insert/update/replace, plus a
**unique sparse** persistent index over it. The computed value is
``(tenant_key, entity_key, reminder type)`` while the task is ``pending`` /
``in_progress`` and ``null`` otherwise, and ``keepNull: false`` unsets the attribute
on anything else — which a sparse index skips. That is what makes the constraint
"at most one **open** care task per plant and reminder type" rather than the useless
and destructive "care tasks are unique", which would reject the second completed
watering task of a plant's life.

This migration repairs a volume that already accumulated duplicates before the
index existed, and materialises the discriminator on the documents that predate the
computed value. Four ordered jobs, all idempotent:

1. **Collapse duplicate open groups.** Every dedup-key group with more than one
   open care task keeps a single survivor and the losers are set to ``skipped``
   with a note. The survivor is the one ``find_open_care_task`` would have
   returned — newest ``due_date``, then newest ``created_at``, tie-broken on the
   highest ``_key`` for determinism — so the task the application has been acting
   on all along is the one that stays open. Losers are **closed, not deleted**:
   they are real history (a user may have looked at one), and ``skipped`` is the
   honest status for a reminder that was never actioned. ``skipped`` is outside
   ``_CARE_OPEN_STATUSES``, so they stop satisfying the reminder and stop blocking
   the index.

2. **Configure the computed value** on ``tasks`` if it is absent or stale.

3. **Backfill the discriminator.** Configuring a computed value does *not*
   retro-compute it — measured, not assumed: an existing document keeps no
   ``care_dedup_key`` until it is written again. Without this step the index would
   be created over an empty key space and be **inert for exactly the pre-existing
   data**, i.e. a new insert would not collide with an open task that predates the
   migration. A no-op ``UPDATE d WITH {}`` over the open care tasks that still lack
   the attribute is what materialises it.

4. **Create the unique sparse index** if absent. Safe now — step 1 removed the
   collisions and step 3 made the remaining open tasks visible to it. It is
   deliberately *not* wrapped in a fallback: if it still fails, a duplicate the
   scan did not model exists and the migration must say so loudly rather than
   leave a volume that silently keeps minting duplicates.

Idempotent (M-3): a re-run finds no duplicate groups, the computed value already
configured, nothing left to backfill and the index present → ``changed == 0``.
Dry-run (M-5): all four jobs are previewed and nothing is written. Irreversible
(M-6): step 1 rewrites the losers' status (their prior state is not retained) and
there is no honest inverse for "un-close these".
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.common.enums import TaskCategory, TaskStatus
from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Status the surplus tasks of a duplicate group are closed into. Outside
#: ``ArangoTaskRepository._CARE_OPEN_STATUSES``, so a closed loser neither
#: satisfies the reminder nor occupies the index slot. Not ``completed``: nobody
#: performed the care, and ``completed`` would additionally suppress the next
#: reminder for the rest of the UTC day through the #509 recency rule.
_LOSER_STATUS = TaskStatus.SKIPPED.value

#: Note stamped on a closed loser, so an operator (or a puzzled user) can tell
#: this apart from a reminder they skipped themselves.
_LOSER_NOTE = "Closed by migration v0045: duplicate open care reminder for the same plant and reminder type (#1301)."

#: Groups the open care tasks by the same dedup identity the computed value
#: derives, expressed inline because step 1 must also run on a volume where the
#: computed value does not exist yet. Kept in one place with the index expression
#: by ``tests/integration/test_v0045_care_task_dedup_migration.py``, which asserts
#: the two agree on real documents rather than on a string comparison.
_DUPLICATE_GROUPS_AQL = """
FOR doc IN @@collection
    FILTER doc.category == @care_category
    FILTER doc.status IN @open_statuses
    FILTER doc.entity_key != null AND doc.entity_key != ''
    FILTER doc.name != null
    LET dedup = CONCAT_SEPARATOR('/', doc.tenant_key, doc.entity_key, LAST(SPLIT(doc.name, @separator)))
    COLLECT dedup_key = dedup INTO grp = doc
    FILTER LENGTH(grp) > 1
    RETURN {dedup_key: dedup_key, docs: grp}
"""

#: Open care tasks that carry no ``care_dedup_key`` yet — the documents written
#: before the computed value was configured. ``RETURN doc._key`` so the report can
#: count them and a dry run can preview without writing.
_UNSTAMPED_KEYS_AQL = f"""
FOR doc IN @@collection
    FILTER doc.category == @care_category
    FILTER doc.status IN @open_statuses
    FILTER doc.entity_key != null AND doc.entity_key != ''
    FILTER doc.name != null
    FILTER doc.{col.CARE_TASK_DEDUP_FIELD} == null
    RETURN doc._key
"""


def _sort_rank(doc: dict[str, Any]) -> tuple[str, str, str]:
    """Recency rank of a care task, descending — highest wins the group.

    Mirrors ``find_open_care_task``'s ``SORT doc.due_date DESC, doc.created_at
    DESC LIMIT 1``: both timestamps are stored as ISO strings, so lexicographic
    order *is* chronological order and a missing one compares as ``""`` (oldest).
    ``_key`` is appended purely as a deterministic tie-break, so a re-run over an
    unchanged volume picks the same survivor.
    """
    return (
        str(doc.get("due_date") or ""),
        str(doc.get("created_at") or ""),
        str(doc.get("_key") or ""),
    )


def _pick_survivor(docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the task of a duplicate group that stays open."""
    return max(docs, key=_sort_rank)


class DedupOpenCareTasksUniqueIndexMigration(Migration):
    version = "0045"
    name = "dedup_open_care_tasks_unique_index"
    description = (
        "Close surplus duplicate OPEN care-reminder tasks per (tenant, plant, reminder type), "
        "configure and backfill the care_dedup_key computed value, and create the unique sparse "
        "index so the read-then-create race can no longer mint duplicate care tasks."
    )
    reversible = False

    # ── read helpers (no-op-safe on an empty/fresh database) ──────────────────

    def _open_care_bind_vars(self) -> dict[str, Any]:
        """Bind vars selecting the open care tasks, shared by both read queries."""
        return {
            "@collection": col.TASKS,
            "care_category": TaskCategory.CARE_REMINDER.value,
            "open_statuses": col.CARE_TASK_OPEN_STATUSES,
        }

    def _loser_keys(self, db: StandardDatabase) -> list[str]:
        """Keys of every non-survivor in a duplicate open-care-task group (read-only).

        M-5-safe: pure read, returns ``[]`` when ``tasks`` is absent or holds no
        duplicates.
        """
        if not db.has_collection(col.TASKS):
            return []
        losers: list[str] = []
        bind_vars = {**self._open_care_bind_vars(), "separator": col.CARE_TASK_NAME_SEPARATOR}
        for group in db.aql.execute(_DUPLICATE_GROUPS_AQL, bind_vars=bind_vars):
            docs = list(group["docs"])
            survivor_key = str(_pick_survivor(docs).get("_key", ""))
            losers.extend(str(doc.get("_key", "")) for doc in docs if str(doc.get("_key", "")) != survivor_key)
        return losers

    def _unstamped_keys(self, db: StandardDatabase) -> list[str]:
        """Keys of the open care tasks still missing the computed discriminator."""
        if not db.has_collection(col.TASKS):
            return []
        return [str(key) for key in db.aql.execute(_UNSTAMPED_KEYS_AQL, bind_vars=self._open_care_bind_vars())]

    def _has_dedup_index(self, handle: Any) -> bool:
        return any(
            isinstance(idx, dict)
            and idx.get("type") == "persistent"
            and idx.get("fields") == col.CARE_TASK_DEDUP_INDEX_FIELDS
            and idx.get("unique")
            and idx.get("sparse")
            for idx in handle.indexes()
        )

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.TASKS):
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=0,
                changed=0,
                dry_run=dry_run,
                details={"tasks_collection_absent": True},
            )

        handle = db.collection(col.TASKS)
        loser_keys = self._loser_keys(db)
        has_computed_value = col.has_care_task_dedup_computed_value(handle)
        has_index = self._has_dedup_index(handle)
        scanned = len(loser_keys)

        if dry_run:
            # The backfill count can only be *previewed* meaningfully once the
            # computed value exists; on a volume that has not been configured yet
            # every open care task will need one, which is what this counts.
            unstamped = self._unstamped_keys(db)
            details: dict[str, Any] = {
                "duplicate_losers": len(loser_keys),
                "will_configure_computed_value": not has_computed_value,
                "will_backfill_dedup_key": len(unstamped),
                "index_already_present": has_index,
                "will_create_unique_index": not has_index,
            }
            logger.info("dedup_open_care_tasks_unique_index_dry_run", scanned=scanned, details=details)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details=details,
            )

        # 1. Close the losing duplicates in a single batched UPDATE.
        if loser_keys:
            db.aql.execute(
                "FOR key IN @keys "
                "UPDATE {_key: key, status: @status, completion_notes: @note, updated_at: DATE_ISO8601(DATE_NOW())} "
                "IN @@collection",
                bind_vars={
                    "keys": loser_keys,
                    "status": _LOSER_STATUS,
                    "note": _LOSER_NOTE,
                    "@collection": col.TASKS,
                },
            )

        # 2. Configure the computed value, so ArangoDB maintains the discriminator
        #    from here on (every insert, update and replace — including the
        #    backfill below).
        computed_value_changes = 0
        if not has_computed_value:
            col.configure_care_task_dedup_computed_value(handle)
            computed_value_changes = 1

        # 3. Materialise it on the documents that predate it. Configuring a
        #    computed value does not rewrite stored documents, so without this the
        #    index below would not see a single pre-existing open care task.
        unstamped_keys = self._unstamped_keys(db)
        if unstamped_keys:
            db.aql.execute(
                "FOR key IN @keys UPDATE {_key: key} WITH {} IN @@collection",
                bind_vars={"keys": unstamped_keys, "@collection": col.TASKS},
            )

        # 4. Create the constraint. No fallback: a failure here means a duplicate
        #    the scan above did not model, and a silent downgrade to "no index"
        #    would leave the volume minting duplicates while reporting success.
        index_changes = 0
        if not has_index:
            handle.add_persistent_index(
                fields=col.CARE_TASK_DEDUP_INDEX_FIELDS,
                unique=True,
                sparse=True,
                name=col.CARE_TASK_DEDUP_INDEX_NAME,
            )
            index_changes = 1

        changed = len(loser_keys) + computed_value_changes + len(unstamped_keys) + index_changes
        details = {
            "closed_duplicate_losers": len(loser_keys),
            "loser_status": _LOSER_STATUS,
            "computed_value_configured": bool(computed_value_changes),
            "backfilled_dedup_keys": len(unstamped_keys),
            "unique_index_created": bool(index_changes),
        }
        logger.info("dedup_open_care_tasks_unique_index_applied", scanned=scanned, changed=changed, details=details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details=details,
        )


migration = DedupOpenCareTasksUniqueIndexMigration()
