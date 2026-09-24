"""#1700 — the erasure surfaces the plan-seeded reach test cannot judge on its own.

``test_account_erasure_reach.py`` seeds one synthetic row per declared step and
proves each step reaches it. What it cannot show is that the *product*
consequence holds on rows written by the real repositories into a database
built by the real ``ensure_collections`` (unique indexes included):

* a calendar feed's token stops serving once its owner is erased (REQ-015);
* the personal tenant survives, still readable through its model and its unique
  ``slug`` index, but no longer carries the owner's key or display name; an
  organisation tenant the subject founded keeps its name and loses only the
  owner reference, and its other member is untouched (REQ-024);
* the unverified-account cleanup — which runs only the ``account_cascade``
  slice — now also removes the membership registration created, and the
  location assignment hanging off it.

Runs against a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import asyncio
import secrets

import pytest
from arango import ArangoClient

import tests.integration.test_account_erasure_reach as reach
from app.common.enums import TenantRole
from app.common.exceptions import ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.erasure_engine import ANONYMIZED_KEY_PREFIX, ANONYMIZED_MARKER
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.calendar import CalendarFeed
from app.domain.models.location_assignment import LocationAssignment
from app.domain.models.membership import Membership
from app.domain.services.calendar_service import CalendarService
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("erasure_special_cases")

SUBJECT = "user-a"
OTHER = "user-b"
DISPLAY_NAME = "Gärtnerin Annegret Beispiel"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


def _tenant_service(database) -> TenantService:
    return TenantService(
        tenant_repo=ArangoTenantRepository(database),
        membership_repo=ArangoMembershipRepository(database),
        invitation_repo=None,  # type: ignore[arg-type]
        assignment_repo=ArangoLocationAssignmentRepository(database),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )


def _insert_user(database, key: str, *, verified: bool = True) -> None:
    document = reach._user_document(key)
    document["display_name"] = DISPLAY_NAME if key == SUBJECT else document["display_name"]
    document["email_verified"] = verified
    database.collection(col.USERS).insert(document)


def _erase(database, user_key: str) -> None:
    privacy_service, _ = reach._services(database)
    asyncio.run(privacy_service.erase_account(user_key))


class TestCalendarFeedTokenStopsServing:
    def test_the_feed_token_of_an_erased_user_no_longer_resolves(self, database):
        _insert_user(database, "feed-owner")
        repo = ArangoCalendarFeedRepository(database)
        token = secrets.token_urlsafe(24)
        feed = repo.save(CalendarFeed(tenant_key="t-feed", name="Mein Kalender", token=token, user_key="feed-owner"))
        service = CalendarService(feed_repo=repo, aggregation_engine=None)  # type: ignore[arg-type]
        # Positive control: before the erasure the token resolves to the feed.
        assert repo.get_by_token(token) is not None

        _erase(database, "feed-owner")

        assert repo.get_by_token(token) is None
        with pytest.raises(ValidationError, match="Invalid feed token"):
            service.generate_ical_for_feed(feed.key, token)


class TestTenantsOfAnErasedOwner:
    @pytest.fixture(scope="class")
    def tenants(self, database):
        _insert_user(database, SUBJECT)
        _insert_user(database, OTHER)
        service = _tenant_service(database)
        personal = service.create_personal_tenant(SUBJECT, DISPLAY_NAME)
        organisation = service.create_organization(SUBJECT, "Gemeinschaftsgarten Nord")
        service.admin_add_membership(organisation.key, OTHER, TenantRole.GROWER)
        other_membership = ArangoMembershipRepository(database).get_by_user_and_tenant(OTHER, organisation.key)
        assert other_membership is not None
        before_other = database.collection(col.MEMBERSHIPS).get(other_membership.key)
        _erase(database, SUBJECT)
        return personal, organisation, before_other

    def test_the_personal_tenant_stays_readable_and_names_nobody(self, database, tenants):
        personal, _, _ = tenants
        after = ArangoTenantRepository(database).get_by_key(personal.key)

        assert after is not None, "the personal tenant is retained (it may hold CanG-retained harvests)"
        assert after.owner_user_key == ANONYMIZED_MARKER
        assert after.name == f"{ANONYMIZED_KEY_PREFIX}{personal.key}"
        assert after.slug == f"{ANONYMIZED_KEY_PREFIX}{personal.key}"
        raw = database.collection(col.TENANTS).get(personal.key)
        assert SUBJECT not in str(raw.values())
        assert DISPLAY_NAME not in str(raw.values())
        # The slug index is unique; the rewritten slug resolves to exactly this tenant.
        assert ArangoTenantRepository(database).get_by_slug(after.slug).key == personal.key

    def test_an_organisation_keeps_its_name_and_loses_the_owner_reference(self, database, tenants):
        _, organisation, _ = tenants
        after = ArangoTenantRepository(database).get_by_key(organisation.key)

        assert after is not None
        assert after.owner_user_key == ANONYMIZED_MARKER
        assert after.name == "Gemeinschaftsgarten Nord"
        assert after.slug == organisation.slug

    def test_the_other_member_of_the_organisation_is_untouched(self, database, tenants):
        _, _, before_other = tenants
        assert database.collection(col.MEMBERSHIPS).get(before_other["_key"]) == before_other

    def test_the_subject_holds_no_membership_any_more(self, database, tenants):
        assert ArangoMembershipRepository(database).list_by_user(SUBJECT) == []


class TestUnverifiedCleanupRemovesTheRegistrationMembership:
    def test_membership_and_its_location_assignment_go_with_the_unverified_account(self, database):
        _insert_user(database, "unverified", verified=False)
        tenant = _tenant_service(database).create_personal_tenant("unverified", "Neu Registriert")
        membership = ArangoMembershipRepository(database).get_by_user_and_tenant("unverified", tenant.key)
        assert membership is not None
        assignment = ArangoLocationAssignmentRepository(database).create(
            LocationAssignment(membership_key=membership.key, location_key="loc-1", tenant_key=tenant.key)
        )
        # A foreign membership in the same tenant with its own assignment stays.
        foreign = ArangoMembershipRepository(database).create(
            Membership(user_key="someone-else", tenant_key=tenant.key, role=TenantRole.VIEWER)
        )
        foreign_assignment = ArangoLocationAssignmentRepository(database).create(
            LocationAssignment(membership_key=foreign.key, location_key="loc-1", tenant_key=tenant.key)
        )

        assert ArangoUserRepository(database).delete("unverified") is True

        assert database.collection(col.MEMBERSHIPS).get(membership.key) is None
        assert database.collection(col.LOCATION_ASSIGNMENTS).get(assignment.key) is None
        dangling = list(
            database.aql.execute(
                "FOR e IN @@edges FILTER e._from == @id RETURN e._key",
                bind_vars={"@edges": col.ASSIGNMENT_FOR, "id": f"{col.LOCATION_ASSIGNMENTS}/{assignment.key}"},
            )
        )
        assert dangling == []
        assert database.collection(col.MEMBERSHIPS).get(foreign.key) is not None
        assert database.collection(col.LOCATION_ASSIGNMENTS).get(foreign_assignment.key) is not None
