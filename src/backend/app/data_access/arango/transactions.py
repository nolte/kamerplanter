"""The one way to run an ArangoDB **stream transaction** (REQ-053 WP 1.2, GP-NFR-013).

Until this module existed every atomic write opened the transaction by hand —
``care_reminder_repository.create_linked_profile`` (#1292), ``tenant_repository.
create_with_lead_membership`` (#2118), the two erasure executors, the export
store, the legal-retention purge and three migrations — and each site carried its
own copy of the same three obligations: commit exactly once, abort on *any*
failure without letting the abort mask it, and turn the server's conflict codes
into the domain's typed errors. Copies drift: ``create_edge`` grew its ``1200``
branch months after ``_insert_doc`` (#1458), and every caller in between was a
500. The garden-plan batch (GP-API-003), the atomic task completion (GP-FR-083),
quick planting (GP-API-017) and bed clearing (GP-API-019) each need the same
three obligations again; this module is where they are written once.

What the helper guarantees, and what the unit tests pin against a fake driver:

* **One commit, or none.** The body runs inside ``with``; leaving it normally
  commits once, leaving it by *any* exception — ``KeyboardInterrupt`` included —
  aborts. Nothing staged is visible to another connection before the commit, and
  an aborted transaction leaves no document behind, which is why a failure needs
  no cleanup (measured for #1292 against ArangoDB 3.12.8). The handle the body
  gets cannot commit or abort on its own; both are this module's job.
* **The abort never wins.** An abort can fail on its own — the server tears a
  transaction down after a write-write conflict, a dropped connection surfaces as
  a plain ``ConnectionError`` — and that secondary failure is logged and dropped
  so the caller sees the error that got us here.
* **Conflicts are typed.** ``1210`` (unique constraint violated) becomes
  :class:`~app.common.exceptions.DuplicateError`, ``1200`` (write-write conflict)
  becomes :class:`~app.common.exceptions.WriteConflictError` — the two answers the
  server may give the loser of one race, published as ``conflict.duplicate`` and
  ``conflict.write`` (``data_access/arango/conflicts.py`` is the one spelling).
  A write through :meth:`StreamTransaction.collection` is translated with the
  collection and the document in hand, so the duplicate names its real field and
  value; the bulk methods are forced to *raise* on the first refused document
  rather than return it inline, so a half-applied batch is never committed; a
  conflict the server defers to the commit, or one raised by an AQL statement, is
  translated generically on the way out. No raw driver conflict leaves the
  ``with`` block. A failure to *open* the transaction (a collection lock not
  granted within ``lockTimeout``) is not a conflict on the data and stays the
  driver's ``TransactionInitError``: a write that never started must never be
  mistaken for one the data refused (``v0048`` relies on exactly that).
* **A time budget.** The body is measured from ``begin`` to the commit decision;
  past the budget the transaction is aborted instead of committed and
  :class:`~app.common.exceptions.TransactionTimeBudgetExceededError` (422) is
  raised. The check runs at the commit decision, at every AQL statement issued
  through the handle (which also carries the remaining budget to the server as
  ``maxRuntime``, so one long query is cut off rather than run to completion),
  and whenever a long body asks :meth:`StreamTransaction.check_budget` between
  operations. Half the budget bounds the wait for the *collection* locks taken
  at ``begin`` (``lockTimeout``, which is what ``exclusive`` declarations wait
  on); a document-level lock contended inside the body still surfaces as the
  server's ``1200``.

Not a retry loop, deliberately: whether a lost race is resolved by re-reading
(``1200``) or by adopting the winner (``1210``) is the caller's decision — see
``CareReminderService`` — and a helper that retried would make it for them.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any

import structlog
from arango.aql import AQL
from arango.collection import StandardCollection
from arango.database import StandardDatabase, TransactionDatabase
from arango.exceptions import AQLQueryExecuteError, ArangoServerError, TransactionCommitError

from app.common.exceptions import KamerplanterError, TransactionTimeBudgetExceededError
from app.data_access.arango.conflicts import QUERY_KILLED, conflict_error_for

logger = structlog.get_logger()

#: GP-NFR-013: the plan batch — the largest atomic write this helper will carry —
#: gets 10 s before it is refused as too complex. Everything smaller inherits the
#: same ceiling rather than a tighter guess of its own.
DEFAULT_TIME_BUDGET_SECONDS = 10.0

#: The smallest ``maxRuntime`` handed to the server: a budget already spent still
#: issues the statement with a positive limit rather than an invalid zero.
_MIN_QUERY_RUNTIME_SECONDS = 0.001

#: What the body may not do through the handle — both are the context manager's
#: job, and a second commit is the one thing the server refuses outright.
_CONTEXT_MANAGER_ONLY = frozenset({"commit_transaction", "abort_transaction", "begin_transaction"})


def _lock_timeout_for(budget_seconds: float) -> int:
    """Half the budget, in whole seconds, at least one.

    The lock wait precedes the body and counts against the same budget; a wait as
    long as the whole budget would leave nothing for the writes and turn every
    contended open into a 422 instead of the 409 it is. ``lockTimeout`` is an
    integer on the wire, so a budget under two seconds still waits one.
    """
    return max(1, math.floor(budget_seconds / 2))


class TransactionCollection:
    """A collection handle bound to one open transaction, with typed conflicts on every write.

    ``insert``/``update``/``replace``/``delete`` are translated with the
    collection *and* the document in hand, so a duplicate names its real field
    and value. The bulk methods (``insert_many`` …) are forced to raise on the
    first refused document: python-arango's default is to return per-document
    errors **inline** in the result list and raise nothing, which would let a
    half-applied batch reach the commit — the opposite of what a transaction is
    for. A caller that wants per-document outcomes does not get them through the
    handle; it writes one document at a time and catches per write. Everything
    else (``get``, ``find``, ``has`` …) is the driver's own method, delegated.
    """

    __slots__ = ("_name", "_raw")

    def __init__(self, name: str, raw: StandardCollection) -> None:
        self._name = name
        self._raw = raw

    @property
    def name(self) -> str:
        return self._name

    def _translated(self, method: str, data: Mapping[str, Any] | None, *args: Any, **kwargs: Any) -> Any:
        """Call the driver's *method*; a 1210/1200 rejection becomes its domain error."""
        try:
            return getattr(self._raw, method)(*args, **kwargs)
        except ArangoServerError as exc:
            mapped = conflict_error_for(exc, entity=self._name, data=data)
            if mapped is not None:
                raise mapped from exc
            raise

    def insert(self, document: Mapping[str, Any], **kwargs: Any) -> Any:
        """Insert *document*; returns whatever the driver returns (``{"new": …}`` with ``return_new=True``)."""
        return self._translated("insert", document, dict(document), **kwargs)

    def update(self, document: Mapping[str, Any], **kwargs: Any) -> Any:
        """Partial update of *document* (which carries ``_key``); a ``_rev`` mismatch is a write conflict."""
        return self._translated("update", document, dict(document), **kwargs)

    def replace(self, document: Mapping[str, Any], **kwargs: Any) -> Any:
        return self._translated("replace", document, dict(document), **kwargs)

    def delete(self, document: str | Mapping[str, Any], **kwargs: Any) -> Any:
        data = {"_key": document} if isinstance(document, str) else dict(document)
        return self._translated("delete", data, document if isinstance(document, str) else data, **kwargs)

    def insert_many(self, documents: Sequence[Mapping[str, Any]], **kwargs: Any) -> Any:
        """Insert all of *documents* or raise on the first the server refuses (never an inline error list)."""
        kwargs["raise_on_document_error"] = True
        return self._translated("insert_many", None, [dict(doc) for doc in documents], **kwargs)

    def update_many(self, documents: Sequence[Mapping[str, Any]], **kwargs: Any) -> Any:
        kwargs["raise_on_document_error"] = True
        return self._translated("update_many", None, [dict(doc) for doc in documents], **kwargs)

    def replace_many(self, documents: Sequence[Mapping[str, Any]], **kwargs: Any) -> Any:
        kwargs["raise_on_document_error"] = True
        return self._translated("replace_many", None, [dict(doc) for doc in documents], **kwargs)

    def delete_many(self, documents: Sequence[Mapping[str, Any]], **kwargs: Any) -> Any:
        kwargs["raise_on_document_error"] = True
        return self._translated("delete_many", None, [dict(doc) for doc in documents], **kwargs)

    def __getattr__(self, attribute: str) -> Any:
        if attribute.startswith("_"):
            # Never resolve dunders or privates through the driver: ``copy``/``pickle``
            # probe for them on an instance whose slots are not set yet, and a
            # delegating ``__getattr__`` would recurse into itself.
            raise AttributeError(attribute)
        return getattr(self._raw, attribute)


