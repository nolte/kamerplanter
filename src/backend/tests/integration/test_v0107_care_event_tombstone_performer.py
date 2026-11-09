"""#2770 — v0107 replaces erased-account tombstones in ``care_events.performed_by_user_key`` (real ArangoDB).

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0107_care_event_tombstone_performer.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, TOMBSTONE_FULLMATCH_REGEX
from app.migrations.versions import v0107_care_event_tombstone_performer as v0107
from app.migrations.versions.v0107_care_event_tombstone_performer import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the correction is one AQL update over a real server"),
]

_DB_NAME = run_database_name("v0107_care_event_tombstone_performer")
TOMBSTONE = "anon_0123456789abcdef"


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    database.collection(col.CARE_EVENTS).insert_many(
        [
            {"_key": "e_tomb", "tenant_key": "t1", "performed_by_user_key": TOMBSTONE},
            {"_key": "e_user", "tenant_key": "t1", "performed_by_user_key": "u1"},
            {"_key": "e_marker", "tenant_key": "t1", "performed_by_user_key": ANONYMIZED_MARKER},
            {"_key": "e_near", "tenant_key": "t1", "performed_by_user_key": "anon_0123"},
            {"_key": "e_none", "tenant_key": "t1", "performed_by_user_key": None},
        ]
    )
    yield database
    system.delete_database(_DB_NAME)


def _performers(db) -> dict[str, object]:  # type: ignore[no-untyped-def]
    return {d["_key"]: d.get("performed_by_user_key") for d in db.collection(col.CARE_EVENTS).all()}


def test_the_frozen_shape_and_marker_match_the_erasure_engine_at_the_time_of_writing() -> None:
    assert v0107._TOMBSTONE_REGEX == TOMBSTONE_FULLMATCH_REGEX
    assert v0107._MARKER == ANONYMIZED_MARKER


def test_the_dry_run_counts_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    assert report.details == {"will_replace": 1}
    assert _performers(db)["e_tomb"] == TOMBSTONE


def test_only_a_tombstone_is_replaced_and_a_second_run_changes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert report.changed == 1
    assert _performers(db) == {
        "e_tomb": ANONYMIZED_MARKER,
        "e_user": "u1",
        "e_marker": ANONYMIZED_MARKER,
        "e_near": "anon_0123",
        "e_none": None,
    }
    assert migration.up(db).changed == 0
