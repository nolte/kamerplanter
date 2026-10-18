"""ArangoDB persistence of the care log (REQ-053 §13, §20.10; WP 4.1, #2400).

``care_events`` is append-only (GP-FR-101): this repository inserts, sets the three supersede / void columns of an
existing document, writes the redaction (GP-FR-109) and — for the retention sweep (NFR-011 R-25) — anonymises
documents past their period. It never deletes; the erasure cascade (REQ-025) is the only physical delete.

**One writer of the document shape.** :func:`write_care_event` writes the document and its edges
(``care_event_at`` to the bed, ``care_event_for`` to each plant, ``task_logged_as`` from the task) inside a
transaction the *caller* opened. The plan batch (``change_bed_status``), the task completion (WP 4.3), clearing
(WP 3.2) and the backfill (WP 3.4) compose their own transactions around it instead of re-spelling the document.

Every read takes ``tenant_key`` keyword-only without a default and filters the document on it: an event of another
tenant answers exactly like an absent one.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.aql import AQL
from arango.cursor import Cursor
from arango.database import StandardDatabase
from pydantic import BaseModel

from app.common.exceptions import NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.transactions import StreamTransaction, TransactionAql, stream_transaction
from app.domain.interfaces.care_event_repository import (
    AnonymizedBatch,
    CareEventFilter,
    CareEventRow,
    ICareEventRepository,
    PendingPhotos,
)
from app.domain.models.care_event import (
    ACCOUNT_FIELDS,
    ANONYMIZED_MARKER,
    FREE_TEXT_FIELDS,
    REDACTED,
    UNDO_REASON,
    CareEvent,
)
from app.domain.models.garden_plan import PlanAuditRecord

logger = structlog.get_logger()

#: Collections a care-event write touches; a transaction that calls :func:`write_care_event` declares all of them.
CARE_EVENT_WRITE_COLLECTIONS: tuple[str, ...] = (
    col.CARE_EVENTS,
    col.CARE_EVENT_AT,
    col.CARE_EVENT_FOR,
    col.TASK_LOGGED_AS,
)

#: A supersede chain longer than this is not a chain a person made; the walk stops (and the redaction with it).
_MAX_CHAIN = 100

_EVENT_BY_KEY = """
LET e = DOCUMENT(CONCAT(@events, @key))
FILTER e != null AND e.tenant_key == @tenant_key
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def write_care_event(txn: StreamTransaction, event: CareEvent, now: str, *, link_task: bool = True) -> dict[str, Any]:
    """Insert ``event`` and its edges inside the caller's transaction; returns the stored document.

    The caller declares :data:`CARE_EVENT_WRITE_COLLECTIONS` for writing. ``created_at`` is stamped here, the
    ``_key`` is the database's. A ``None`` field is not stored (an absent attribute reads as ``null`` in AQL).
    ``link_task=False`` leaves the ``task_logged_as`` edge out: a correction carries its predecessor's ``task_key``
    for display, but the task is logged *as* the first entry (one edge per completion, WP 4.3).
    """
    doc = _dump(event, by_alias=True, exclude_none=True, mode="json")
    doc.pop("_key", None)
    doc["created_at"] = now
    stored = txn.collection(col.CARE_EVENTS).insert(doc, return_new=True)["new"]
    event_id = f"{col.CARE_EVENTS}/{stored['_key']}"
    txn.collection(col.CARE_EVENT_AT).insert(
        {"_from": event_id, "_to": f"{col.LOCATIONS}/{event.location_key}", "created_at": now}
    )
    for plant_key in event.plant_keys:
        txn.collection(col.CARE_EVENT_FOR).insert(
            {"_from": event_id, "_to": f"{col.PLANT_INSTANCES}/{plant_key}", "created_at": now}
        )
    if event.task_key and link_task:
        txn.collection(col.TASK_LOGGED_AS).insert(
            {"_from": f"{col.TASKS}/{event.task_key}", "_to": event_id, "created_at": now}
        )
    return cast("dict[str, Any]", stored)


