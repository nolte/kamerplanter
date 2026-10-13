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
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ErasureRequest
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("erasure_record_purge")
NOW = datetime(2026, 9, 25, 4, 30, tzinfo=UTC)
CUTOFF = datetime(2025, 9, 25, 4, 30, tzinfo=UTC)
OLD = NOW - timedelta(days=400)
YOUNG = NOW - timedelta(days=100)
SALT = "purge-integration-salt-not-a-secret-0123"


def _tomb(name: str) -> str:
    """A real tombstone: a completed erasure rewrote ``user_key`` to one (GDPR-006)."""
    return ErasureEngine.compute_tombstone_hash(name, SALT)


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
        "completed_old": ErasureRequest(user_key=_tomb("completed-old"), status="completed", completed_at=OLD),
        "completed_young": ErasureRequest(user_key=_tomb("completed-young"), status="completed", completed_at=YOUNG),
        "partial_old": ErasureRequest(user_key=_tomb("partial-old"), status="partially_completed", requested_at=OLD),
        "scheduled_old": ErasureRequest(user_key=_tomb("scheduled-old"), status="scheduled", requested_at=OLD),
        "in_progress_old": ErasureRequest(user_key=_tomb("in-progress-old"), status="in_progress", requested_at=OLD),
        "completed_old_via_update": ErasureRequest(user_key=_tomb("completed-update"), status="in_progress"),
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
        undated = repo.create(ErasureRequest(user_key=_tomb("undated"), status="completed"))

        repo.delete_completed_before(CUTOFF.isoformat())

        assert repo.get_by_key(undated.key) is not None


class TestACompletedRecordWithoutATombstone:
    """GDPR-006 (#1773 review): a legacy ``completed`` record still naming its subject is held.

    It is not proof of an erasure — the erasure rewrites ``user_key`` to the
    tombstone inside its transaction — and may be the only trace of an Art. 17
    duty still owed. Both AQL statements must skip it: the edge statement as
    well, or the record would lose its ``requested_erasure`` edge and stay.
    """

    def test_it_is_kept_with_its_edge_and_counted(self, database, seeded):
        repo = ArangoErasureRepository(database)
        legacy = repo.create(ErasureRequest(user_key="plain-user-4411", status="completed", completed_at=OLD))

        assert repo.count_completed_without_tombstone_before(CUTOFF.isoformat()) == 1
        assert repo.delete_completed_before(CUTOFF.isoformat()) == 2

        assert repo.get_by_key(legacy.key) is not None
        assert f"{col.ERASURE_REQUESTS}/{legacy.key}" in _edge_targets(database)
        assert repo.count_completed_without_tombstone_before(CUTOFF.isoformat()) == 1, "held, not consumed"

    def test_a_young_one_is_not_counted(self, database, seeded):
        repo = ArangoErasureRepository(database)
        repo.create(ErasureRequest(user_key="plain-user-4411", status="completed", completed_at=YOUNG))

        assert repo.count_completed_without_tombstone_before(CUTOFF.isoformat()) == 0


class TestTheCutoffBoundary:
    """GDPR-009 (#1773 review): the string comparison at the whole-second cutoff.

    The service passes ``2025-09-25T04:30:00+00:00``. A completion in that same
    second with a fraction lies *after* the cutoff and must be kept in both
    stored spellings (``….5Z`` from the model, ``….500000+00:00`` from
    ``update_fields``); one a second before the cutoff must go.
    """

    @pytest.mark.parametrize(
        ("completed_at", "purged"),
        [
            ("2025-09-25T04:30:00.5Z", False),
            ("2025-09-25T04:30:00.500000+00:00", False),
            ("2025-09-25T04:30:00Z", False),
            ("2025-09-25T04:30:00+00:00", False),
            ("2025-09-25T04:29:59Z", True),
            ("2025-09-25T04:29:59.999999+00:00", True),
        ],
    )
    def test_the_same_second_is_kept_and_the_second_before_goes(self, database, completed_at, purged):
        database.collection(col.ERASURE_REQUESTS).truncate()
        database.collection(col.REQUESTED_ERASURE).truncate()
        repo = ArangoErasureRepository(database)
        record = repo.create(ErasureRequest(user_key=_tomb("boundary"), status="in_progress"))
        # Written verbatim, so the stored spelling is exactly the one under test.
        database.collection(col.ERASURE_REQUESTS).update(
            {"_key": record.key, "status": "completed", "completed_at": completed_at}
        )

        removed = repo.delete_completed_before(CUTOFF.isoformat())

        assert removed == (1 if purged else 0)
        assert (repo.get_by_key(record.key) is None) is purged
