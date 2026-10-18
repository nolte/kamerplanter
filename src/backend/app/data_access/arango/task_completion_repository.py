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
_UNDO_WRITE: tuple[str, ...] = (col.TASKS, col.CARE_EVENTS)

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
        with stream_transaction(self._db, write=_COMPLETION_WRITE, entity="task_completion") as txn:
            now = _now()
            for write in writes:
                txn.check_budget()
                status = self._stored_status(txn, write.task_key, tenant_key)
                if status not in _COMPLETABLE:
                    raise ValidationError(f"Cannot complete task in status '{status}'.")
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
        with stream_transaction(self._db, write=_UNDO_WRITE, entity="task_completion") as txn:
            status = self._stored_status(txn, write.task_key, tenant_key)
            if status not in write.expected_statuses:
                raise ValidationError(
                    f"Cannot reopen task in status '{status}'. Only completed or skipped tasks can be reopened.",
                )
            if write.event_key:
                self._void_in(txn, write, tenant_key)
            # ``keep_none=False``: the reset fields (``completed_at`` …) are removed, as the plain reopen does.
            txn.collection(col.TASKS).update(
                {"_key": write.task_key, **write.task_patch, "updated_at": _now()}, keep_none=False
            )
        logger.info("task_completion.reopened", undo=bool(write.event_key))

    @staticmethod
    def _void_in(txn: StreamTransaction, write: UndoWrite, tenant_key: str) -> None:
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
        txn.collection(col.CARE_EVENTS).update(
            {
                "_key": write.event_key,
                "voided_at": write.voided_at.astimezone(UTC).isoformat(),
                "voided_by": write.voided_by,
                "void_reason": write.void_reason,
            }
        )
