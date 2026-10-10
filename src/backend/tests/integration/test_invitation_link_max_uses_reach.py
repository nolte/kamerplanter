"""#2182 / REQ-024 AK-07 — an invitation link admits up to ``max_uses`` accounts, then no more.

Driven end to end against a **real** ArangoDB: the real ``/tenants`` router (creating the link as the
garden's member administrator, accepting it as a signed-in account), the real ``TenantService`` over
the real ``ArangoTenantRepository`` / ``ArangoMembershipRepository`` / ``ArangoInvitationRepository``.
The use counting is one conditional AQL ``UPDATE`` (``consume_use_if_pending``); what it leaves is
read straight off the collections.

The measured gap (before the fix): ``LinkInvitationRequest`` had no ``max_uses`` - the field the
frontend already sent was dropped - and acceptance flipped every invitation to ``accepted`` on the
first use, so a link shared with a group admitted exactly one person.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user, require_account_principal
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, InvitationStatus, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("invitation_max_uses")
GARDEN = "t-garden"
GARDEN_SLUG = "community-garden"
LEAD = "lead"

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


class _Stage:
    """One community garden with a lead who holds ``management``; joiners are created on demand."""

    def __init__(self, db, *, max_members: int) -> None:
        self.db = db
        self.memberships = ArangoMembershipRepository(db)
        self.invitations = ArangoInvitationRepository(db)
        self.users: dict[str, User] = {}
        db.collection(col.TENANTS).insert(
            {
                "_key": GARDEN,
                "name": GARDEN_SLUG,
                "slug": GARDEN_SLUG,
                "tenant_type": "organization",
                "owner_user_key": f"u-{LEAD}",
                "status": "active",
                "is_platform": False,
                "max_members": max_members,
                "settings": {},
            }
        )
        self._user(LEAD)
        self.memberships.create(
            Membership(
                user_key=f"u-{LEAD}",
                tenant_key=GARDEN,
                role=TenantRole.LEAD,
                admin_scopes=[AdminScope.MANAGEMENT],
                is_active=True,
            )
        )
        self.service = TenantService(
            tenant_repo=ArangoTenantRepository(db),
            membership_repo=self.memberships,
            invitation_repo=self.invitations,
            assignment_repo=None,  # type: ignore[arg-type]
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
        )

    def _user(self, name: str) -> User:
        if name not in self.users:
            user = User.model_validate(
                {"_key": f"u-{name}", "email": f"{name}@example.com", "display_name": name, "email_verified": True}
            )
            self.db.collection(col.USERS).insert({"_key": user.key, "email": user.email, "display_name": name})
            self.users[name] = user
        return self.users[name]

    def client(self, acting: str) -> TestClient:
        user = self._user(acting)
        app = FastAPI()
        app.include_router(tenants_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[require_account_principal] = lambda: user
        app.dependency_overrides[get_tenant_service] = lambda: self.service
        return TestClient(app, raise_server_exceptions=False)

    def create_link(self, **body):
        return self.client(LEAD).post(f"/api/v1/tenants/{GARDEN_SLUG}/invitations/link", json=body)

    def accept(self, who: str, token: str):
        return self.client(who).post("/api/v1/tenants/invitations/accept", json={"token": token})

    def invitation(self, key: str) -> dict:
        return self.db.collection(col.INVITATIONS).get(key)

    def is_member(self, who: str) -> bool:
        return self.memberships.get_by_user_and_tenant(f"u-{who}", GARDEN) is not None


def _stage(database, *, max_members: int = 50) -> _Stage:
    for name in (
        col.TENANTS,
        col.USERS,
        col.MEMBERSHIPS,
        col.HAS_MEMBERSHIP,
        col.MEMBERSHIP_IN,
        col.INVITATIONS,
        col.HAS_INVITATION,
    ):
        database.collection(name).truncate()
    return _Stage(database, max_members=max_members)


def test_a_link_with_three_uses_admits_three_accounts_and_then_refuses(database):
    stage = _stage(database)
    created = stage.create_link(role="grower", max_uses=3)
    assert created.status_code == 201, created.text
    assert created.json()["max_uses"] == 3
    token, key = created.json()["token"], created.json()["invitation_key"]

    for n, who in enumerate(("anna", "ben", "cleo"), start=1):
        accepted = stage.accept(who, token)
        assert accepted.status_code == 200, accepted.text
        assert stage.is_member(who)
        stored = stage.invitation(key)
        assert stored["use_count"] == n
        assert stored["status"] == ("accepted" if n == 3 else "pending")

    refused = stage.accept("dora", token)

    assert refused.status_code == 422, refused.text
    assert not stage.is_member("dora")
    assert stage.invitation(key)["use_count"] == 3


def test_a_link_without_max_uses_stays_single_use(database):
    stage = _stage(database)
    created = stage.create_link(role="viewer")
    assert created.status_code == 201, created.text
    token, key = created.json()["token"], created.json()["invitation_key"]

    assert stage.accept("anna", token).status_code == 200
    refused = stage.accept("ben", token)

    assert refused.status_code == 422, refused.text
    assert not stage.is_member("ben")
    assert stage.invitation(key)["status"] == "accepted"


@pytest.mark.parametrize("max_uses", [0, -1, 101])
def test_max_uses_outside_its_bounds_is_refused_and_nothing_is_stored(database, max_uses):
    stage = _stage(database)

    refused = stage.create_link(role="viewer", max_uses=max_uses)

    assert refused.status_code == 422, refused.text
    assert database.collection(col.INVITATIONS).count() == 0


def test_the_member_limit_still_decides_every_use_and_a_refused_use_is_not_spent(database):
    """Lead + one seat: a five-use link admits one joiner; the second is refused and keeps the link usable."""
    stage = _stage(database, max_members=2)
    created = stage.create_link(role="viewer", max_uses=5)
    token, key = created.json()["token"], created.json()["invitation_key"]

    assert stage.accept("anna", token).status_code == 200
    refused = stage.accept("ben", token)

    assert refused.status_code == 422, refused.text
    assert refused.json()["error_code"] == "MEMBER_LIMIT_REACHED"
    assert not stage.is_member("ben")
    stored = stage.invitation(key)
    assert (stored["use_count"], stored["status"]) == (1, "pending")


def test_the_same_account_cannot_spend_two_uses(database):
    stage = _stage(database)
    created = stage.create_link(role="viewer", max_uses=5)
    token, key = created.json()["token"], created.json()["invitation_key"]

    assert stage.accept("anna", token).status_code == 200
    again = stage.accept("anna", token)

    assert again.status_code == 422, again.text
    assert stage.invitation(key)["use_count"] == 1


def test_the_listing_shows_uses_granted_and_consumed(database):
    stage = _stage(database)
    token = stage.create_link(role="viewer", max_uses=4).json()["token"]
    stage.accept("anna", token)

    listed = stage.client(LEAD).get(f"/api/v1/tenants/{GARDEN_SLUG}/invitations")

    assert listed.status_code == 200, listed.text
    (row,) = listed.json()
    assert (row["max_uses"], row["use_count"], row["status"]) == (4, 1, "pending")


def test_a_row_stored_before_max_uses_existed_is_single_use(database):
    """A pre-#2182 document carries neither field: it reads, and is consumed, as single use."""
    stage = _stage(database)
    token = stage.create_link(role="viewer", max_uses=1).json()["token"]
    (doc,) = list(database.collection(col.INVITATIONS).all())
    database.collection(col.INVITATIONS).replace(
        {k: v for k, v in doc.items() if k not in ("max_uses", "use_count", "_rev")}
    )

    assert stage.accept("anna", token).status_code == 200
    assert stage.accept("ben", token).status_code == 422
    assert stage.invitation(doc["_key"])["use_count"] == 1


