"""MT-014 (#2111): a membership change leaves a row in the real ``security_audit_log``, and the row ages out.

Driven end to end against a **real** ArangoDB: the real platform-admin routes and the real
``TenantService`` over the real ``ArangoMembershipRepository`` / ``ArangoTenantRepository`` and
the real ``ArangoSecurityAuditRepository``. What the audit holds is read straight off the
collection, so a row observed here is the production path having written it, not a double that
was handed one. The retention sweep and its held-count are run against rows of different age.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.common.auth import require_platform_admin
from app.common.dependencies import get_security_audit_service, get_tenant_service, get_user_service
from app.common.enums import AdminScope, SecurityAuditAction, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.security_audit_repository import ArangoSecurityAuditRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.security_audit_service import SECURITY_AUDIT_RETENTION_DAYS, SecurityAuditService
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name


def _founder(key: str) -> User:
    """The founding account (#2137: ``create_organization`` takes the account, not its key)."""
    return User.model_validate({"_key": key, "email": f"{key}@example.org", "display_name": key})


TEST_DATABASE = run_database_name("security_audit_log")
TENANT = "t-garden"
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])
ADMIN = User.model_validate(
    {
        "_key": "admin-2111",
        "email": "admin-2111@example.com",
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
    for name in (
        col.TENANTS,
        col.USERS,
        col.MEMBERSHIPS,
        col.HAS_MEMBERSHIP,
        col.MEMBERSHIP_IN,
        col.SECURITY_AUDIT_LOG,
    ):
        database.collection(name).truncate()
    for key in ("u-lead", "u-new"):
        database.collection(col.USERS).insert(
            {"_key": key, "email": f"{key}@example.com", "display_name": key, "is_active": True}
        )
    database.collection(col.TENANTS).insert(
        {
            "_key": TENANT,
            "name": "Community Garden",
            "slug": "community-garden",
            "tenant_type": "organization",
            "owner_user_key": "u-lead",
            "is_active": True,
            "is_platform": False,
            "max_members": 50,
            "settings": {},
        }
    )
    return database


def _service(db) -> tuple[TenantService, ArangoMembershipRepository]:
    memberships = ArangoMembershipRepository(db)
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=memberships,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        security_audit=SecurityAuditService(ArangoSecurityAuditRepository(db)),
    )
    return service, memberships


def _client(db) -> tuple[TestClient, TenantService, ArangoMembershipRepository]:
    service, memberships = _service(db)
    users = MagicMock()
    users.get_user.return_value = ADMIN
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: ADMIN
    app.dependency_overrides[get_tenant_service] = lambda: service
    app.dependency_overrides[get_user_service] = lambda: users
    app.dependency_overrides[get_security_audit_service] = lambda: service._security_audit  # noqa: SLF001
    return TestClient(app, raise_server_exceptions=False), service, memberships


def _rows(db) -> list[dict]:
    return sorted(db.collection(col.SECURITY_AUDIT_LOG).all(), key=lambda r: r["created_at"])


def test_an_admin_add_a_role_change_and_a_removal_each_leave_a_row_the_admin_can_read(db) -> None:
    client, _service_, memberships = _client(db)
    base = f"/api/v1/admin/platform/tenants/{TENANT}/members"

    added = client.post(base, json={"user_key": "u-new", "role": "grower", "current_password": PASSWORD})
    assert added.status_code == 201, added.text
    key = added.json()["membership_key"]
    changed = client.patch(f"{base}/{key}/role", json={"role": "viewer", "current_password": PASSWORD})
    assert changed.status_code == 200, changed.text
    removed = client.request("DELETE", f"{base}/{key}", json={"current_password": PASSWORD})
    assert removed.status_code == 204, removed.text

    rows = _rows(db)
    assert [(r["action"], r["actor_user_key"], r["target_user_key"], r["tenant_key"]) for r in rows] == [
        (SecurityAuditAction.MEMBERSHIP_ADDED, ADMIN.key, "u-new", TENANT),
        (SecurityAuditAction.MEMBERSHIP_ROLE_CHANGED, ADMIN.key, "u-new", TENANT),
        (SecurityAuditAction.MEMBERSHIP_REMOVED, ADMIN.key, "u-new", TENANT),
    ]
    assert [(r.get("old_role"), r.get("new_role")) for r in rows] == [
        (None, "grower"),
        ("grower", "viewer"),
        ("viewer", None),
    ]
    assert all(r["via"] == "platform_admin" and "created_at" in r for r in rows)

    listed = client.get("/api/v1/admin/platform/security-audit", params={"tenant_key": TENANT})
    assert listed.status_code == 200, listed.text
    assert [r["action"] for r in listed.json()] == ["membership_removed", "membership_role_changed", "membership_added"]
    assert client.get("/api/v1/admin/platform/security-audit", params={"tenant_key": "elsewhere"}).json() == []
    assert memberships.get_by_user_and_tenant("u-new", TENANT) is None


def test_leaving_scopes_and_creation_leave_rows_through_the_real_repositories(db) -> None:
    service, memberships = _service(db)

    tenant = service.create_organization(_founder("u-lead"), "Second Garden")
    lead = memberships.get_by_user_and_tenant("u-lead", tenant.key or "")
    assert lead is not None
    other = memberships.create(Membership(user_key="u-new", tenant_key=tenant.key or "", role=TenantRole.GROWER))
    service.change_member_scopes(
        tenant.key or "", other.key or "", [AdminScope.MANAGEMENT], [AdminScope.MANAGEMENT], actor_user_key="u-lead"
    )
    service.leave_tenant(tenant.key or "", "u-new")

    rows = _rows(db)
    assert [r["action"] for r in rows] == ["membership_added", "membership_scopes_changed", "membership_left"]
    assert (rows[0]["via"], rows[0]["new_role"]) == ("tenant_creation", "lead")
    assert (rows[1]["old_scopes"], rows[1]["new_scopes"]) == ([], ["management"])
    assert (rows[2]["actor_user_key"], rows[2]["target_user_key"], rows[2]["old_role"]) == ("u-new", "u-new", "grower")


def test_the_retention_sweep_deletes_the_expired_rows_only_and_counts_the_undated(db) -> None:
    repo = ArangoSecurityAuditRepository(db)
    now = datetime.now(UTC)
    stale = (now - timedelta(days=SECURITY_AUDIT_RETENTION_DAYS + 5)).isoformat()
    fresh = (now - timedelta(days=SECURITY_AUDIT_RETENTION_DAYS - 5)).isoformat()
    collection = db.collection(col.SECURITY_AUDIT_LOG)
    for key, created in (("stale", stale), ("fresh", fresh), ("undated", None)):
        doc = {"_key": key, "action": "membership_added", "via": "self", "actor_user_key": "a", "target_user_key": "b"}
        doc["tenant_key"] = TENANT
        if created is not None:
            doc["created_at"] = created
        collection.insert(doc)

    removed = repo.delete_expired(retention_days=SECURITY_AUDIT_RETENTION_DAYS)

    assert removed == 1
    assert sorted(r["_key"] for r in collection.all()) == ["fresh", "undated"]
    assert repo.count_undated() == 1
