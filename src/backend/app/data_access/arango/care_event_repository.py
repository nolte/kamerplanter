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

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.aql import AQL
from arango.cursor import Cursor
from arango.database import StandardDatabase
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.common.exceptions import DuplicateError, NotFoundError, PlanError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.transactions import StreamTransaction, TransactionAql, stream_transaction
from app.domain.engines.soil_analysis_engine import (
    PROFILE_MEASURED_FIELDS,
    SOIL_ANALYSIS_CATEGORY,
    AnalysisEvent,
    derive_profile,
    hand_values_after_edit,
    read_instant,
)
from app.domain.engines.soil_analysis_engine import writes_the_soil_profile as _feeds_the_profile
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
    owns_its_source_document,
)
from app.domain.models.garden_plan import PlanAuditRecord
from app.domain.models.site import SoilProfile
from app.domain.models.task_completion import DomainDocument

logger = structlog.get_logger()

#: Collections a care-event write touches; a transaction that calls :func:`write_care_event` declares all of them.
CARE_EVENT_WRITE_COLLECTIONS: tuple[str, ...] = (
    col.CARE_EVENTS,
    col.CARE_EVENT_AT,
    col.CARE_EVENT_FOR,
    col.TASK_LOGGED_AS,
)

#: The plants standing in a set of locations (not removed), by key: whom a dose on the whole bed is attributed to.
#: Read by :func:`plant_keys_standing_in` only; the bounded form serves a caller that refuses an oversized bed.
_PLANTS_STANDING_IN = """
FOR p IN @@plants
    FILTER p.tenant_key == @tenant_key AND p.location_key IN @location_keys AND p.removed_on == null
    SORT p._key
"""
PLANTS_STANDING_IN_AQL = _PLANTS_STANDING_IN + "    RETURN p._key\n"
PLANTS_STANDING_IN_BOUNDED_AQL = _PLANTS_STANDING_IN + "    LIMIT @limit\n    RETURN p._key\n"

#: Collections the ``feeding_event`` of a care-log entry and its edges are written into (#2833).
FEEDING_EVENT_WRITE_COLLECTIONS: tuple[str, ...] = (col.FEEDING_EVENTS, col.FED_BY, col.FEEDING_USED)

#: The specialist documents a care line can be the record of, with the edges that hang off them:
#: ``(edge collection, direction)`` where ``out`` means the document is the edge's ``_from``. What withdrawing the
#: line removes with the document - the undo of a task completion and the void or correction of a care-log entry.
WITHDRAWABLE_DOCUMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    col.WATERING_EVENTS: ((col.WATERED_PLANT, "out"),),
    col.FEEDING_EVENTS: ((col.FEEDING_USED, "out"), (col.FED_BY, "in")),
    col.HARVEST_BATCHES: ((col.HARVESTED_AS, "in"),),
}

#: What a transaction calling :func:`withdraw_domain_document` declares for writing: every document and edge above.
WITHDRAWABLE_WRITE_COLLECTIONS: tuple[str, ...] = tuple(
    dict.fromkeys(
        name for document, edges in WITHDRAWABLE_DOCUMENTS.items() for name in (document, *(e for e, _ in edges))
    )
)

#: The specialist documents a care-log entry writes itself (#2833): only these are withdrawn with its void or
#: correction, so a care-log transaction declares no more than :data:`FEEDING_EVENT_WRITE_COLLECTIONS`. A harvest
#: batch (with its follow-up records) or a watering row is the task completion's, withdrawn by reopening the task.
CARE_LOG_DOCUMENTS: frozenset[str] = frozenset({col.FEEDING_EVENTS})

_OWNED_DOCUMENT_ID = (
    'LET d = DOCUMENT(CONCAT(@collection, "/", @key)) FILTER d != null AND d.tenant_key == @tenant_key RETURN d._id'
)
_REMOVE_EDGES_FROM = "FOR e IN @@edge FILTER e._from == @id REMOVE e IN @@edge"
_REMOVE_EDGES_TO = "FOR e IN @@edge FILTER e._to == @id REMOVE e IN @@edge"

#: What the re-derivation of a bed's profile touches besides the care events: it writes ``locations`` and reads
#: ``sites`` (a bed belongs to its site's tenant). A transaction calling :func:`rederive_soil_profile` declares both.
SOIL_PROFILE_WRITE_COLLECTIONS: tuple[str, ...] = (col.LOCATIONS,)
SOIL_PROFILE_READ_COLLECTIONS: tuple[str, ...] = (col.SITES,)

