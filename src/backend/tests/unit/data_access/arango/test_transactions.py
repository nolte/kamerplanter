"""``stream_transaction``: one commit or none, typed conflicts, a time budget (REQ-053 WP 1.2, #2320).

What a real server does with an aborted transaction — that nothing it staged is
visible afterwards — is measured in ``tests/integration/test_arango_transactions.py``.
What is doubled here is the helper's own contract around the driver: that the body's
writes are *staged* and only a commit publishes them, that every way of leaving the
``with`` block ends in exactly one of commit or abort, that a driver conflict never
leaves the block untyped, and that the budget is enforced from the clock the helper
was given. The fake stages documents and publishes on commit, so "nothing was
written" is read off what survived, not off a call count.
"""

from __future__ import annotations

import itertools
from typing import Any

import pytest
from arango.exceptions import (
    AQLQueryExecuteError,
    DocumentInsertError,
    DocumentUpdateError,
    TransactionCommitError,
    TransactionInitError,
)

from app.common.exceptions import (
    DuplicateError,
    KamerplanterError,
    TransactionTimeBudgetExceededError,
    WriteConflictError,
)
from app.data_access.arango.conflicts import conflict_error_for
from app.data_access.arango.transactions import DEFAULT_TIME_BUDGET_SECONDS, StreamTransaction, stream_transaction
from tests.unit.data_access.arango.test_care_profile_linked_write import _insert_error, _Request, _Response

DOCS = "txn_docs"
EDGES = "txn_edges"


class _Collection:
    def __init__(self, name: str, tx: _Transaction) -> None:
        self._name, self._tx = name, tx

    def _refused(self) -> None:
        refusal = self._tx.refuse.get(self._name)
        if refusal is not None:
            raise refusal

    def insert(self, data: dict[str, Any], return_new: bool = False):
        self._refused()
        document = dict(data)
        document.pop("_key", None)
        document["_key"] = f"{self._name[:3]}-{next(self._tx.keys)}"
        document["_id"] = f"{self._name}/{document['_key']}"
        self._tx.staged.setdefault(self._name, []).append(document)
        return {"new": dict(document)} if return_new else {"_key": document["_key"]}

    def update(self, data: dict[str, Any], **_: Any):
        self._refused()
        return {"_key": data["_key"]}

    def insert_many(self, documents: list[dict[str, Any]], **kwargs: Any):
        """python-arango's shape: with ``raise_on_document_error`` off, a refusal is RETURNED, not raised."""
        self._tx.bulk_kwargs = dict(kwargs)
        refusal = self._tx.refuse.get(self._name)
        results: list[Any] = []
        for document in documents:
            if refusal is not None and document.get("slug") == "taken":
                if kwargs.get("raise_on_document_error"):
                    raise refusal
                results.append(refusal)
                continue
            results.append(self.insert(document))
        return results

    def get(self, key: str) -> dict[str, Any] | None:
        """A read the helper must delegate untouched — it wraps the writes only."""
        return next((doc for doc in self._tx.staged.get(self._name, []) if doc["_key"] == key), None)


class _Aql:
    def __init__(self, tx: _Transaction) -> None:
        self._tx = tx
        self.calls: list[dict[str, Any]] = []

    def execute(self, query: str, **kwargs: Any) -> list[Any]:
        self.calls.append({"query": query, **kwargs})
        if self._tx.aql_error is not None:
            raise self._tx.aql_error
        return []

    def explain(self, query: str) -> dict[str, Any]:
        return {"query": query}


class _Transaction:
    transaction_id = "tx-1"

    def __init__(
        self,
        *,
        refuse: dict[str, Exception],
        commit_error: Exception | None,
        abort_error: Exception | None,
        aql_error: Exception | None,
    ) -> None:
        self.refuse, self.commit_error, self.abort_error, self.aql_error = refuse, commit_error, abort_error, aql_error
        self.staged: dict[str, list[dict[str, Any]]] = {}
        self.published: dict[str, list[dict[str, Any]]] = {}
        self.bulk_kwargs: dict[str, Any] = {}
        self.keys = itertools.count(1)
        self.commits = 0
        self.aborts = 0
        self.aql = _Aql(self)

    def collection(self, name: str) -> _Collection:
        return _Collection(name, self)

    def commit_transaction(self) -> bool:
        self.commits += 1
        if self.commit_error is not None:
            raise self.commit_error
        self.published = {name: list(docs) for name, docs in self.staged.items()}
        return True

    def abort_transaction(self) -> bool:
        self.aborts += 1
        if self.abort_error is not None:
            raise self.abort_error
        return True


