"""Integration test for MT-032 (#2128) — the due-care selection runs in AQL, measured on the server.

The notification beats used to read the whole ``tasks`` collection of every tenant
and pick out the open care reminders of the day in Python. They now ask
``ArangoTaskRepository.list_open_care_reminders_due`` per tenant, and the unit tests
drive them through ``tests/support/care_reminder_store.CareReminderStore``, a double
that claims the same semantics. This file holds the real query to that claim: tenant,
category, open status, the inclusive window compared as instants (an offset is read,
a stored value without one is UTC), and an open lower bound for the overdue summary.

Run with: pytest tests/integration/test_care_reminders_due_query.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_reminder_store import CareReminderStore

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2128 measures the AQL due-care selection; the double claims its semantics"),
]

_DB_NAME = run_database_name("care_reminders_due")

START = datetime(2026, 10, 11, tzinfo=UTC)
END = datetime(2026, 10, 11, 23, 59, 59, tzinfo=UTC)


def _row(key: str, due: str | None, *, tenant: str = "t1", category: str = "care_reminder", status: str = "pending"):
    return {
        "_key": key,
        "tenant_key": tenant,
        "name": f"{key} — watering",
        "category": category,
        "status": status,
        "due_date": due,
    }


ROWS = [
    _row("due_morning", "2026-10-11T06:00:00+00:00"),
    _row("due_z_suffix", "2026-10-11T12:00:00Z"),
    _row("due_naive_utc", "2026-10-11T12:00:00"),  # no offset: UTC, as the beats read it
    _row("due_first_second", "2026-10-11T00:00:00+00:00"),  # inclusive lower bound
    _row("due_last_second", "2026-10-11T23:59:59+00:00"),  # inclusive upper bound
    _row("due_in_progress", "2026-10-11T08:00:00+00:00", status="in_progress"),
    # 01:00 at +02:00 is 23:00 UTC of the day BEFORE — a string prefix would call it today
    _row("offset_yesterday", "2026-10-11T01:00:00+02:00"),
    _row("overdue", "2026-10-09T06:00:00+00:00"),
    _row("tomorrow", "2026-10-12T00:00:00+00:00"),
    _row("completed", "2026-10-11T06:00:00+00:00", status="completed"),
    _row("skipped", "2026-10-11T06:00:00+00:00", status="skipped"),
    _row("not_care", "2026-10-11T06:00:00+00:00", category="maintenance"),
    _row("no_due_date", None),
    _row("unparseable", "soon"),
    _row("other_tenant", "2026-10-11T06:00:00+00:00", tenant="t2"),
]

TODAY = {
    "due_morning",
    "due_z_suffix",
    "due_naive_utc",
    "due_first_second",
    "due_last_second",
    "due_in_progress",
}


@pytest.fixture(scope="module")
def repo():
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.collections import ensure_collections
    from app.data_access.arango.connection import ArangoConnection
    from app.data_access.arango.task_repository import ArangoTaskRepository

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    database = conn.connect()
    ensure_collections(database)
    database.collection(col.TASKS).insert_many(ROWS, overwrite=True)
    yield ArangoTaskRepository(database)
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


def _keys(tasks) -> set[str]:
    return {t.key for t in tasks}


def test_the_day_window_selects_exactly_the_open_care_reminders_due_that_day(repo) -> None:
    assert _keys(repo.list_open_care_reminders_due(tenant_key="t1", due_from=START, due_until=END)) == TODAY


def test_an_open_lower_bound_adds_the_overdue_ones(repo) -> None:
    selected = _keys(repo.list_open_care_reminders_due(tenant_key="t1", due_until=END))

    assert selected == TODAY | {"overdue", "offset_yesterday"}


def test_another_tenants_reminder_is_not_selected(repo) -> None:
    assert _keys(repo.list_open_care_reminders_due(tenant_key="t2", due_from=START, due_until=END)) == {"other_tenant"}


def test_an_empty_tenant_key_is_refused_before_the_query(repo) -> None:
    with pytest.raises(ValueError, match="tenant_key"):
        repo.list_open_care_reminders_due(tenant_key="", due_until=END)


@pytest.mark.parametrize("due_from", [START, None])
def test_the_unit_test_double_answers_like_the_server(repo, due_from) -> None:
    """``CareReminderStore`` stands in for this query in every beat unit test; it must not answer differently."""
    for tenant in ("t1", "t2"):
        server = _keys(repo.list_open_care_reminders_due(tenant_key=tenant, due_from=due_from, due_until=END))
        double = {
            r["_key"]
            for r in CareReminderStore(ROWS).list_open_care_reminders_due(
                tenant_key=tenant, due_from=due_from, due_until=END
            )
        }
        assert double == server
