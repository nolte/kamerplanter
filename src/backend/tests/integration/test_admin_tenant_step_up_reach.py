"""#2009 / REQ-024 AK-56 — without the admin's step-up a tenant stays active and its member stays in it.

Driven end to end against a **real** ArangoDB: the real platform-admin routes, the real
``TenantService`` with its real step-up verifier, over the real
``ArangoTenantRepository`` and ``ArangoMembershipRepository`` (which own the
``has_membership`` / ``membership_in`` edges). What survives a refused request is read
straight off the collections — the tenant document's ``is_active``, the membership
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
from app.common.auth import require_platform_admin
from app.common.dependencies import get_tenant_service, get_user_service
from app.common.enums import TenantRole
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
            "is_active": True,
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
    assert db.collection(col.TENANTS).get(TENANT)["is_active"] is True

    # The control: the same request with the admin's own password goes through.
    accepted = client.patch(
        f"/api/v1/admin/platform/tenants/{TENANT}", json={"is_active": False, "current_password": PASSWORD}
    )
    assert accepted.status_code == 200, accepted.text
    stored = db.collection(col.TENANTS).get(TENANT)
    assert stored["is_active"] is False
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