#: The transaction storing a ``soil_analysis`` writes the bed's profile as well (WP 8.7): of the plain inserts only
#: this one declares ``locations``, so no other insert declares a collection it never writes.
SOIL_ANALYSIS_WRITE_COLLECTIONS: tuple[str, ...] = (*CARE_EVENT_WRITE_COLLECTIONS, *SOIL_PROFILE_WRITE_COLLECTIONS)


def writes_the_soil_profile(event: CareEvent | dict[str, Any]) -> bool:
    """Whether storing, voiding or replacing ``event`` (a model or a stored document) derives the bed's profile again.

    The engine's one predicate (:func:`~app.domain.engines.soil_analysis_engine.writes_the_soil_profile`) for both
    shapes; every caller in the data-access tier asks here.
    """
    if isinstance(event, CareEvent):
        return _feeds_the_profile(event.category, event.measurements)
    doc: dict[str, Any] = event
    return _feeds_the_profile(doc.get("category"), doc.get("measurements"))


def write_collections_for(events: Sequence[CareEvent]) -> tuple[str, ...]:
    """The collections an insert of ``events`` declares for writing."""
    if any(writes_the_soil_profile(event) for event in events):
        return SOIL_ANALYSIS_WRITE_COLLECTIONS
    return CARE_EVENT_WRITE_COLLECTIONS


def read_collections_for(events: Sequence[CareEvent]) -> tuple[str, ...]:
    """The collections an insert of ``events`` declares for reading (the re-derivation's ``sites``)."""
    return SOIL_PROFILE_READ_COLLECTIONS if any(writes_the_soil_profile(event) for event in events) else ()


def _location_key_of(doc: dict[str, Any]) -> str:
    return str(doc.get("location_key"))


def profile_locations(events: Sequence[CareEvent | dict[str, Any]]) -> list[str]:
    """The beds whose profile ``events`` feed, each once, in a stable order."""
    keys = {
        event.location_key if isinstance(event, CareEvent) else _location_key_of(event)
        for event in events
        if writes_the_soil_profile(event)
    }
    return sorted(keys)


#: Most analyses of one bed the re-derivation reads (newest first, open and closed). Only the newest open analysis
#: of each parameter matters, so the bound keeps the read finite without changing a real bed; hitting it is logged.
MAX_DERIVATION_ANALYSES = 500

#: The bed's soil analyses, open ones (``@open``) or closed ones, newest first. The index ``tenant_key,
#: location_key, performed_at`` selects the bed, the category is filtered inside the index scan before the sort.
_ANALYSES_OF_BED = """
FOR e IN @@events
    FILTER e.tenant_key == @tenant_key AND e.location_key == @location_key AND e.category == @category
    FILTER (e.voided_at == null AND e.superseded_by_key == null) == @open
    SORT DATE_TIMESTAMP(e.performed_at) DESC, DATE_TIMESTAMP(e.created_at) DESC, e._key DESC
    LIMIT @limit
    RETURN { key: e._key, performed_at: e.performed_at, category: e.category, measurements: e.measurements }
"""

#: The bed and whether its site belongs to the tenant (a bed has no ``tenant_key`` of its own, #2107).
_LOCATION_OF_TENANT = """
LET l = DOCUMENT(CONCAT(@locations, @key))
LET s = l == null ? null : DOCUMENT(CONCAT(@sites, l.site_key))
RETURN { location: l, owned: s != null AND s.tenant_key == @tenant_key }
"""

#: The profile write, guarded by the same ownership predicate in the same statement (defence in depth): a bed whose
#: site is not the tenant's is not written. It **always** writes - ``soil_profile_rev`` moves even when the profile
#: comes out unchanged - so two derivations of one bed running concurrently collide on ArangoDB's write-write
#: conflict instead of one silently skipping its write on a state the other is changing (#2706, M1).
_WRITE_OWNED_PROFILE = """
FOR l IN @@locations
    FILTER l._key == @key
    LET s = DOCUMENT(CONCAT(@sites, l.site_key))
    FILTER s != null AND s.tenant_key == @tenant_key
    UPDATE l WITH MERGE(
        { soil_profile_rev: (IS_NUMBER(l.soil_profile_rev) ? l.soil_profile_rev : 0) + 1 },
        @write_profile ? { soil_profile: @profile } : {}
    ) IN @@locations OPTIONS { mergeObjects: false }
    RETURN 1
"""


#: A supersede chain longer than this is not a chain a person made; the walk stops (and the redaction with it).
_MAX_CHAIN = 100

_EVENT_BY_KEY = """
LET e = DOCUMENT(CONCAT(@events, @key))
FILTER e != null AND e.tenant_key == @tenant_key
"""

#: The event a buffered write stored (WP 9.3): served by the unique ``(tenant_key, client_event_id)`` index (v0106).
_EVENT_BY_CLIENT_ID = """
FOR e IN @@events
    FILTER e.tenant_key == @tenant_key AND e.client_event_id == @client_event_id
    SORT e._key
    LIMIT 1
    RETURN e._key
"""

