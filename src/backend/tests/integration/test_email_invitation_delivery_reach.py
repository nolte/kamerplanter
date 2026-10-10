"""#2162 - an e-mail invitation is mailed to its address, and the inviter learns whether the mail left.

Driven end to end against a **real** ArangoDB: the real ``POST /tenants/{slug}/invitations/email`` and
``POST /tenants/invitations/accept`` routes, the real ``TenantService`` over the real tenant, membership and
invitation repositories, and the real mail templates (:class:`TemplatedEmailAdapter`) with only the last hop
- handing the rendered mail to SMTP or Resend - replaced by a recorder.

The measured defect (before the fix): the route stored the invitation and answered 201 with its token, but
nothing was mailed - ``IEmailService`` had no invitation mail at all - and the settings page threw the token
away and said "sent". An e-mail invitation reached nobody.

What the fix holds: the mail goes to the invited address and carries the link to the accept page; that link's
token is the one that admits the invited, proven address; ``delivered`` says whether the mail left, and when
it did not, the invitation still exists and ``accept_url`` is the same link for the inviter to pass on.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

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
from app.data_access.external.console_email_adapter import ConsoleEmailAdapter
from app.data_access.external.templated_email_adapter import TemplatedEmailAdapter
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.interfaces.email_service import EmailUndeliverableError, IEmailService
from app.domain.models.membership import Membership
from app.domain.models.user import User
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("email_invitation_delivery")
TENANT = "t-garden"
SLUG = "garden"
INVITED = "friend@example.com"
FRONTEND = "https://garden.example.net"

pytestmark = pytest.mark.usefixtures("arango_db")


class _RecordingMailer(TemplatedEmailAdapter):
    """The real templates; the hand-over to a transport is recorded, or fails as configured."""

    def __init__(self, failure: Exception | None = None) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self._failure = failure

    def _send(self, to_email: str, subject: str, html_body: str) -> None:
        if self._failure is not None:
            raise self._failure
        self.sent.append((to_email, subject, html_body))


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
        col.INVITATIONS,
        col.HAS_INVITATION,
    ):
        database.collection(name).truncate()
    database.collection(col.TENANTS).insert(
        {
            "_key": TENANT,
            "name": "Garden",
            "slug": SLUG,
            "tenant_type": "organization",
            "owner_user_key": "u-lead",
            "is_active": True,
            "is_platform": False,
            "max_members": 50,
            "settings": {},
        }
    )
    database.collection(col.USERS).insert({"_key": "u-lead", "email": "lead@example.com", "display_name": "lead"})
    ArangoMembershipRepository(database).create(
        Membership(
            user_key="u-lead",
            tenant_key=TENANT,
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT],
            is_active=True,
        )
    )
    return database


LEAD = User.model_validate({"_key": "u-lead", "email": "lead@example.com", "display_name": "lead"})
INVITEE = User.model_validate(
    {
        "_key": "u-friend",
        "email": INVITED,
        "display_name": "friend",
        "email_verified": True,
        "email_confirmed_at": datetime.now(UTC).isoformat(),
    }
)


def _client(db, mailer: IEmailService | None, acting: User, *, per_day: int = 50) -> TestClient:
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=ArangoInvitationRepository(db),
        assignment_repo=None,  # type: ignore[arg-type]
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        email_service=mailer,
        frontend_url=FRONTEND,
        invitation_emails_per_day=per_day,
    )
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_user] = lambda: acting
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False)


def _invite(db, mailer: IEmailService | None):
    return _client(db, mailer, LEAD).post(
        f"/api/v1/tenants/{SLUG}/invitations/email", json={"email": INVITED, "role": "grower"}
    )


def _stored_invitations(db) -> list[dict]:
    return list(db.collection(col.INVITATIONS).all())


def test_the_invitation_is_mailed_to_its_address_with_a_link_that_admits_it(db):
    mailer = _RecordingMailer()

    created = _invite(db, mailer)

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["delivered"] is True
    ((to, subject, html),) = mailer.sent
    assert (to, subject) == (INVITED, "Kamerplanter — Invitation")
    (link,) = re.findall(r'href="([^"]+)"', html)
    link = link.replace("&amp;", "&")
    # The mailed link and the one the inviter is shown are the same link (one builder, #2162).
    assert link == body["accept_url"]
    parts = urlsplit(link)
    assert f"{parts.scheme}://{parts.netloc}{parts.path}" == f"{FRONTEND}/invitations/accept"
    (token,) = parse_qs(parts.query)["token"]
    # No requester-chosen text reaches an address nobody proved (#1856): not the tenant's name.
    assert "Garden" not in html

    accepted = _client(db, mailer, INVITEE).post("/api/v1/tenants/invitations/accept", json={"token": token})

    assert accepted.status_code == 200, accepted.text
    (membership,) = [m for m in db.collection(col.MEMBERSHIPS).all() if m["user_key"] == "u-friend"]
    assert (membership["tenant_key"], membership["role"]) == (TENANT, "grower")


@pytest.mark.parametrize(
    "failure",
    [
        pytest.param(OSError("smtp down"), id="transport failure"),
        pytest.param(EmailUndeliverableError("refused"), id="mail service refused"),
    ],
)
def test_a_mail_that_does_not_leave_is_reported_and_the_invitation_stays_usable(db, failure):
    created = _invite(db, _RecordingMailer(failure))

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["delivered"] is False
    (stored,) = _stored_invitations(db)
    assert (stored["status"], stored["email"]) == ("pending", INVITED)
    (token,) = parse_qs(urlsplit(body["accept_url"]).query)["token"]
    assert token == body["token"]


def test_the_console_adapter_outside_debug_does_not_claim_delivery(db):
    """The default adapter of an install without SMTP: nothing leaves, and the answer says so."""
    with patch("app.data_access.external.console_email_adapter.settings") as console_settings:
        console_settings.debug = False
        created = _invite(db, ConsoleEmailAdapter())

    assert created.status_code == 201, created.text
    assert created.json()["delivered"] is False
    assert len(_stored_invitations(db)) == 1


def test_without_a_mailer_the_invitation_is_not_reported_as_delivered(db):
    created = _invite(db, None)

    assert created.status_code == 201, created.text
    assert created.json()["delivered"] is False


def test_a_link_invitation_carries_its_accept_link_and_no_delivery_claim(db):
    created = _client(db, _RecordingMailer(), LEAD).post(
        f"/api/v1/tenants/{SLUG}/invitations/link", json={"role": "viewer"}
    )

    assert created.status_code == 201, created.text
    body = created.json()
    assert body["delivered"] is None
    assert body["accept_url"] == f"{FRONTEND}/invitations/accept?token={body['token']}"


def test_beyond_the_daily_budget_the_route_answers_429_and_mails_nobody(db):
    """Review W-1: the invitation route mails addresses the inviter names; one account's day is bounded."""
    mailer = _RecordingMailer()
    client = _client(db, mailer, LEAD, per_day=2)
    sent = [
        client.post(f"/api/v1/tenants/{SLUG}/invitations/email", json={"email": f"f{i}@example.com", "role": "viewer"})
        for i in range(2)
    ]

    refused = client.post(
        f"/api/v1/tenants/{SLUG}/invitations/email", json={"email": "f3@example.com", "role": "viewer"}
    )

    assert [r.status_code for r in sent] == [201, 201]
    assert refused.status_code == 429, refused.text
    assert refused.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert len(mailer.sent) == 2
    assert len(_stored_invitations(db)) == 2
    # A link invitation mails nothing and is not counted against the mail budget.
    assert client.post(f"/api/v1/tenants/{SLUG}/invitations/link", json={"role": "viewer"}).status_code == 201
