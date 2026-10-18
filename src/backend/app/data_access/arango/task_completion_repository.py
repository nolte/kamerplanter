"""ArangoDB persistence of the atomic task completion (REQ-053 §12.3, GP-FR-083, GP-FR-149; WP 4.3).

The transaction is :func:`~app.data_access.arango.transactions.stream_transaction`, the care event is written by
:func:`~app.data_access.arango.care_event_repository.write_care_event` (the one writer of the document shape), the
specialist documents are inserted here from the plain documents the engine built. The collections a transaction
writes are declared up front: the task, the care-event set, and the specialist documents with their edges.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError, PlanError, ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import CARE_EVENT_WRITE_COLLECTIONS, write_care_event
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.interfaces.task_completion_repository import ITaskCompletionRepository
from app.domain.models.care_event import CareEvent
from app.domain.models.task_completion import CompletedTask, CompletionWrite, DomainDocument, UndoWrite

logger = structlog.get_logger()

#: Statuses a task may be completed from.
_COMPLETABLE = ("pending", "in_progress")

#: Collections the specialist documents and their edges live in.
_DOMAIN_WRITE: tuple[str, ...] = (
    col.WATERING_EVENTS,
    col.WATERED_PLANT,
    col.FEEDING_EVENTS,
    col.FED_BY,
    col.FEEDING_USED,
    col.HARVEST_BATCHES,
    col.HARVESTED_AS,
)

_COMPLETION_WRITE: tuple[str, ...] = (col.TASKS, *CARE_EVENT_WRITE_COLLECTIONS, *_DOMAIN_WRITE)
_UNDO_WRITE: tuple[str, ...] = (col.TASKS, col.CARE_EVENTS, *_DOMAIN_WRITE)

#: The documents a completion writes, with the edges that hang off them: ``(edge collection, direction)`` where
#: ``out`` means the document is the edge's ``_from``. What the withdrawal of a completion removes with the document.
_WITHDRAWABLE: dict[str, tuple[tuple[str, str], ...]] = {
    col.WATERING_EVENTS: ((col.WATERED_PLANT, "out"),),
    col.FEEDING_EVENTS: ((col.FEEDING_USED, "out"), (col.FED_BY, "in")),
    col.HARVEST_BATCHES: ((col.HARVESTED_AS, "in"),),
}

#: Records that hang off a harvest batch; a batch that has one is no longer the bare result of the completion.
_HARVEST_DEPENDENTS: tuple[tuple[str, str], ...] = (
    (col.QUALITY_ASSESSMENTS, "batch_key"),
    (col.YIELD_METRICS, "batch_key"),
    (col.POST_HARVEST_BATCHES, "harvest_batch_key"),
)
_UNDO_READ: tuple[str, ...] = tuple(collection for collection, _ in _HARVEST_DEPENDENTS)

#: ``void_reason`` of a line a re-completion replaces (the task was reopened without an undo).
REOPENED_REASON = "reopened"

_OWNED_DOCUMENT_ID = (
    'LET d = DOCUMENT(CONCAT(@collection, "/", @key)) FILTER d != null AND d.tenant_key == @tenant_key RETURN d._id'
)
_REMOVE_EDGES_FROM = "FOR e IN @@edge FILTER e._from == @id REMOVE e IN @@edge"
_REMOVE_EDGES_TO = "FOR e IN @@edge FILTER e._to == @id REMOVE e IN @@edge"
_DEPENDENT_BY_BATCH_KEY = "FOR d IN @@collection FILTER d.batch_key == @key LIMIT 1 RETURN 1"
_DEPENDENT_BY_HARVEST_BATCH_KEY = "FOR d IN @@collection FILTER d.harvest_batch_key == @key LIMIT 1 RETURN 1"

_OPEN_EVENT_OF_TASK = """
FOR e IN @@events
    FILTER e._key == @key AND e.task_key == @task_key AND e.tenant_key == @tenant_key
        AND e.voided_at == null AND e.superseded_by_key == null
    RETURN e
