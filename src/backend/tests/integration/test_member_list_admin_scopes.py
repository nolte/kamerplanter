"""#2166 — ``ArangoMembershipRepository.list_by_tenant`` reports each member's ``admin_scopes``.

The member list (``GET /tenants/{slug}/members``) is a read projection: the AQL
returns an object literal and :class:`~app.domain.models.membership.MemberInfo`
is built from it. ``admin_scopes`` has a default (``[]``), so a projection that
leaves the field out does not fail — every member then reports no scope at all,
the ``management`` holder included. Measured before the fix: the API answered
``[]`` for every member.

Against a real server, because the defect lives in the AQL text.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import AdminScope
from app.data_access.arango import collections as col
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2166 measures the member-list projection on a real ArangoDB"),
]

TEST_DATABASE = run_database_name("member_list_admin_scopes")
TENANT = "t-scopes"


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


def _member(database, key: str, joined_at: str, scopes: list[str] | None) -> None:
    database.collection(col.USERS).insert({"_key": key, "email": f"{key}@example.com", "display_name": key})
    doc: dict[str, object] = {
        "_key": f"m-{key}",
        "user_key": key,
        "tenant_key": TENANT,
        "role": "lead",
        "is_active": True,
        "joined_at": joined_at,
    }
    if scopes is not None:
        doc["admin_scopes"] = scopes
    database.collection(col.MEMBERSHIPS).insert(doc)


def test_the_member_list_reports_the_stored_admin_scopes(database):
    _member(database, "both", "2026-09-01T10:00:00+00:00", ["technical", "management"])
    _member(database, "manager", "2026-09-02T10:00:00+00:00", ["management"])
    _member(database, "none", "2026-09-03T10:00:00+00:00", [])
    # A document written before REQ-049 carries no field at all: it reads as no scope, not as a failure.
    _member(database, "legacy", "2026-09-04T10:00:00+00:00", None)

    members = ArangoMembershipRepository(database).list_by_tenant(TENANT)

    assert {m.user_key: m.admin_scopes for m in members} == {
        "both": [AdminScope.MANAGEMENT, AdminScope.TECHNICAL],
        "manager": [AdminScope.MANAGEMENT],
        "none": [],
        "legacy": [],
    }
    # The windowed read (MT-035) is the same projection.
    window = ArangoMembershipRepository(database).list_by_tenant(TENANT, offset=0, limit=2)
    assert [m.admin_scopes for m in window] == [[AdminScope.MANAGEMENT, AdminScope.TECHNICAL], [AdminScope.MANAGEMENT]]
