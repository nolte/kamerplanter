"""``stream_transaction`` against a real ArangoDB (REQ-053 WP 1.2, #2320).

The unit tier doubles the driver and pins the helper's contract; what no double can
decide is what the *server* does: that an aborted stream transaction leaves no
document behind, that nothing staged is visible to a second connection before the
commit, what a unique-index rejection inside the transaction does to the rest of
it, that ``maxRuntime`` really cuts a statement off inside a transaction, and that
a contended collection lock is refused at ``begin`` after ``lockTimeout``. Those are
measured here against a disposable collection in a run-scoped database (#1661).

**Falsification.** Every "nothing is there" assertion about the helper's own abort
is paired with a positive control that reads the same collection through the same
connection after a commit and finds the rows — so an empty answer cannot be the
reader being blind.

Run with: pytest tests/integration/ -v   (requires docker compose up arangodb)
"""

from __future__ import annotations

import itertools
import time

import pytest
from arango import ArangoClient

from app.common.exceptions import DuplicateError, TransactionTimeBudgetExceededError, WriteConflictError
from app.data_access.arango.transactions import stream_transaction
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("what the server does with an aborted stream transaction is the measurement"),
]

_DB_NAME = run_database_name("stream_transaction")
DOCS = "txn_docs"

#: A statement that cannot finish inside a sub-second ``maxRuntime``, yet costs
#: nothing once the server kills it. ``SLEEP`` rather than a large range: the
#: optimizer folds ``FOR i IN 1..N COLLECT WITH COUNT`` into a constant (measured —
#: 200 million iterations answered in well under a second).
_LONG_QUERY = "RETURN SLEEP(5)"


@pytest.fixture
def db(arango_db):
    """A run-scoped database with one disposable collection carrying a unique index on ``slug``."""
    if arango_db.has_database(_DB_NAME):
        arango_db.delete_database(_DB_NAME)
    arango_db.create_database(_DB_NAME)
    client = ArangoClient(hosts=ARANGO_URL)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    collection = database.create_collection(DOCS)
    collection.add_index({"type": "persistent", "fields": ["slug"], "unique": True})
    yield database
    client.close()
    arango_db.delete_database(_DB_NAME)


def _second_connection():
    """Another connection — what a concurrent request would read through."""
    client = ArangoClient(hosts=ARANGO_URL)
    return client, client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)


def _slugs(database) -> list[str]:
    return sorted(doc["slug"] for doc in database.collection(DOCS).all())


def _clock_reading(*readings: float):
    """A clock that answers the given readings in order and then repeats the last one."""
    return itertools.chain(readings[:-1], itertools.repeat(readings[-1])).__next__


class TestAnAbortLeavesNothingBehind:
    def test_a_failure_after_the_first_write_removes_it(self, db):
        with pytest.raises(RuntimeError), stream_transaction(db, write=[DOCS]) as txn:
            txn.collection(DOCS).insert({"slug": "first"})
            txn.collection(DOCS).insert({"slug": "second"})
            raise RuntimeError("the third write cannot be computed")

        assert _slugs(db) == [], "an aborted stream transaction left a document behind"

        # Positive control: the same reader finds what a commit published.
        with stream_transaction(db, write=[DOCS]) as txn:
            txn.collection(DOCS).insert({"slug": "first"})
            txn.collection(DOCS).insert({"slug": "second"})
        assert _slugs(db) == ["first", "second"]

    def test_a_body_over_its_budget_is_aborted_on_the_server_too(self, db):
        # Opened at 0 s; every later reading says 11 s — past a 10 s budget without sleeping.
        with (
            pytest.raises(TransactionTimeBudgetExceededError),
            stream_transaction(db, write=[DOCS], time_budget_seconds=10, clock=_clock_reading(0.0, 11.0)) as txn,
        ):
            txn.collection(DOCS).insert({"slug": "late"})

        assert _slugs(db) == []

        # Positive control: the same body inside its budget is committed.
        with stream_transaction(db, write=[DOCS], time_budget_seconds=10, clock=_clock_reading(0.0, 9.0)) as txn:
            txn.collection(DOCS).insert({"slug": "late"})
        assert _slugs(db) == ["late"]


