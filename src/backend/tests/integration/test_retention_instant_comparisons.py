"""#1784 — every retention and expiry selector compares instants, against a real ArangoDB.

**The defect class.** ArangoDB orders strings by ICU collation, not by the time
they spell. The timestamps this system stores come in several spellings of the
same instant: Pydantic's JSON dump writes ``…:00Z`` for a whole second and
``…:00.500000Z`` otherwise, ``datetime.isoformat()`` (every ``update_fields``
write and ``BaseArangoRepository._now()``) writes ``…:00+00:00``, AQL's
``DATE_ISO8601`` writes ``…:00.000Z``. Under ICU collation ``.`` sorts before
``+`` and before ``Z``, so a record half a second *after* a cutoff compared as
text lands *before* it (measured on ArangoDB 3.12.8)::

    '2025-09-25T04:30:00.500000Z' < '2025-09-25T04:30:00+00:00'   -> true

A retention sweep built on ``doc.x < @cutoff`` therefore deletes a record that
is not due yet, and keeps one that is — the #1786 purge was the first measured
instance. The repair compares ``DATE_TIMESTAMP`` on both sides.

**How each selector is measured.** Every row of :data:`SELECTORS` names one
production repository method and what "selected" means for it (returned,
removed, flipped to ``expired``). It is then driven with one record per test:

* a record 0.5 s **after** a cutoff spelled without a fraction, the record spelled
  with one — it must land on the *after* side;
* a record 0.5 s **before** a cutoff spelled with a fraction, the record spelled
  without one — it must land on the *before* side;
* a record without the timestamp — it lands where the method's own semantics
  say (:attr:`Selector.undated_selected`), and each row says why.

Both directions are needed: the first catches a selector that picks too much,
the second one that picks too little, and string order gets both wrong.

No personal data: every value is synthetic.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.actuator_repository import ArangoActuatorRepository
from app.data_access.arango.ai_repository import (
    ArangoAiAuditRepository,
    ArangoAiConversationRepository,
    ArangoAiTipCacheRepository,
)
from app.data_access.arango.data_export_repository import ArangoDataExportRepository
from app.data_access.arango.email_change_repository import ArangoEmailChangeRepository
from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.data_access.arango.glossary_repository import ArangoGlossaryTermCacheRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository, ArangoMcpIdempotencyRepository
from app.data_access.arango.notification_repository import ArangoNotificationRepository
from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository
from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("instant_cmp")

#: Direction (a): a cutoff spelled the way ``isoformat()`` spells a whole second …
CUTOFF_WHOLE = "2025-09-25T04:30:00+00:00"
#: … and a record half a second after it, in the spellings a fractional second gets.
AFTER_SPELLINGS = ("2025-09-25T04:30:00.5Z", "2025-09-25T04:30:00.500000Z")

#: Direction (b): a cutoff with a fraction …
CUTOFF_FRACTION = "2025-09-25T04:29:59.5Z"
#: … and a record half a second before it, spelled without one.
BEFORE_SPELLINGS = ("2025-09-25T04:29:59+00:00", "2025-09-25T04:29:59Z")

#: Far enough from every cutoff above that no spelling question arises.
FAR_PAST = "2020-01-01T00:00:00+00:00"
FAR_FUTURE = "2030-01-01T00:00:00+00:00"

TENANT = "tenant-instant"
USER = "user-instant"

#: Every collection a selector below reads or writes, plus the edge collections
#: their delete paths touch.
_DOCUMENT_COLLECTIONS = (
    col.USERS,
    col.AUTH_PROVIDERS,
    col.DATA_EXPORT_REQUESTS,
    col.ERASURE_REQUESTS,
    col.EMAIL_CHANGE_REQUESTS,
    col.INVITATIONS,
    col.REFRESH_TOKENS,
    col.AI_CONVERSATIONS,
    col.AI_TIP_CACHE,
    col.AI_AUDIT_LOG,
    col.GLOSSARY_TERM_CACHE,
    col.MCP_AUDIT_LOG,
    col.MCP_IDEMPOTENCY_RECORD,
    col.MANUAL_OVERRIDES,
    col.NOTIFICATIONS,
    col.PLANT_DIARY_ENTRIES,
)
_EDGE_COLLECTIONS = (col.HAS_SESSION,)


pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENT_COLLECTIONS:
        db.create_collection(name)
    for name in _EDGE_COLLECTIONS:
        db.create_collection(name, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database: StandardDatabase) -> StandardDatabase:
    """The module database, emptied before every test: each test seeds exactly one record."""
    for name in (*_DOCUMENT_COLLECTIONS, *_EDGE_COLLECTIONS):
        database.collection(name).truncate()
    return database


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso)


# ── what "selected" means, per kind of method ─────────────────────────────────


def _remaining(db: StandardDatabase, collection: str) -> set[str]:
    return {doc["_key"] for doc in db.collection(collection).all()}


def _removed_by(collection: str, action: Callable[[StandardDatabase, str], object]):
    """Selected = the documents the call removed."""

    def run(db: StandardDatabase, cutoff: str) -> set[str]:
        before = _remaining(db, collection)
        action(db, cutoff)
        return before - _remaining(db, collection)

    return run


def _flipped_by(collection: str, attribute: str, value: object, action: Callable[[StandardDatabase, str], object]):
    """Selected = the documents on which the call set ``attribute`` to ``value``."""

    def run(db: StandardDatabase, cutoff: str) -> set[str]:
        action(db, cutoff)
        return {doc["_key"] for doc in db.collection(collection).all() if doc.get(attribute) == value}

    return run


def _returned_keys(action: Callable[[StandardDatabase, str], object]):
    """Selected = the keys of the models (or ``(key, …)`` pairs) the call returned."""

    def run(db: StandardDatabase, cutoff: str) -> set[str]:
        result = action(db, cutoff)
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            result = result[0]  # ``(items, total)``
        if result is None:
            return set()
        if not isinstance(result, list):
            result = [result]
        keys = set()
        for item in result:
            keys.add(item[0] if isinstance(item, tuple) else item.key)
        return keys

    return run


def _claimed(db: StandardDatabase, cutoff: str) -> set[str]:
    repo = ArangoErasureRepository(db)
    keys = _remaining(db, col.ERASURE_REQUESTS)
    return {key for key in keys if repo.claim_for_run(key, now_iso=FAR_FUTURE, stale_before_iso=cutoff) is not None}


#: :attr:`Selector.unreadable` default: an unreadable timestamp lands with the undated ones.
_AS_UNDATED = "as-undated"


@dataclass(frozen=True)
class Selector:
    """One production method whose result hangs on a stored timestamp.

    Attributes:
        name: Test id.
        collection: Where the probe record is inserted.
        base: A document that satisfies every other predicate of the method.
        field: The timestamp the method compares.
        selects: ``"before"`` when the method selects records whose ``field``
            lies before the cutoff (``<``/``<=``), ``"after"`` for ``>``/``>=``.
        run: Calls the production method with the cutoff (an ISO string, in the
            spelling under test) and returns the keys it selected.
        undated_selected: Whether a record without ``field`` is selected.
        why_undated: The method's own reason for that answer.
        unreadable: Whether a record whose ``field`` is not a timestamp at all is
            selected. ``DATE_TIMESTAMP`` reads it as ``null``, so it follows the
            undated answer for a ``<`` selector; for an ``>`` selector whose
            ``null`` means "no expiry" it does not (``null > n`` is false).
            ``None`` where the method would return the record as a model, which
            rejects the value on read — not measurable through this path.
    """

    name: str
    collection: str
    base: dict
    field: str
    selects: str
    run: Callable[[StandardDatabase, str], set[str]]
    undated_selected: bool
    why_undated: str
    unreadable: bool | None | str = field(default=_AS_UNDATED, kw_only=True)

    @property
    def unreadable_selected(self) -> bool | None:
        return self.undated_selected if self.unreadable == _AS_UNDATED else self.unreadable  # type: ignore[return-value]


SELECTORS: tuple[Selector, ...] = (
    Selector(
        name="user.get_unverified_before",
        collection=col.USERS,
        base={"email": "reaper@example.com", "display_name": "Reaper probe", "email_verified": False},
        field="created_at",
        selects="before",
        run=_returned_keys(lambda db, cut: ArangoUserRepository(db).get_unverified_before(cut)),
        undated_selected=False,
        why_undated="an account whose age cannot be read is never erased as abandoned",
    ),
    Selector(
        name="data_export.list_expiry_due",
        collection=col.DATA_EXPORT_REQUESTS,
        base={"user_key": USER, "status": "completed"},
        field="expires_at",
        selects="before",
        run=_returned_keys(lambda db, cut: ArangoDataExportRepository(db).list_expiry_due(cut)),
        undated_selected=False,
        why_undated="the query already required expires_at != null",
    ),
    Selector(
        name="data_export.list_stale_pending",
        collection=col.DATA_EXPORT_REQUESTS,
        base={"user_key": USER, "status": "pending"},
        field="requested_at",
        selects="before",
        run=_returned_keys(lambda db, cut: ArangoDataExportRepository(db).list_stale_pending(cut)),
        undated_selected=False,
        why_undated="the query already required requested_at != null",
    ),
    Selector(
        name="erasure.list_due_for_hard_delete[scheduled_at]",
        collection=col.ERASURE_REQUESTS,
        base={"user_key": USER, "status": "scheduled"},
        field="hard_delete_scheduled_at",
        selects="before",
        run=_returned_keys(
            lambda db, cut: ArangoErasureRepository(db).list_due_for_hard_delete(cut, stale_before_iso=FAR_PAST)
        ),
        undated_selected=False,
        why_undated="the query already required hard_delete_scheduled_at != null",
    ),
    Selector(
        name="erasure.list_due_for_hard_delete[stale_before]",
        collection=col.ERASURE_REQUESTS,
        base={"user_key": USER, "status": "in_progress", "hard_delete_scheduled_at": FAR_PAST},
        field="updated_at",
        selects="before",
        run=_returned_keys(
            lambda db, cut: ArangoErasureRepository(db).list_due_for_hard_delete(FAR_FUTURE, stale_before_iso=cut)
        ),
        undated_selected=True,
        why_undated="an in_progress run that never stamped updated_at is a crashed run: stale by design",
        unreadable=None,
    ),
    Selector(
        name="erasure.claim_for_run",
        collection=col.ERASURE_REQUESTS,
        base={"user_key": USER, "status": "in_progress"},
        field="updated_at",
        selects="before",
        run=_claimed,
        undated_selected=True,
        why_undated="an in_progress run that never stamped updated_at is a crashed run: stale by design",
    ),
    Selector(
        name="email_change.expire_old",
        collection=col.EMAIL_CHANGE_REQUESTS,
        base={
            "user_key": USER,
            "new_email": "new@example.com",
            "verification_token_hash": "hash-not-a-secret",
            "status": "pending",
        },
        field="expires_at",
        selects="before",
        run=_flipped_by(
            col.EMAIL_CHANGE_REQUESTS,
            "status",
            "expired",
            lambda db, cut: ArangoEmailChangeRepository(db).expire_old(cut),
        ),
        undated_selected=True,
        why_undated="expires_at is required; a request whose expiry cannot be read is treated as expired",
    ),
    Selector(
        name="invitation.cleanup_expired",
        collection=col.INVITATIONS,
        base={
            "tenant_key": TENANT,
            "invited_by_user_key": USER,
            "token_hash": "hash-not-a-secret",
            "status": "pending",
        },
        field="expires_at",
        selects="before",
        run=_flipped_by(
            col.INVITATIONS,
            "status",
            "expired",
            lambda db, cut: ArangoInvitationRepository(db).cleanup_expired(now=_dt(cut)),
        ),
        undated_selected=True,
        why_undated="expires_at is required; an invitation whose expiry cannot be read is treated as expired",
    ),
    Selector(
        name="refresh_token.cleanup_expired",
        collection=col.REFRESH_TOKENS,
        base={"user_key": USER, "token_hash": "hash-not-a-secret", "revoked": False},
        field="expires_at",
        selects="before",
        run=_removed_by(
            col.REFRESH_TOKENS, lambda db, cut: ArangoRefreshTokenRepository(db).cleanup_expired(now=_dt(cut))
        ),
        undated_selected=True,
        why_undated="expires_at is required; a session whose expiry cannot be read is treated as expired",
    ),
    Selector(
        name="refresh_token.list_active_for_user",
        collection=col.REFRESH_TOKENS,
        base={"user_key": USER, "token_hash": "hash-not-a-secret", "revoked": False},
        field="expires_at",
        selects="after",
        run=_returned_keys(lambda db, cut: ArangoRefreshTokenRepository(db).list_active_for_user(USER, now=_dt(cut))),
        undated_selected=False,
        why_undated="a session without an expiry is not shown as active",
    ),
    Selector(
        name="refresh_token.list_unanonymized_ips_before",
        collection=col.REFRESH_TOKENS,
        base={
            "user_key": USER,
            "token_hash": "hash-not-a-secret",
            "revoked": False,
            "expires_at": FAR_FUTURE,
            "ip_address": "192.0.2.10",
        },
        field="created_at",
        selects="before",
        run=_returned_keys(lambda db, cut: ArangoRefreshTokenRepository(db).list_unanonymized_ips_before(cut)),
        undated_selected=True,
        why_undated=(
            "minimising, not destructive (#1784 review GDPR-001): anonymising an IP of unknown age "
            "harms nobody, keeping it plain until the token expires (up to 30 days) does"
        ),
    ),
    Selector(
        name="ai_conversation.delete_expired",
        collection=col.AI_CONVERSATIONS,
        base={"tenant_key": TENANT, "user_key": USER},
        field="expires_at",
        selects="before",
        run=_removed_by(
            col.AI_CONVERSATIONS, lambda db, cut: ArangoAiConversationRepository(db).delete_expired(now=_dt(cut))
        ),
        undated_selected=False,
        why_undated="the query already required expires_at != null (a conversation without TTL is kept)",
    ),
    Selector(
        name="ai_tip_cache.find_valid",
        collection=col.AI_TIP_CACHE,
        base={
            "tenant_key": TENANT,
            "title": "Tip",
            "body": "Body",
            "context_type": "plant_instance",
            "context_key": "p1",
        },
        field="valid_until",
        selects="after",
        run=_returned_keys(
            lambda db, cut: ArangoAiTipCacheRepository(db).find_valid(TENANT, "plant_instance", "p1", now=_dt(cut))
        ),
        undated_selected=True,
        why_undated="valid_until == null means 'no expiry' (explicit in the query)",
        unreadable=False,
    ),
    Selector(
        name="ai_audit.delete_older_than",
        collection=col.AI_AUDIT_LOG,
        base={"tenant_key": TENANT, "endpoint": "ask", "question_hash": "q-hash"},
        field="created_at",
        selects="before",
        run=_removed_by(col.AI_AUDIT_LOG, lambda db, cut: ArangoAiAuditRepository(db).delete_older_than(_dt(cut))),
        undated_selected=False,
        why_undated="the query already required created_at != null",
    ),
    Selector(
        name="glossary_cache.find_valid",
        collection=col.GLOSSARY_TERM_CACHE,
        base={"term_slug": "vpd", "language": "de", "expertise_level": "beginner", "answer_text": "Antwort"},
        field="valid_until",
        selects="after",
        run=_returned_keys(
            lambda db, cut: ArangoGlossaryTermCacheRepository(db).find_valid("vpd", "de", "beginner", now=_dt(cut))
        ),
        undated_selected=True,
        why_undated="valid_until == null means 'no expiry' (explicit in the query)",
        unreadable=False,
    ),
    Selector(
        name="glossary_cache.delete_expired",
        collection=col.GLOSSARY_TERM_CACHE,
        base={"term_slug": "vpd", "language": "de", "expertise_level": "beginner", "answer_text": "Antwort"},
        field="valid_until",
        selects="before",
        run=_removed_by(
            col.GLOSSARY_TERM_CACHE,
            lambda db, cut: ArangoGlossaryTermCacheRepository(db).delete_expired(now=_dt(cut)),
        ),
        undated_selected=False,
        why_undated="the query already required valid_until != null",
    ),
    Selector(
        name="mcp_audit.delete_expired",
        collection=col.MCP_AUDIT_LOG,
        base={"tool_name": "list_plants", "tenant_key": TENANT, "status": "success"},
        field="created_at",
        selects="before",
        run=_removed_by(
            col.MCP_AUDIT_LOG,
            lambda db, cut: ArangoMcpAuditRepository(db).delete_expired(retention_days=0, now=_dt(cut)),
        ),
        undated_selected=False,
        why_undated="age-based: an entry whose age cannot be read is not proven past retention",
    ),
    Selector(
        name="mcp_idempotency.delete_expired",
        collection=col.MCP_IDEMPOTENCY_RECORD,
        base={
            "service_account_key": "sa-1",
            "tenant_key": TENANT,
            "tool_name": "create_task",
            "idempotency_key": "idem-1",
            "input_hash": "in-hash",
            "result_payload": {},
        },
        field="expires_at",
        selects="before",
        run=_removed_by(
            col.MCP_IDEMPOTENCY_RECORD,
            lambda db, cut: ArangoMcpIdempotencyRepository(db).delete_expired(now=_dt(cut)),
        ),
        undated_selected=True,
        why_undated="store() always stamps a TTL; a record whose expiry cannot be read is treated as expired",
    ),
    Selector(
        name="actuator.expire_overrides",
        collection=col.MANUAL_OVERRIDES,
        base={"actuator_key": "a1", "is_active": True, "started_at": FAR_PAST, "created_by": USER},
        field="expires_at",
        selects="before",
        run=_flipped_by(
            col.MANUAL_OVERRIDES,
            "is_active",
            False,
            lambda db, cut: ArangoActuatorRepository(db).expire_overrides(cut),
        ),
        undated_selected=True,
        why_undated="expires_at is required; an override whose expiry cannot be read is treated as expired",
    ),
    Selector(
        name="notification.list_for_user_since",
        collection=col.NOTIFICATIONS,
        base={"user_key": USER, "notification_type": "care.watering", "title": "t", "body": "b"},
        field="created_at",
        selects="after",
        run=_returned_keys(lambda db, cut: ArangoNotificationRepository(db).list_for_user_since(USER, _dt(cut))),
        undated_selected=False,
        why_undated="the query already required created_at != null",
    ),
    Selector(
        name="notification.find_overdue_watering",
        collection=col.NOTIFICATIONS,
        base={
            "user_key": USER,
            "notification_type": "care.watering.due",
            "title": "t",
            "body": "b",
            "escalation_level": 1,
        },
        field="created_at",
        selects="before",
        run=_returned_keys(
            lambda db, cut: ArangoNotificationRepository(db).find_overdue_watering(_dt(cut), escalation_level=1)
        ),
        undated_selected=False,
        why_undated="age-based: a notification whose age cannot be read is not proven overdue",
    ),
    Selector(
        name="plant_diary.list_pending_analyses[lease]",
        collection=col.PLANT_DIARY_ENTRIES,
        base={
            "tenant_key": TENANT,
            "plant_key": "p1",
            "entry_type": "observation",
            "text": "Blatt gelb",
            "analysis_state": "in_progress",
        },
        field="analysis_lease_expires_at",
        selects="before",
        run=_returned_keys(lambda db, cut: ArangoPlantDiaryRepository(db).list_pending_analyses(TENANT, now=_dt(cut))),
        undated_selected=True,
        why_undated="a claimed entry without a lease is broken and back in the queue (AK-06, explicit in the query)",
        unreadable=None,
    ),
)


def _seed(db: StandardDatabase, selector: Selector, stamp: str | None) -> str:
    doc = {**selector.base}
    if stamp is not None:
        doc[selector.field] = stamp
    return db.collection(selector.collection).insert(doc)["_key"]


@pytest.mark.parametrize("record", AFTER_SPELLINGS)
@pytest.mark.parametrize("selector", SELECTORS, ids=lambda s: s.name)
def test_a_record_half_a_second_after_the_cutoff_is_on_the_after_side(db, selector: Selector, record: str):
    key = _seed(db, selector, record)

    selected = selector.run(db, CUTOFF_WHOLE)

    expected = selector.selects == "after"
    assert (key in selected) is expected, (
        f"{selector.name}: {selector.field}={record!r} is 0.5 s after the cutoff {CUTOFF_WHOLE!r}, "
        f"so it must {'be' if expected else 'not be'} selected. Compared as a string, "
        "'.' sorts before '+' and the record reads as earlier than the cutoff."
    )


@pytest.mark.parametrize("record", BEFORE_SPELLINGS)
@pytest.mark.parametrize("selector", SELECTORS, ids=lambda s: s.name)
def test_a_record_half_a_second_before_the_cutoff_is_on_the_before_side(db, selector: Selector, record: str):
    key = _seed(db, selector, record)

    selected = selector.run(db, CUTOFF_FRACTION)

    expected = selector.selects == "before"
    assert (key in selected) is expected, (
        f"{selector.name}: {selector.field}={record!r} is 0.5 s before the cutoff {CUTOFF_FRACTION!r}, "
        f"so it must {'be' if expected else 'not be'} selected. Compared as a string, "
        "the cutoff's '.5' sorts before the record's '+00:00'/'Z' and the record reads as later."
    )


@pytest.mark.parametrize("selector", SELECTORS, ids=lambda s: s.name)
def test_a_record_without_the_timestamp_lands_where_the_method_says(db, selector: Selector):
    key = _seed(db, selector, None)

    selected = selector.run(db, CUTOFF_WHOLE)

    assert (key in selected) is selector.undated_selected, f"{selector.name}: {selector.why_undated}"


@pytest.mark.parametrize("selector", [s for s in SELECTORS if s.unreadable_selected is not None], ids=lambda s: s.name)
def test_an_unreadable_timestamp_is_never_read_as_long_ago(db, selector: Selector):
    """``DATE_TIMESTAMP`` of an unparsable string is ``null``; where it lands is decided, not collated.

    Compared as text, ``'not-a-timestamp'`` sorts after every date (letters after
    digits), so it read as "far future" to a ``<`` selector and as "valid" to a
    ``>`` one — whichever the collation happened to give.
    """
    key = _seed(db, selector, "not-a-timestamp")

    selected = selector.run(db, CUTOFF_WHOLE)

    assert (key in selected) is selector.unreadable_selected, f"{selector.name}: {selector.why_undated}"


class TestTheIpAnonymisationTask:
    """``anonymize_old_ips`` reaches the database only through the repository (#1784)."""

    def test_the_task_anonymises_what_the_repository_selects(self, db, monkeypatch):
        from app.common import dependencies
        from app.tasks import auth_tasks

        tokens = db.collection(col.REFRESH_TOKENS)
        base = {"user_key": USER, "token_hash": "h", "revoked": False, "expires_at": FAR_FUTURE}
        old = tokens.insert({**base, "ip_address": "192.0.2.77", "created_at": FAR_PAST})["_key"]
        young = tokens.insert({**base, "ip_address": "192.0.2.78", "created_at": FAR_FUTURE})["_key"]
        monkeypatch.setattr(dependencies, "get_refresh_token_repo", lambda: ArangoRefreshTokenRepository(db))

        result = auth_tasks.anonymize_old_ips()

        assert result == {"anonymized": 1}
        assert tokens.get(old)["ip_address"] == "192.0.2.0"
        assert tokens.get(old)["ip_anonymized_at"]
        assert tokens.get(young)["ip_address"] == "192.0.2.78"
        # A second run finds nothing: ``ip_anonymized_at`` takes the row out of the selection.
        assert ArangoRefreshTokenRepository(db).list_unanonymized_ips_before(FAR_FUTURE) == []
