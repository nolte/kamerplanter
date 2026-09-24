"""#1664 — an erasure without a user key writes nothing.

The executor filters every step by ``doc[@field] == @user_key``. Rows that were
never attributed carry an empty key — ``pest_detections.user_key`` defaults to
``""``, a diary entry imported without an author has ``created_by == ""`` — so a
plan whose ``user_key`` is ``""`` does not erase "nobody": it deletes every such
detection and anonymises every such diary entry, all of them other users' data.

The unit tier pins that the executor refuses the plan. Only a real server can
show that the refusal happens *before* the write, so this seeds exactly those
unattributed rows, hands the executor a plan with an empty key (``model_copy``
skips the model's own refusal, the way a caller that assembles a plan would),
and reads the rows back.

Runs in CI against a service container; locally it needs a database::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_erasure_empty_user_key.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.domain.engines.erasure_engine import ErasureEngine
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("privacy_erasure_empty_key")
#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "empty-key-test-salt-not-a-secret-012345"
TENANT = "t-empty-key"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    yield client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    system.delete_database(TEST_DATABASE)


def _unattributed_rows(database) -> dict[str, dict]:
    """One row per collection that a ``""`` key would reach; returns their ids with content."""
    plan = ErasureEngine().build_erasure_plan("seed-only")
    detections = next(step for step in plan.steps if step.collection == "pest_detections")
    diary = next(rule for rule in plan.anonymize if rule.collection == "plant_diary_entries")
    users = next(step.collection for step in plan.steps if step.kind == "user")
    rows = {
        detections.collection: {"_key": "unattributed", detections.user_field: "", "tenant_key": TENANT},
        diary.collection: {"_key": "unattributed", diary.user_field: "", "tenant_key": TENANT, "text": "kept"},
        users: {"_key": "someone-else", "email": "someone-else@example.com"},
    }
    ids: dict[str, dict] = {}
    for collection, doc in rows.items():
        if not database.has_collection(collection):
            database.create_collection(collection)
        inserted = database.collection(collection).insert(doc)
        ids[inserted["_id"]] = database.collection(collection).get(inserted["_key"])
    return ids


def _read(database, doc_id: str) -> dict | None:
    collection, key = doc_id.split("/", 1)
    return database.collection(collection).get(key)


@pytest.mark.parametrize("user_key", ["", "   "])
def test_an_empty_user_key_is_refused_and_no_foreign_row_is_touched(database, user_key):
    before = _unattributed_rows(database)
    plan = ErasureEngine().build_erasure_plan("placeholder").model_copy(update={"user_key": user_key})

    with pytest.raises(ValueError, match="user key"):
        ArangoErasureExecutor(database).run_erasure_plan(
            plan, tombstone=ErasureEngine.compute_tombstone_hash(user_key, SALT)
        )

    after = {doc_id: _read(database, doc_id) for doc_id in before}
    assert after == before
