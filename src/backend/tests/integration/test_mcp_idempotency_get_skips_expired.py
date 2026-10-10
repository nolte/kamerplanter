"""#2169 — the idempotency read hands out live records only.

``ArangoMcpIdempotencyRepository.get()`` filtered by scope alone, so a record
past its ``expires_at`` stayed a hit until the hourly
``mcp.cleanup_expired_idempotency`` sweep removed it — the REQ-033 24 h window
hung on the sweep. ``IdempotencyStore`` re-checks liveness (#2144), but that
check sits above a boundary every unit test doubles; the repository is the
owner of "which record exists", and only a real server can show what its AQL
selects for a stored ISO stamp, a naive one, a missing one and a garbled one.

Runs in CI against a service container; locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_mcp_idempotency_get_skips_expired.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.mcp_repository import ArangoMcpIdempotencyRepository
from app.domain.models.mcp import McpIdempotencyRecord
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("mcp_idempotency_get_live")
NOW = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
SCOPE = ("sa-1", "tenant-a", "create_site", "idem-1")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.MCP_IDEMPOTENCY_RECORD)
    yield db
    system.delete_database(TEST_DATABASE)


def _store(database, *, expires_at: datetime) -> ArangoMcpIdempotencyRepository:
    """Write the record through the production ``store`` — the stamp format the read must handle."""
    repo = ArangoMcpIdempotencyRepository(database)
    sa_key, tenant_key, tool, idem = SCOPE
    repo.store(
        McpIdempotencyRecord(
            service_account_key=sa_key,
            tenant_key=tenant_key,
            tool_name=tool,
            idempotency_key=idem,
            input_hash="h",
            result_payload={"summary": "created"},
            created_at=expires_at - timedelta(hours=24),
            expires_at=expires_at,
        )
    )
    return repo


def _overwrite_expires_at(database, value: object) -> None:
    key = ArangoMcpIdempotencyRepository._doc_key(*SCOPE)
    database.collection(col.MCP_IDEMPOTENCY_RECORD).update({"_key": key, "expires_at": value}, keep_none=False)


def test_a_live_record_is_returned(database):
    repo = _store(database, expires_at=NOW + timedelta(minutes=1))

    record = repo.get(*SCOPE, now=NOW)

    assert record is not None
    assert record.result_payload == {"summary": "created"}


def test_a_record_past_its_expiry_is_not_returned_although_it_is_still_stored(database):
    repo = _store(database, expires_at=NOW - timedelta(minutes=1))

    assert repo.get(*SCOPE, now=NOW) is None
    # Not swept yet — the read, not the sweep, is what refuses it.
    assert database.collection(col.MCP_IDEMPOTENCY_RECORD).count() == 1


def test_the_expiry_instant_itself_is_already_expired(database):
    """Same bound as ``IdempotencyStore._is_live`` (``expires_at > now``)."""
    repo = _store(database, expires_at=NOW)

    assert repo.get(*SCOPE, now=NOW) is None


def test_without_now_the_clock_decides(database):
    repo = _store(database, expires_at=datetime.now(UTC) - timedelta(seconds=5))

    assert repo.get(*SCOPE) is None


@pytest.mark.parametrize(
    ("stamp", "live"),
    [
        # A naive stamp is read as UTC, like ``_is_live`` and ``delete_expired``.
        ("2026-10-10T12:30:00", True),
        ("2026-10-10T11:30:00", False),
        # An offset stamp is compared as the instant it names: 13:30+02:00 is 11:30Z.
        ("2026-10-10T13:30:00+02:00", False),
        # Missing or unreadable: delete_expired sweeps it, so the read must not hand it out.
        (None, False),
        ("not-a-date", False),
    ],
)
def test_the_comparison_is_by_instant_and_unreadable_counts_as_expired(database, stamp, live):
    repo = _store(database, expires_at=NOW + timedelta(hours=1))
    _overwrite_expires_at(database, stamp)

    assert (repo.get(*SCOPE, now=NOW) is not None) is live
