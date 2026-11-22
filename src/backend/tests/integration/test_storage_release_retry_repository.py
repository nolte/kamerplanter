"""#2630 — owed object releases stored in ArangoDB (owed releases merge per object, due order, settle, failed again).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_storage_release_retry_repository.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.storage_release_retry_repository import ArangoStorageReleaseRetryRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the owed releases are stored in a real collection"),
]

_DB_NAME = run_database_name("storage_release_retries")
MAIN = "t/t1/underlay/2026/11/abc.jpg"
THUMB = "t/t1/underlay/2026/11/abc.thumb.webp"


@pytest.fixture
def repo():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield ArangoStorageReleaseRetryRepository(database), database
    system.delete_database(_DB_NAME)


def test_a_second_failure_for_the_same_object_merges_into_one_row(repo) -> None:  # type: ignore[no-untyped-def]
    store, db = repo

    store.owe_release(tenant_key="t1", object_keys=[MAIN])
    store.owe_release(tenant_key="t1", object_keys=[MAIN, THUMB])

    (owed,) = store.due(10)
    assert set(owed.object_keys) == {MAIN, THUMB}
    assert owed.tenant_key == "t1" and owed.attempts == 0 and owed.created_at
    assert db.collection(col.STORAGE_RELEASE_RETRIES).count() == 1


def test_a_failed_attempt_is_counted_and_a_resolved_one_is_gone(repo) -> None:  # type: ignore[no-untyped-def]
    store, _ = repo
    store.owe_release(tenant_key="t1", object_keys=[MAIN])
    (owed,) = store.due(10)

    store.release_failed_again(owed.key)
    store.release_failed_again(owed.key)
    assert store.due(10)[0].attempts == 2

    store.settle_release(owed.key)
    assert store.due(10) == []
    store.settle_release(owed.key)  # idempotent
