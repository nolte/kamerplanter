"""#1806 GDPR-003 — records an age selector can never select are counted, against a real ArangoDB.

Each destructive retention selector (R-02 accounts, ``ai_audit_log``, ``mcp_audit_log``,
orphaned task photos, R-04 consent records, R-07b e-mail changes, the glossary cache)
compares its timestamp as an instant and so skips a record
whose timestamp is missing or unreadable — deleting it would be a guess. That is the
safe side, but until now nothing counted what was skipped, so such a record was held
for ever without a trace. Each selector now has a ``count_undated*`` twin built on the
same predicate with the date test inverted. Measured here, per selector, from both
sides: the selector must *not* take the undated record, the counter must count exactly
it, and a dated record must be counted by neither.

Runs in CI against the service container; locally it needs a database of its own
(a missing one is a failure in CI, a loud skip locally — ``conftest.py``). Start one with::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.ai_repository import ArangoAiAuditRepository
from app.data_access.arango.attachment_repository import (
    ATTACHMENT_REF_FIELDS,
    PHOTO_REF_COLLECTIONS,
    ArangoAttachmentRepository,
)
from app.data_access.arango.consent_repository import ArangoConsentRepository
from app.data_access.arango.email_change_repository import ArangoEmailChangeRepository
from app.data_access.arango.glossary_repository import ArangoGlossaryTermCacheRepository
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("undated_held")
NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
LONG_AGO = "2020-01-01T00:00:00+00:00"
CUTOFF = datetime(2026, 1, 1, tzinfo=UTC)

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    names = dict.fromkeys(
        [
            col.USERS,
            col.AUTH_PROVIDERS,
            col.AI_AUDIT_LOG,
            col.MCP_AUDIT_LOG,
            col.ATTACHMENTS,
            col.CONSENT_RECORDS,
            col.EMAIL_CHANGE_REQUESTS,
            col.GLOSSARY_TERM_CACHE,
            *PHOTO_REF_COLLECTIONS,
            *(collection for collection, _field in ATTACHMENT_REF_FIELDS),
        ]
    )
    for name in names:
        db.create_collection(name)
    # The deletes remove the edges into a selected record first (consent, e-mail change).
    for edge_name in (col.HAS_CONSENT, col.REQUESTED_EMAIL_CHANGE):
        db.create_collection(edge_name, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for name in (
        col.USERS,
        col.AUTH_PROVIDERS,
        col.AI_AUDIT_LOG,
        col.MCP_AUDIT_LOG,
        col.ATTACHMENTS,
        col.CONSENT_RECORDS,
        col.EMAIL_CHANGE_REQUESTS,
        col.GLOSSARY_TERM_CACHE,
    ):
        database.collection(name).truncate()
    return database


UNDATED_SPELLINGS = [
    pytest.param({}, id="absent"),
    pytest.param({"created_at": None}, id="null"),
    pytest.param({"created_at": "not-a-date"}, id="garbage"),
]


class TestAiAuditLog:
    @pytest.mark.parametrize("stamp", UNDATED_SPELLINGS)
    def test_the_undated_entry_is_counted_and_not_deleted(self, db, stamp):
        db.collection(col.AI_AUDIT_LOG).insert({"_key": "undated", **stamp})
        db.collection(col.AI_AUDIT_LOG).insert({"_key": "old", "created_at": LONG_AGO})
        repo = ArangoAiAuditRepository(db)

        assert repo.count_undated() == 1
        assert repo.delete_older_than(CUTOFF) == 1  # only the dated one
        assert {d["_key"] for d in db.collection(col.AI_AUDIT_LOG).all()} == {"undated"}

    def test_nothing_held_counts_zero(self, db):
        db.collection(col.AI_AUDIT_LOG).insert({"_key": "dated", "created_at": LONG_AGO})
        assert ArangoAiAuditRepository(db).count_undated() == 0


class TestMcpAuditLog:
    @pytest.mark.parametrize("stamp", UNDATED_SPELLINGS)
    def test_the_undated_entry_is_counted_and_not_deleted(self, db, stamp):
        db.collection(col.MCP_AUDIT_LOG).insert({"_key": "undated", **stamp})
        db.collection(col.MCP_AUDIT_LOG).insert({"_key": "old", "created_at": LONG_AGO})
        repo = ArangoMcpAuditRepository(db)

        assert repo.count_undated() == 1
        assert repo.delete_expired(retention_days=30, now=NOW) == 1
        assert {d["_key"] for d in db.collection(col.MCP_AUDIT_LOG).all()} == {"undated"}

    def test_nothing_held_counts_zero(self, db):
        db.collection(col.MCP_AUDIT_LOG).insert({"_key": "dated", "created_at": LONG_AGO})
        assert ArangoMcpAuditRepository(db).count_undated() == 0


class TestUnverifiedAccounts:
    def _user(self, key, **fields):
        return {"_key": key, "email": f"{key}@example.com", "display_name": key, "email_verified": False, **fields}

    @pytest.mark.parametrize("stamp", UNDATED_SPELLINGS)
    def test_the_undated_unverified_account_is_counted_and_never_selected(self, db, stamp):
        users = db.collection(col.USERS)
        users.insert(self._user("undated", **stamp))
        users.insert(self._user("old", created_at=LONG_AGO))
        repo = ArangoUserRepository(db)

        assert repo.count_unverified_undated() == 1
        assert [u.key for u in repo.get_unverified_before(CUTOFF.isoformat())] == ["old"]

    def test_a_verified_or_federated_undated_account_is_not_a_held_candidate(self, db):
        users = db.collection(col.USERS)
        users.insert(self._user("verified", email_verified=True))
        users.insert(self._user("federated"))
        db.collection(col.AUTH_PROVIDERS).insert({"_key": "link", "user_key": "federated", "provider": "github"})

        # Neither could ever be selected for erasure, so neither is "held" by R-02.
        assert ArangoUserRepository(db).count_unverified_undated() == 0


class TestOrphanedTaskPhotos:
    def _photo(self, key, *, category="task", **stamp):
        return {
            "_key": key,
            "tenant_key": "t",
            "mime_type": "image/jpeg",
            "byte_size": 1,
            "sha256": f"sha-{key}",
            "original_filename": f"{key}.jpg",
            "created_by": "u",
            "category": category,
            "storage_key": f"t/{category}/{key}.jpg",
            **stamp,
        }

    @pytest.mark.parametrize("stamp", UNDATED_SPELLINGS)
    def test_an_undated_orphan_is_counted_and_never_returned(self, db, stamp):
        photos = db.collection(col.ATTACHMENTS)
        photos.insert(self._photo("undated", **stamp))
        photos.insert(self._photo("old", created_at=LONG_AGO))
        repo = ArangoAttachmentRepository(db)

        assert repo.count_undated_orphaned_task_photos() == 1
        assert [a.key for a in repo.find_orphaned_task_photos(older_than=NOW)] == ["old"]

    def test_a_referenced_or_non_task_undated_photo_is_not_an_orphan(self, db):
        photos = db.collection(col.ATTACHMENTS)
        photos.insert(self._photo("referenced"))
        photos.insert(self._photo("diary", category="diary"))
        db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": "t", "photo_refs": ["referenced"]})

        assert ArangoAttachmentRepository(db).count_undated_orphaned_task_photos() == 0


class TestConsentRecords:
    """R-04 — the clock runs from ``revoked_at``; a revoked record without a readable one never ages out."""

    def _consent(self, key, **fields):
        return {"_key": key, "user_key": "u", "purpose": f"p-{key}", "granted": False, **fields}

    @pytest.mark.parametrize(
        "stamp",
        [
            pytest.param({}, id="revoked-without-a-stamp"),
            pytest.param({"revoked_at": None}, id="null"),
            pytest.param({"revoked_at": "not-a-date"}, id="garbage"),
        ],
    )
    def test_a_revoked_record_without_a_readable_stamp_is_counted_and_not_deleted(self, db, stamp):
        records = db.collection(col.CONSENT_RECORDS)
        records.insert(self._consent("undated", **stamp))
        records.insert(self._consent("old", revoked_at=LONG_AGO))
        repo = ArangoConsentRepository(db)

        assert repo.count_undated_revoked() == 1
        assert repo.delete_revoked_before(CUTOFF.isoformat()) == 1  # only the dated one
        assert {d["_key"] for d in records.all()} == {"undated"}

    def test_an_active_grant_is_not_held(self, db):
        # Never revoked: not due, and not an anomaly either — the ordinary state.
        db.collection(col.CONSENT_RECORDS).insert(self._consent("active", granted=True))
        db.collection(col.CONSENT_RECORDS).insert(self._consent("dated", revoked_at=LONG_AGO))

        assert ArangoConsentRepository(db).count_undated_revoked() == 0


class TestEmailChangeRequests:
    """R-07b — a confirmed change is due on ``revert_expires_at`` or on ``confirmed_at``; with neither it is held."""

    NOW_ISO = NOW.isoformat()

    def _change(self, key, **fields):
        return {"_key": key, "user_key": "u", "status": "confirmed", "revert_token_hash": None, **fields}

    @pytest.mark.parametrize(
        "stamps",
        [
            pytest.param({}, id="absent"),
            pytest.param({"confirmed_at": None, "revert_expires_at": None}, id="null"),
            pytest.param({"confirmed_at": "x", "revert_expires_at": "y"}, id="garbage"),
        ],
    )
    def test_a_confirmed_change_with_no_readable_stamp_is_counted_and_not_deleted(self, db, stamps):
        changes = db.collection(col.EMAIL_CHANGE_REQUESTS)
        changes.insert(self._change("undated", **stamps))
        changes.insert(self._change("old", confirmed_at=LONG_AGO, revert_expires_at=LONG_AGO))
        repo = ArangoEmailChangeRepository(db)

        assert repo.count_undated_confirmed() == 1
        assert repo.delete_confirmed_past_revert_window(self.NOW_ISO) == 1
        assert {d["_key"] for d in changes.all()} == {"undated"}

    def test_a_change_with_one_readable_stamp_or_not_confirmed_is_not_held(self, db):
        changes = db.collection(col.EMAIL_CHANGE_REQUESTS)
        changes.insert(self._change("window-only", revert_expires_at="2099-01-01T00:00:00+00:00"))
        changes.insert(self._change("confirmed-only", confirmed_at=LONG_AGO))
        changes.insert(self._change("pending", status="pending"))  # R-07 uses ``expires_at``, not these

        assert ArangoEmailChangeRepository(db).count_undated_confirmed() == 0


class TestGlossaryCache:
    @pytest.mark.parametrize(
        "stamp",
        [
            pytest.param({}, id="absent"),
            pytest.param({"valid_until": None}, id="null"),
            pytest.param({"valid_until": "not-a-date"}, id="garbage"),
        ],
    )
    def test_a_row_without_a_readable_valid_until_is_counted_and_not_deleted(self, db, stamp):
        cache = db.collection(col.GLOSSARY_TERM_CACHE)
        cache.insert({"_key": "undated", **stamp})
        cache.insert({"_key": "old", "valid_until": LONG_AGO})
        repo = ArangoGlossaryTermCacheRepository(db)

        assert repo.count_undated() == 1
        assert repo.delete_expired(now=NOW) == 1
        assert {d["_key"] for d in cache.all()} == {"undated"}

    def test_nothing_held_counts_zero(self, db):
        db.collection(col.GLOSSARY_TERM_CACHE).insert({"_key": "dated", "valid_until": LONG_AGO})
        assert ArangoGlossaryTermCacheRepository(db).count_undated() == 0
