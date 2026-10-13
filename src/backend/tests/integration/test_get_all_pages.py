"""Integration test for #2012 — ``get_all_pages`` against a real ArangoDB.

A beat task used to call ``get_all(offset=0, limit=1000, all_tenants=True)`` once and
treat the page as the collection. The helper that replaced that read is only as good
as the real ``get_all`` contract it relies on: rows sorted by ``_key``, ``offset``
/ ``limit`` honoured by the AQL ``LIMIT``, and ``total`` counting the *whole*
collection (not the page). A repository double is free to invent any of the three,
so this file measures them against the server.

Run with: pytest tests/integration/test_get_all_pages.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2012 measures the real get_all paging contract; no double may answer it"),
]

_DB_NAME = run_database_name("get_all_pages")
_ROWS = 2105  # two full pages of 1000 plus a partial one, across two tenants


@pytest.fixture(scope="module")
def db():
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.collections import ensure_collections
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    database = conn.connect()
    ensure_collections(database)
    database.collection(col.TASKS).insert_many(
        [{"_key": f"t{i:05d}", "tenant_key": f"tenant{i % 2}", "name": f"Task {i}"} for i in range(_ROWS)],
        overwrite=True,
    )
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


def test_one_page_is_not_the_collection(db):
    """The premise of #2012, measured: a 1000-row window of a 2105-row collection."""
    from app.data_access.arango.task_repository import ArangoTaskRepository

    page, total = ArangoTaskRepository(db).get_all(offset=0, limit=1000, all_tenants=True)

    assert (len(page), total) == (1000, _ROWS)


def test_get_all_pages_returns_every_row_once_in_key_order(db):
    from app.data_access.arango.base_repository import get_all_pages
    from app.data_access.arango.task_repository import ArangoTaskRepository

    rows = get_all_pages(ArangoTaskRepository(db), all_tenants=True)

    assert [r.key for r in rows] == [f"t{i:05d}" for i in range(_ROWS)]


def test_get_all_pages_honours_a_tenant_scope(db):
    from app.data_access.arango.base_repository import get_all_pages
    from app.data_access.arango.task_repository import ArangoTaskRepository

    rows = get_all_pages(ArangoTaskRepository(db), tenant_key="tenant1", page_size=500)

    assert len(rows) == _ROWS // 2
    assert {r.tenant_key for r in rows} == {"tenant1"}