def retention_patch(doc: dict[str, Any], now: str) -> dict[str, Any]:
    """The update that anonymises one expired event (NFR-011 R-25, GP-NFR-055); a pure function of the document.

    The five account references become the erasure marker, the five free-text fields ``[redacted]``. The photo
    references go once the objects are deleted (:meth:`ArangoCareEventRepository.clear_photo_refs`), so a failed
    storage call leaves them for the next run. ``category``, ``performed_at``, ``quantity``, ``location_key`` and
    ``plant_keys`` stay (the crop-rotation look-back, Art. 17 para. 3). Only attributes the document has are
    touched: an absent one stays absent.
    """
    patch: dict[str, Any] = {"_key": doc["_key"], "retention_anonymized_at": now}
    for name in ACCOUNT_FIELDS:
        if doc.get(name) is not None:
            patch[name] = ANONYMIZED_MARKER
    for name in FREE_TEXT_FIELDS:
        if doc.get(name) is not None or name == "summary":
            patch[name] = REDACTED
    # The reasons a person typed for a cancellation or a redaction are free text as well; ``undo`` is the fixed
    # word of the field-mode snackbar, not text.
    if doc.get("void_reason") not in (None, UNDO_REASON):
        patch["void_reason"] = REDACTED
    if doc.get("redaction_reason") is not None:
        patch["redaction_reason"] = REDACTED
    return patch


