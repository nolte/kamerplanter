"""#2114 (MT-017): an ended membership takes the task assignments with it, and the beat asks the membership.

Driven against a **real** ArangoDB: the real ``TenantService`` over the real membership, tenant and task
repositories, then the real beat tasks ``dispatch_due_care_notifications`` / ``send_daily_summary`` over the real
task and membership collections (only the notification sender is a recorder - what it is *handed* is the
measurement). Two properties:

* leaving a tenant clears the assignee of **that tenant's** tasks and no one else's, and of no other tenant's;
* an assignment that outlived its membership anyway - data written before this fix, or a failed clear - reaches
  nobody: the beat notifies by the stored membership of ``(user, tenant)``.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

import app.common.dependencies as deps
from app.common.enums import TenantRole
from app.data_access.arango import collections as col
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import Membership
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("membership_end_assignments")
EX = "u-ex"
STAYS = "u-stays"

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


def _task(key: str, tenant: str, user: str) -> dict:
    return {
        "_key": key,
        "name": f"{key} — watering",
        "category": "care_reminder",
        "status": "pending",
        "priority": "medium",
        "tenant_key": tenant,
        "assigned_to_user_key": user,
        "entity_type": "plant_instance",
        "entity_key": f"p-{key}",
        "due_date": datetime.now(UTC).isoformat(),
    }


@pytest.fixture
def db(database):
    for name in (col.TENANTS, col.USERS, col.MEMBERSHIPS, col.HAS_MEMBERSHIP, col.MEMBERSHIP_IN, col.TASKS):
        database.collection(name).truncate()
    for key in (EX, STAYS):
        database.collection(col.USERS).insert({"_key": key, "email": f"{key}@example.com", "display_name": key})
    for key in ("t1", "t2"):
        database.collection(col.TENANTS).insert(
            {
                "_key": key,
                "name": key,
                "slug": key,
                "tenant_type": "organization",
                "owner_user_key": STAYS,
                "is_active": True,
                "is_platform": False,
                "max_members": 50,
                "settings": {},
            }
        )
    memberships = ArangoMembershipRepository(database)
    for user, tenant, role in (
        (STAYS, "t1", TenantRole.LEAD),
        (EX, "t1", TenantRole.GROWER),
        (STAYS, "t2", TenantRole.LEAD),
        (EX, "t2", TenantRole.GROWER),
    ):
        memberships.create(Membership(user_key=user, tenant_key=tenant, role=role, is_active=True))
    for task in (
        _task("ex-t1", "t1", EX),
        _task("stays-t1", "t1", STAYS),
        _task("ex-t2", "t2", EX),
    ):
        database.collection(col.TASKS).insert(task)
    return database


def _service(db) -> TenantService:
    return TenantService(
        tenant_repo=ArangoTenantRepository(db),
        membership_repo=ArangoMembershipRepository(db),
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
        task_repo=ArangoTaskRepository(db),
    )


def _assignee(db, key: str) -> str | None:
    return db.collection(col.TASKS).get(key).get("assigned_to_user_key")


class _Recorder:
    def __init__(self) -> None:
        self.care: list[tuple[str, list[str]]] = []
        self.summaries: list[tuple[str, str]] = []

    async def send_care_notifications(self, tenant_key: str, tasks: list[dict]) -> dict:
        self.care.append((tenant_key, sorted(t["user_key"] for t in tasks)))
        return {"users_notified": len(tasks), "total_sent": len(tasks)}

    def get_preferences(self, _user_key: str):
        prefs = MagicMock()
        prefs.daily_summary.enabled = True
        return prefs

    async def send_notification(self, **kwargs) -> None:
        self.summaries.append((kwargs["user_key"], kwargs["tenant_key"]))


@pytest.fixture
def beat(db, monkeypatch):
    recorder = _Recorder()
    monkeypatch.setattr(deps, "get_notification_service", lambda: recorder)
    monkeypatch.setattr(deps, "get_task_repo", lambda: ArangoTaskRepository(db))
    monkeypatch.setattr(deps, "get_membership_repo", lambda: ArangoMembershipRepository(db))
    # #2166 — the beat asks the stored tenant as well (``tenant_gate.ActiveTenants``); this database's.
    monkeypatch.setattr(deps, "get_tenant_repo", lambda: ArangoTenantRepository(db))
    return recorder


def test_leaving_clears_the_assignee_of_that_tenants_tasks_only(db) -> None:
    _service(db).leave_tenant("t1", EX)

    assert _assignee(db, "ex-t1") is None
    assert _assignee(db, "stays-t1") == STAYS
    # The same account is still a member of t2: its assignment there is untouched.
    assert _assignee(db, "ex-t2") == EX


def test_the_beat_notifies_nobody_for_an_assignment_that_outlived_its_membership(db, beat) -> None:
    """Data written before the fix: the membership is gone, the assignment is not."""
    ArangoMembershipRepository(db).delete(
        ArangoMembershipRepository(db).get_by_user_and_tenant(EX, "t1").key  # type: ignore[union-attr]
    )
    assert _assignee(db, "ex-t1") == EX

    from app.tasks.notification_tasks import dispatch_due_care_notifications, send_daily_summary

    dispatch_due_care_notifications()
    send_daily_summary()

    assert ("t1", [EX]) not in beat.care
    assert [pair for pair in beat.summaries if pair == (EX, "t1")] == []
    # What the member still is a member of is still notified, under that tenant.
    assert ("t2", [EX]) in beat.care
    assert (EX, "t2") in beat.summaries


def test_a_user_in_two_tenants_gets_one_summary_per_tenant(db, beat) -> None:
    db.collection(col.TASKS).insert(_task("ex-t1-second", "t1", EX))

    from app.tasks.notification_tasks import send_daily_summary

    send_daily_summary()

    assert sorted(pair for pair in beat.summaries if pair[0] == EX) == [(EX, "t1"), (EX, "t2")]
