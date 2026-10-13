"""#1824 — ``ArangoMembershipRepository.active_member_joined_at`` against a real server.

The erasure-together rule tells a member who was there when the erasure froze a
personal tenant from one who joined after it by the start of the membership. The
query must apply the same population as ``active_member_user_keys`` (active
membership of an *active* account) and hand back an instant, whatever offset the
stored string carries.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("membership_joined_at")
TENANT = "t-1"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    yield database
    system.delete_database(TEST_DATABASE)


def _account(database, key: str, *, active: bool = True) -> None:
    database.collection(col.USERS).insert({"_key": key, "email": f"{key}@example.com", "is_active": active})


def _membership(database, user: str, joined_at: str | None, *, tenant: str = TENANT, active: bool = True) -> None:
    doc = {"user_key": user, "tenant_key": tenant, "is_active": active, "role": "grower"}
    if joined_at is not None:
        doc["joined_at"] = joined_at
    database.collection(col.MEMBERSHIPS).insert(doc)


def test_it_reports_the_start_of_every_active_membership_of_an_active_account(database):
    for key in ("early", "late", "unknown", "garbled", "closing", "left"):
        _account(database, key, active=key != "closing")
    _membership(database, "early", "2026-09-01T10:00:00+00:00")
    _membership(database, "late", "2026-10-01T12:00:00+02:00")
    _membership(database, "unknown", None)
    _membership(database, "garbled", "yesterday-ish")
    _membership(database, "closing", "2026-09-01T10:00:00+00:00")
    _membership(database, "left", "2026-09-01T10:00:00+00:00", active=False)
    _membership(database, "early", "2026-09-01T10:00:00+00:00", tenant="t-elsewhere")

    joined = ArangoMembershipRepository(database).active_member_joined_at(tenant_key=TENANT)

    assert joined == {
        "early": datetime(2026, 9, 1, 10, tzinfo=UTC),
        "late": datetime(2026, 10, 1, 10, tzinfo=UTC),
        "unknown": None,
        "garbled": None,  # unreadable counts as not recorded — it must not fail an erasure retry
    }
    # The same population as the key list the erasure decision reads.
    assert sorted(joined) == sorted(ArangoMembershipRepository(database).active_member_user_keys(tenant_key=TENANT))