class TestNothingIsVisibleBeforeTheCommit:
    def test_a_second_connection_sees_the_rows_only_after_the_commit(self, db):
        client, other = _second_connection()
        try:
            with stream_transaction(db, write=[DOCS]) as txn:
                txn.collection(DOCS).insert({"slug": "staged"})
                assert _slugs(other) == [], "a staged document was readable through another connection"
            assert _slugs(other) == ["staged"], "the positive control: the reader sees the commit"
        finally:
            client.close()


class TestAUniqueIndexRejectionInsideTheTransaction:
    def test_the_helpers_abort_removes_the_write_before_the_duplicate(self, db):
        """Measured: the server answers the second insert with ``1210``; the helper's abort takes the first with it."""
        db.collection(DOCS).insert({"slug": "taken"})

        with pytest.raises(DuplicateError) as caught, stream_transaction(db, write=[DOCS]) as txn:
            txn.collection(DOCS).insert({"slug": "fresh"})
            txn.collection(DOCS).insert({"slug": "taken"})

        assert caught.value.details[0]["field"] == "slug"
        assert "taken" in caught.value.message
        assert _slugs(db) == ["taken"], "the write before the duplicate survived the abort"

    def test_a_duplicate_caught_inside_the_body_does_not_end_the_transaction(self, db):
        """What a caller that adopts the winner (WP 4.3) relies on, measured rather than assumed.

        ArangoDB 3.12 rolls back only the refused operation: the transaction stays
        open, earlier writes stay staged, later writes are accepted and the commit
        publishes everything but the refused document. This is the contract a body
        may build on when it catches ``DuplicateError`` and carries on.
        """
        db.collection(DOCS).insert({"slug": "taken"})

        with stream_transaction(db, write=[DOCS]) as txn:
            txn.collection(DOCS).insert({"slug": "before"})
            with pytest.raises(DuplicateError):
                txn.collection(DOCS).insert({"slug": "taken"})
            txn.collection(DOCS).insert({"slug": "after"})

        assert _slugs(db) == ["after", "before", "taken"]


class TestTheBudgetReachesTheServer:
    def test_a_long_statement_is_killed_at_the_remaining_budget(self, db):
        """``maxRuntime`` inside a stream transaction: the server ends the query, the helper aborts and types it."""
        started = time.monotonic()
        with (
            pytest.raises(TransactionTimeBudgetExceededError),
            # 9.8 s of a 10 s budget already gone when the statement is issued: 0.2 s of maxRuntime.
            stream_transaction(db, write=[DOCS], time_budget_seconds=10, clock=_clock_reading(0.0, 9.8)) as txn,
        ):
            txn.collection(DOCS).insert({"slug": "doomed"})
            txn.aql.execute(_LONG_QUERY)

        assert time.monotonic() - started < 5, "the statement ran to completion instead of being killed"
        assert _slugs(db) == []


class TestAContendedCollectionLock:
    def test_an_exclusive_lock_held_elsewhere_is_a_write_conflict_after_the_lock_timeout(self, db):
        """Two exclusive declarations on one collection: the second waits ``lockTimeout`` (budget / 2), then 409."""
        client, other = _second_connection()
        holder = other.begin_transaction(exclusive=[DOCS])
        try:
            started = time.monotonic()
            with (
                pytest.raises(WriteConflictError) as caught,
                stream_transaction(db, write=[DOCS], exclusive=[DOCS], time_budget_seconds=2),
            ):
                pytest.fail("the body ran although the lock is held elsewhere")
            waited = time.monotonic() - started
        finally:
            holder.abort_transaction()
            client.close()

        assert "lock" in caught.value.details[0]["reason"]
        assert 0.5 < waited < 10, f"the lock wait ({waited:.1f} s) is not the derived lockTimeout of 1 s"
