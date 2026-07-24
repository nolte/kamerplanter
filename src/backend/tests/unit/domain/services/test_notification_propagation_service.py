"""Unit tests for :class:`NotificationPropagationService` (REQ-030 §4.2, #742).

The source→notification feedback loop is exercised end-to-end against a small
in-memory notification repository double, so every rule's real effect (update in
place, mark done, delete, single-entry idempotency, tenant isolation) is asserted
on the resulting notification rows — not just on mock calls.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import ReminderType
from app.domain.models.notification import Notification, NotificationStatus
from app.domain.models.task import Task
from app.domain.services.notification_propagation_service import (
    NotificationPropagationService,
)


class FakeNotificationRepo:
    """Minimal in-memory :class:`INotificationRepository` for propagation tests."""

    def __init__(self) -> None:
        self._store: dict[str, Notification] = {}
        self._seq = 0

    # ── writes ──
    def create(self, notification: Notification) -> Notification:
        self._seq += 1
        key = f"n{self._seq}"
        notification.key = key
        notification.created_at = datetime.now(UTC) + timedelta(seconds=self._seq)
        self._store[key] = notification
        return notification

    def update(self, key: str, notification: Notification) -> Notification:
        notification.key = key
        self._store[key] = notification
        return notification

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def mark_read(self, key: str, read_at: datetime) -> Notification | None:
        notif = self._store.get(key)
        if notif is None:
            return None
        notif.read_at = read_at
        return notif

    def mark_acted(self, key: str, acted_at: datetime) -> Notification | None:
        notif = self._store.get(key)
        if notif is None:
            return None
        notif.acted_at = acted_at
        return notif

    # ── reads ──
    def get(self, key: str) -> Notification | None:
        return self._store.get(key)

    def list_by_group_key(self, group_key: str, tenant_key: str) -> list[Notification]:
        rows = [n for n in self._store.values() if n.group_key == group_key and n.tenant_key == tenant_key]
        rows.sort(key=lambda n: n.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return rows

    # ── test helpers ──
    def all_rows(self) -> list[Notification]:
        return list(self._store.values())


@pytest.fixture
def repo() -> FakeNotificationRepo:
    return FakeNotificationRepo()


@pytest.fixture
def service(repo: FakeNotificationRepo) -> NotificationPropagationService:
    return NotificationPropagationService(repo)


def _task(**kwargs) -> Task:
    defaults = {
        "_key": "task1",
        "tenant_key": "t1",
        "name": "Prune apple tree",
        "status": "pending",
        "due_date": datetime(2026, 7, 24, tzinfo=UTC),
        "assigned_to_user_key": "user-a",
        "entity_key": "plant1",
        "entity_type": "plant_instance",
    }
    defaults.update(kwargs)
    return Task(**defaults)


# ── Rule 1: task moved (due date changed) → notification shows new due ──────


class TestTaskDueSync:
    def test_creates_due_notification_for_assigned_task(self, service, repo):
        service.sync_task_due_notification(_task())

        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].notification_type == "task.due"
        assert rows[0].group_key == "task.due:task1"
        assert rows[0].user_key == "user-a"
        assert "2026-07-24" in rows[0].body

    def test_title_prefers_german_name_to_mirror_ui(self, service, repo):
        # The UI renders name_de under the German default locale, so the in-app
        # notification title must use it too (an English title would never match
        # what the user sees on the task detail page).
        service.sync_task_due_notification(
            _task(name="Water indoor plants", name_de="Zimmerpflanzen gießen"),
            recipient_user_key="owner",
        )
        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].title == "Zimmerpflanzen gießen"

    def test_moving_due_updates_in_place_no_duplicate(self, service, repo):
        service.sync_task_due_notification(_task())
        moved = _task(due_date=datetime(2026, 7, 28, tzinfo=UTC), name="Prune apple tree -- moved")
        service.sync_task_due_notification(moved)

        rows = repo.all_rows()
        assert len(rows) == 1  # updated in place, not duplicated
        assert "2026-07-28" in rows[0].body
        assert rows[0].title == "Prune apple tree -- moved"

    def test_unassigned_task_without_actor_creates_no_notification(self, service, repo):
        # No assignee and no acting owner → no resolvable recipient → no notification.
        service.sync_task_due_notification(_task(assigned_to_user_key=None))
        assert repo.all_rows() == []

    def test_actor_owns_due_notification_over_assignee(self, service, repo):
        # The acting owner (editor) receives the due notification, not the assignee.
        service.sync_task_due_notification(_task(assigned_to_user_key="assignee"), recipient_user_key="owner")
        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].user_key == "owner"

    def test_unassigned_task_with_actor_notifies_owner(self, service, repo):
        # An unassigned task still notifies its acting owner (threaded from the API).
        service.sync_task_due_notification(_task(assigned_to_user_key=None), recipient_user_key="owner")
        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].user_key == "owner"
        assert rows[0].notification_type == "task.due"

    def test_plant_scoped_care_reminder_task_is_skipped(self, service, repo):
        # A plant-scoped care task is owned by the care path → skipped here.
        service.sync_task_due_notification(
            _task(category="care_reminder", entity_key="plant1"), recipient_user_key="owner"
        )
        assert repo.all_rows() == []

    def test_standalone_care_task_gets_due_notification(self, service, repo):
        # A standalone care task (no plant) has no care-path counterpart → notify.
        service.sync_task_due_notification(
            _task(category="care_reminder", entity_key=None, entity_type=None),
            recipient_user_key="owner",
        )
        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].notification_type == "task.due"
        assert rows[0].user_key == "owner"

    def test_empty_tenant_is_noop(self, service, repo):
        service.sync_task_due_notification(_task(tenant_key=""))
        assert repo.all_rows() == []

    def test_completing_via_sync_marks_existing_done(self, service, repo):
        service.sync_task_due_notification(_task())
        # Now the task is completed → the live notification must be closed.
        service.sync_task_due_notification(_task(status="completed"))
        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].read_at is not None
        assert rows[0].acted_at is not None


# ── Rule 2: task reassigned → new member gets assignment notification ───────


class TestTaskReassign:
    def test_new_assignee_gets_assignment_and_owner_keeps_due(self, service, repo):
        # The owner ("owner") holds the due notification ...
        service.sync_task_due_notification(_task(assigned_to_user_key="user-a"), recipient_user_key="owner")
        # ... reassigning from user-a to user-b delivers an assignment to user-b.
        reassigned = _task(assigned_to_user_key="user-b")
        service.on_task_reassigned(reassigned, previous_user_key="user-a")

        rows = repo.all_rows()
        assigned = [n for n in rows if n.notification_type == "task.assigned"]
        assert len(assigned) == 1
        assert assigned[0].user_key == "user-b"
        assert "assigned" in assigned[0].body.lower()

        # The owner's due notification is untouched by the reassignment.
        due = [n for n in rows if n.notification_type == "task.due"]
        assert len(due) == 1
        assert due[0].user_key == "owner"

    def test_same_assignee_is_noop(self, service, repo):
        service.on_task_reassigned(_task(assigned_to_user_key="user-a"), previous_user_key="user-a")
        assert repo.all_rows() == []

    def test_reassign_to_none_removes_previous_assignment_only(self, service, repo):
        service.sync_task_due_notification(_task(assigned_to_user_key="user-a"), recipient_user_key="owner")
        service.on_task_reassigned(_task(assigned_to_user_key="user-a"), previous_user_key=None)
        # Unassigning drops the assignment notification ...
        service.on_task_reassigned(_task(assigned_to_user_key=None), previous_user_key="user-a")
        rows = repo.all_rows()
        assert [n for n in rows if n.notification_type == "task.assigned"] == []
        # ... but the owner's due notification survives.
        due = [n for n in rows if n.notification_type == "task.due"]
        assert len(due) == 1
        assert due[0].user_key == "owner"


# ── Rule 3: task deleted → orphaned notification removed ────────────────────


class TestTaskDeleted:
    def test_delete_removes_all_task_notifications(self, service, repo):
        task = _task()
        service.sync_task_due_notification(task)
        service.on_task_reassigned(_task(assigned_to_user_key="user-a"), previous_user_key=None)
        assert repo.all_rows()  # something exists

        service.on_task_deleted(task)
        assert repo.all_rows() == []

    def test_delete_only_touches_own_task(self, service, repo):
        service.sync_task_due_notification(_task(_key="task1"))
        service.sync_task_due_notification(_task(_key="task2", name="Other"))
        service.on_task_deleted(_task(_key="task1"))

        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].group_key == "task.due:task2"


# ── Rule 4: task completed → open due notification marked done ──────────────


class TestTaskCompleted:
    def test_completed_marks_read_and_acted(self, service, repo):
        service.sync_task_due_notification(_task())
        service.on_task_completed(_task(status="completed"))

        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].read_at is not None
        assert rows[0].acted_at is not None

    def test_completed_care_task_closes_care_notification(self, service, repo):
        # A per-plant care notification exists ...
        service.sync_care_notification(
            tenant_key="t1",
            user_key="user-a",
            plant_key="plant1",
            plant_label="Monstera",
            reminder_type=ReminderType.WATERING,
            due_date=datetime(2026, 7, 24, tzinfo=UTC),
        )
        # ... completing the matching care task via the queue closes it.
        care_task = _task(
            category="care_reminder",
            name="Monstera — watering",
            entity_key="plant1",
            status="completed",
        )
        service.on_task_completed(care_task)

        care_rows = [n for n in repo.all_rows() if n.group_key == "care.watering:plant1"]
        assert len(care_rows) == 1
        assert care_rows[0].read_at is not None
        assert care_rows[0].acted_at is not None


# ── Rule 5: watering interval changed → single rescheduled care notification ─


class TestCareReschedule:
    def test_upsert_creates_single_actionable_notification(self, service, repo):
        service.sync_care_notification(
            tenant_key="t1",
            user_key="user-a",
            plant_key="plant1",
            plant_label="Monstera",
            reminder_type=ReminderType.WATERING,
            due_date=datetime(2026, 8, 1, tzinfo=UTC),
        )
        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].notification_type == "care.watering"
        assert rows[0].group_key == "care.watering:plant1"
        assert "2026-08-01" in rows[0].body
        # Carries the §4.2 actionable confirm button.
        assert [a.action_id for a in rows[0].actions] == ["confirm"]

    def test_repeated_reschedule_stays_single_entry(self, service, repo):
        for due in (datetime(2026, 8, 1, tzinfo=UTC), datetime(2026, 8, 14, tzinfo=UTC)):
            service.sync_care_notification(
                tenant_key="t1",
                user_key="user-a",
                plant_key="plant1",
                plant_label="Monstera",
                reminder_type=ReminderType.WATERING,
                due_date=due,
            )
        rows = repo.all_rows()
        assert len(rows) == 1  # no duplicate for the same plant + type
        assert "2026-08-14" in rows[0].body

    def test_prunes_stray_duplicate_to_one(self, service, repo):
        # Simulate two pre-existing rows for the same group (legacy drift).
        for _ in range(2):
            repo.create(
                Notification(
                    tenant_key="t1",
                    user_key="user-a",
                    notification_type="care.watering",
                    title="Monstera",
                    body="old",
                    group_key="care.watering:plant1",
                    status=NotificationStatus.DELIVERED,
                )
            )
        service.sync_care_notification(
            tenant_key="t1",
            user_key="user-a",
            plant_key="plant1",
            plant_label="Monstera",
            reminder_type=ReminderType.WATERING,
            due_date=datetime(2026, 8, 1, tzinfo=UTC),
        )
        rows = repo.all_rows()
        assert len(rows) == 1  # duplicates pruned

    def test_empty_tenant_is_noop(self, service, repo):
        service.sync_care_notification(
            tenant_key="",
            user_key="user-a",
            plant_key="plant1",
            plant_label="Monstera",
            reminder_type=ReminderType.WATERING,
            due_date=datetime(2026, 8, 1, tzinfo=UTC),
        )
        assert repo.all_rows() == []


# ── Rule 6: care reminder confirmed → notification done ─────────────────────


class TestCareConfirmed:
    def test_confirm_marks_notification_done(self, service, repo):
        service.sync_care_notification(
            tenant_key="t1",
            user_key="user-a",
            plant_key="plant1",
            plant_label="Monstera",
            reminder_type=ReminderType.WATERING,
            due_date=datetime(2026, 8, 1, tzinfo=UTC),
        )
        service.on_care_confirmed(tenant_key="t1", plant_key="plant1", reminder_type=ReminderType.WATERING)

        rows = repo.all_rows()
        assert len(rows) == 1
        assert rows[0].read_at is not None
        assert rows[0].acted_at is not None

    def test_confirm_without_notification_is_safe(self, service, repo):
        service.on_care_confirmed(tenant_key="t1", plant_key="plant1", reminder_type=ReminderType.WATERING)
        assert repo.all_rows() == []


# ── Negative: tenant isolation across all mutating hooks ────────────────────


class TestTenantIsolation:
    def test_foreign_tenant_notification_untouched_on_complete(self, service, repo):
        # A notification owned by tenant t2 for the same group_key.
        foreign = repo.create(
            Notification(
                tenant_key="t2",
                user_key="user-x",
                notification_type="task.due",
                title="foreign",
                body="foreign",
                group_key="task.due:task1",
                status=NotificationStatus.DELIVERED,
            )
        )
        service.on_task_completed(_task(tenant_key="t1"))
        # The foreign tenant's notification is never marked done.
        assert repo.get(foreign.key).read_at is None

    def test_care_confirm_is_tenant_scoped(self, service, repo):
        foreign = repo.create(
            Notification(
                tenant_key="t2",
                user_key="user-x",
                notification_type="care.watering",
                title="foreign",
                body="foreign",
                group_key="care.watering:plant1",
                status=NotificationStatus.DELIVERED,
            )
        )
        service.on_care_confirmed(tenant_key="t1", plant_key="plant1", reminder_type=ReminderType.WATERING)
        assert repo.get(foreign.key).read_at is None