class _Db:
    def __init__(self, init_error: Exception | None = None, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self._init_error = init_error
        self.transaction: _Transaction | None = None
        self.begin_kwargs: dict[str, Any] = {}

    def begin_transaction(self, **kwargs: Any) -> _Transaction:
        assert self.transaction is None, "the helper opened a second transaction"
        self.begin_kwargs = kwargs
        if self._init_error is not None:
            raise self._init_error
        self.transaction = _Transaction(**self._kwargs)
        return self.transaction


class _Clock:
    """A clock the test advances by hand; ``time.monotonic`` is a parameter of the helper for this."""

    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _db(
    *,
    refuse: dict[str, Exception] | None = None,
    commit_error: Exception | None = None,
    abort_error: Exception | None = None,
    aql_error: Exception | None = None,
    init_error: Exception | None = None,
) -> _Db:
    return _Db(
        init_error=init_error,
        refuse=refuse or {},
        commit_error=commit_error,
        abort_error=abort_error,
        aql_error=aql_error,
    )


def _commit_error(code: int) -> TransactionCommitError:
    return TransactionCommitError(
        _Response(code, "unique constraint violated - in index 7 over '[\"slug\"]'"), _Request()
    )


def _tx(db: _Db) -> _Transaction:
    assert db.transaction is not None, "the helper never opened the transaction"
    return db.transaction


class TestTheHappyPath:
    def test_the_body_is_published_by_exactly_one_commit(self):
        db = _db()

        with stream_transaction(db, write=[DOCS, EDGES]) as txn:  # type: ignore[arg-type]
            written = txn.collection(DOCS).insert({"slug": "a"}, return_new=True)
            txn.collection(EDGES).insert({"_from": f"{DOCS}/{written['new']['_key']}", "_to": "x/y"})
            assert _tx(db).published == {}, "a document was visible before the commit"

        tx = _tx(db)
        assert tx.commits == 1 and tx.aborts == 0
        assert [doc["slug"] for doc in tx.published[DOCS]] == ["a"]
        assert len(tx.published[EDGES]) == 1

    def test_the_declaration_reaches_the_driver_with_half_the_budget_as_lock_timeout(self):
        db = _db()

        with stream_transaction(db, write=[DOCS], read=[EDGES], time_budget_seconds=2.5):  # type: ignore[arg-type]
            pass

        assert db.begin_kwargs == {
            "read": [EDGES],
            "write": [DOCS],
            "exclusive": None,
            "allow_implicit": False,
            "lock_timeout": 1,
        }

    def test_the_default_budget_is_the_spec_figure_and_waits_five_seconds_for_locks(self):
        db = _db()
        assert DEFAULT_TIME_BUDGET_SECONDS == 10.0  # GP-NFR-013

        with stream_transaction(db, write=[DOCS]):  # type: ignore[arg-type]
            pass

        assert db.begin_kwargs["lock_timeout"] == 5

    def test_reads_and_the_rest_of_the_driver_are_delegated(self):
        db = _db()

        with stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            written = txn.collection(DOCS).insert({"slug": "a"}, return_new=True)
            assert txn.collection(DOCS).get(written["new"]["_key"]) == written["new"]
            assert txn.collection(DOCS).name == DOCS
            assert txn.aql.execute("RETURN 1") == []
            assert txn.aql.explain("RETURN 1") == {"query": "RETURN 1"}
            assert txn.transaction_id == "tx-1", "an attribute the handle does not define is the driver's"


class TestLeavingByAnExceptionAbortsAndPublishesNothing:
    def test_an_exception_in_the_body_aborts_and_propagates_unchanged(self):
        db = _db()
        failure = RuntimeError("the second write cannot be computed")

        with pytest.raises(RuntimeError) as caught, stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})
            raise failure

        tx = _tx(db)
        assert caught.value is failure
        assert tx.aborts == 1 and tx.commits == 0
        assert tx.published == {}, "the first write survived the failure of the second"
        assert tx.staged[DOCS], "the fake never staged the first write — the test proves nothing"

    def test_a_base_exception_aborts_too(self):
        """``KeyboardInterrupt`` is not an ``Exception``; a transaction left open on it is a lock held forever."""
        db = _db()

        with pytest.raises(KeyboardInterrupt), stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})
            raise KeyboardInterrupt

        assert _tx(db).aborts == 1 and _tx(db).commits == 0

    def test_a_domain_error_from_the_body_passes_through_as_itself(self):
        db = _db()
        refusal = KamerplanterError("already decided upstream", error_code="X", status_code=409)

        with pytest.raises(KamerplanterError) as caught, stream_transaction(db, write=[DOCS]):  # type: ignore[arg-type]
            raise refusal

        assert caught.value is refusal
        assert _tx(db).aborts == 1


