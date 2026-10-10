"""#2114 (MT-017, REQ-024 AK-62): the care-reminder beat notifies active members only, and a summary is one tenant's.

``dispatch_due_care`` and ``send_daily_summary`` took the recipient from the task's ``assigned_to`` and notified it
with no look at the membership: an account that had left a tenant went on receiving its plant names and due dates.
The daily summary also took the tenant of **the first task document** of a user, so a user in two tenants got one
notification holding both tenants' tasks, filed under the wrong tenant. Both now ask the stored membership of
``(user, tenant)`` - the question ``frost_forecast_tasks`` already asks - and the summary is built per
``(user, tenant)``.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import ModuleType
from unittest.mock import MagicMock

import pytest

TODAY = datetime.now(UTC).isoformat()


class _Memberships:
    """``IMembershipRepository.get_by_user_and_tenant`` over a set of active ``(user, tenant)`` pairs."""

    def __init__(self, *active: tuple[str, str], inactive: tuple[tuple[str, str], ...] = ()) -> None:
        self.active = set(active)
        self.inactive = set(inactive)
        self.asked: list[tuple[str, str]] = []

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str):
        self.asked.append((user_key, tenant_key))
        if (user_key, tenant_key) in self.active:
            return MagicMock(is_active=True)
        if (user_key, tenant_key) in self.inactive:
            return MagicMock(is_active=False)
        return None


class _Notifier:
    def __init__(self) -> None:
        self.care: list[tuple[str, list[str]]] = []
        self.summaries: list[dict] = []
        self.prefs = MagicMock()
        self.prefs.daily_summary.enabled = True

    async def send_care_notifications(self, tenant_key: str, tasks: list[dict]) -> dict:
        self.care.append((tenant_key, [t["user_key"] for t in tasks]))
        return {"users_notified": len({t["user_key"] for t in tasks}), "total_sent": len(tasks)}

    def get_preferences(self, _user_key: str):
        return self.prefs

    async def send_notification(self, **kwargs) -> None:
        self.summaries.append(kwargs)


def _task(name: str, user: str, tenant: str) -> dict:
    return {
        "category": "care_reminder",
        "status": "pending",
        "due_date": TODAY,
        "priority": "medium",
        "name": f"{name} — watering",
        "plant_key": f"p-{name}",
        "assigned_to": user,
        "tenant_key": tenant,
    }


@pytest.fixture
def world(monkeypatch):
    deps = ModuleType("app.common.dependencies")
    notifier = _Notifier()
    memberships = _Memberships()
    tasks = MagicMock()
    deps.get_task_repo = MagicMock(return_value=tasks)  # type: ignore[attr-defined]
    deps.get_notification_service = MagicMock(return_value=notifier)  # type: ignore[attr-defined]
    deps.get_membership_repo = MagicMock(return_value=memberships)  # type: ignore[attr-defined]
    # #2166 — every tenant here is active; the tenant gate has its own test (test_care_beats_skip_closed_tenants).
    deps.get_tenant_repo = MagicMock(return_value=MagicMock(get_by_key=lambda key: MagicMock(is_active=True)))  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)

    class World:
        pass

    w = World()
    w.notifier, w.memberships, w.tasks = notifier, memberships, tasks  # type: ignore[attr-defined]

    def given(*docs: dict) -> None:
        tasks.get_all.return_value = (list(docs), len(docs))

    w.given = given  # type: ignore[attr-defined]
    return w


def test_an_ex_member_is_not_notified_of_the_tenants_due_care(world) -> None:
    from app.tasks.notification_tasks import dispatch_due_care_notifications

    world.memberships.active.add(("current", "t1"))
    world.given(_task("Monstera", "ex-member", "t1"), _task("Basil", "current", "t1"))

    result = dispatch_due_care_notifications()

    assert world.notifier.care == [("t1", ["current"])]
    assert result["tasks_found"] == 1


def test_a_deactivated_membership_is_not_notified_either(world) -> None:
    from app.tasks.notification_tasks import dispatch_due_care_notifications

    world.memberships.inactive.add(("suspended", "t1"))
    world.given(_task("Monstera", "suspended", "t1"))

    result = dispatch_due_care_notifications()

    assert world.notifier.care == []
    assert result["status"] == "empty"


def test_a_member_of_another_tenant_is_not_a_member_of_this_one(world) -> None:
    """The check is per ``(user, tenant)``: membership in t2 does not cover a task of t1."""
    from app.tasks.notification_tasks import dispatch_due_care_notifications

    world.memberships.active.add(("someone", "t2"))
    world.given(_task("Monstera", "someone", "t1"))

    dispatch_due_care_notifications()

    assert world.notifier.care == []


def test_the_membership_of_a_pair_is_asked_once_per_run(world) -> None:
    from app.tasks.notification_tasks import dispatch_due_care_notifications

    world.memberships.active.add(("current", "t1"))
    world.given(*[_task(f"Plant{i}", "current", "t1") for i in range(5)])

    dispatch_due_care_notifications()

    assert world.memberships.asked == [("current", "t1")]


def test_a_user_in_two_tenants_gets_one_summary_per_tenant_with_that_tenants_tasks(world) -> None:
    from app.tasks.notification_tasks import send_daily_summary

    world.memberships.active.update({("both", "t1"), ("both", "t2")})
    world.given(_task("Alpha", "both", "t1"), _task("Beta", "both", "t2"), _task("Gamma", "both", "t2"))

    result = send_daily_summary()

    by_tenant = {s["tenant_key"]: s for s in world.notifier.summaries}
    assert sorted(by_tenant) == ["t1", "t2"]
    assert "Alpha" in by_tenant["t1"]["body"] and "Beta" not in by_tenant["t1"]["body"]
    assert "Beta" in by_tenant["t2"]["body"] and "Gamma" in by_tenant["t2"]["body"]
    assert "Alpha" not in by_tenant["t2"]["body"]
    assert result["summaries_sent"] == 2
    # one notification group per (user, tenant): a second summary must not replace the first
    assert len({s["group_key"] for s in world.notifier.summaries}) == 2


def test_the_summary_leaves_out_the_tenants_the_user_left(world) -> None:
    from app.tasks.notification_tasks import send_daily_summary

    world.memberships.active.add(("both", "t2"))
    world.given(_task("Alpha", "both", "t1"), _task("Beta", "both", "t2"))

    send_daily_summary()

    assert [s["tenant_key"] for s in world.notifier.summaries] == ["t2"]
    assert "Alpha" not in world.notifier.summaries[0]["body"]


def test_an_ex_member_gets_no_summary_at_all(world) -> None:
    from app.tasks.notification_tasks import send_daily_summary

    world.given(_task("Alpha", "ex-member", "t1"))

    result = send_daily_summary()

    assert world.notifier.summaries == []
    assert result["summaries_sent"] == 0