class ArangoCareEventRepository(BaseArangoRepository[CareEvent], ICareEventRepository):
    """``care_events`` (migration v0093) with its ``care_event_at`` / ``care_event_for`` / ``task_logged_as`` edges."""

    _model_cls = CareEvent
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.CARE_EVENTS)

    # ── Reads ─────────────────────────────────────────────────────────────

    def _wrapped(self, doc: dict[str, Any]) -> CareEvent:
        return CareEvent.model_validate(self._from_doc(doc))

    def get(self, key: str, *, tenant_key: str) -> CareEvent | None:
        self._require_tenant_key(tenant_key, "get")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"{_EVENT_BY_KEY} RETURN e",
                bind_vars={"events": f"{col.CARE_EVENTS}/", "key": key, "tenant_key": tenant_key},
            ),
        )
        doc = next(cursor, None)
        return self._wrapped(doc) if doc is not None else None

    def get_row(self, key: str, *, tenant_key: str) -> CareEventRow | None:
        self._require_tenant_key(tenant_key, "get_row")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            {_EVENT_BY_KEY}
            LET by = e.performed_by_user_key == null ? null : DOCUMENT(CONCAT(@users, e.performed_by_user_key))
            LET for_user = e.performed_for_user_key == null ? null : DOCUMENT(CONCAT(@users, e.performed_for_user_key))
            RETURN {{event: e, performed_by_name: by.display_name, performed_for_name: for_user.display_name}}
            """,
                bind_vars={
                    "events": f"{col.CARE_EVENTS}/",
                    "users": f"{col.USERS}/",
                    "key": key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        row = next(cursor, None)
        return self._row(row) if row is not None else None

    def _row(self, row: dict[str, Any]) -> CareEventRow:
        return CareEventRow(
            event=self._wrapped(row["event"]),
            performed_by_name=row.get("performed_by_name"),
            performed_for_name=row.get("performed_for_name"),
        )

    def chain(self, key: str, *, tenant_key: str) -> list[CareEvent]:
        self._require_tenant_key(tenant_key, "chain")
        return [self._wrapped(doc) for doc in self._chain_docs(self._db.aql, key, tenant_key)]

    @staticmethod
    def _chain_docs(aql: AQL | TransactionAql, key: str, tenant_key: str) -> list[dict[str, Any]]:
        """``key``'s chain, oldest first: back along ``supersedes_key``, forward along ``superseded_by_key``."""

        def load(doc_key: str | None) -> dict[str, Any] | None:
            if not doc_key:
                return None
            cursor = cast(
                "Cursor",
                aql.execute(
                    f"{_EVENT_BY_KEY} RETURN e",
                    bind_vars={"events": f"{col.CARE_EVENTS}/", "key": doc_key, "tenant_key": tenant_key},
                ),
            )
            return cast("dict[str, Any] | None", next(cursor, None))

        head = load(key)
        if head is None:
            return []
        older: list[dict[str, Any]] = []
        cursor_doc = head
        while len(older) < _MAX_CHAIN and (previous := load(cursor_doc.get("supersedes_key"))) is not None:
            older.append(previous)
            cursor_doc = previous
        newer: list[dict[str, Any]] = []
        cursor_doc = head
        while len(newer) < _MAX_CHAIN and (following := load(cursor_doc.get("superseded_by_key"))) is not None:
            newer.append(following)
            cursor_doc = following
        return [*reversed(older), head, *newer]

    def list_events(self, criteria: CareEventFilter, *, tenant_key: str, offset: int, limit: int) -> list[CareEventRow]:
        self._require_tenant_key(tenant_key, "list_window")
        filters = ["e.tenant_key == @tenant_key"]
        binds: dict[str, Any] = {
            "@events": col.CARE_EVENTS,
            "users": f"{col.USERS}/",
            "tenant_key": tenant_key,
            "offset": offset,
            "limit": limit,
        }
        if criteria.location_key:
            filters.append("e.location_key == @location_key")
            binds["location_key"] = criteria.location_key
        if criteria.plant_key:
            filters.append("@plant_key IN e.plant_keys")
            binds["plant_key"] = criteria.plant_key
        if criteria.category:
            filters.append("e.category == @category")
            binds["category"] = criteria.category
        if criteria.performed_by:
            filters.append("e.performed_by_user_key == @performed_by")
            binds["performed_by"] = criteria.performed_by
        if not criteria.include_superseded:
            filters.append("e.superseded_by_key == null")
        if criteria.performed_from is not None:
            filters.append("DATE_TIMESTAMP(e.performed_at) >= DATE_TIMESTAMP(@performed_from)")
            binds["performed_from"] = criteria.performed_from.astimezone(UTC).isoformat()
        if criteria.performed_to is not None:
            filters.append("DATE_TIMESTAMP(e.performed_at) <= DATE_TIMESTAMP(@performed_to)")
            binds["performed_to"] = criteria.performed_to.astimezone(UTC).isoformat()
        where = "\n                ".join(f"FILTER {clause}" for clause in filters)
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR e IN @@events
                {where}
                SORT DATE_TIMESTAMP(e.performed_at) DESC, e._key DESC
                LIMIT @offset, @limit
                LET by = e.performed_by_user_key == null ? null : DOCUMENT(CONCAT(@users, e.performed_by_user_key))
                LET for_user = e.performed_for_user_key == null
                    ? null : DOCUMENT(CONCAT(@users, e.performed_for_user_key))
                RETURN {{event: e, performed_by_name: by.display_name, performed_for_name: for_user.display_name}}
            """,
                bind_vars=binds,
            ),
        )
        return [self._row(row) for row in cursor]

    def plants_in_locations(self, plant_keys: list[str], location_keys: list[str], *, tenant_key: str) -> set[str]:
        self._require_tenant_key(tenant_key, "plants_in_locations")
        if not plant_keys or not location_keys:
            return set()
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR p IN @@plants
                FILTER p._key IN @plant_keys AND p.tenant_key == @tenant_key AND p.location_key IN @location_keys
                RETURN p._key
            """,
                bind_vars={
                    "@plants": col.PLANT_INSTANCES,
                    "plant_keys": plant_keys,
                    "location_keys": location_keys,
                    "tenant_key": tenant_key,
                },
            ),
        )
        return {str(key) for key in cursor}

    # ── Writes ────────────────────────────────────────────────────────────

    def insert(self, event: CareEvent, *, tenant_key: str) -> CareEvent:
        self._require_tenant_key(tenant_key, "insert")
        if event.tenant_key != tenant_key:
            raise ValueError("insert: the event belongs to another tenant than the one it is written under.")
        with stream_transaction(self._db, write=CARE_EVENT_WRITE_COLLECTIONS, entity="care_event") as txn:
            stored = write_care_event(txn, event, _now())
        return self._wrapped(stored)

    def _load_in(self, txn: StreamTransaction, key: str, tenant_key: str) -> dict[str, Any]:
        doc = next(
            iter(
                txn.aql.execute(
                    f"{_EVENT_BY_KEY} RETURN e",
                    bind_vars={"events": f"{col.CARE_EVENTS}/", "key": key, "tenant_key": tenant_key},
                )
            ),
            None,
        )
        if doc is None:
            raise NotFoundError("CareEvent", key)
        return cast("dict[str, Any]", doc)

    @staticmethod
    def _refuse_if_closed(doc: dict[str, Any]) -> None:
        """V-13: no branching and no continuing a cancelled line — the head of a chain is the only open end."""
        if doc.get("superseded_by_key") or doc.get("voided_at"):
            raise PlanError(
                "care_event.sequence",
                "The care event is superseded or voided already; correct the newest entry of its chain.",
                status_code=422,
                field="supersedes_key",
            )

    def supersede(self, predecessor_key: str, event: CareEvent, *, tenant_key: str) -> CareEvent:
        self._require_tenant_key(tenant_key, "supersede")
        if event.tenant_key != tenant_key:
            raise ValueError("supersede: the event belongs to another tenant than the one it is written under.")
        with stream_transaction(self._db, write=CARE_EVENT_WRITE_COLLECTIONS, entity="care_event") as txn:
            predecessor = self._load_in(txn, predecessor_key, tenant_key)
            self._refuse_if_closed(predecessor)
            if predecessor.get("location_key") != event.location_key or event.supersedes_key != predecessor_key:
                raise PlanError(
                    "care_event.sequence",
                    "A correction stays on the bed of its predecessor and names it.",
                    status_code=422,
                    field="supersedes_key",
                )
            stored = write_care_event(txn, event, _now(), link_task=False)
            txn.collection(col.CARE_EVENTS).update({"_key": predecessor_key, "superseded_by_key": stored["_key"]})
        return self._wrapped(stored)

    def void(self, key: str, *, tenant_key: str, voided_by: str, reason: str, at: datetime) -> CareEvent:
        self._require_tenant_key(tenant_key, "void")
        with stream_transaction(self._db, write=(col.CARE_EVENTS,), entity="care_event") as txn:
            current = self._load_in(txn, key, tenant_key)
            self._refuse_if_closed(current)
            updated = txn.collection(col.CARE_EVENTS).update(
                {
                    "_key": key,
                    "voided_at": at.astimezone(UTC).isoformat(),
                    "voided_by": voided_by,
                    "void_reason": reason,
                },
                return_new=True,
            )["new"]
        return self._wrapped(updated)

    def redact(
        self, key: str, *, tenant_key: str, redacted_by: str, reason: str, at: datetime
    ) -> tuple[list[CareEvent], list[str]]:
        self._require_tenant_key(tenant_key, "redact")
        stamp = at.astimezone(UTC).isoformat()
        with stream_transaction(
            self._db,
            write=(col.CARE_EVENTS, col.GARDEN_PLAN_AUDIT),
            read=(col.SITES,),
            entity="care_event",
        ) as txn:
            docs = self._chain_docs(txn.aql, key, tenant_key)
            if not docs:
                raise NotFoundError("CareEvent", key)
            detached: list[str] = []
            redacted: list[CareEvent] = []
            events = txn.collection(col.CARE_EVENTS)
            for doc in docs:
                detached.extend(str(ref) for ref in doc.get("photo_refs") or [])
                patch: dict[str, Any] = {
                    "_key": doc["_key"],
                    "photo_refs": [],
                    "redacted_at": stamp,
                    "redacted_by": redacted_by,
                    "redaction_reason": reason,
                }
                for name in FREE_TEXT_FIELDS:
                    if doc.get(name) is not None or name == "summary":
                        patch[name] = REDACTED
                if doc.get("void_reason") not in (None, UNDO_REASON):
                    patch["void_reason"] = REDACTED
                redacted.append(self._wrapped(events.update(patch, return_new=True)["new"]))
            head = next(doc for doc in docs if doc["_key"] == key)
            revision = next(
                iter(
                    txn.aql.execute(
                        "RETURN DOCUMENT(CONCAT(@sites, @site_key)).plan.plan_revision || 0",
                        bind_vars={"sites": f"{col.SITES}/", "site_key": head["site_key"]},
                    )
                ),
                0,
            )
            audit = PlanAuditRecord(
                tenant_key=tenant_key,
                site_key=head["site_key"],
                revision=int(revision),
                user_key=redacted_by,
                op="redact",
                entity="care_event",
                key=key,
                # The category, never the text: the audit outlives the redaction it records.
                summary=str(head.get("category", ""))[:200],
                at=at,
            )
            txn.collection(col.GARDEN_PLAN_AUDIT).insert(_dump(audit, mode="json"))
        return redacted, list(dict.fromkeys(detached))

    # ── Retention (NFR-011 R-25) ──────────────────────────────────────────

    def anonymize_expired(
        self, *, cutoff: datetime, pflschg_cutoff: datetime, now: datetime, batch: int
    ) -> AnonymizedBatch:
        bind_vars: dict[str, Any] = {
            "@events": col.CARE_EVENTS,
            "pflschg": ["pest_control", "ipm"],
            "cutoff": cutoff.astimezone(UTC).isoformat(),
            "pflschg_cutoff": pflschg_cutoff.astimezone(UTC).isoformat(),
            "batch": batch,
        }
        docs = list(
            cast(
                "Cursor",
                self._db.aql.execute(
                    """
            FOR e IN @@events
                FILTER e.retention_anonymized_at == null OR LENGTH(e.photo_refs || []) > 0
                LET performed = DATE_TIMESTAMP(e.performed_at)
                FILTER performed != null
                FILTER performed < (e.category IN @pflschg ? DATE_TIMESTAMP(@pflschg_cutoff) : DATE_TIMESTAMP(@cutoff))
                LIMIT @batch
                RETURN e
            """,
                    bind_vars=bind_vars,
                ),
            )
        )
        result = AnonymizedBatch(selected=len(docs))
        if not docs:
            return result
        stamp = now.astimezone(UTC).isoformat()
        fresh = [doc for doc in docs if doc.get("retention_anonymized_at") is None]
        if fresh:
            outcomes = self._db.collection(col.CARE_EVENTS).update_many([retention_patch(doc, stamp) for doc in fresh])
            # ``update_many`` reports a refused document inline instead of raising; a half batch must not read as done.
            failures = [outcome for outcome in cast("list[Any]", outcomes) if isinstance(outcome, Exception)]
            if failures:
                raise failures[0]
        result.anonymized = len(fresh)
        result.pending_photos = [
            PendingPhotos(str(doc["_key"]), str(doc.get("tenant_key", "")), tuple(str(r) for r in doc["photo_refs"]))
            for doc in docs
            if doc.get("photo_refs")
        ]
        return result

    def clear_photo_refs(self, event_keys: list[str]) -> int:
        if not event_keys:
            return 0
        outcomes = self._db.collection(col.CARE_EVENTS).update_many(
            [{"_key": key, "photo_refs": []} for key in event_keys]
        )
        failures = [outcome for outcome in cast("list[Any]", outcomes) if isinstance(outcome, Exception)]
        if failures:
            raise failures[0]
        return len(event_keys)
