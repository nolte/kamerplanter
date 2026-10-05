"""#2137 (MT-041): a service account and its keys against a **real** ArangoDB.

The real ``TenantService`` and ``AuthService`` over the real user, membership, tenant, API-key and
security-audit repositories; only the step-up is the passed double (the real verifier is driven in
``tests/api/test_service_account_routes_api.py``). What is asserted is read off the collections, or
obtained by authenticating the raw key the creation returned — the production path, not a fixture:

* the stored account is ``service`` without a password and cannot sign in;
* the stored key is scoped to its tenant and carries the controls; it is refused outside its allowlist;
* the quota query counts service accounts only;
* the rotation's overlap is written by ``expire_no_later_than`` (``DATE_TIMESTAMP``, never later than
  the stored end, whatever spelling the stored timestamp has) and enforced on the next authentication;
* a removal revokes the keys, ends the membership and deactivates the account.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.enums import AdminScope, SecurityAuditAction, TenantRole
from app.common.exceptions import KamerplanterError, UnauthorizedError
from app.data_access.arango import collections as col
from app.data_access.arango.api_key_repository import ArangoApiKeyRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.security_audit_repository import ArangoSecurityAuditRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.step_up import STEP_UP_PASSED, PassedStepUpVerifier

TEST_DATABASE = run_database_name("service_accounts")
TENANT = "t-garden"
LEAD = User.model_validate({"_key": "u-lead", "email": "lead@example.com", "display_name": "Lead"})
INSIDE = "192.168.1.20"
OUTSIDE = "203.0.113.7"

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
        col.API_KEYS,
        col.HAS_API_KEY,
        col.SECURITY_AUDIT_LOG,
    ):
        database.collection(name).truncate()
    database.collection(col.USERS).insert(
        {"_key": "u-lead", "email": "lead@example.com", "display_name": "Lead", "is_active": True}
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
    ArangoMembershipRepository(database).create(
        Membership(
            user_key="u-lead",
            tenant_key=TENANT,
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT, AdminScope.TECHNICAL],
            is_active=True,
        )
    )
    return database


def _services(db, *, max_service_accounts: int = 20) -> tuple[TenantService, AuthService]:
    users = ArangoUserRepository(db)
    keys = ArangoApiKeyRepository(db)
    tenant_service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        security_audit=SecurityAuditService(ArangoSecurityAuditRepository(db)),
        step_up_verifier=PassedStepUpVerifier(),  # type: ignore[arg-type]
        task_repo=MagicMock(),
        user_repo=users,
        api_key_repo=keys,
        max_service_accounts=max_service_accounts,
    )
    auth_service = AuthService(
        user_repo=users,
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="https://app.test",
        api_key_repo=keys,
        tenant_service=tenant_service,
    )
    return tenant_service, auth_service


def _create(tenant_service: TenantService, name: str = "Home Assistant"):  # noqa: ANN202
    return tenant_service.create_service_account(
        TENANT,
        name=name,
        role=TenantRole.GROWER,
        ip_allowlist=["192.168.1.0/24"],
        rate_limit_per_minute=None,
        expires_at=datetime.now(UTC) + timedelta(days=90),
        requester=LEAD,
        client_ip=None,
        **STEP_UP_PASSED,
    )


def _rotate(tenant_service: TenantService, account_key: str, overlap_minutes: int):  # noqa: ANN202
    return tenant_service.rotate_service_account_key(
        TENANT,
        account_key,
        overlap_minutes=overlap_minutes,
        expires_at=None,
        requester=LEAD,
        client_ip=None,
        **STEP_UP_PASSED,
    )


def test_the_stored_account_key_and_audit_row(db) -> None:
    tenant_service, _ = _services(db)

    created = _create(tenant_service)

    account = db.collection(col.USERS).get(created.key)
    assert account["account_type"] == "service"
    assert account.get("password_hash") is None
    membership = db.collection(col.MEMBERSHIPS).get(created.membership_key)
    assert (membership["role"], membership["tenant_key"], membership.get("admin_scopes") or []) == (
        "grower",
        TENANT,
        [],
    )
    (key,) = list(db.collection(col.API_KEYS).find({"user_key": created.key}))
    assert key["tenant_scope"] == TENANT
    assert key["ip_allowlist"] == ["192.168.1.0/24"]
    assert key["expires_at"] is not None
    assert key["key_hash"] != created.api_key.raw_key
    (row,) = list(db.collection(col.SECURITY_AUDIT_LOG).find({"target_user_key": created.key}))
    assert (row["action"], row["via"], row["actor_user_key"]) == ("membership_added", "tenant_admin", "u-lead")


def test_the_key_authenticates_inside_its_allowlist_only(db) -> None:
    tenant_service, auth_service = _services(db)
    created = _create(tenant_service)

    principal = auth_service.authenticate_api_key(created.api_key.raw_key, client_ip=INSIDE)

    assert principal is not None and principal.key == created.key
    assert principal.api_key_tenant_scope == TENANT
    with pytest.raises(UnauthorizedError):
        auth_service.authenticate_api_key(created.api_key.raw_key, client_ip=OUTSIDE)


def test_the_service_account_cannot_sign_in(db) -> None:
    tenant_service, auth_service = _services(db)
    created = _create(tenant_service)
    email = db.collection(col.USERS).get(created.key)["email"]

    with pytest.raises(KamerplanterError) as refused:
        auth_service.login_local(email, "any password at all", ip_address=INSIDE)

    assert refused.value.status_code == 401


def test_the_quota_counts_service_accounts_only(db) -> None:
    tenant_service, _ = _services(db, max_service_accounts=2)
    _create(tenant_service, "First")
    _create(tenant_service, "Second")

    counted = ArangoMembershipRepository(db).active_service_account_memberships(tenant_key=TENANT)
    with pytest.raises(KamerplanterError) as refused:
        _create(tenant_service, "Third")

    assert len(counted) == 2, "the lead's own membership is not a service account"
    assert refused.value.error_code == "SERVICE_ACCOUNT_LIMIT_REACHED"


def test_a_rotation_with_overlap_keeps_the_old_key_until_the_window_closes(db) -> None:
    tenant_service, auth_service = _services(db)
    created = _create(tenant_service)
    old_raw = created.api_key.raw_key

    rotated = _rotate(tenant_service, created.key, overlap_minutes=30)

    stored_old = db.collection(col.API_KEYS).get(created.api_key.key)
    ends_at = datetime.fromisoformat(stored_old["expires_at"])
    assert abs(ends_at - (datetime.now(UTC) + timedelta(minutes=30))) < timedelta(minutes=1)
    assert auth_service.authenticate_api_key(old_raw, client_ip=INSIDE) is not None
    new_principal = auth_service.authenticate_api_key(rotated.api_key.raw_key, client_ip=INSIDE)
    assert new_principal is not None and new_principal.key == created.key
    # The successor kept the allowlist.
    with pytest.raises(UnauthorizedError):
        auth_service.authenticate_api_key(rotated.api_key.raw_key, client_ip=OUTSIDE)

    # The window closes: the next authentication refuses the old key — no task had to run.
    keys = ArangoApiKeyRepository(db)
    assert keys.expire_no_later_than(created.api_key.key, datetime.now(UTC) - timedelta(seconds=1))
    assert auth_service.authenticate_api_key(old_raw, client_ip=INSIDE) is None
    (row,) = list(
        db.collection(col.SECURITY_AUDIT_LOG).find({"action": SecurityAuditAction.SERVICE_ACCOUNT_KEY_ROTATED.value})
    )
    assert row["target_user_key"] == created.key


def test_an_overlap_never_extends_a_key_that_ends_sooner(db) -> None:
    keys = ArangoApiKeyRepository(db)
    tenant_service, _ = _services(db)
    created = _create(tenant_service)
    soon = (datetime.now(UTC) + timedelta(minutes=5)).replace(microsecond=0)
    # Stored in the other ISO spelling, on a whole second ("...:00Z"); the window ends half a second
    # later ("...:00.500000+00:00"). As text the stored value sorts *after* it ('Z' > '.'), so a string
    # comparison would move the end later — the comparison must be on time.
    db.collection(col.API_KEYS).update({"_key": created.api_key.key, "expires_at": soon.strftime("%Y-%m-%dT%H:%M:%SZ")})

    changed = keys.expire_no_later_than(created.api_key.key, soon + timedelta(milliseconds=500))

    assert changed is False
    assert db.collection(col.API_KEYS).get(created.api_key.key)["expires_at"] == soon.strftime("%Y-%m-%dT%H:%M:%SZ")
    # The control: an earlier end is written.
    assert keys.expire_no_later_than(created.api_key.key, soon - timedelta(minutes=1)) is True


def test_a_rotation_without_overlap_revokes_the_old_key_at_once(db) -> None:
    tenant_service, auth_service = _services(db)
    created = _create(tenant_service)

    _rotate(tenant_service, created.key, overlap_minutes=0)

    assert db.collection(col.API_KEYS).get(created.api_key.key)["revoked"] is True
    assert auth_service.authenticate_api_key(created.api_key.raw_key, client_ip=INSIDE) is None


def test_removal_revokes_ends_and_deactivates(db) -> None:
    tenant_service, auth_service = _services(db)
    created = _create(tenant_service)

    tenant_service.remove_service_account(TENANT, created.key, requester=LEAD, client_ip=None, **STEP_UP_PASSED)

    assert all(k["revoked"] for k in db.collection(col.API_KEYS).find({"user_key": created.key}))
    assert db.collection(col.MEMBERSHIPS).get(created.membership_key) is None
    assert db.collection(col.USERS).get(created.key)["is_active"] is False
    assert auth_service.authenticate_api_key(created.api_key.raw_key, client_ip=INSIDE) is None
    assert ArangoMembershipRepository(db).active_service_account_memberships(tenant_key=TENANT) == []
