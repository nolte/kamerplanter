"""#2133 (MT-037): the member limit holds against a real ArangoDB, on the real routes.

Driven end to end: the real ``POST /tenants/invitations/accept`` route and the real ``TenantService`` over the
real tenant, membership and invitation repositories. What a refusal leaves behind is read straight off the
collections - the active memberships of the tenant, the invitation document's status.

Measured before the fix (the same module against the unchanged service): a personal tenant stored with
``max_members=1`` answered ``200`` to a second and a third acceptance and held three active memberships.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.tenants.router import router as tenants_router
from app.common.auth import require_account_principal
from app.common.dependencies import get_tenant_service
from app.common.enums import TenantRole
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

TEST_DATABASE = run_database_name("member_limit")
TENANT = "t-garden"

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


def _seed(database, *, tenant_type: str, max_members: int, members: int) -> None:
    for name in (col.TENANTS, col.USERS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.INVITATIONS):
        database.collection(name).truncate()
    database.collection(col.TENANTS).insert(
        {
            "_key": TENANT,
            "name": "Garden",
            "slug": "garden",
            "tenant_type": tenant_type,
            "owner_user_key": "u-lead",
            "is_active": True,
            "is_platform": False,
            "max_members": max_members,
            "settings": {},
        }
    )
    repo = ArangoMembershipRepository(database)
    repo.create(Membership(user_key="u-lead", tenant_key=TENANT, role=TenantRole.LEAD, is_active=True))
    for n in range(1, members):
        repo.create(Membership(user_key=f"u-member-{n}", tenant_key=TENANT, role=TenantRole.GROWER, is_active=True))


def _service(db) -> TenantService:
    return TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=ArangoInvitationRepository(db),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )


def _account(key: str) -> User:
    return User.model_validate({"_key": key, "email": f"{key}@example.com", "display_name": key})


def _accept(service: TenantService, token: str, account: User):
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_account_principal] = lambda: account
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/tenants/invitations/accept", json={"token": token}
    )


def _active_members(db) -> list[str]:
    return sorted(m["user_key"] for m in db.collection(col.MEMBERSHIPS).all() if m["is_active"])


def test_a_personal_tenant_of_one_refuses_the_second_member(database) -> None:
    _seed(database, tenant_type="personal", max_members=1, members=1)
    service = _service(database)
    token = service.create_link_invitation(TENANT, "u-lead", TenantRole.GROWER).token

    refused = _accept(service, token, _account("u-friend"))

    assert refused.status_code == 422, refused.text
    assert refused.json()["error_code"] == "MEMBER_LIMIT_REACHED"
    assert _active_members(database) == ["u-lead"]
    (invitation,) = list(database.collection(col.INVITATIONS).all())
    assert invitation["status"] == "pending"  # handed back: usable once a seat is free


def test_an_organisation_of_two_refuses_the_third_and_takes_the_second(database) -> None:
    _seed(database, tenant_type="organization", max_members=2, members=1)
    service = _service(database)
    first = service.create_link_invitation(TENANT, "u-lead", TenantRole.GROWER).token
    second = service.create_link_invitation(TENANT, "u-lead", TenantRole.GROWER).token

    accepted = _accept(service, first, _account("u-second"))
    refused = _accept(service, second, _account("u-third"))

    assert accepted.status_code == 200, accepted.text
    assert refused.status_code == 422, refused.text
    assert _active_members(database) == ["u-lead", "u-second"]


def test_a_tenant_already_above_its_limit_keeps_every_member(database) -> None:
    """Data written before the limit was enforced: nobody is removed, only the next join is refused."""
    _seed(database, tenant_type="personal", max_members=1, members=3)
    service = _service(database)
    token = service.create_link_invitation(TENANT, "u-lead", TenantRole.GROWER).token

    refused = _accept(service, token, _account("u-fourth"))

    assert refused.status_code == 422, refused.text
    assert _active_members(database) == ["u-lead", "u-member-1", "u-member-2"]


def test_the_active_count_skips_a_deactivated_membership(database) -> None:
    """A membership the tenant deletion switched off (``is_active=false``) holds no seat."""
    _seed(database, tenant_type="organization", max_members=2, members=2)
    database.aql.execute(
        "FOR m IN memberships FILTER m.user_key == 'u-member-1' UPDATE m WITH { is_active: false } IN memberships"
    )

    assert ArangoMembershipRepository(database).count_active_members(tenant_key=TENANT) == 1
