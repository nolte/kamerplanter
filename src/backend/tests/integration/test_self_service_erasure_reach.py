"""#1645 — the self-service Art. 17 erasure reaches every step of the declared plan.

Sibling of ``test_account_erasure_reach.py`` (the platform-admin path, #1664).
Until #1645 the scheduled self-service path — ``request_erasure`` now, the daily
``retention.execute_scheduled_erasures`` beat 90 days later — ran the object
storage and reference-index phases and nothing in ArangoDB: every document of
the subject survived, no anonymisation rule was applied, and the erasure record
kept the subject's plaintext key.

This module drives that path end to end over a real server, the way the beat
does: ``PrivacyService.request_erasure`` creates the request, then
``PrivacyService.execute_scheduled_erasures`` runs with a clock past the grace
period. Evidence is read off the rows, never off a status field alone:

* every row of the subject in a delete step is gone;
* every retained row of the subject survives with no trace of the subject;
* the erasure request the subject filed is retained, ends ``completed`` and
  carries the ``anon_…`` tombstone hash instead of the key;
* every row of a second user is byte-for-byte unchanged (``_rev`` included).

The seeded collections come off the plan, through the sibling module's seeding
helpers, so a new declared step is seeded here without an edit.

Runs in CI against a service container; locally it needs a database::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_self_service_erasure_reach.py -v
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

# The module, not its names: importing ``test_*`` functions by name would make
# pytest collect the sibling's tests a second time in this module.
import tests.integration.test_account_erasure_reach as reach
from app.common.exceptions import ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("privacy_self_service_erasure_reach")

SUBJECT = reach.SUBJECT
OTHER = reach.OTHER
SALT = reach.SALT

pytestmark = pytest.mark.usefixtures("arango_db")


def _service(database) -> PrivacyService:
    """The privacy service as ``get_privacy_service`` builds it for the beat.

    Real ArangoDB repositories on every collection the Art. 17 path reads or
    writes; the object-storage and pgvector phases are left unwired (they are
    not ArangoDB and are covered by the unit tier).
    """
    password_engine = MagicMock()
    password_engine.verify_password.return_value = True
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=ArangoErasureRepository(database),
        email_change_repo=MagicMock(),
        user_repo=ArangoUserRepository(database),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=password_engine,
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://localhost",
        membership_repo=ArangoMembershipRepository(database),
        pest_image_repo=ArangoPestImageRepository(database),
        erasure_executor=ArangoErasureExecutor(database),
        tombstone_salt=SALT,
    )


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    yield client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def erased(database):
    """Seed A and B, file A's request, run the daily beat past the grace period."""
    plan = reach._plan()
    seeded = reach._seed(database, plan)
    before_other = reach._snapshot(database, seeded[OTHER])

    service = _service(database)
    request = service.request_erasure(SUBJECT, "confirm")
    assert request.key is not None
    beat_clock = datetime.now(UTC) + timedelta(days=PrivacyService.HARD_DELETE_DAYS + 1)
    finalised = asyncio.run(_service(database).execute_scheduled_erasures(beat_clock))
    return SimpleNamespace(
        plan=plan,
        seeded=seeded,
        before_other=before_other,
        request_id=f"{col.ERASURE_REQUESTS}/{request.key}",
        finalised=finalised,
        beat_clock=beat_clock,
    )


def test_every_subject_row_of_a_delete_step_is_gone(database, erased):
    survivors = [
        doc_id
        for doc_id in reach._deleted_rows(erased.plan, erased.seeded[SUBJECT], SUBJECT)
        if reach._read(database, doc_id) is not None
    ]
    assert survivors == []


def test_the_edge_the_request_itself_wrote_is_gone(database, erased):
    """``request_erasure`` writes ``users -> erasure_requests``; the plan removes it."""
    cursor = database.aql.execute(
        "FOR e IN @@edges FILTER e._from == @user RETURN e._key",
        bind_vars={"@edges": col.REQUESTED_ERASURE, "user": f"{col.USERS}/{SUBJECT}"},
    )
    assert list(cursor) == []


def test_every_retained_subject_row_survives_without_a_trace_of_the_subject(database, erased):
    lost: list[str] = []
    traces: list[str] = []
    for doc_id in reach._retained_rows(erased.plan, SUBJECT):
        doc = reach._read(database, doc_id)
        if doc is None:
            lost.append(doc_id)
            continue
        traces.extend(
            f"{doc_id}.{field}={value!r}"
            for field, value in doc.items()
            if not field.startswith("_") and value in (SUBJECT, reach._display_text(SUBJECT))
        )
    assert lost == []
    assert traces == []


def test_the_request_the_subject_filed_ends_completed_under_the_hash(database, erased):
    """The audit record survives, says ``completed`` and no longer names the subject.

    ``_pseudonymize_audit_collections`` rewrites ``erasure_requests.user_key``
    inside the run; the status write that follows must address the request by
    its document key and must not put the plaintext key back.
    """
    doc: dict[str, Any] | None = reach._read(database, erased.request_id)
    assert doc is not None, "the erasure request is the Art. 5(2) audit record and must be retained"
    tombstone = ErasureEngine.compute_tombstone_hash(SUBJECT, SALT)
    assert doc["user_key"] == tombstone
    assert doc["status"] == "completed"
    assert doc["completed_at"] is not None
    assert doc.get("error_message") is None
    assert [field for field, value in doc.items() if value == SUBJECT] == []
    assert erased.finalised == 1


def test_every_row_of_the_other_user_is_unchanged(database, erased):
    after = reach._snapshot(database, erased.seeded[OTHER])
    changed = [doc_id for doc_id, doc in erased.before_other.items() if after[doc_id] != doc]
    assert changed == []
    assert all(doc is not None for doc in erased.before_other.values())


def test_the_next_beat_selects_nothing_and_writes_nothing(database, erased):
    """A completed request is not re-selected, so no second run rewrites the audit hash."""
    before = reach._snapshot(database, erased.seeded[SUBJECT]) | reach._snapshot(database, erased.seeded[OTHER])
    request_before = reach._read(database, erased.request_id)

    finalised = asyncio.run(_service(database).execute_scheduled_erasures(erased.beat_clock + timedelta(days=1)))

    assert finalised == 0
    after = reach._snapshot(database, erased.seeded[SUBJECT]) | reach._snapshot(database, erased.seeded[OTHER])
    assert after == before
    assert reach._read(database, erased.request_id) == request_before


def test_a_partially_completed_request_blocks_a_new_one(database, erased):
    """Operator decision (#1645): ``partially_completed`` is an open Art. 17 duty.

    The daily beat still owes that request a run, so a second request for the
    same account would only schedule a duplicate. Read through the real query.
    """
    subject = "user-d"
    database.collection(col.USERS).insert(reach._user_document(subject))
    database.collection(col.ERASURE_REQUESTS).insert(
        {"_key": "d-open", "user_key": subject, "status": "partially_completed", "error_message": "storage down"}
    )

    active = ArangoErasureRepository(database).find_active_for_user(subject)
    assert active is not None and active.key == "d-open"
    with pytest.raises(ValidationError):
        _service(database).request_erasure(subject, "confirm")
    remaining = list(
        database.aql.execute(
            "FOR r IN @@c FILTER r.user_key == @u RETURN r._key",
            bind_vars={"@c": col.ERASURE_REQUESTS, "u": subject},
        )
    )
    assert remaining == ["d-open"]
