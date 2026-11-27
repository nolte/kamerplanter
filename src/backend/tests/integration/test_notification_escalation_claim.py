"""ADR-008 F-8 — the escalation claim is one conditional write, measured against ArangoDB.

``ArangoNotificationRepository.claim_escalation_level`` replaces the escalation's
read-then-full-replace (``get`` + ``update``; ``update`` compares no ``_rev``). Two
overlapping escalation runs that both read a row at level 0 used to both "win"
and both send. The claim filters on key, tenant and "level still below" and
updates in the same statement, so exactly one caller gets the row back.

The concurrency test forces the overlap deterministically: a barrier holds both
callers at the repository boundary until both have arrived — at ``get`` for a
read-then-write implementation (both then read level 0), at
``claim_escalation_level`` for the conditional one. Whatever the implementation,
the assertion is the same expression: exactly one ``True``.

No personal data: every value is synthetic. Traces to issue #1061, feature F-8.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.notification_repository import ArangoNotificationRepository
from app.domain.models.notification import Notification
from app.domain.services.notification_propagation_service import NotificationPropagationService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("escalation_claim")
TENANT = "tenant-claim"
OTHER_TENANT = "tenant-other"
KEY = "notif-claim-1"
READ_AT = "2026-11-20T08:00:00+00:00"

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
    database.collection(col.NOTIFICATIONS).insert(
        {
            "_key": KEY,
            "tenant_key": TENANT,
            "user_key": "user-claim",
            "notification_type": "care.watering",
            "title": "t",
            "body": "b",
            "group_key": "care.watering:plant-claim",
            "escalation_level": 0,
            "read_at": READ_AT,
            "acted_at": None,
            "legacy_attr": "kept",
            "created_at": "2026-11-01T00:00:00+00:00",
        }
    )
    return database


def _stored(db: StandardDatabase) -> dict:
    return db.collection(col.NOTIFICATIONS).get(KEY)


class TestTheRepositoryClaim:
    def test_raises_the_level_once_and_touches_nothing_else(self, db: StandardDatabase) -> None:
        repo = ArangoNotificationRepository(db)

        first = repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1)
        second = repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1)

        assert first is not None
        assert first.escalation_level == 1
        assert second is None
        stored = _stored(db)
        assert stored["escalation_level"] == 1
        assert stored["read_at"] == READ_AT
        assert stored["legacy_attr"] == "kept"

    def test_never_lowers_a_level(self, db: StandardDatabase) -> None:
        repo = ArangoNotificationRepository(db)
        for level in (1, 2, 3):
            assert repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=level) is not None

        assert repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=2) is None
        assert _stored(db)["escalation_level"] == 3

    def test_a_level_cannot_be_skipped(self, db: StandardDatabase) -> None:
        """#3135: only the next level — a run holding an old read cannot jump a level another run claimed."""
        repo = ArangoNotificationRepository(db)

        assert repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=2) is None
        assert _stored(db)["escalation_level"] == 0
        assert repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1) is not None
        assert repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=3) is None
        assert _stored(db)["escalation_level"] == 1

    @pytest.mark.parametrize("stored", ["absent", None])
    def test_a_row_without_a_level_claims_level_one(self, db: StandardDatabase, stored: object) -> None:
        """A legacy row without the field (or with null) is at level 0, not stranded (#3135)."""
        if stored == "absent":
            doc = _stored(db)
            del doc["escalation_level"]
            db.collection(col.NOTIFICATIONS).replace(doc)
            assert "escalation_level" not in _stored(db)
        else:
            db.collection(col.NOTIFICATIONS).update({"_key": KEY, "escalation_level": None}, keep_none=True)
            assert _stored(db)["escalation_level"] is None

        claimed = ArangoNotificationRepository(db).claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1)

        assert claimed is not None
        assert _stored(db)["escalation_level"] == 1


class TestTheRefreshLeavesTheLevelAlone:
    """#3135: the full-model refresh never writes ``escalation_level``; only claim and reset move it."""

    def test_a_claim_between_the_refreshs_read_and_write_survives(self, db: StandardDatabase) -> None:
        repo = ArangoNotificationRepository(db)
        stale = repo.get(KEY)
        assert stale is not None and stale.escalation_level == 0
        assert repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1) is not None

        stale.title = "refreshed"
        repo.update(KEY, stale)

        stored = _stored(db)
        assert stored["title"] == "refreshed"
        assert stored["escalation_level"] == 1

    def test_the_reset_is_its_own_tenant_scoped_write(self, db: StandardDatabase) -> None:
        repo = ArangoNotificationRepository(db)
        repo.claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1)

        assert repo.reset_escalation_level(KEY, tenant_key=OTHER_TENANT) is False
        assert repo.reset_escalation_level(KEY, tenant_key="") is False
        assert _stored(db)["escalation_level"] == 1
        assert repo.reset_escalation_level(KEY, tenant_key=TENANT) is True
        stored = _stored(db)
        assert stored["escalation_level"] == 0
        assert stored["read_at"] == READ_AT
        assert repo.reset_escalation_level(KEY, tenant_key=TENANT) is False

    def test_another_tenant_claims_nothing(self, db: StandardDatabase) -> None:
        repo = ArangoNotificationRepository(db)

        assert repo.claim_escalation_level(KEY, tenant_key=OTHER_TENANT, escalation_level=1) is None
        assert repo.claim_escalation_level(KEY, tenant_key="", escalation_level=1) is None
        assert _stored(db)["escalation_level"] == 0

    def test_an_unknown_key_claims_nothing(self, db: StandardDatabase) -> None:
        assert (
            ArangoNotificationRepository(db).claim_escalation_level("nope", tenant_key=TENANT, escalation_level=1)
            is None
        )


class _RendezvousRepo(ArangoNotificationRepository):
    """Holds two callers at the repository boundary until both arrived (forces the overlap)."""

    def __init__(self, db: StandardDatabase, barrier: threading.Barrier) -> None:
        super().__init__(db)
        self._barrier = barrier

    def get(self, key: str) -> Notification | None:
        self._barrier.wait(timeout=10)
        return super().get(key)

    def claim_escalation_level(self, key: str, *, tenant_key: str, escalation_level: int) -> Notification | None:
        self._barrier.wait(timeout=10)
        return super().claim_escalation_level(key, tenant_key=tenant_key, escalation_level=escalation_level)


def test_two_overlapping_escalation_runs_claim_the_level_exactly_once(db: StandardDatabase) -> None:
    row = ArangoNotificationRepository(db).get(KEY)
    assert row is not None
    barrier = threading.Barrier(2)
    service = NotificationPropagationService(_RendezvousRepo(db, barrier))

    def claim() -> bool:
        return service.on_notification_escalated(row.model_copy(deep=True), tenant_key=TENANT, escalation_level=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))

    assert sorted(results) == [False, True]
    stored = _stored(db)
    assert stored["escalation_level"] == 1
    assert stored["read_at"] == READ_AT


def test_the_claim_stamps_updated_at(db: StandardDatabase) -> None:
    before = datetime.now(UTC).isoformat()
    ArangoNotificationRepository(db).claim_escalation_level(KEY, tenant_key=TENANT, escalation_level=1)
    assert _stored(db)["updated_at"] >= before
