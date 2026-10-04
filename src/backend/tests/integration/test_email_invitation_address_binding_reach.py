"""#2115 (MT-018): an e-mail invitation is accepted only by the account holding the proven invited address.

Driven end to end against a **real** ArangoDB: the real ``POST /tenants/invitations/accept`` route and the real
``TenantService`` over the real invitation, membership and tenant repositories. What a refusal leaves behind is
read straight off the collections: the invitation document still ``pending``, no membership, no edge.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import UTC, datetime
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

TEST_DATABASE = run_database_name("email_invitation_binding")
TENANT = "t-garden"
INVITED = "friend@example.com"

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
    for name in (col.TENANTS, col.USERS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.INVITATIONS):
        database.collection(name).truncate()
    database.collection(col.TENANTS).insert(
        {
            "_key": TENANT,
            "name": "Garden",
            "slug": "garden",
            "tenant_type": "organization",
            "owner_user_key": "u-lead",
            "is_active": True,
            "is_platform": False,
            "max_members": 50,
            "settings": {},
        }
    )
    ArangoMembershipRepository(database).create(
        Membership(user_key="u-lead", tenant_key=TENANT, role=TenantRole.LEAD, is_active=True)
    )
    return database


def _account(key: str, email: str, *, proven: bool = True) -> User:
    return User.model_validate(
        {
            "_key": key,
            "email": email,
            "display_name": key,
            "email_verified": proven,
            "email_confirmed_at": datetime.now(UTC).isoformat() if proven else None,
        }
    )


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


def _accept(db, service: TenantService, token: str, account: User):
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_account_principal] = lambda: account
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/tenants/invitations/accept", json={"token": token}
    )


def _members_of(db, user: str) -> list[dict]:
    return [m for m in db.collection(col.MEMBERSHIPS).all() if m["user_key"] == user]


def _status(db) -> str:
    (doc,) = list(db.collection(col.INVITATIONS).all())
    return doc["status"]


def test_a_foreign_account_holding_the_token_does_not_get_the_membership(db) -> None:
    service = _service(db)
    token = service.create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.GROWER).token

    refused = _accept(db, service, token, _account("u-intruder", "intruder@example.com"))

    assert refused.status_code == 403, refused.text
    assert INVITED not in refused.text
    assert _members_of(db, "u-intruder") == []
    assert _status(db) == "pending"
    assert [e for e in db.collection(col.HAS_MEMBERSHIP).all() if e["_from"] == "users/u-intruder"] == []


def test_the_invited_address_must_be_proven(db) -> None:
    service = _service(db)
    token = service.create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.GROWER).token

    refused = _accept(db, service, token, _account("u-claimant", INVITED, proven=False))

    assert refused.status_code == 403, refused.text
    assert _members_of(db, "u-claimant") == []
    assert _status(db) == "pending"


def test_the_account_holding_the_proven_address_accepts_whatever_its_case(db) -> None:
    service = _service(db)
    token = service.create_email_invitation(TENANT, "u-lead", INVITED, TenantRole.GROWER).token

    accepted = _accept(db, service, token, _account("u-friend", INVITED.upper().replace("EXAMPLE.COM", "example.com")))

    assert accepted.status_code == 200, accepted.text
    (membership,) = _members_of(db, "u-friend")
    assert (membership["tenant_key"], membership["role"]) == (TENANT, "grower")
    assert _status(db) == "accepted"


def test_a_link_invitation_stays_open_to_any_signed_in_account(db) -> None:
    service = _service(db)
    token = service.create_link_invitation(TENANT, "u-lead", TenantRole.VIEWER).token

    accepted = _accept(db, service, token, _account("u-walkin", "walkin@example.com", proven=False))

    assert accepted.status_code == 200, accepted.text
    assert [m["role"] for m in _members_of(db, "u-walkin")] == ["viewer"]
