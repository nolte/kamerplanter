"""#3135 — ``find_overdue_watering`` keys on the announced due date, against a real ArangoDB.

The statement used to select by the row's ``created_at`` and by the type prefix
``care.watering``. The care row is reused across occurrences and keeps its
creation time, so a reminder for the *next* watering — or one retimed into the
future — was escalated as overdue at once; the prefix also took the escalation
rows themselves. Every case of ``tests/support/overdue_watering_cases.py`` is
seeded as a stored document and the real statement is asked, against every cutoff
spelling; the unit fake is held to the same table
(``test_overdue_watering_fake_matches_the_case_table``).

No personal data: every value is synthetic.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.notification_repository import ArangoNotificationRepository
from app.domain.engines.notification_engine import overdue_cutoff
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.overdue_watering_cases import CASES, CUTOFF, CUTOFF_SPELLINGS, LEVEL, TENANT, Case, document

TEST_DATABASE = run_database_name("overdue_watering")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.NOTIFICATIONS)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase) -> StandardDatabase:
    database.collection(col.NOTIFICATIONS).truncate()
    return database


def _selected(db: StandardDatabase, cutoff: datetime, *, tenant_key: str = TENANT) -> set[str]:
    return {
        n.key or ""
        for n in ArangoNotificationRepository(db).find_overdue_watering(cutoff, LEVEL, tenant_key=tenant_key)
    }


@pytest.mark.parametrize("cutoff", CUTOFF_SPELLINGS)
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_overdue_watering_candidates(db: StandardDatabase, case: Case, cutoff: str) -> None:
    db.collection(col.NOTIFICATIONS).insert(document(case))

    assert (case.name in _selected(db, datetime.fromisoformat(cutoff))) is case.selected, case.why


def test_all_cases_in_one_collection_select_exactly_the_expected_rows(db: StandardDatabase) -> None:
    """The cases side by side: no clause leaks between documents."""
    db.collection(col.NOTIFICATIONS).insert_many([document(case) for case in CASES])

    assert _selected(db, CUTOFF) == {case.name for case in CASES if case.selected}
    assert _selected(db, CUTOFF, tenant_key="") == set()


@pytest.mark.parametrize("days", [2, 4, 7])
def test_the_engines_own_cutoff_selects_a_reminder_due_that_many_days_ago(db: StandardDatabase, days: int) -> None:
    """A positive case against the cutoff exactly as production builds it.

    Every other assertion could stay green while the engine handed ArangoDB a
    cutoff ``DATE_TIMESTAMP`` cannot read — then nothing is ever "before" it and
    production never escalates. This one cannot.
    """
    today = date(2026, 11, 20)
    due_day = date.fromordinal(today.toordinal() - days)
    on_time = {**document(CASES[0]), "_key": "due-that-day", "data": {"due_date": f"{due_day}T23:30:00+00:00"}}
    not_yet = {
        **document(CASES[0]),
        "_key": "due-a-day-later",
        "data": {"due_date": f"{date.fromordinal(due_day.toordinal() + 1)}T00:00:00+00:00"},
    }
    db.collection(col.NOTIFICATIONS).insert_many([on_time, not_yet])

    assert _selected(db, overdue_cutoff(today, days)) == {"due-that-day"}
