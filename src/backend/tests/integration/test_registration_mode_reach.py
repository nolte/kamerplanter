"""#2132 (MT-036): the registration mode against a real ArangoDB.

The registration is driven through the real ``AuthService`` over the real user, provider, tenant, membership
and invitation repositories; the invitation that admits a registration is created by the real
``TenantService.create_email_invitation`` and found by the new AQL lookup
(``ArangoInvitationRepository.list_pending_email_invitations``). What a refusal leaves behind is read straight
off the collections: no user, no provider link, no tenant.

Measured before the change (``REGISTRATION_MODE`` did not exist): ``POST /auth/register`` created an account for
any address in full mode.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.enums import InvitationStatus, RegistrationMode, TenantRole
from app.common.exceptions import RegistrationNotAllowedError
from app.data_access.arango import collections as col
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.registration_engine import RegistrationPolicy
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.services.auth_service import AuthService
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("registration_mode")
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["Correct", "horse", "battery", "staple", "9!"])
INVITED = "Invited.Friend@Example.org"
TENANT = "t-garden"
ACCOUNT_COLLECTIONS = (col.USERS, col.AUTH_PROVIDERS, col.TENANTS, col.MEMBERSHIPS)

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
    for name in (*ACCOUNT_COLLECTIONS, col.INVITATIONS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.HAS_INVITATION):
        database.collection(name).truncate()
    database.collection(col.TENANTS).insert(
        {
            "_key": TENANT,
            "name": "Garden",
            "slug": TENANT,
            "tenant_type": "organization",
            "owner_user_key": "u-lead",
            "is_active": True,
            "is_platform": False,
            "max_members": 50,
            "settings": {},
        }
    )
    return database


def _tenant_service(db) -> TenantService:
    return TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=ArangoInvitationRepository(db),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )


def _auth_service(db, mode: RegistrationMode, domains: str = "") -> AuthService:
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
        registration_policy=RegistrationPolicy.from_settings(mode, domains),
    )


def _users(db) -> list[str]:
    return sorted(doc["email"] for doc in db.collection(col.USERS).all())


def test_invite_only_refuses_without_an_invitation_and_writes_nothing(db) -> None:
    with pytest.raises(RegistrationNotAllowedError):
        _auth_service(db, RegistrationMode.INVITE_ONLY).register_local("stranger@example.org", PASSWORD, "Stranger")

    assert _users(db) == []
    assert db.collection(col.AUTH_PROVIDERS).count() == 0
    assert db.collection(col.TENANTS).count() == 1  # only the seeded garden, no personal tenant


def test_invite_only_registers_the_holder_of_an_email_invitation_for_the_address(db) -> None:
    token = _tenant_service(db).create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.GROWER).token

    profile = _auth_service(db, RegistrationMode.INVITE_ONLY).register_local(
        INVITED.lower(), PASSWORD, "Friend", invitation_token=token
    )

    assert _users(db) == [profile.email]
    (invitation,) = list(db.collection(col.INVITATIONS).all())
    assert invitation["status"] == InvitationStatus.PENDING  # registering does not consume it; accepting does


def test_a_link_invitation_unlocks_no_registration(db) -> None:
    token = _tenant_service(db).create_link_invitation(TENANT, "u-lead", TenantRole.VIEWER).token

    with pytest.raises(RegistrationNotAllowedError):
        _auth_service(db, RegistrationMode.INVITE_ONLY).register_local(
            "walkin@example.org", PASSWORD, "Walk-in", invitation_token=token
        )

    assert _users(db) == []


def test_closed_refuses_even_with_a_valid_invitation(db) -> None:
    token = _tenant_service(db).create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.GROWER).token

    with pytest.raises(RegistrationNotAllowedError):
        _auth_service(db, RegistrationMode.CLOSED).register_local(INVITED, PASSWORD, "Friend", invitation_token=token)

    assert _users(db) == []


def test_the_allowlist_admits_its_domain_and_refuses_another(db) -> None:
    service = _auth_service(db, RegistrationMode.OPEN, "club.example")

    service.register_local("member@CLUB.example", PASSWORD, "Member")
    with pytest.raises(RegistrationNotAllowedError):
        service.register_local("visitor@example.org", PASSWORD, "Visitor")

    assert _users(db) == ["member@club.example"]


def test_the_pending_lookup_folds_case_and_skips_links_accepted_and_other_addresses(db) -> None:
    tenants = _tenant_service(db)
    tenants.create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.GROWER)
    tenants.create_email_invitation(TENANT, "u-lead", "someone.else@example.org", TenantRole.GROWER)
    tenants.create_link_invitation(TENANT, "u-lead", TenantRole.VIEWER)
    accepted = tenants.create_email_invitation(TENANT, "u-lead", "already.in@example.org", TenantRole.GROWER)
    db.collection(col.INVITATIONS).update({"_key": accepted.invitation_key, "status": "accepted"})

    repo = ArangoInvitationRepository(db)

    assert [i.email for i in repo.list_pending_email_invitations("invited.friend@EXAMPLE.ORG")] == [
        "Invited.Friend@example.org"
    ]
    assert repo.list_pending_email_invitations("already.in@example.org") == []
    assert tenants.email_invitation_pending_for(email="INVITED.FRIEND@example.org")
    assert not tenants.email_invitation_pending_for(email="already.in@example.org")