class TestAConflictNeverLeavesTheBlockUntyped:
    @pytest.mark.parametrize(
        ("code", "expected"),
        [(1210, DuplicateError), (1200, WriteConflictError)],
        ids=["unique-constraint-violated", "write-write-conflict"],
    )
    def test_an_insert_rejection_is_typed_after_the_collection_and_aborts(self, code: int, expected: type[Exception]):
        db = _db(refuse={EDGES: _insert_error(code)})

        with pytest.raises(expected) as caught, stream_transaction(db, write=[DOCS, EDGES]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})
            txn.collection(EDGES).insert({"_from": "a", "_to": "b"})

        tx = _tx(db)
        assert tx.aborts == 1 and tx.commits == 0 and tx.published == {}
        assert EDGES in caught.value.message, "the error names the collection that was refused, not the first one"
        assert isinstance(caught.value.__cause__, DocumentInsertError)

    def test_a_duplicate_names_the_real_field_and_the_colliding_value(self):
        """What the per-write translation buys over the generic one: the field the server named, and its value.

        The message fixture of ``_insert_error`` names ``_from`` as the violated index.
        """
        db = _db(refuse={DOCS: _insert_error(1210)})

        with pytest.raises(DuplicateError) as caught, stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"_from": "plant_instances/42", "slug": "taken"})

        assert caught.value.details[0]["field"] == "_from"
        assert "plant_instances/42" in caught.value.message

    def test_an_update_rejection_is_typed_with_the_collection_too(self):
        """WP 4.3 (task completion) updates with a ``_rev`` fence; the loser's 1200 must name the collection."""
        error = DocumentUpdateError(_Response(1200, "conflict, _rev check failed"), _Request())
        db = _db(refuse={DOCS: error})

        with pytest.raises(WriteConflictError) as caught, stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).update({"_key": "k1", "status": "completed"})

        assert DOCS in caught.value.message
        assert caught.value.__cause__ is error
        assert _tx(db).aborts == 1 and _tx(db).commits == 0

    def test_a_bulk_write_raises_on_the_first_refused_document_instead_of_committing_the_rest(self):
        """python-arango returns per-document errors inline by default; the handle forces it to raise."""
        db = _db(refuse={DOCS: _insert_error(1210)})

        with pytest.raises(DuplicateError), stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert_many(
                [{"slug": "a"}, {"slug": "taken"}, {"slug": "c"}],
                raise_on_document_error=False,  # the caller's choice is overridden, not honoured
            )

        tx = _tx(db)
        assert tx.bulk_kwargs["raise_on_document_error"] is True
        assert tx.commits == 0 and tx.aborts == 1 and tx.published == {}

    def test_a_bulk_write_without_a_refusal_commits_all_of_it(self):
        db = _db()

        with stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert_many([{"slug": "a"}, {"slug": "b"}])

        assert [doc["slug"] for doc in _tx(db).published[DOCS]] == ["a", "b"]

    def test_an_unrecognised_driver_code_keeps_propagating_unchanged(self):
        """Only 1200/1210 are answers a caller can resolve; everything else stays the driver's failure."""
        db = _db(refuse={DOCS: _insert_error(1104)})

        with pytest.raises(DocumentInsertError), stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})

        assert _tx(db).aborts == 1

    @pytest.mark.parametrize(
        ("code", "expected"),
        [(1210, DuplicateError), (1200, WriteConflictError)],
        ids=["unique-constraint-violated", "write-write-conflict"],
    )
    def test_a_conflict_the_server_defers_to_the_commit_is_typed_too(self, code: int, expected: type[Exception]):
        """Not reached on a single server in any measurement here, but the server's choice, not ours (#1292)."""
        db = _db(commit_error=_commit_error(code))

        with pytest.raises(expected) as caught, stream_transaction(db, write=[DOCS, EDGES]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})

        tx = _tx(db)
        assert tx.commits == 1, "the commit was attempted exactly once"
        assert tx.aborts == 1, "a refused commit is still followed by the abort"
        assert DOCS in caught.value.message, "the default entity is the first write collection"

    def test_a_conflict_raised_by_an_aql_statement_is_typed_on_the_way_out(self):
        """The generic arm: no collection or document in hand, but still never a raw 409."""
        error = AQLQueryExecuteError(_Response(1200, "conflict"), _Request())
        db = _db(aql_error=error)

        with (
            pytest.raises(WriteConflictError) as caught,
            stream_transaction(db, write=[DOCS], entity="plan") as txn,  # type: ignore[arg-type]
        ):
            txn.aql.execute("UPDATE ...")

        assert caught.value.__cause__ is error
        assert "plan" in caught.value.message
        assert _tx(db).aborts == 1

    @pytest.mark.parametrize("code", [18, 1200, 1203], ids=["lock-timeout", "conflict-at-begin", "no-collection"])
    def test_a_transaction_that_could_not_be_opened_is_never_a_conflict(self, code: int):
        """A write that never started is not a write the data refused.

        ``v0048_backfill_missing_care_profiles._persist`` counts ``WriteConflictError``
        as "the edge is already taken" and must never count a transaction the server
        refused to open as that — so a ``begin`` failure, whatever its code, stays
        the driver's ``TransactionInitError``, as it did before the helper existed.
        """
        error = TransactionInitError(_Response(code, "cannot begin transaction"), _Request())
        db = _db(init_error=error)

        with (
            pytest.raises(TransactionInitError) as caught,
            stream_transaction(db, write=[DOCS], exclusive=[DOCS]),  # type: ignore[arg-type]
        ):
            pytest.fail("the body ran although no transaction was opened")

        assert caught.value is error
        assert db.transaction is None

    def test_conflict_error_for_answers_none_for_everything_else(self):
        assert conflict_error_for(_insert_error(1104), entity=DOCS) is None
        assert conflict_error_for(_insert_error(1202), entity=DOCS) is None


