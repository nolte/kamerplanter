"""#2078 / REQ-024 AK-58 — a member cannot raise their own role; ``lead`` in ``platform`` needs a lead to grant it.

Driven end to end against a **real** ArangoDB: the real ``/tenants/{slug}`` router (the member
administrator's own routes), the real ``TenantService`` with its real step-up verifier, over the
real ``ArangoTenantRepository`` / ``ArangoMembershipRepository`` / ``ArangoInvitationRepository``.
What a refused request leaves behind is read straight off the collections.

The measured defect (before the fix): a ``management`` holder in the ``platform`` tenant who is not
its ``lead`` sent ``PATCH /tenants/platform/members/{own membership}/role`` with their **own**
password as the step-up (#2032) and became ``lead`` — which ``is_platform_admin`` reads as the
platform role. The step-up proves who is asking, not that they may be given that role.

The rule: no member raises their *own* role through the tenant-scoped route (in any tenant), and
``lead`` in the ``platform`` tenant — which *is* the platform role — is granted, by role change or
by invitation, only by someone who already holds it. Outside the platform tenant a ``management``
holder may still appoint a ``lead`` (REQ-049 §2.4: a tenant whose only lead left must be able to
regain one).

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import get_current_user
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
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

TEST_DATABASE = run_database_name("member_role_escalation")
PLATFORM = "platform"
GARDEN = "t-garden"
GARDEN_SLUG = "community-garden"
# Assembled at runtime: a literal shaped like a credential trips the secret scanner (#1838).
PASSWORD = " ".join(["correct", "horse", "battery", "staple"])

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
    """The platform tenant and one community garden, each with a lead, a secretary and a plain member."""

    def __init__(self, db) -> None:
        self.db = db
        self.memberships = ArangoMembershipRepository(db)
        self.invitations = ArangoInvitationRepository(db)
        self.users: dict[str, User] = {}
        self.keys: dict[str, str] = {}
        for key, slug, is_platform in ((PLATFORM, PLATFORM, True), (GARDEN, GARDEN_SLUG, False)):
            db.collection(col.TENANTS).insert(
                {
                    "_key": key,
                    "name": slug,
                    "slug": slug,
                    "tenant_type": "organization",
                    "owner_user_key": "u-owner",
                    "is_active": True,
                    "is_platform": is_platform,
                    "max_members": 50,
                    "settings": {},
                }
            )
        for tenant, prefix in ((PLATFORM, "plat"), (GARDEN, "garden")):
            # The lead holds ``management`` too (the personal-tenant shape); the secretary holds only it.
            self._member(f"{prefix}-lead", tenant, TenantRole.LEAD, [AdminScope.MANAGEMENT])
            self._member(f"{prefix}-secretary", tenant, TenantRole.VIEWER, [AdminScope.MANAGEMENT])
            self._member(f"{prefix}-grower", tenant, TenantRole.GROWER, [AdminScope.MANAGEMENT])
            self._member(f"{prefix}-viewer", tenant, TenantRole.VIEWER, [])

    def _member(self, name: str, tenant: str, role: TenantRole, scopes: list[AdminScope]) -> None:
        user = User.model_validate(
            {
                "_key": f"u-{name}",
                "email": f"{name}@example.com",
                "display_name": name,
                "password_hash": PasswordEngine().hash_password(PASSWORD),
            }
        )
        self.users[name] = user
        self.db.collection(col.USERS).insert({"_key": user.key, "email": user.email, "display_name": name})
        created = self.memberships.create(
            Membership(user_key=user.key or "", tenant_key=tenant, role=role, admin_scopes=scopes, is_active=True)
        )
        self.keys[name] = created.key or ""

    def role_of(self, name: str) -> str:
        return self.db.collection(col.MEMBERSHIPS).get(self.keys[name])["role"]

    def invitation_count(self) -> int:
        return self.db.collection(col.INVITATIONS).count()

    def client(self, acting: str) -> TestClient:
        service = TenantService(
            tenant_repo=ArangoTenantRepository(self.db),
            membership_repo=self.memberships,
            invitation_repo=self.invitations,
            assignment_repo=None,  # type: ignore[arg-type]
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
        )
        app = FastAPI()
        app.include_router(tenants_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.dependency_overrides[get_current_user] = lambda: self.users[acting]
        app.dependency_overrides[get_tenant_service] = lambda: service
        return TestClient(app, raise_server_exceptions=False)

    def set_role(self, acting: str, slug: str, target: str, role: str):
        return self.client(acting).patch(
            f"/api/v1/tenants/{slug}/members/{self.keys[target]}/role",
            json={"role": role, "current_password": PASSWORD},
        )


@pytest.fixture
def stage(database):
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
    return _Stage(database)


# ── the escalation itself ────────────────────────────────────────────────────


@pytest.mark.parametrize("who", ["plat-secretary", "plat-grower"])
def test_a_platform_member_with_management_cannot_make_themselves_lead(stage, who):
    refused = stage.set_role(who, PLATFORM, who, "lead")

    assert refused.status_code == 403, refused.text
    assert stage.role_of(who) != "lead"


def test_a_member_of_an_ordinary_tenant_cannot_raise_their_own_role(stage):
    for target in ("grower", "lead"):
        refused = stage.set_role("garden-secretary", GARDEN_SLUG, "garden-secretary", target)

        assert refused.status_code == 403, refused.text
        assert stage.role_of("garden-secretary") == "viewer"


def test_a_platform_member_who_is_not_lead_cannot_hand_out_lead(stage):
    refused = stage.set_role("plat-secretary", PLATFORM, "plat-viewer", "lead")

    assert refused.status_code == 403, refused.text
    assert stage.role_of("plat-viewer") == "viewer"


@pytest.mark.parametrize("path", ["invitations/email", "invitations/link"])
def test_a_platform_member_who_is_not_lead_cannot_invite_a_lead(stage, path):
    body = {"role": "lead", **({"email": "new@example.com"} if path.endswith("email") else {})}

    refused = stage.client("plat-secretary").post(f"/api/v1/tenants/{PLATFORM}/{path}", json=body)

    assert refused.status_code == 403, refused.text
    assert stage.invitation_count() == 0


# ── the controls: what stays allowed ─────────────────────────────────────────


def test_a_platform_lead_hands_out_lead_by_role_change_and_by_invitation(stage):
    granted = stage.set_role("plat-lead", PLATFORM, "plat-viewer", "lead")
    assert granted.status_code == 200, granted.text
    assert stage.role_of("plat-viewer") == "lead"

    invited = stage.client("plat-lead").post(
        f"/api/v1/tenants/{PLATFORM}/invitations/email", json={"email": "new@example.com", "role": "lead"}
    )
    assert invited.status_code == 201, invited.text
    assert stage.invitation_count() == 1


def test_a_platform_member_with_management_still_hands_out_roles_below_lead(stage):
    granted = stage.set_role("plat-secretary", PLATFORM, "plat-viewer", "grower")
    assert granted.status_code == 200, granted.text
    assert stage.role_of("plat-viewer") == "grower"

    invited = stage.client("plat-secretary").post(
        f"/api/v1/tenants/{PLATFORM}/invitations/link", json={"role": "grower"}
    )
    assert invited.status_code == 201, invited.text


def test_the_secretary_of_an_ordinary_tenant_still_appoints_a_lead(stage):
    """REQ-049 §2.4: no rank ceiling — a tenant whose only lead left must be able to regain one."""
    granted = stage.set_role("garden-secretary", GARDEN_SLUG, "garden-viewer", "lead")

    assert granted.status_code == 200, granted.text
    assert stage.role_of("garden-viewer") == "lead"


def test_a_member_may_lower_their_own_role(stage):
    lowered = stage.set_role("garden-lead", GARDEN_SLUG, "garden-lead", "grower")

    assert lowered.status_code == 200, lowered.text
    assert stage.role_of("garden-lead") == "grower"
