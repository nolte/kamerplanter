"""#1767 — the erasure claim and the export-expiry selection against a real ArangoDB.

The unit tier pins the service logic on doubles that mirror these queries; what
only a server can say is whether the AQL does what the doubles assume:

* ``ArangoErasureRepository.claim_for_run`` hands a request to exactly one of
  several concurrent callers (SEC-003), refuses a ``completed`` one and one a
  fresh run holds, and takes over a stale one;
* ``ArangoDataExportRepository.list_expiry_due`` selects ``completed`` exports
  past their window **and** ``expired`` ones that still point at a bundle,
  without changing either — and the service writes ``expired`` only after the
  bundle delete succeeded (GDPR-005).

No personal data: every value is synthetic.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.data_export_repository import ArangoDataExportRepository
from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import DataExportRequest, ErasureRequest
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("erasure_claim_export_expiry")
NOW = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)
STALE_BEFORE = NOW - timedelta(hours=PrivacyService.ERASURE_STALE_AFTER_HOURS)

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in (col.ERASURE_REQUESTS, col.DATA_EXPORT_REQUESTS, col.USERS):
        db.create_collection(name)
    for edge in (col.REQUESTED_ERASURE, col.REQUESTED_EXPORT):
        db.create_collection(edge, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


def _claim(repo: ArangoErasureRepository, key: str) -> ErasureRequest | None:
    return repo.claim_for_run(key, now_iso=NOW.isoformat(), stale_before_iso=STALE_BEFORE.isoformat())


class TestTheClaim:
    def test_an_open_request_is_claimed_once(self, database):
        repo = ArangoErasureRepository(database)
        request = repo.create(ErasureRequest(user_key="claim-once", status="scheduled", hard_delete_scheduled_at=NOW))

        first = _claim(repo, request.key)
        second = _claim(repo, request.key)

        assert first is not None
        assert first.status == "in_progress"
        assert second is None

    def test_concurrent_claims_hand_the_request_to_exactly_one_caller(self, database):
        repo = ArangoErasureRepository(database)
        request = repo.create(ErasureRequest(user_key="claim-race", status="scheduled", hard_delete_scheduled_at=NOW))

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: _claim(ArangoErasureRepository(database), request.key), range(8)))

        assert sum(result is not None for result in results) == 1

    def test_a_completed_request_is_never_claimed(self, database):
        repo = ArangoErasureRepository(database)
        request = repo.create(ErasureRequest(user_key="claim-done", status="completed", hard_delete_scheduled_at=NOW))

        assert _claim(repo, request.key) is None

    def test_a_stale_run_is_taken_over(self, database):
        repo = ArangoErasureRepository(database)
        request = repo.create(ErasureRequest(user_key="claim-stale", status="scheduled", hard_delete_scheduled_at=NOW))
        database.collection(col.ERASURE_REQUESTS).update(
            {
                "_key": request.key,
                "status": "in_progress",
                "updated_at": (STALE_BEFORE - timedelta(minutes=1)).isoformat(),
            }
        )

        assert _claim(repo, request.key) is not None


class TestTheDeterministicCreate:
    def test_a_second_create_under_the_same_key_is_refused(self, database):
        from app.common.exceptions import DuplicateError

        repo = ArangoErasureRepository(database)
        request = ErasureRequest(user_key="create-twice", status="scheduled", hard_delete_scheduled_at=NOW)
        created = repo.create_with_key(request, "anon_0123456789abcdef")

        assert created.key == "anon_0123456789abcdef"
        with pytest.raises(DuplicateError):
            repo.create_with_key(request.model_copy(update={"key": None}), "anon_0123456789abcdef")


def _export(name: str, *, status: str, expires_at: datetime | None, file_path: str | None) -> DataExportRequest:
    return DataExportRequest(
        user_key=f"export-user-{name}",
        status=status,
        requested_at=NOW - timedelta(days=4),
        expires_at=expires_at,
        file_path=file_path,
        file_size_bytes=10 if file_path else None,
    )


class _Storage:
    def __init__(self) -> None:
        self.objects = {"b/past": b"x", "b/legacy": b"x", "b/future": b"x"}
        self.fail = False

    async def delete_object(self, key: str) -> None:
        if self.fail:
            raise ConnectionError("object store unavailable")
        self.objects.pop(key, None)


def _privacy_service(database, storage: _Storage) -> PrivacyService:
    return PrivacyService(
        export_repo=ArangoDataExportRepository(database),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=ArangoErasureRepository(database),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://localhost",
        storage_adapter=storage,
    )


@pytest.fixture(scope="module")
def exports(database) -> dict[str, str]:
    """Seed four exports; hand back ``name -> stored key`` (the repository assigns keys)."""
    repo = ArangoDataExportRepository(database)
    seeded = {
        "past": _export("past", status="completed", expires_at=NOW - timedelta(hours=1), file_path="b/past"),
        "future": _export("future", status="completed", expires_at=NOW + timedelta(hours=1), file_path="b/future"),
        "legacy": _export("legacy", status="expired", expires_at=NOW - timedelta(days=9), file_path="b/legacy"),
        "clean": _export("clean", status="expired", expires_at=NOW - timedelta(days=9), file_path=None),
    }
    return {name: repo.create(export).key for name, export in seeded.items()}


class TestExportExpiry:
    def test_the_selection_changes_nothing_and_finds_the_legacy_residue(self, database, exports):
        repo = ArangoDataExportRepository(database)

        due = repo.list_expiry_due(NOW.isoformat())

        assert sorted(e.key for e in due) == sorted([exports["legacy"], exports["past"]])
        assert repo.get_by_key(exports["past"]).status == "completed", "selecting must not expire"

    def test_a_failed_delete_leaves_the_record_and_the_next_run_finishes_it(self, database, exports):
        storage = _Storage()
        service = _privacy_service(database, storage)
        repo = ArangoDataExportRepository(database)

        storage.fail = True
        assert asyncio.run(service.expire_data_exports(NOW)) == 0
        past = repo.get_by_key(exports["past"])
        assert (past.status, past.file_path) == ("completed", "b/past")

        storage.fail = False
        assert asyncio.run(service.expire_data_exports(NOW)) == 2
        for name in ("past", "legacy"):
            export = repo.get_by_key(exports[name])
            assert (export.status, export.file_path, export.file_size_bytes) == ("expired", None, None)
        assert set(storage.objects) == {"b/future"}


class TestTheExportCompletionGuard:
    """#1767 review SEC-A — a build finishing behind an erasure cannot complete."""

    def test_completion_lands_only_while_processing(self, database):
        repo = ArangoDataExportRepository(database)
        open_export = repo.create(_export("guard-open", status="processing", expires_at=None, file_path=None))
        closed_export = repo.create(_export("guard-closed", status="processing", expires_at=None, file_path=None))

        assert repo.fail_open_for_user("export-user-guard-closed", "The account is being erased.") == 1

        completed = repo.complete_if_processing(
            open_export.key, {"status": "completed", "file_path": "b/open", "error_message": None}
        )
        refused = repo.complete_if_processing(closed_export.key, {"status": "completed", "file_path": "b/closed"})

        assert completed is not None
        assert (completed.status, completed.file_path) == ("completed", "b/open")
        assert refused is None
        stored = repo.get_by_key(closed_export.key)
        assert (stored.status, stored.file_path) == ("failed", None)

    def test_the_processing_flip_does_not_reopen_a_closed_export(self, database):
        repo = ArangoDataExportRepository(database)
        pending = repo.create(_export("flip-open", status="pending", expires_at=None, file_path=None))
        closed = repo.create(_export("flip-closed", status="pending", expires_at=None, file_path=None))
        repo.fail_open_for_user("export-user-flip-closed", "The account is being erased.")

        started = repo.start_processing(pending.key, from_statuses=["pending"], fields={"manifest_collections": []})
        refused = repo.start_processing(closed.key, from_statuses=["pending"], fields={"manifest_collections": []})

        assert started is not None
        assert started.status == "processing"
        assert refused is None
        assert repo.get_by_key(closed.key).status == "failed"