#: The events of one replayable zone round (WP 9.13), by the raw id they all carry: one statement, so one snapshot - a
#: reader that meets a round's commit sees all of its events or none. Served by the sparse
#: ``(tenant_key, client_round_id)`` index; bounded by ``@limit``.
_EVENTS_OF_CLIENT_ROUND = """
FOR e IN @@events
    FILTER e.tenant_key == @tenant_key AND e.client_round_id == @client_round_id
    SORT e._key
    LIMIT @limit
    RETURN e
"""

#: The readable names of ``e.plant_keys`` (bind ``@plants`` = ``"plant_instances/"``), one primary-key lookup per
#: plant: ``plant_name``, else ``instance_id``; a plant that is gone or another tenant's is left out (#2514). Shared
#: with the bed history (``bed_history_repository``) so both lists name a plant alike.
PLANT_NAMES_AQL = """
LET plant_names = (
    FOR plant_key IN (e.plant_keys == null ? [] : e.plant_keys)
        LET p = DOCUMENT(CONCAT(@plants, plant_key))
        FILTER p != null AND p.tenant_key == e.tenant_key
        RETURN p.plant_name != null ? p.plant_name : p.instance_id
)
"""


def plant_names_of(value: Any) -> tuple[str, ...]:
    """The ``plant_names`` of an AQL row as a tuple of strings; a plant without either name is skipped."""
    if not isinstance(value, list):
        return ()
    return tuple(str(name) for name in value if name)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _dump(model: BaseModel, **options: Any) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump(**options)