def test_handing_back_a_use_never_reopens_a_revoked_invitation(database):
    """The rollback of a failed join: one use fewer, but ``revoked`` stays ``revoked`` (#2182)."""
    stage = _stage(database)
    key = stage.create_link(role="viewer", max_uses=1).json()["invitation_key"]
    consumed = stage.invitations.consume_use_if_pending(key, {"accepted_by_user_key": "u-anna"})
    assert consumed is not None and consumed.status == InvitationStatus.ACCEPTED
    stage.service.revoke_invitation(GARDEN, key)

    released = stage.invitations.release_use(key, "u-anna")

    assert released is not None
    assert (released.status, released.use_count, released.accepted_by_user_key) == (
        InvitationStatus.REVOKED,
        0,
        None,
    )


def test_handing_back_the_last_use_reopens_an_accepted_invitation(database):
    stage = _stage(database)
    key = stage.create_link(role="viewer", max_uses=2).json()["invitation_key"]
    stage.invitations.consume_use_if_pending(key, {"accepted_by_user_key": "u-anna"})
    stage.invitations.consume_use_if_pending(key, {"accepted_by_user_key": "u-ben"})
    assert stage.invitation(key)["status"] == "accepted"

    released = stage.invitations.release_use(key, "u-ben")

    assert released is not None
    assert (released.status, released.use_count, released.accepted_by_user_key) == (
        InvitationStatus.PENDING,
        1,
        None,
    )
