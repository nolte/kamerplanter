"""#1533 — ``find_open_task_by_name`` against a real ArangoDB.

The unit tests of the beat tasks answer this predicate with an in-memory double.
A double cannot be wrong about AQL, which is the part that decides whether a beat
run creates a duplicate or suppresses a legitimate task, so the predicate itself is
measured here: tenant scope, exact name, open status, and — the property the
replaced ``get_all_tasks(0, 200, …)`` page did not have — an answer that does not
depend on a page size.

Needs a real ArangoDB (``tests/integration/conftest.py``); missing is a failure in
CI and a loud skip locally.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

TEST_DATABASE = "kp_test_open_task_by_name"
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"
NAME = "maintenance:water_change:tank_1"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    database.create_collection(col.TASKS)
    yield database
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def repo(db):
    return ArangoTaskRepository(db)


def _insert(db, *, key: str, name: str = NAME, tenant: str = TENANT, status: str = "pending", due_days: int = 0):
    db.collection(col.TASKS).insert(
        {
            "_key": key,
            "name": name,
            "instruction": "seeded",
            "category": "maintenance",
            "tenant_key": tenant,
            "status": status,
            "due_date": (datetime.now(UTC) + timedelta(days=due_days)).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        }
    )


def test_an_open_task_of_the_tenant_is_found(db, repo) -> None:
    _insert(db, key="t1")

    found = repo.find_open_task_by_name(NAME, tenant_key=TENANT)

    assert found is not None
    assert found.key == "t1"


def test_a_foreign_tenants_task_is_invisible(db, repo) -> None:
    """The cross-tenant half of #1533, asked of the store itself."""
    _insert(db, key="t1", tenant=OTHER_TENANT)

    assert repo.find_open_task_by_name(NAME, tenant_key=TENANT) is None


@pytest.mark.parametrize("status", ["completed", "skipped", "failed", "dormant"])
def test_a_closed_task_does_not_answer_the_idempotency_question(db, repo, status: str) -> None:
    """Every ``TaskStatus`` that is not pending/in_progress, spelled from the enum.

    The values are the real ones (``app.common.enums.TaskStatus``) rather than
    plausible-looking strings: a status the store can never hold would make this a
    case that certifies nothing.
    """
    _insert(db, key="t1", status=status)

    assert repo.find_open_task_by_name(NAME, tenant_key=TENANT) is None


def test_in_progress_counts_as_open(db, repo) -> None:
    _insert(db, key="t1", status="in_progress")

    assert repo.find_open_task_by_name(NAME, tenant_key=TENANT) is not None


def test_a_different_name_does_not_match(db, repo) -> None:
    _insert(db, key="t1", name="maintenance:water_change:tank_2")

    assert repo.find_open_task_by_name(NAME, tenant_key=TENANT) is None


def test_the_match_is_found_behind_hundreds_of_other_tasks(db, repo) -> None:
    """The cap-then-filter half: no page size stands between caller and answer.

    The replaced code paged 200 maintenance tasks ordered by ``due_date`` ascending
    and narrowed them in Python. The match here sorts *last* by that order, so it
    was exactly what fell off the page — and the beat run then created a duplicate
    on every pass.
    """
    for i in range(250):
        _insert(db, key=f"filler-{i}", name=f"maintenance:other:{i}", due_days=i)
    _insert(db, key="match", due_days=999)

    found = repo.find_open_task_by_name(NAME, tenant_key=TENANT)

    assert found is not None
    assert found.key == "match"


def test_an_empty_tenant_key_is_refused_rather_than_answered_globally(db, repo) -> None:
    _insert(db, key="t1", tenant=OTHER_TENANT)

    with pytest.raises(ValueError, match="tenant"):
        repo.find_open_task_by_name(NAME, tenant_key="")


def test_get_all_tasks_refuses_the_empty_tenant_sentinel(db, repo) -> None:
    """The surface repair: unscoped is not a spelling of this call any more."""
    _insert(db, key="t1", tenant=OTHER_TENANT)

    with pytest.raises(ValueError, match="tenant"):
        repo.get_all_tasks(0, 50, None, tenant_key="")