class TestTheTimeBudget:
    def test_a_body_that_outran_the_budget_is_aborted_instead_of_committed(self):
        db = _db()
        clock = _Clock()

        with (
            pytest.raises(TransactionTimeBudgetExceededError) as caught,
            stream_transaction(db, write=[DOCS], time_budget_seconds=10, clock=clock) as txn,  # type: ignore[arg-type]
        ):
            txn.collection(DOCS).insert({"slug": "a"})
            clock.advance(10.5)

        tx = _tx(db)
        assert tx.commits == 0 and tx.aborts == 1 and tx.published == {}
        assert caught.value.status_code == 422
        assert caught.value.error_code == "TRANSACTION_TIME_BUDGET_EXCEEDED"
        assert "10.50 s" in caught.value.message and "10 s" in caught.value.message

    def test_a_body_inside_the_budget_commits(self):
        db = _db()
        clock = _Clock()

        with stream_transaction(db, write=[DOCS], time_budget_seconds=10, clock=clock) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})
            clock.advance(9.9)
            assert txn.remaining_seconds() == pytest.approx(0.1)
            assert not txn.over_budget()

        assert _tx(db).commits == 1

    def test_the_body_can_stop_early_through_check_budget(self):
        """A batch loop asks between operations rather than doing all 500 and then being refused."""
        db = _db()
        clock = _Clock()
        performed = 0

        with (
            pytest.raises(TransactionTimeBudgetExceededError),
            stream_transaction(db, write=[DOCS], time_budget_seconds=1, clock=clock) as txn,  # type: ignore[arg-type]
        ):
            for _ in range(500):
                txn.check_budget()
                txn.collection(DOCS).insert({"slug": "a"})
                performed += 1
                clock.advance(0.3)

        assert performed == 4, "check_budget let the loop run on after the budget was spent"
        assert _tx(db).aborts == 1 and _tx(db).commits == 0

    def test_an_aql_statement_carries_the_remaining_budget_to_the_server(self):
        """One long query is cut off by ``maxRuntime`` rather than run to completion and then refused."""
        db = _db()
        clock = _Clock()

        with stream_transaction(db, write=[DOCS], time_budget_seconds=10, clock=clock) as txn:  # type: ignore[arg-type]
            clock.advance(4)
            txn.aql.execute("RETURN 1")
            txn.aql.execute("RETURN 2", max_runtime=1.5)

        calls = _tx(db).aql.calls
        assert calls[0]["max_runtime"] == pytest.approx(6.0)
        assert calls[1]["max_runtime"] == 1.5, "a limit the caller chose is kept"

    def test_an_aql_statement_after_the_budget_is_refused_before_it_is_sent(self):
        db = _db()
        clock = _Clock()

        with (
            pytest.raises(TransactionTimeBudgetExceededError),
            stream_transaction(db, write=[DOCS], time_budget_seconds=1, clock=clock) as txn,  # type: ignore[arg-type]
        ):
            clock.advance(2)
            txn.aql.execute("RETURN 1")

        assert _tx(db).aql.calls == [], "the statement was sent although the budget was spent"
        assert _tx(db).aborts == 1

    def test_a_query_the_server_killed_for_the_budget_is_the_budget_error(self):
        killed = AQLQueryExecuteError(_Response(1500, "query killed"), _Request())
        db = _db(aql_error=killed)

        with (
            pytest.raises(TransactionTimeBudgetExceededError) as caught,
            stream_transaction(db, write=[DOCS]) as txn,  # type: ignore[arg-type]
        ):
            txn.aql.execute("FOR i IN 1..1e9 RETURN i")

        assert caught.value.__cause__ is killed
        assert _tx(db).aborts == 1 and _tx(db).commits == 0

    def test_a_query_killed_under_the_callers_own_limit_stays_the_drivers_error(self):
        db = _db(aql_error=AQLQueryExecuteError(_Response(1500, "query killed"), _Request()))

        with pytest.raises(AQLQueryExecuteError), stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.aql.execute("FOR i IN 1..1e9 RETURN i", max_runtime=0.5)

    @pytest.mark.parametrize("budget", [0, -1, float("nan"), float("inf")])
    def test_a_budget_that_is_not_a_positive_finite_number_is_refused_before_anything_is_opened(self, budget: float):
        db = _db()

        with (
            pytest.raises(ValueError, match="positive finite"),
            stream_transaction(db, write=[DOCS], time_budget_seconds=budget),  # type: ignore[arg-type]
        ):
            pass

        assert db.transaction is None and db.begin_kwargs == {}

    def test_an_empty_write_declaration_is_refused_before_anything_is_opened(self):
        db = _db()

        with pytest.raises(ValueError, match="write collection"), stream_transaction(db, write=[]):  # type: ignore[arg-type]
            pass

        assert db.transaction is None