class TransactionAql:
    """The transaction's AQL executor, with the remaining budget handed to the server.

    Every ``execute`` first checks the budget (a spent budget raises before the
    statement is sent) and then sets ``maxRuntime`` to what is left, unless the
    caller set its own. A statement the server kills for that reason comes back
    as the budget error rather than a raw ``1500 query killed``; a kill the
    caller did not ask for (an operator's ``KILL``, a ``maxRuntime`` the caller
    chose) stays the driver's error. Anything else about the executor —
    ``explain``, ``validate``, ``cache`` … — is delegated.
    """

    __slots__ = ("_handle", "_raw")

    def __init__(self, raw: AQL, handle: StreamTransaction) -> None:
        self._raw = raw
        self._handle = handle

    def execute(self, query: str, **kwargs: Any) -> Any:
        self._handle.check_budget()
        budgeted = "max_runtime" not in kwargs
        if budgeted:
            kwargs["max_runtime"] = max(self._handle.remaining_seconds(), _MIN_QUERY_RUNTIME_SECONDS)
        try:
            return self._raw.execute(query, **kwargs)
        except AQLQueryExecuteError as exc:
            if budgeted and exc.error_code == QUERY_KILLED:
                raise self._handle.budget_error() from exc
            raise

    def __getattr__(self, attribute: str) -> Any:
        if attribute.startswith("_"):
            raise AttributeError(attribute)
        return getattr(self._raw, attribute)


