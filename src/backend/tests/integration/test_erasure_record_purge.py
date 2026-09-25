"""#1772 — the NFR-011 R-06 purge of erasure records against a real ArangoDB.

``ArangoErasureRepository.delete_completed_before`` hard-deletes the
``erasure_requests`` records whose erasure **completed** before the cutoff, and
the ``requested_erasure`` edges that still point at them. A request that is
still owed a run — ``scheduled``, ``in_progress``, ``partially_completed`` — is
never selected, however old: deleting it would drop an Art. 17 duty, not a
proof. The unit tier runs the same predicate on ``FakeErasureRepo``; this file
measures whether the AQL does what the double assumes.

Two completed-old records are seeded on purpose: one written through
``create`` (the model's JSON form, ``…Z``) and one completed through
``update_fields`` the way :meth:`PrivacyService._mark_erasure` completes a
request (``isoformat``, ``…+00:00``). The cutoff is compared as a string, so
both spellings must be selected.

No personal data: every value is synthetic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.domain.models.privacy import ErasureRequest
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("erasure_record_purge")
NOW = datetime(2026, 9, 25, 4, 30, tzinfo=UTC)
CUTOFF = datetime(2025, 9, 25, 4, 30, tzinfo=UTC)
OLD = NOW - timedelta(days=400)
YOUNG = NOW - timedelta(days=100)

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in (col.ERASURE_REQUESTS, col.USERS):
        db.create_collection(name)
    db.create_collection(col.REQUESTED_ERASURE, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def seeded(database) -> dict[str, str]:
    """Seed one record per case; hand back ``name -> stored key``."""
    database.collection(col.ERASURE_REQUESTS).truncate()
    database.collection(col.REQUESTED_ERASURE).truncate()
    repo = ArangoErasureRepository(database)
    records = {
        "completed_old": ErasureRequest(user_key="tomb-completed-old", status="completed", completed_at=OLD),
        "completed_young": ErasureRequest(user_key="tomb-completed-young", status="completed", completed_at=YOUNG),
        "partial_old": ErasureRequest(user_key="tomb-partial-old", status="partially_completed", requested_at=OLD),
        "scheduled_old": ErasureRequest(user_key="tomb-scheduled-old", status="scheduled", requested_at=OLD),
        "in_progress_old": ErasureRequest(user_key="tomb-in-progress-old", status="in_progress", requested_at=OLD),
        "completed_old_via_update": ErasureRequest(user_key="tomb-completed-update", status="in_progress"),
    }
    keys = {name: repo.create(record).key for name, record in records.items()}
    # Completed the way the service completes a request: a named-field write.
    repo.update_fields(keys["completed_old_via_update"], {"status": "completed", "completed_at": OLD.isoformat()})
    return keys


def _edge_targets(database) -> set[str]:
    return {edge["_to"] for edge in database.collection(col.REQUESTED_ERASURE).all()}


class TestThePurge:
    def test_only_completed_records_past_the_cutoff_and_their_edges_go(self, database, seeded):
        repo = ArangoErasureRepository(database)
        purged = {seeded["completed_old"], seeded["completed_old_via_update"]}
        kept = set(seeded.values()) - purged
        assert _edge_targets(database) == {f"{col.ERASURE_REQUESTS}/{key}" for key in seeded.values()}

        removed = repo.delete_completed_before(CUTOFF.isoformat())

        assert removed == 2
        remaining = {doc["_key"] for doc in database.collection(col.ERASURE_REQUESTS).all()}
        assert remaining == kept
        assert _edge_targets(database) == {f"{col.ERASURE_REQUESTS}/{key}" for key in kept}

    def test_a_second_run_finds_nothing(self, database, seeded):
        repo = ArangoErasureRepository(database)

        assert repo.delete_completed_before(CUTOFF.isoformat()) == 2
        assert repo.delete_completed_before(CUTOFF.isoformat()) == 0

    def test_a_completed_record_without_a_completion_time_is_kept(self, database, seeded):
        repo = ArangoErasureRepository(database)
        undated = repo.create(ErasureRequest(user_key="tomb-undated", status="completed"))

        repo.delete_completed_before(CUTOFF.isoformat())

        assert repo.get_by_key(undated.key) is not None
