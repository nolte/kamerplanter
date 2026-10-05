"""#2118 (MT-022): a tenant is founded with its lead membership, both edges and audit row - or not at all.

Measured on a **real** ArangoDB 3.12.8 before the change, by injecting a failing second edge write into
``create_personal_tenant``: the tenant document (its slug taken), the membership and one edge stayed behind and
nobody could reach or delete the tenant; and a registration whose personal-tenant write failed left a user with
its provider and no tenant, which the retry then answered as "registered" without ever creating one.

Here the same faults are injected at **each** of the five writes of the founding transaction and the collections
are read afterwards: nothing is left. The registration is driven through the real ``AuthService`` over the real
user, provider and tenant repositories: a failed registration leaves no account, and the retry - with the fault
gone - produces the full set. Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.exceptions import DuplicateError
from app.data_access.arango import collections as col
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.security_audit_repository import ArangoSecurityAuditRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name


def _founder(key: str) -> User:
    """The founding account (#2137: ``create_organization`` takes the account, not its key)."""
    return User.model_validate({"_key": key, "email": f"{key}@example.org", "display_name": key})


TEST_DATABASE = run_database_name("tenant_founding_atomicity")
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["Correct", "horse", "battery", "staple", "9!"])
FOUNDING_COLLECTIONS = (col.TENANTS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.SECURITY_AUDIT_LOG)

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
    for name in (*FOUNDING_COLLECTIONS, col.USERS, col.AUTH_PROVIDERS):
        database.collection(name).truncate()
    return database


def _tenant_service(db) -> TenantService:
    return TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        security_audit=SecurityAuditService(ArangoSecurityAuditRepository(db)),
    )


def _counts(db, names=FOUNDING_COLLECTIONS) -> dict[str, int]:
    return {name: db.collection(name).count() for name in names}


def _fail_on(monkeypatch, collection: str) -> None:
    original = ArangoTenantRepository._insert_in

    def failing(self, transaction, name, data):
        if name == collection:
            raise RuntimeError(f"injected: the write to {name} fails")
        return original(self, transaction, name, data)

    monkeypatch.setattr(ArangoTenantRepository, "_insert_in", failing)


def test_the_founding_writes_all_five_documents(db) -> None:
    tenant = _tenant_service(db).create_personal_tenant("u-1", "Garden Owner")

    assert _counts(db) == dict.fromkeys(FOUNDING_COLLECTIONS, 1)
    (membership,) = list(db.collection(col.MEMBERSHIPS).all())
    assert (membership["tenant_key"], membership["role"]) == (tenant.key, "lead")
    (audit,) = list(db.collection(col.SECURITY_AUDIT_LOG).all())
    assert (audit["via"], audit["tenant_key"], audit["membership_key"]) == (
        "registration",
        tenant.key,
        membership["_key"],
    )


@pytest.mark.parametrize("failing", FOUNDING_COLLECTIONS)
def test_a_failure_on_any_one_write_leaves_no_tenant_no_member_no_edge_no_audit(db, monkeypatch, failing: str) -> None:
    service = _tenant_service(db)
    _fail_on(monkeypatch, failing)

    with pytest.raises(RuntimeError, match="injected"):
        service.create_personal_tenant("u-1", "Garden Owner")

    assert _counts(db) == dict.fromkeys(FOUNDING_COLLECTIONS, 0)


def test_a_failed_founding_leaves_the_slug_free_and_the_next_one_gets_it(db, monkeypatch) -> None:
    service = _tenant_service(db)
    with monkeypatch.context() as patched:
        _fail_on(patched, col.MEMBERSHIP_IN)
        with pytest.raises(RuntimeError):
            service.create_organization(_founder("u-1"), "Community Garden")

    founded = service.create_organization(_founder("u-1"), "Community Garden")

    assert founded.slug == "community-garden"  # not "-2": the failed attempt took nothing


def test_a_taken_slug_is_a_duplicate_and_the_existing_tenant_is_untouched(db, monkeypatch) -> None:
    service = _tenant_service(db)
    first = service.create_organization(_founder("u-1"), "Community Garden")
    before = _counts(db)
    monkeypatch.setattr(service, "_ensure_unique_slug", lambda slug, exclude_key=None: first.slug)

    with pytest.raises(DuplicateError):
        service.create_organization(_founder("u-2"), "Community Garden")

    assert _counts(db) == before


def _auth_service(db) -> AuthService:
    return AuthService(
        user_repo=ArangoUserRepository(db),
        auth_provider_repo=ArangoAuthProviderRepository(db),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=MagicMock(),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="https://app.test",
        tenant_service=_tenant_service(db),
        require_email_verification=False,
    )


def _account_set(db) -> dict[str, int]:
    return _counts(db, (col.USERS, col.AUTH_PROVIDERS, *FOUNDING_COLLECTIONS))


@pytest.mark.parametrize("failing", [col.MEMBERSHIP_IN, col.SECURITY_AUDIT_LOG])
def test_a_registration_whose_tenant_write_fails_leaves_no_account_and_the_retry_succeeds(
    db, monkeypatch, failing: str
) -> None:
    auth = _auth_service(db)
    with monkeypatch.context() as patched:
        _fail_on(patched, failing)
        with pytest.raises(RuntimeError, match="injected"):
            auth.register_local("new@example.com", PASSWORD, "New Gardener")

    assert _account_set(db) == dict.fromkeys(_account_set(db), 0), "nothing of the failed registration remains"

    # The retry is a genuine registration, not the duplicate-suppression answer to a stranded account.
    auth.register_local("new@example.com", PASSWORD, "New Gardener")
    assert _account_set(db) == dict.fromkeys(_account_set(db), 1)


def test_a_registration_whose_provider_write_fails_leaves_no_account(db, monkeypatch) -> None:
    auth = _auth_service(db)

    def failing_create(self, provider):
        raise RuntimeError("injected: the provider write fails")

    monkeypatch.setattr(ArangoAuthProviderRepository, "create", failing_create)

    with pytest.raises(RuntimeError, match="injected"):
        auth.register_local("new@example.com", PASSWORD, "New Gardener")

    assert _account_set(db) == dict.fromkeys(_account_set(db), 0)