class StreamTransaction:
    """What ``with stream_transaction(...) as txn`` hands the body.

    Shaped like the driver's :class:`~arango.database.TransactionDatabase` so
    that code which takes a transaction handle (the erasure executors' step
    runners) can be handed this one unchanged: :meth:`collection` and
    :attr:`aql` are the typed, budgeted wrappers, every other attribute is the
    driver's. ``commit_transaction``/``abort_transaction`` are **not** reachable
    — both are the context manager's job, and a body that committed on its own
    would make the helper's commit a second one, which the server refuses.
    """

    def __init__(
        self,
        raw: TransactionDatabase,
        *,
        entity: str,
        write: Sequence[str],
        budget_seconds: float,
        started: float,
        clock: Callable[[], float],
    ) -> None:
        self._raw = raw
        self._entity = entity
        self._write = list(write)
        self._budget = budget_seconds
        self._started = started
        self._clock: Callable[[], float] = clock

    @property
    def entity(self) -> str:
        return self._entity

    @property
    def aql(self) -> TransactionAql:
        """``txn.aql.execute(...)`` runs inside the transaction, bounded by the remaining budget."""
        return TransactionAql(self._raw.aql, self)

    def collection(self, name: str) -> TransactionCollection:
        """A handle on *name* inside this transaction; the collection must be declared to ``write``."""
        return TransactionCollection(name, self._raw.collection(name))

    def elapsed_seconds(self) -> float:
        clock = self._clock
        return clock() - self._started

    def remaining_seconds(self) -> float:
        """How much of the budget is left; negative once it is spent."""
        return self._budget - self.elapsed_seconds()

    def over_budget(self) -> bool:
        return self.elapsed_seconds() > self._budget

    def budget_error(self) -> TransactionTimeBudgetExceededError:
        """The budget error for *now*, logged once here so both raisers report the same facts."""
        elapsed = self.elapsed_seconds()
        logger.warning(
            "arango_transaction_over_budget",
            entity=self._entity,
            elapsed_seconds=round(elapsed, 3),
            budget_seconds=self._budget,
            write=self._write,
        )
        return TransactionTimeBudgetExceededError(self._entity, budget_seconds=self._budget, elapsed_seconds=elapsed)

    def check_budget(self) -> None:
        """Stop a long body early: raise the budget error now rather than after more work.

        The context manager aborts on the way out, so the body need not — and
        cannot — abort itself. A batch that loops over hundreds of operations
        calls this once per operation; the plan batch (GP-NFR-013) is the model.

        Raises:
            TransactionTimeBudgetExceededError: once the budget is spent.
        """
        if self.over_budget():
            raise self.budget_error()

    def __getattr__(self, attribute: str) -> Any:
        if attribute in _CONTEXT_MANAGER_ONLY:
            raise AttributeError(f"{attribute} is the context manager's job; the body cannot end the transaction")
        if attribute.startswith("_"):
            raise AttributeError(attribute)
        return getattr(self._raw, attribute)


def _abort_quietly(transaction: TransactionDatabase, *, entity: str) -> None:
    """Roll back, never masking the failure that got us here.

    Broad on purpose: narrowing to :class:`ArangoError` would let a transport
    failure (a dropped connection is a plain ``ConnectionError``) replace the
    ``DuplicateError`` the caller is about to see, turning a resolvable lost race
    back into the 500 of #1292.
    """
    try:
        transaction.abort_transaction()
    except Exception:  # noqa: BLE001 — see the docstring; masking the primary error is worse
        logger.warning("arango_transaction_abort_failed", entity=entity, exc_info=True)


