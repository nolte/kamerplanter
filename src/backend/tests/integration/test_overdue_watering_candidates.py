"""#3135 — ``find_overdue_watering`` keys on the announced due date, against a real ArangoDB.

The statement used to select by the row's ``created_at`` and by the type prefix
``care.watering``. The care row is reused across occurrences and keeps its
creation time, so a reminder for the *next* watering — or one retimed into the
future — was escalated as overdue at once; the prefix also took the escalation
rows themselves. Every case of ``tests/support/overdue_watering_cases.py`` is
seeded as a stored document and the real statement is asked; the unit fake is
held to the same table (``test_overdue_watering_fake_matches_the_case_table``).

No personal data: every value is synthetic.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.notification_repository import ArangoNotificationRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.overdue_watering_cases import CASES, CUTOFF, LEVEL, TENANT, Case, document

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


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_overdue_watering_candidates(db: StandardDatabase, case: Case) -> None:
    db.collection(col.NOTIFICATIONS).insert(document(case))

    selected = {n.key for n in ArangoNotificationRepository(db).find_overdue_watering(CUTOFF, LEVEL, tenant_key=TENANT)}

    assert (case.name in selected) is case.selected, case.why


def test_all_cases_in_one_collection_select_exactly_the_expected_rows(db: StandardDatabase) -> None:
    """The cases side by side: no clause leaks between documents."""
    db.collection(col.NOTIFICATIONS).insert_many([document(case) for case in CASES])

    selected = {n.key for n in ArangoNotificationRepository(db).find_overdue_watering(CUTOFF, LEVEL, tenant_key=TENANT)}

    assert selected == {case.name for case in CASES if case.selected}
    assert ArangoNotificationRepository(db).find_overdue_watering(CUTOFF, LEVEL, tenant_key="") == []