class TestAFailingAbortNeverMasksTheRealError:
    def test_the_caller_still_sees_the_conflict(self):
        """The abort is cleanup; the conflict is the answer. A dropped connection is a plain ``ConnectionError``."""
        db = _db(refuse={DOCS: _insert_error(1210)}, abort_error=ConnectionError("connection reset"))

        with pytest.raises(DuplicateError), stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            txn.collection(DOCS).insert({"slug": "a"})

        assert _tx(db).aborts == 1

    def test_the_caller_still_sees_the_budget_error(self):
        db = _db(abort_error=ConnectionError("connection reset"))
        clock = _Clock()

        with (
            pytest.raises(TransactionTimeBudgetExceededError),
            stream_transaction(db, write=[DOCS], time_budget_seconds=1, clock=clock),  # type: ignore[arg-type]
        ):
            clock.advance(2)

        assert _tx(db).aborts == 1 and _tx(db).commits == 0


class TestTheHandleIsNotTheDriver:
    def test_the_body_cannot_commit_or_abort_on_its_own(self):
        """Both are the context manager's job; a second commit is what the server refuses outright.

        Every other driver attribute IS reachable through the handle (``transaction_id``
        above), so this is a named refusal, not an accident of a missing method.
        """
        db = _db()

        with stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            assert isinstance(txn, StreamTransaction)
            for forbidden in ("commit_transaction", "abort_transaction", "begin_transaction"):
                with pytest.raises(AttributeError, match="context manager"):
                    getattr(txn, forbidden)()
            assert _tx(db).commits == 0

        assert _tx(db).commits == 1, "only the context manager committed, and once"

    def test_private_lookups_never_fall_through_to_the_driver(self):
        """``copy``/``pickle`` probe for dunders before the slots exist; delegating them would recurse."""
        db = _db()

        with stream_transaction(db, write=[DOCS]) as txn:  # type: ignore[arg-type]
            with pytest.raises(AttributeError):
                _ = txn.collection(DOCS)._missing
            with pytest.raises(AttributeError):
                _ = txn.aql._missing
