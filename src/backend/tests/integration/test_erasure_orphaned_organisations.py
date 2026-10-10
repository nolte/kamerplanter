"""#2134 (MT-038) — the organisation settlement of an account erasure, on a real ArangoDB.

The issue asked for exactly these two integration cases (the later ones are #2166's):

* the erasure of an organisation's **only member** leaves a ``tenant_erasure_records``
  row for the organisation (``scheduled``, origin ``orphaned_organisation``) and the
  tenant ``orphaned``;
* the erasure of the **only manager** with two remaining members hands ``management``
  to the longest-serving ``lead``.

Runs the real ``TenantService`` over the real repositories — the account filter of
``active_memberships_of`` (an account whose erasure is pending is deactivated and must
not count) and the conditional record insert are AQL, which a double would only assert.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_erasure_orphaned_organisations.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.common.enums import AdminScope, TenantStatus
from app.common.exceptions import ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the member filter and the record insert are AQL over a real server"),
]

_DB_NAME = run_database_name("erasure_orphaned_organisations")
NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
SUBJECT = "u-subject"
ORG = "t-org"


@pytest.fixture(autouse=True)
def _configured_log_pseudonym_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config.settings import settings as _settings

    monkeypatch.setattr(_settings, "log_pseudonym_salt", "log-pseudonym-test-salt-not-a-secret-01234")


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _service(db) -> tuple[TenantService, MagicMock]:  # type: ignore[no-untyped-def]
    mailer = MagicMock()
    users = MagicMock()
    users.get_by_key.side_effect = lambda key: MagicMock(email=f"{key}@example.org")
    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        tenant_erasure_repo=ArangoTenantErasureRepository(db),
        tombstone_salt="integration-tombstone-salt-0123456789abcdef",
        tenant_erasure_grace_days=90,
        email_service=mailer,
        user_repo=users,
    )
    return service, mailer


def _user(db, key: str, *, active: bool = True, account_type: str = "human") -> None:  # type: ignore[no-untyped-def]
    db.collection(col.USERS).insert(
        {
            "_key": key,
            "email": f"{key}@example.org",
            "display_name": key,
            "is_active": active,
            "account_type": account_type,
        }
    )


def _member(db, user_key: str, role: str, scopes: list[str], joined: str) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.MEMBERSHIPS).insert(
        {
            "_key": f"m-{user_key}",
            "user_key": user_key,
            "tenant_key": ORG,
            "role": role,
            "admin_scopes": scopes,
            "is_active": True,
            "joined_at": joined,
        }
    )


def _org(db) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.TENANTS).insert(
        {
            "_key": ORG,
            "name": "Lindenhof",
            "slug": "lindenhof",
            "tenant_type": "organization",
            "owner_user_key": SUBJECT,
            "status": "active",
        }
    )
    # The subject's account erasure is requested: the account is closed (#1788 review GDPR-01).
    _user(db, SUBJECT, active=False)


def test_the_only_member_leaves_a_scheduled_record_and_an_orphaned_organisation(db) -> None:  # type: ignore[no-untyped-def]
    _org(db)
    _member(db, SUBJECT, "lead", ["management"], "2025-01-01T00:00:00+00:00")
    service, _mailer = _service(db)

    outcomes = service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

    assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "orphaned")]
    record = db.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(ORG))
    assert record["status"] == "scheduled"
    assert record["origin"] == "orphaned_organisation"
    assert record.get("last_attempt_at") is None  # never claimed: cancellable by nobody, erased by the beat
    tenant = ArangoTenantRepository(db).get_by_key(ORG)
    assert tenant is not None and tenant.status == TenantStatus.ORPHANED
    assert tenant.deletion_scheduled_at == NOW + timedelta(days=90)


def test_the_only_manager_hands_management_to_the_longest_serving_lead(db) -> None:  # type: ignore[no-untyped-def]
    _org(db)
    _member(db, SUBJECT, "lead", ["management"], "2024-01-01T00:00:00+00:00")
    _user(db, "u-lead-old")
    _member(db, "u-lead-old", "lead", ["technical"], "2025-02-01T00:00:00+00:00")
    _user(db, "u-lead-young")
    _member(db, "u-lead-young", "lead", [], "2026-02-01T00:00:00+00:00")
    # A lead whose own erasure is pending is no heir: their account is closed.
    _user(db, "u-lead-leaving", active=False)
    _member(db, "u-lead-leaving", "lead", [], "2023-01-01T00:00:00+00:00")
    service, mailer = _service(db)

    outcomes = service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

    assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "management_passes_to_lead")]
    stored: dict[str, Any] = {doc["user_key"]: doc for doc in db.collection(col.MEMBERSHIPS).all()}
    assert stored["u-lead-old"]["admin_scopes"] == [AdminScope.MANAGEMENT.value, AdminScope.TECHNICAL.value]
    assert stored["u-lead-young"]["admin_scopes"] == []
    assert stored["u-lead-leaving"]["admin_scopes"] == []
    assert db.collection(col.TENANT_ERASURE_RECORDS).get(TenantErasureEngine.record_key(ORG)) is None
    told = {call.kwargs["to_email"] for call in mailer.send_notification_email.call_args_list}
    assert told == {"u-lead-old@example.org", "u-lead-young@example.org"}


# ── #2166 — only a live person administers ──────────────────────────────────


def test_a_service_account_lead_never_inherits_management(db) -> None:  # type: ignore[no-untyped-def]
    """W2: the longest-serving lead is a service account — the longest-serving *person* lead inherits."""
    _org(db)
    _member(db, SUBJECT, "lead", ["management"], "2024-01-01T00:00:00+00:00")
    _user(db, "u-robot", account_type="service")
    _member(db, "u-robot", "lead", [], "2023-01-01T00:00:00+00:00")
    _user(db, "u-lead")
    _member(db, "u-lead", "lead", [], "2026-02-01T00:00:00+00:00")
    service, _mailer = _service(db)

    outcomes = service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

    assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "management_passes_to_lead")]
    stored: dict[str, Any] = {doc["user_key"]: doc for doc in db.collection(col.MEMBERSHIPS).all()}
    assert stored["u-robot"]["admin_scopes"] == []
    assert stored["u-lead"]["admin_scopes"] == [AdminScope.MANAGEMENT.value]


def test_an_organisation_whose_only_lead_is_a_service_account_is_orphaned(db) -> None:  # type: ignore[no-untyped-def]
    """W2: management handed to a machine identity would leave nobody who can pass the step-up."""
    _org(db)
    _member(db, SUBJECT, "lead", ["management"], "2024-01-01T00:00:00+00:00")
    _user(db, "u-robot", account_type="service")
    _member(db, "u-robot", "lead", [], "2023-01-01T00:00:00+00:00")
    _user(db, "u-grower")
    _member(db, "u-grower", "grower", [], "2025-01-01T00:00:00+00:00")
    service, _mailer = _service(db)

    outcomes = service.settle_organisations_of_erased_account(SUBJECT, now=NOW)

    assert [(o.tenant_key, o.outcome) for o in outcomes] == [(ORG, "orphaned")]
    stored: dict[str, Any] = {doc["user_key"]: doc for doc in db.collection(col.MEMBERSHIPS).all()}
    assert stored["u-robot"]["admin_scopes"] == []


def test_a_closed_accounts_management_does_not_count_for_inv1(db) -> None:  # type: ignore[no-untyped-def]
    """W1: a holder whose erasure is pending (account closed) is no second manager.

    Before #2166 ``count_managers`` counted every active ``management`` membership, also the
    closed account's, so the last *live* holder could leave and strand the organisation.
    """
    _org(db)  # SUBJECT: account closed by its erasure request
    _member(db, SUBJECT, "lead", ["management"], "2024-01-01T00:00:00+00:00")
    _user(db, "u-manager")
    _member(db, "u-manager", "lead", ["management"], "2025-01-01T00:00:00+00:00")
    repo = ArangoMembershipRepository(db)
    service, _mailer = _service(db)

    assert repo.count_managers(ORG) == 1
    assert repo.count_managers(ORG, other_than_user_key="u-manager") == 0
    # The closed account's membership may still be removed: one live holder remains.
    assert repo.count_managers(ORG, other_than_user_key=SUBJECT) == 1
    with pytest.raises(ValidationError, match="management"):
        service.leave_tenant(ORG, "u-manager")
    assert db.collection(col.MEMBERSHIPS).get("m-u-manager") is not None