def write_care_event(
    txn: StreamTransaction,
    event: CareEvent,
    now: str,
    *,
    link_task: bool = True,
) -> dict[str, Any]:
    """Insert ``event`` and its edges inside the caller's transaction; returns the stored document.

    The caller declares :data:`CARE_EVENT_WRITE_COLLECTIONS` for writing. ``created_at`` is stamped here, the
    ``_key`` is the database's. A ``None`` field is not stored (an absent attribute reads as ``null`` in AQL).
    The bed's profile is not written here: a caller storing a soil analysis calls :func:`rederive_soil_profile`
    for :func:`profile_locations` afterwards, in the same transaction.
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


def plant_keys_standing_in(
    db: StandardDatabase, location_keys: list[str], *, tenant_key: str, limit: int | None = None
) -> list[str]:
    """The tenant's plants standing in ``location_keys`` (not removed), sorted: whom a whole-bed dose is attributed to.

    One read for the task completion and the care-log entry (#2833), so the attribution cannot drift between them.
    ``limit`` bounds the read (the first ``limit`` keys); a caller that must refuse an oversized bed asks for one
    more than it accepts and counts.
    """
    if not location_keys:
        return []
    bind_vars: dict[str, Any] = {
        "@plants": col.PLANT_INSTANCES,
        "location_keys": location_keys,
        "tenant_key": tenant_key,
    }
    query = PLANTS_STANDING_IN_AQL
    if limit is not None:
        query = PLANTS_STANDING_IN_BOUNDED_AQL
        bind_vars["limit"] = limit
    cursor = cast("Cursor", db.aql.execute(query, bind_vars=bind_vars))
    return [str(key) for key in cursor]


def owned_domain_reference(event: dict[str, Any]) -> dict[str, str] | None:
    """The ``source_ref`` of a stored line when the line wrote that document itself, else ``None`` (#2833).

    Only such a document is withdrawn with the line's void or correction
    (:func:`~app.domain.models.care_event.owns_its_source_document`, :data:`CARE_LOG_DOCUMENTS`); a backfilled or
    reconciled line mirrors a document that stays.
    """
    reference = event.get("source_ref")
    if not isinstance(reference, dict) or not owns_its_source_document(event.get("trigger")):
        return None
    if reference.get("collection") not in CARE_LOG_DOCUMENTS or not reference.get("key"):
        return None
    return {"collection": str(reference["collection"]), "key": str(reference["key"])}


def withdraw_domain_document(txn: StreamTransaction, reference: dict[str, Any], *, tenant_key: str) -> bool:
    """Remove the specialist document ``reference`` names and its edges, inside the caller's transaction.

    The inverse of :func:`write_domain_document`, shared by the undo of a task completion and the void or
    correction of a care-log entry. Tolerant by design: a reference outside :data:`WITHDRAWABLE_DOCUMENTS`, a
    document that is gone already (withdrawn before) or another tenant's is left alone and answers ``False`` - a
    second withdrawal of the same document is never an error. The caller declares
    :data:`WITHDRAWABLE_WRITE_COLLECTIONS` for writing; whether a harvest batch with follow-up records may go is the
    caller's decision, made before.
    """
    collection, doc_key = reference.get("collection"), reference.get("key")
    if collection not in WITHDRAWABLE_DOCUMENTS or not doc_key:
        return False
    document = next(
        iter(
            cast(
                "Cursor",
                txn.aql.execute(
                    _OWNED_DOCUMENT_ID,
                    bind_vars={"collection": collection, "key": doc_key, "tenant_key": tenant_key},
                ),
            )
        ),
        None,
    )
    if document is None:
        return False
    document_id = f"{collection}/{doc_key}"
    for edge, direction in WITHDRAWABLE_DOCUMENTS[str(collection)]:
        if direction == "out":
            txn.aql.execute(_REMOVE_EDGES_FROM, bind_vars={"@edge": edge, "id": document_id})
        else:
            txn.aql.execute(_REMOVE_EDGES_TO, bind_vars={"@edge": edge, "id": document_id})
    txn.collection(str(collection)).delete(str(doc_key))
    return True


def write_domain_document(txn: StreamTransaction, domain: DomainDocument, now: str) -> dict[str, str]:
    """Insert a specialist document (§12.1) and its edges inside the caller's transaction; returns its reference.

    The one writer of the documents a care event is the line of: the task completion (WP 4.3) and the care-log
    entry of a feeding or a nutrient amendment (#2833, #2854) both call it, then store the event with ``source_ref``
    set to the returned ``{"collection", "key"}`` - the reference the consistency job (GP-FR-105) reads as "already
    logged".
    The caller declares ``domain.collection`` and the edge collections for writing.
    """
    stored = txn.collection(domain.collection).insert(domain.document, return_new=True)["new"]
    own_id = f"{domain.collection}/{stored['_key']}"
    for edge, other_id, attributes in domain.edges_out:
        txn.collection(edge).insert({"_from": own_id, "_to": other_id, "created_at": now, **attributes})
    for edge, other_id, attributes in domain.edges_in:
        txn.collection(edge).insert({"_from": other_id, "_to": own_id, "created_at": now, **attributes})
    return {"collection": domain.collection, "key": str(stored["_key"])}


def _analyses(txn: StreamTransaction, location_key: str, tenant_key: str, *, open_ones: bool) -> list[AnalysisEvent]:
    """The bed's open (or closed) soil analyses, newest first, at most :data:`MAX_DERIVATION_ANALYSES`."""
    rows: list[dict[str, Any]] = list(
        cast(
            "Cursor",
            txn.aql.execute(
                _ANALYSES_OF_BED,
                bind_vars={
                    "@events": col.CARE_EVENTS,
                    "tenant_key": tenant_key,
                    "location_key": location_key,
                    "category": SOIL_ANALYSIS_CATEGORY,
                    "open": open_ones,
                    "limit": MAX_DERIVATION_ANALYSES,
                },
            ),
        )
    )
    if len(rows) >= MAX_DERIVATION_ANALYSES:
        logger.warning(
            "soil_analysis.derivation_bound_reached",
            location_key=location_key,
            limit=MAX_DERIVATION_ANALYSES,
            open=open_ones,
        )
    return [
        AnalysisEvent(key=str(row["key"]), performed_at=performed_at, measurements=row["measurements"])
        for row in rows
        if (performed_at := read_instant(row.get("performed_at"))) is not None and writes_the_soil_profile(row)
    ]


def _owned_location(txn: StreamTransaction, location_key: str, tenant_key: str) -> dict[str, Any] | None:
    """The bed if its site is the tenant's; ``None`` when it is gone; a foreign bed is logged and ``None`` too."""
    found: dict[str, Any] | None = next(
        iter(
            cast(
                "Cursor",
                txn.aql.execute(
                    _LOCATION_OF_TENANT,
                    bind_vars={
                        "locations": f"{col.LOCATIONS}/",
                        "sites": f"{col.SITES}/",
                        "key": location_key,
                        "tenant_key": tenant_key,
                    },
                ),
            )
        ),
        None,
    )
    if found is None or found.get("location") is None:
        return None
    if not found.get("owned"):
        logger.warning("soil_analysis.profile_write_refused_foreign_bed", location_key=location_key)
        return None
    return cast("dict[str, Any]", found["location"])


def _soil_of(location: dict[str, Any]) -> dict[str, Any]:
    profile = location.get("soil_profile")
    return cast("dict[str, Any]", profile) if isinstance(profile, dict) else {}


def _write_profile(
    txn: StreamTransaction, location_key: str, tenant_key: str, profile: dict[str, Any] | None, *, write: bool = True
) -> None:
    txn.aql.execute(
        _WRITE_OWNED_PROFILE,
        bind_vars={
            "@locations": col.LOCATIONS,
            "sites": f"{col.SITES}/",
            "key": location_key,
            "tenant_key": tenant_key,
            "profile": profile,
            "write_profile": write,
        },
    )


def _refused(exc: PydanticValidationError) -> PlanError:
    """A derived profile the model refuses: 422 naming the field, never a value (the transaction aborts)."""
    locations = [error["loc"] for error in exc.errors()]
    path = ".".join(str(part) for part in locations[0]) if locations else ""
    return PlanError(
        "soil_profile.derivation_invalid",
        "The soil profile derived from the analyses and hand entries is not valid; nothing was written.",
        status_code=422,
        field=".".join(("soil_profile", path)) if path else "soil_profile",
    )


def rederive_soil_profile(txn: StreamTransaction, location_key: str, *, tenant_key: str) -> None:
    """Derive the bed's ``soil_profile``, inside the caller's transaction (#2706, the one write path).

    Runs after every store, void, correction or withdrawn task completion of a soil analysis and after a hand edit
    (``PATCH /locations``): per measured field the newest observation wins (:func:`derive_profile`). The caller
    declared :data:`SOIL_PROFILE_WRITE_COLLECTIONS` and :data:`SOIL_PROFILE_READ_COLLECTIONS` and has already
    written its own columns in ``txn``, so the read sees them. The bed is **always** written (``soil_profile_rev``
    moves even when the profile comes out unchanged), so two derivations of one bed collide on the write-write
    conflict. At most :data:`MAX_DERIVATION_ANALYSES` open analyses are read (logged when reached); the closed ones
    are read only for a row from before ``hand_values`` (legacy rule), bounded alike. A bed that is gone or whose
    site is not the tenant's (fail closed) is left alone; a derived profile the model refuses raises 422
    ``soil_profile.derivation_invalid`` and aborts the transaction.
    """
    location = _owned_location(txn, location_key, tenant_key)
    if location is None:
        return
    current = _soil_of(location)
    analyses = _analyses(txn, location_key, tenant_key, open_ones=True)
    legacy = not isinstance(current.get("hand_values"), dict) and any(
        current.get(value_field) is not None for value_field, _ in PROFILE_MEASURED_FIELDS
    )
    history = [*analyses, *_analyses(txn, location_key, tenant_key, open_ones=False)] if legacy else analyses
    derived = cast("dict[str, Any]", _json_value(derive_profile(current, analyses, history=history)))
    try:
        SoilProfile(**derived)
    except PydanticValidationError as exc:
        raise _refused(exc) from exc
    # A bed that had no profile and derives none keeps none; the revision moves either way.
    _write_profile(txn, location_key, tenant_key, derived, write=bool(derived) or bool(current))


def write_soil_profile_edit(
    txn: StreamTransaction,
    location_key: str,
    *,
    tenant_key: str,
    profile: dict[str, Any] | None,
    check_last_analysis_at: bool,
    expected_last_analysis_at: datetime | None,
) -> None:
    """A ``soil_profile`` sent with ``PATCH /locations``, written through the derivation (#2706).

    Inside the caller's transaction (it declared what :func:`rederive_soil_profile` needs). In order: the
    precondition - a body that carried ``last_analysis_at`` must carry the stored one, else 409
    ``soil_profile.stale``; ``null`` stores ``null``; a row from before ``hand_values`` is derived first (its values
    get their hand entries from the legacy rule, never from the edit); then the edited measured fields become hand
    entries at now (unchanged ones none), the other soil fields are taken as sent, and the derivation computes the
    measured fields and ``last_analysis_at``. The derived fields are never written from the body.
    """
    location = _owned_location(txn, location_key, tenant_key)
    if location is None:
        raise NotFoundError("Location", location_key)
    current = _soil_of(location)
    stored_last = read_instant(current.get("last_analysis_at"))
    expected = read_instant(expected_last_analysis_at)
    if check_last_analysis_at and stored_last != expected:
        raise PlanError(
            "soil_profile.stale",
            "The soil profile changed since it was read (a soil analysis was stored); reload and try again.",
            status_code=409,
            field="soil_profile.last_analysis_at",
        )
    if profile is None:
        _write_profile(txn, location_key, tenant_key, None)
        return
    as_read = current
    if current and not isinstance(current.get("hand_values"), dict):
        rederive_soil_profile(txn, location_key, tenant_key=tenant_key)
        location = _owned_location(txn, location_key, tenant_key) or location
        current = _soil_of(location)
    derived_fields = {name for pair in PROFILE_MEASURED_FIELDS for name in pair if name} | {
        "last_analysis_at",
        "hand_values",
    }
    staged = {name: value for name, value in profile.items() if name not in derived_fields}
    staged.update({name: value for name, value in current.items() if name in derived_fields})
    # Compared with the profile as the client read it: on a legacy row the derivation above may have replaced an
    # echoed value, and that echo is not a hand edit (#2706 review).
    staged["hand_values"] = hand_values_after_edit(current, profile, datetime.now(UTC), as_read=as_read)
    _write_profile(txn, location_key, tenant_key, cast("dict[str, Any]", _json_value(staged)))
    rederive_soil_profile(txn, location_key, tenant_key=tenant_key)


def _json_value(value: Any) -> Any:
    """A derived profile as the database stores it: every instant (nested ones too) as ISO text."""
    if isinstance(value, datetime):
        instant: datetime = value
        return instant.isoformat()
    if isinstance(value, dict):
        mapping: dict[str, Any] = value
        return {str(name): _json_value(mapping[name]) for name in mapping}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


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


#: Blanks the free-text product name a care line copied into its ``feeding_event`` (#2854); a document that is gone
#: (withdrawn), another tenant's or one without a name is left alone.
REDACT_FEEDING_LABELS_AQL = """
FOR target IN @targets
    LET d = DOCUMENT(@@feedings, target.key)
    FILTER d != null AND d.tenant_key == target.tenant_key AND d.product_label != null
    UPDATE d WITH { product_label: @redacted } IN @@feedings
"""


def feeding_label_targets(docs: list[dict[str, Any]]) -> list[dict[str, str]]:
    """The ``feeding_events`` whose ``product_label`` is a copy of these lines' free text (#2854).

    Every ``source_ref`` into ``feeding_events``, whoever wrote the document: a ``product_label`` there only ever
    comes from a care line (the builder of the care log and the task completion), so redacting or anonymising the
    line's text must reach the copy as well (GP-FR-109, R-25).
    """
    targets: list[dict[str, str]] = []
    for doc in docs:
        reference = doc.get("source_ref")
        if isinstance(reference, dict) and reference.get("collection") == col.FEEDING_EVENTS and reference.get("key"):
            targets.append({"key": str(reference["key"]), "tenant_key": str(doc.get("tenant_key", ""))})
    return targets


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
            {PLANT_NAMES_AQL}
            RETURN {{
                event: e, performed_by_name: by.display_name, performed_for_name: for_user.display_name,
                plant_names: plant_names
            }}
            """,
                bind_vars={
                    "events": f"{col.CARE_EVENTS}/",
                    "users": f"{col.USERS}/",
                    "plants": f"{col.PLANT_INSTANCES}/",
                    "key": key,
                    "tenant_key": tenant_key,
                },
            ),
        )
        row = next(cursor, None)
        return self._row(row) if row is not None else None

    def find_key_by_client_event_id(self, client_event_id: str, *, tenant_key: str) -> str | None:
        self._require_tenant_key(tenant_key, "find_key_by_client_event_id")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                _EVENT_BY_CLIENT_ID,
                bind_vars={"@events": col.CARE_EVENTS, "tenant_key": tenant_key, "client_event_id": client_event_id},
            ),
        )
        key = next(cursor, None)
        return str(key) if key is not None else None

    def find_client_round(self, client_round_id: str, *, tenant_key: str, limit: int) -> list[CareEvent]:
        self._require_tenant_key(tenant_key, "find_client_round")
        bind_vars: dict[str, Any] = {
            "@events": col.CARE_EVENTS,
            "tenant_key": tenant_key,
            "client_round_id": client_round_id,
            "limit": limit,
        }
        cursor = cast("Cursor", self._db.aql.execute(_EVENTS_OF_CLIENT_ROUND, bind_vars=bind_vars))
        return [self._wrapped(doc) for doc in cursor]

    def _row(self, row: dict[str, Any]) -> CareEventRow:
        return CareEventRow(
            event=self._wrapped(row["event"]),
            performed_by_name=row.get("performed_by_name"),
            performed_for_name=row.get("performed_for_name"),
            plant_names=plant_names_of(row.get("plant_names")),
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
            "plants": f"{col.PLANT_INSTANCES}/",
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
        if criteria.exclude_voided:
            filters.append("e.voided_at == null")
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
                {PLANT_NAMES_AQL}
                RETURN {{
                    event: e, performed_by_name: by.display_name, performed_for_name: for_user.display_name,
                    plant_names: plant_names
                }}
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

    def plant_keys_standing_in(self, location_keys: list[str], *, tenant_key: str, limit: int) -> list[str]:
        self._require_tenant_key(tenant_key, "plant_keys_standing_in")
        return plant_keys_standing_in(self._db, location_keys, tenant_key=tenant_key, limit=limit)

    # ── Writes ────────────────────────────────────────────────────────────

    def insert(self, event: CareEvent, *, tenant_key: str) -> CareEvent:
        self._require_tenant_key(tenant_key, "insert")
        if event.tenant_key != tenant_key:
            raise ValueError("insert: the event belongs to another tenant than the one it is written under.")
        with stream_transaction(
            self._db, write=write_collections_for([event]), read=read_collections_for([event]), entity="care_event"
        ) as txn:
            stored = write_care_event(txn, event, _now())
            for location_key in profile_locations([event]):
                rederive_soil_profile(txn, location_key, tenant_key=tenant_key)
        return self._wrapped(stored)

    def insert_with_feeding_event(self, event: CareEvent, feeding: DomainDocument, *, tenant_key: str) -> CareEvent:
        self._require_tenant_key(tenant_key, "insert_with_feeding_event")
        if event.tenant_key != tenant_key or feeding.document.get("tenant_key") != tenant_key:
            raise ValueError("insert_with_feeding_event: a document belongs to another tenant than the one it writes.")
        if feeding.collection != col.FEEDING_EVENTS:
            raise ValueError("insert_with_feeding_event: the specialist document is not a feeding event.")
        if event.source_ref is not None:
            # A line names exactly one document: a server caller's own reference is never replaced by this one.
            raise ValueError("insert_with_feeding_event: the event names a source document already.")
        with stream_transaction(
            self._db,
            write=(*write_collections_for([event]), *FEEDING_EVENT_WRITE_COLLECTIONS),
            read=read_collections_for([event]),
            entity="care_event",
        ) as txn:
            now = _now()
            # The feeding event first: the care event points at it. A refused care-event insert (the client-event
            # index of a replay) aborts the transaction, so no feeding event is left behind without its line.
            reference = write_domain_document(txn, feeding, now)
            stored = write_care_event(txn, event.model_copy(update={"source_ref": reference}), now)
            for location_key in profile_locations([event]):
                rederive_soil_profile(txn, location_key, tenant_key=tenant_key)
        return self._wrapped(stored)

    def insert_many(self, events: list[CareEvent], *, tenant_key: str) -> list[CareEvent]:
        self._require_tenant_key(tenant_key, "insert_many")
        if any(event.tenant_key != tenant_key for event in events):
            raise ValueError("insert_many: an event belongs to another tenant than the one it is written under.")
        if not events:
            return []
        now = _now()
        # Like ``insert`` (and its conflict fallback): a soil analysis in the batch writes the bed's profile too.
        with stream_transaction(
            self._db, write=write_collections_for(events), read=read_collections_for(events), entity="care_event"
        ) as txn:
            stored = [write_care_event(txn, event, now) for event in events]
            for location_key in profile_locations(events):
                rederive_soil_profile(txn, location_key, tenant_key=tenant_key)
        return [self._wrapped(doc) for doc in stored]

    def insert_backfilled(self, events: list[CareEvent], *, tenant_key: str) -> tuple[int, int]:
        self._require_tenant_key(tenant_key, "insert_backfilled")
        if any(event.tenant_key != tenant_key for event in events):
            raise ValueError("insert_backfilled: an event belongs to another tenant than the one it is written under.")
        if any(event.trigger != "backfill" or not event.source_ref for event in events):
            raise ValueError("insert_backfilled: every event is a backfill and names its source (source_ref).")
        if not events:
            return 0, 0
        try:
            self.insert_many(events, tenant_key=tenant_key)
        except DuplicateError, WriteConflictError:
            # A concurrent writer logged one of these documents since the caller looked: the batch was aborted as a
            # whole (all or none), so write the events one by one and let the unique index say which are present.
            written = 0
            for event in events:
                for attempt in range(3):
                    try:
                        self.insert(event, tenant_key=tenant_key)
                    except DuplicateError:
                        break
                    except WriteConflictError:  # a live writer touched the same bed: retry, then give up loudly
                        if attempt == 2:
                            raise
                        continue
                    written += 1
                    break
            return written, len(events) - written
        return len(events), 0

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
        return self._write_supersession(predecessor_key, event, None, tenant_key=tenant_key)

    def supersede_with_feeding_event(
        self, predecessor_key: str, event: CareEvent, feeding: DomainDocument, *, tenant_key: str
    ) -> CareEvent:
        self._require_tenant_key(tenant_key, "supersede_with_feeding_event")
        if feeding.document.get("tenant_key") != tenant_key:
            raise ValueError("supersede_with_feeding_event: the feeding event belongs to another tenant.")
        if feeding.collection != col.FEEDING_EVENTS:
            raise ValueError("supersede_with_feeding_event: the specialist document is not a feeding event.")
        return self._write_supersession(predecessor_key, event, feeding, tenant_key=tenant_key)

    def _write_supersession(
        self, predecessor_key: str, event: CareEvent, feeding: DomainDocument | None, *, tenant_key: str
    ) -> CareEvent:
        """The correction in one transaction: the predecessor's own document goes, the successor's (if any) comes.

        A care-log entry's ``feeding_event`` describes the dose the entry stated; a correction that changes the dose,
        the material or the category must not leave the old one counting in the fertiliser balance (#2833).
        """
        if event.tenant_key != tenant_key:
            raise ValueError("supersede: the event belongs to another tenant than the one it is written under.")
        if event.source_ref is not None:
            raise ValueError("supersede: a correction names its source document through the feeding event only.")
        # Replacing a soil analysis (by anything) or writing one derives the bed's profile again (#2706); the
        # transaction always declares what that touches, so no read before it decides the declaration. The same
        # holds for the specialist document a care-log entry wrote (withdrawn) and the correction's (written).
        with stream_transaction(
            self._db,
            write=(*SOIL_ANALYSIS_WRITE_COLLECTIONS, *FEEDING_EVENT_WRITE_COLLECTIONS),
            read=SOIL_PROFILE_READ_COLLECTIONS,
            entity="care_event",
        ) as txn:
            predecessor = self._load_in(txn, predecessor_key, tenant_key)
            self._refuse_if_closed(predecessor)
            if predecessor.get("location_key") != event.location_key or event.supersedes_key != predecessor_key:
                raise PlanError(
                    "care_event.sequence",
                    "A correction stays on the bed of its predecessor and names it.",
                    status_code=422,
                    field="supersedes_key",
                )
            now = _now()
            owned = owned_domain_reference(predecessor)
            if owned is not None:
                withdraw_domain_document(txn, owned, tenant_key=tenant_key)
            if feeding is not None:
                event = event.model_copy(update={"source_ref": write_domain_document(txn, feeding, now)})
            stored = write_care_event(txn, event, now, link_task=False)
            txn.collection(col.CARE_EVENTS).update({"_key": predecessor_key, "superseded_by_key": stored["_key"]})
            # A correction that drops a parameter or moves ``performed_at`` earlier must not leave the predecessor's
            # value or its later ``last_analysis_at`` behind: the profile is derived from the open analyses again.
            for location_key in profile_locations([predecessor, event]):
                rederive_soil_profile(txn, location_key, tenant_key=tenant_key)
        return self._wrapped(stored)

    def void(self, key: str, *, tenant_key: str, voided_by: str, reason: str, at: datetime) -> CareEvent:
        self._require_tenant_key(tenant_key, "void")
        # A voided soil analysis takes its values out of the bed's profile (#2706); a voided care-log amendment
        # takes its feeding event out of the fertiliser balance (#2833) - the snackbar undo is its only way back.
        with stream_transaction(
            self._db,
            write=(col.CARE_EVENTS, *FEEDING_EVENT_WRITE_COLLECTIONS, *SOIL_PROFILE_WRITE_COLLECTIONS),
            read=SOIL_PROFILE_READ_COLLECTIONS,
            entity="care_event",
        ) as txn:
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
            owned = owned_domain_reference(current)
            if owned is not None:
                withdraw_domain_document(txn, owned, tenant_key=tenant_key)
            for location_key in profile_locations([current]):
                rederive_soil_profile(txn, location_key, tenant_key=tenant_key)
        return self._wrapped(updated)

    def redact(
        self, key: str, *, tenant_key: str, redacted_by: str, reason: str, at: datetime
    ) -> tuple[list[CareEvent], list[str]]:
        self._require_tenant_key(tenant_key, "redact")
        stamp = at.astimezone(UTC).isoformat()
        with stream_transaction(
            self._db,
            write=(col.CARE_EVENTS, col.GARDEN_PLAN_AUDIT, col.FEEDING_EVENTS),
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
            # The product name the chain copied into its feeding events goes with the line's text (#2854).
            txn.aql.execute(
                REDACT_FEEDING_LABELS_AQL,
                bind_vars={
                    "@feedings": col.FEEDING_EVENTS,
                    "targets": [t for t in feeding_label_targets(docs) if t["tenant_key"] == tenant_key],
                    "redacted": REDACTED,
                },
            )
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
            # R-25 reaches the product name a line copied into its feeding event as well (#2854).
            label_vars: dict[str, Any] = {
                "@feedings": col.FEEDING_EVENTS,
                "targets": feeding_label_targets(fresh),
                "redacted": REDACTED,
            }
            self._db.aql.execute(REDACT_FEEDING_LABELS_AQL, bind_vars=label_vars)
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
