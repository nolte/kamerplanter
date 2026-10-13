"""#2009 / #2032 / REQ-024 AK-56, AK-57 — no step-up, no change: a tenant stays active, its members unchanged.

Driven end to end against a **real** ArangoDB: the real platform-admin routes, the real
``TenantService`` with its real step-up verifier, over the real
``ArangoTenantRepository`` and ``ArangoMembershipRepository`` (which own the
``has_membership`` / ``membership_in`` edges). What survives a refused request is read
straight off the collections — the tenant document's ``status`` (``is_active`` until v0085), the membership
document and both of its edges — so a refusal observed here is the production path
leaving the store as it was, not a double that never wrote.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user, require_platform_admin
from app.common.dependencies import get_tenant_service, get_user_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("admin_tenant_step_up")
TENANT = "t-garden"
MEMBER = "u-lead"
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
ADMIN = User.model_validate(
    {
        "_key": "admin-2009",
        "email": "admin-2009@example.com",
        "display_name": "Admin",
        "password_hash": PasswordEngine().hash_password(PASSWORD),
    }
)

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for name in (col.TENANTS, col.USERS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN):
        database.collection(name).truncate()
    database.collection(col.USERS).insert(
        {"_key": MEMBER, "email": "lead@example.com", "display_name": "Lead", "is_active": True}
    )
    database.collection(col.TENANTS).insert(
        {
            "_key": TENANT,
            "name": "Community Garden",
            "slug": "community-garden",
            "tenant_type": "organization",
            "owner_user_key": MEMBER,
            "status": "active",  # v0085 (#2123): the lifecycle state replaced the bool
            "is_platform": False,
            "max_members": 50,
            "settings": {},
        }
    )
    return database


def _client(db) -> tuple[TestClient, str]:
    memberships = ArangoMembershipRepository(db)
    # The tenant's only lead — with its two edges, created the way the product creates them.
    lead = memberships.create(Membership(user_key=MEMBER, tenant_key=TENANT, role=TenantRole.LEAD, is_active=True))
    # No step_up_verifier argument: the default is the real verifier, which is what this test measures.
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=memberships,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )
    users = MagicMock()
    users.get_user.return_value = ADMIN
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: ADMIN
    app.dependency_overrides[get_tenant_service] = lambda: service
    app.dependency_overrides[get_user_service] = lambda: users
    return TestClient(app, raise_server_exceptions=False), lead.key or ""


def _membership_intact(db, membership_key: str) -> bool:
    membership_id = f"{col.MEMBERSHIPS}/{membership_key}"
    has = [e for e in db.collection(col.HAS_MEMBERSHIP).all() if e["_to"] == membership_id]
    into = [e for e in db.collection(col.MEMBERSHIP_IN).all() if e["_from"] == membership_id]
    return db.collection(col.MEMBERSHIPS).get(membership_key) is not None and len(has) == 1 and len(into) == 1


def test_a_tenant_stays_active_without_the_admins_step_up_and_is_deactivated_with_it(db):
    client, _lead = _client(db)

    refused = client.patch(f"/api/v1/admin/platform/tenants/{TENANT}", json={"is_active": False})

    assert refused.status_code == 401, refused.text
    assert db.collection(col.TENANTS).get(TENANT)["status"] == "active"

    # The control: the same request with the admin's own password goes through.
    accepted = client.patch(
        f"/api/v1/admin/platform/tenants/{TENANT}", json={"is_active": False, "current_password": PASSWORD}
    )
    assert accepted.status_code == 200, accepted.text
    stored = db.collection(col.TENANTS).get(TENANT)
    assert stored["status"] == "suspended"  # the admin's bool is the suspension switch (#2123)
    assert "current_password" not in stored


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/admin/platform/tenants/" + TENANT + "/members/{key}", id="tenant view"),
        pytest.param("/api/v1/admin/platform/users/" + MEMBER + "/memberships/{key}", id="user view"),
    ],
)
def test_the_last_lead_stays_without_the_admins_step_up_and_is_removed_with_it(db, path: str):
    client, lead = _client(db)

    refused = client.request("DELETE", path.format(key=lead))

    assert refused.status_code == 401, refused.text
    assert _membership_intact(db, lead)

    accepted = client.request("DELETE", path.format(key=lead), json={"current_password": PASSWORD})
    assert accepted.status_code == 204, accepted.text
    assert db.collection(col.MEMBERSHIPS).get(lead) is None
    assert not _membership_intact(db, lead)


# ── #2106: adding an account to a tenant ─────────────────────────────────────


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/admin/platform/tenants/" + TENANT + "/members", id="tenant view"),
        pytest.param("/api/v1/admin/platform/users/u-newcomer/memberships", id="user view"),
    ],
)
def test_nobody_is_added_without_the_admins_step_up_and_is_added_with_it(db, path: str):
    db.collection(col.USERS).insert(
        {"_key": "u-newcomer", "email": "newcomer@example.com", "display_name": "Newcomer", "is_active": True}
    )
    client, _lead = _client(db)
    body = (
        {"user_key": "u-newcomer", "role": "grower"} if "tenants" in path else {"tenant_key": TENANT, "role": "grower"}
    )

    def memberships_of_newcomer() -> list[dict]:
        return [m for m in db.collection(col.MEMBERSHIPS).all() if m["user_key"] == "u-newcomer"]

    refused = client.post(path, json=body)

    assert refused.status_code == 401, refused.text
    assert memberships_of_newcomer() == []
    assert [e for e in db.collection(col.HAS_MEMBERSHIP).all() if e["_from"] == "users/u-newcomer"] == []

    # The control: the same request with the admin's own password goes through, with both edges.
    accepted = client.post(path, json={**body, "current_password": PASSWORD})
    assert accepted.status_code == 201, accepted.text
    (stored,) = memberships_of_newcomer()
    assert stored["role"] == "grower"
    assert "current_password" not in stored
    assert _membership_intact(db, stored["_key"])


# ── #2032: the role of a member, and the tenant administrator's own routes ───


def _role_of(db, membership_key: str) -> str:
    return db.collection(col.MEMBERSHIPS).get(membership_key)["role"]


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/api/v1/admin/platform/tenants/" + TENANT + "/members/{key}/role", id="tenant view"),
        pytest.param("/api/v1/admin/platform/users/" + MEMBER + "/memberships/{key}/role", id="user view"),
    ],
)
def test_the_last_lead_keeps_its_role_without_the_admins_step_up_and_is_demoted_with_it(db, path: str):
    client, lead = _client(db)

    refused = client.patch(path.format(key=lead), json={"role": "viewer"})

    assert refused.status_code == 401, refused.text
    assert _role_of(db, lead) == "lead"

    accepted = client.patch(path.format(key=lead), json={"role": "viewer", "current_password": PASSWORD})
    assert accepted.status_code == 200, accepted.text
    stored = db.collection(col.MEMBERSHIPS).get(lead)
    assert stored["role"] == "viewer"
    assert "current_password" not in stored


def _tenant_admin_client(db) -> tuple[TestClient, str, str]:
    """The tenant's own secretary (``management``, viewer) acting through ``/tenants/{slug}/…``."""
    memberships = ArangoMembershipRepository(db)
    lead = memberships.create(Membership(user_key=MEMBER, tenant_key=TENANT, role=TenantRole.LEAD, is_active=True))
    secretary = User.model_validate(
        {
            "_key": "secretary-2032",
            "email": "secretary-2032@example.com",
            "display_name": "Secretary",
            "password_hash": PasswordEngine().hash_password(PASSWORD),
        }
    )
    db.collection(col.USERS).insert({"_key": secretary.key, "email": secretary.email, "display_name": "Secretary"})
    memberships.create(
        Membership(
            user_key=secretary.key or "",
            tenant_key=TENANT,
            role=TenantRole.VIEWER,
            admin_scopes=[AdminScope.MANAGEMENT],
            is_active=True,
        )
    )
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=memberships,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: secretary
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False), lead.key or "", "community-garden"


def test_a_tenant_admin_neither_demotes_nor_removes_the_last_lead_without_the_step_up(db):
    client, lead, slug = _tenant_admin_client(db)
    role_path = f"/api/v1/tenants/{slug}/members/{lead}/role"
    member_path = f"/api/v1/tenants/{slug}/members/{lead}"

    demoted = client.patch(role_path, json={"role": "viewer"})
    removed = client.request("DELETE", member_path)

    assert (demoted.status_code, removed.status_code) == (401, 401), (demoted.text, removed.text)
    assert _role_of(db, lead) == "lead"
    assert _membership_intact(db, lead)

    # The controls: with the actor's own password both go through, the removal taking both edges.
    assert client.patch(role_path, json={"role": "viewer", "current_password": PASSWORD}).status_code == 200
    assert _role_of(db, lead) == "viewer"
    gone = client.request("DELETE", member_path, json={"current_password": PASSWORD})
    assert gone.status_code == 200, gone.text
    assert not _membership_intact(db, lead)
    assert db.collection(col.MEMBERSHIPS).get(lead) is None