def _typed(error: BaseException, *, entity: str) -> BaseException:
    """The error to raise on the way out: a server conflict translated, anything else itself."""
    if isinstance(error, KamerplanterError) or not isinstance(error, ArangoServerError):
        return error
    return conflict_error_for(error, entity=entity) or error


@contextmanager
def stream_transaction(
    db: StandardDatabase,
    *,
    write: Sequence[str],
    read: Sequence[str] = (),
    exclusive: Sequence[str] = (),
    entity: str | None = None,
    time_budget_seconds: float = DEFAULT_TIME_BUDGET_SECONDS,
    allow_implicit: bool = False,
    clock: Callable[[], float] = time.monotonic,
) -> Iterator[StreamTransaction]:
    """Run the body atomically: commit once on success, abort on any failure, typed conflicts, a time budget.

    Args:
        db: The synchronous database the transaction is opened on.
        write: Every collection the body writes. A collection written but not
            declared makes ArangoDB refuse the write, so this is the contract,
            not a hint.
        read: Collections the body only reads (locked shared).
        exclusive: Collections the body needs an exclusive lock on.
        entity: What a conflict or a budget error is reported *about*; defaults to
            the first ``write`` collection, which is what the existing hand-rolled
            sites name.
        time_budget_seconds: The budget measured from ``begin`` to the commit
            decision; half of it bounds the collection-lock wait at ``begin``.
            Must be a positive, finite number.
        allow_implicit: Whether the body may touch undeclared collections for
            reading; ``False`` so a missing declaration fails loudly.
        clock: A monotonic clock, a parameter so the budget can be tested
            without waiting.

    Yields:
        The :class:`StreamTransaction` handle the body writes through.

    Raises:
        DuplicateError: ArangoDB ``1210`` from a write, an AQL statement or the commit.
        WriteConflictError: ArangoDB ``1200`` from the same places — never from ``begin``.
        TransactionInitError: the transaction could not be opened (a collection
            lock not granted within ``lock_timeout``, a missing collection); the
            driver's own error, untranslated, because nothing was written.
        TransactionTimeBudgetExceededError: the body outran its budget; aborted.
        ValueError: ``write`` is empty or the budget is not a positive finite
            number — refused before anything is opened.
    """
    if not write:
        raise ValueError("a stream transaction must declare at least one write collection")
    if not math.isfinite(time_budget_seconds) or time_budget_seconds <= 0:
        raise ValueError(f"time_budget_seconds must be a positive finite number, got {time_budget_seconds!r}")
    about = entity or write[0]

    started = clock()
    # A failure to OPEN the transaction — a collection lock not granted within
    # ``lock_timeout`` (error 18), a ``1200`` at begin, a missing collection — is
    # deliberately NOT translated into the conflict family. A conflict says "the
    # data refused this write"; a transaction that never started wrote nothing,
    # and callers tell the two apart: ``v0048_backfill_missing_care_profiles``
    # counts ``WriteConflictError`` as "the edge is already taken" and must never
    # count a write that never happened as that. The driver's
    # ``TransactionInitError`` therefore propagates as itself, which is what every
    # hand-rolled site raised before this helper existed.
    raw = db.begin_transaction(
        read=list(read) or None,
        write=list(write),
        exclusive=list(exclusive) or None,
        allow_implicit=allow_implicit,
        lock_timeout=_lock_timeout_for(time_budget_seconds),
    )
    handle = StreamTransaction(
        raw, entity=about, write=write, budget_seconds=time_budget_seconds, started=started, clock=clock
    )
    try:
        yield handle
    except BaseException as exc:
        _abort_quietly(raw, entity=about)
        typed = _typed(exc, entity=about)
        if typed is exc:
            raise
        raise typed from exc

    if handle.over_budget():
        _abort_quietly(raw, entity=about)
        raise handle.budget_error()

    try:
        raw.commit_transaction()
    except TransactionCommitError as exc:
        # A commit the server refused has already discarded the transaction on
        # most paths; the abort is best effort and its failure is logged, not raised.
        _abort_quietly(raw, entity=about)
        typed = _typed(exc, entity=about)
        if typed is exc:
            raise
        raise typed from exc
    logger.debug(
        "arango_transaction_committed",
        entity=about,
        elapsed_seconds=round(handle.elapsed_seconds(), 3),
        write=list(write),
    )