"""

_TASK_STATUS = """
FOR t IN @@tasks
    FILTER t._key == @key AND t.tenant_key == @tenant_key
    RETURN t.status
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ArangoTaskCompletionRepository(ITaskCompletionRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _require_tenant(tenant_key: str, method: str) -> None:
        if not tenant_key:
            raise ValueError(f"{method} is tenant-scoped and requires a non-empty tenant_key (#2107).")

    # ── Reads ─────────────────────────────────────────────────────────────

    def plant_location(self, plant_key: str, *, tenant_key: str) -> str | None:
        self._require_tenant(tenant_key, "plant_location")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@plants
                FILTER p._key == @key AND p.tenant_key == @tenant_key
                RETURN p.location_key
            """,
                bind_vars={"@plants": col.PLANT_INSTANCES, "key": plant_key, "tenant_key": tenant_key},
            ),
        )
        location = next(cursor, None)
        return str(location) if location else None

    def plants_in_locations(self, location_keys: list[str], *, tenant_key: str) -> list[str]:
        self._require_tenant(tenant_key, "plants_in_locations")
        if not location_keys:
            return []
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@plants
                FILTER p.tenant_key == @tenant_key AND p.location_key IN @location_keys AND p.removed_on == null
                SORT p._key
                RETURN p._key
            """,
                bind_vars={"@plants": col.PLANT_INSTANCES, "location_keys": location_keys, "tenant_key": tenant_key},
            ),
        )
        return [str(key) for key in cursor]

    def task_event(self, task_key: str, *, tenant_key: str) -> CareEvent | None:
        self._require_tenant(tenant_key, "task_event")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR e IN @@events
                FILTER e.task_key == @task_key AND e.tenant_key == @tenant_key
                    AND e.voided_at == null AND e.superseded_by_key == null
                SORT DATE_TIMESTAMP(e.created_at) DESC
                LIMIT 1
                RETURN e
            """,
                bind_vars={"@events": col.CARE_EVENTS, "task_key": task_key, "tenant_key": tenant_key},
            ),
        )
        doc = next(cursor, None)
        if doc is None:
            return None
        doc["_key"] = doc.get("_key", "")
        return CareEvent.model_validate(doc)

    # ── Transitions ───────────────────────────────────────────────────────

    @staticmethod
    def _stored_status(txn: StreamTransaction, key: str, tenant_key: str) -> str:
        status = next(
            iter(txn.aql.execute(_TASK_STATUS, bind_vars={"@tasks": col.TASKS, "key": key, "tenant_key": tenant_key})),
            None,
        )
        if status is None:
            raise NotFoundError("Task", key)
        return str(status)

    @staticmethod
    def _insert_domain(txn: StreamTransaction, domain: DomainDocument, now: str) -> dict[str, str]:
        stored = txn.collection(domain.collection).insert(domain.document, return_new=True)["new"]
        own_id = f"{domain.collection}/{stored['_key']}"
        for edge, other_id, attributes in domain.edges_out:
            txn.collection(edge).insert({"_from": own_id, "_to": other_id, "created_at": now, **attributes})
        for edge, other_id, attributes in domain.edges_in:
            txn.collection(edge).insert({"_from": other_id, "_to": own_id, "created_at": now, **attributes})
        return {"collection": domain.collection, "key": str(stored["_key"])}

    def complete(self, writes: Sequence[CompletionWrite], *, tenant_key: str) -> list[CompletedTask]:
        self._require_tenant(tenant_key, "complete")
        completed: list[CompletedTask] = []
        with stream_transaction(self._db, write=_COMPLETION_WRITE, read=_UNDO_READ, entity="task_completion") as txn:
            now = _now()
            for write in writes:
                txn.check_budget()
                status = self._stored_status(txn, write.task_key, tenant_key)
                if status not in _COMPLETABLE:
                    raise ValidationError(f"Cannot complete task in status '{status}'.")
                if write.event is not None and write.replaces_event_key:
                    # The task was reopened without an undo and is completed again by the author of the earlier
                    # line (or a lead): that line, and its specialist document, described a completion that no
                    # longer holds; replace it instead of adding to it. A line closed meanwhile is left alone.
                    earlier = self._open_event(txn, write.task_key, write.replaces_event_key, tenant_key)
                    if earlier is not None:
                        self._withdraw(
                            txn,
                            earlier,
                            tenant_key=tenant_key,
                            voided_by=write.event.performed_by_user_key or "",
                            reason=REOPENED_REASON,
                            at=now,
                            strict=True,
                        )
                reference: dict[str, str] | None = None
                if write.domain is not None:
                    reference = self._insert_domain(txn, write.domain, now)
                event_key: str | None = None
                if write.event is not None:
                    if write.event.tenant_key != tenant_key:
                        raise ValueError("complete: the event belongs to another tenant than the one it writes under.")
                    event = write.event.model_copy(update={"source_ref": reference}) if reference else write.event
                    event_key = str(write_care_event(txn, event, now)["_key"])
                txn.collection(col.TASKS).update({"_key": write.task_key, **write.task_patch, "updated_at": now})
                completed.append(CompletedTask(write.task_key, event_key, reference))
        logger.info(
            "task_completion.committed",
            task_count=len(completed),
            event_count=sum(1 for item in completed if item.event_key),
            document_count=sum(1 for item in completed if item.domain_ref),
        )
        return completed

    def reopen(self, write: UndoWrite, *, tenant_key: str) -> None:
        self._require_tenant(tenant_key, "reopen")
        with stream_transaction(self._db, write=_UNDO_WRITE, read=_UNDO_READ, entity="task_completion") as txn:
            status = self._stored_status(txn, write.task_key, tenant_key)
            if status not in write.expected_statuses:
                raise ValidationError(
                    f"Cannot reopen task in status '{status}'. Only completed or skipped tasks can be reopened.",
                )
            if write.event_key:
                current = self._event_in(txn, write, tenant_key)
                self._withdraw(
                    txn,
                    current,
                    tenant_key=tenant_key,
                    voided_by=write.voided_by,
                    reason=write.void_reason,
                    at=write.voided_at.astimezone(UTC).isoformat(),
                    strict=True,
                )
            # ``keep_none=False``: the reset fields (``completed_at`` …) are removed, as the plain reopen does.
            txn.collection(col.TASKS).update(
                {"_key": write.task_key, **write.task_patch, "updated_at": _now()}, keep_none=False
            )
        logger.info("task_completion.reopened", undo=bool(write.event_key))

    @staticmethod
    def _open_event(txn: StreamTransaction, task_key: str, event_key: str, tenant_key: str) -> dict[str, Any] | None:
        """The task's care event ``event_key`` if it is still open (not voided, not superseded), else ``None``."""
        cursor = txn.aql.execute(
            _OPEN_EVENT_OF_TASK,
            bind_vars={"@events": col.CARE_EVENTS, "key": event_key, "task_key": task_key, "tenant_key": tenant_key},
        )
        return next((cast("dict[str, Any]", doc) for doc in cursor), None)

    @staticmethod
    def _event_in(txn: StreamTransaction, write: UndoWrite, tenant_key: str) -> dict[str, Any]:
        current = next(
            iter(
                txn.aql.execute(
                    """
                LET e = DOCUMENT(CONCAT(@events, @key))
                FILTER e != null AND e.tenant_key == @tenant_key AND e.task_key == @task_key
                RETURN e
                """,
                    bind_vars={
                        "events": f"{col.CARE_EVENTS}/",
                        "key": write.event_key,
                        "tenant_key": tenant_key,
                        "task_key": write.task_key,
                    },
                )
            ),
            None,
        )
        if current is None:
            raise NotFoundError("CareEvent", write.event_key or "")
        closed = cast("dict[str, Any]", current)
        if closed.get("superseded_by_key") or closed.get("voided_at"):
            raise PlanError(
                "care_event.sequence",
                "The care event is superseded or voided already; correct the newest entry of its chain.",
                status_code=422,
                field="supersedes_key",
            )
        return closed

    @classmethod
    def _withdraw(
        cls,
        txn: StreamTransaction,
        event: dict[str, Any],
        *,
        tenant_key: str,
        voided_by: str,
        reason: str,
        at: str,
        strict: bool,
    ) -> None:
        """Void the care line and remove the specialist document the completion wrote with it, in this transaction.

        The undo is the inverse of the completion: a watering or feeding row, or a harvest batch, that stayed behind
        would keep counting a deed the author took back. A harvest batch that has collected follow-up records
        (assessment, yield, post-harvest) is no longer the bare result of the completion: ``strict`` refuses the
        withdrawal then (409 ``task.undo_blocked``), where a non-strict caller keeps the batch and only voids the line.
        """
        reference = event.get("source_ref") or {}
        collection, doc_key = reference.get("collection"), reference.get("key")
        withdraw_document = collection in _WITHDRAWABLE and bool(doc_key)
        if withdraw_document and collection == col.HARVEST_BATCHES and cls._has_dependents(txn, str(doc_key)):
            if strict:
                raise PlanError(
                    "task.undo_blocked",
                    "The harvest batch of this completion has follow-up records; remove them before taking it back.",
                    status_code=409,
                    field="task",
                )
            withdraw_document = False
        txn.collection(col.CARE_EVENTS).update(
            {
                "_key": event["_key"],
                "voided_at": at,
                "voided_by": voided_by,
                "void_reason": reason,
            }
        )
        if not withdraw_document:
            return
        document = cast(
            "dict[str, Any] | None",
            next(
                iter(
                    txn.aql.execute(
                        _OWNED_DOCUMENT_ID,
                        bind_vars={"collection": collection, "key": doc_key, "tenant_key": tenant_key},
                    )
                ),
                None,
            ),
        )
        if document is None:
            return
        document_id = f"{collection}/{doc_key}"
        for edge, direction in _WITHDRAWABLE[str(collection)]:
            if direction == "out":
                txn.aql.execute(_REMOVE_EDGES_FROM, bind_vars={"@edge": edge, "id": document_id})
            else:
                txn.aql.execute(_REMOVE_EDGES_TO, bind_vars={"@edge": edge, "id": document_id})
        txn.collection(str(collection)).delete(str(doc_key))

    @staticmethod
    def _has_dependents(txn: StreamTransaction, batch_key: str) -> bool:
        for collection, field in _HARVEST_DEPENDENTS:
            bind = {"@collection": collection, "key": batch_key}
            if field == "batch_key":
                found = next(iter(txn.aql.execute(_DEPENDENT_BY_BATCH_KEY, bind_vars=bind)), None)
            else:
                found = next(iter(txn.aql.execute(_DEPENDENT_BY_HARVEST_BATCH_KEY, bind_vars=bind)), None)
            if found is not None:
                return True
        return False
