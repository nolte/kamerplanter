"""#769 — the care notification's read state across a full care sequence.

``confirm_reminder`` and ``update_profile`` both drive *two* propagation hooks on
the same ``care.<type>:<plant>`` row, and only their **composition** decides what
the user sees. Testing the hooks in isolation cannot see that: #769 shipped with
:class:`NotificationPropagationService` fully covered, because no test ran
``on_care_confirmed`` (marks the row read) and the follow-up
``sync_care_notification`` (reuses the very same row) back to back.

These tests therefore wire the **real** propagation service and the stateful
:class:`~tests.unit.domain.services.notification_fakes.FakeNotificationRepo` and
:class:`~tests.unit.domain.services.care_task_fakes.FakeTaskRepo` behind
:class:`CareReminderService`, and assert on the badge predicate
(``read_at is null``) rather than on hook calls. Two rules are pinned:

* a notification announcing a **newly created** care task is unread — it is a new
  future care date the user has never seen (the #769 defect);
* a notification merely **retimed** for the occurrence the user already has keeps
  its read state — an interval edit must not resurface a note the user
  deliberately dealt with (this would be #769's mirror-image defect).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.notification import Notification, NotificationStatus
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.notification_propagation_service import NotificationPropagationService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo
from tests.unit.domain.services.notification_fakes import FakeNotificationRepo

PLANT_KEY = "plant-1"
PLANT_LABEL = "Monstera"
TENANT = "tenant-A"
USER = "user-a"
INTERVAL_DAYS = 7
CARE_GROUP_KEY = f"care.{ReminderType.WATERING.value}:{PLANT_KEY}"


def _profile(**kwargs) -> CareProfile:
    defaults = {
        "key": "cp-1",
        "plant_key": PLANT_KEY,
        "watering_interval_days": INTERVAL_DAYS,
        "winter_watering_multiplier": 1.0,
        "auto_create_watering_task": True,
        "adaptive_learning_enabled": False,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return CareProfile(**defaults)


def _due_watering_task(key: str = "task-due") -> Task:
    """The plant's open watering care task, due today."""
    return Task(
        key=key,
        name=f"{PLANT_LABEL} — {ReminderType.WATERING.value}",
        instruction=f"Water {PLANT_LABEL} (every {INTERVAL_DAYS} days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=TaskStatus.PENDING,
        due_date=datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0),
    )


def _service(
    task_repo: FakeTaskRepo,
    notification_repo: FakeNotificationRepo,
    *,
    profile: CareProfile | None = None,
) -> CareReminderService:
    """Wire the care service to the *real* propagation service (no mocks between)."""
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = profile or _profile()
    care_repo.get_last_confirmation.return_value = None
    care_repo.update_profile.side_effect = lambda _key, updated: updated
    care_repo.create_confirmation.side_effect = lambda conf: CareConfirmation(**{**conf.model_dump(), "_key": "conf-1"})

    plant = SimpleNamespace(
        key=PLANT_KEY,
        plant_name=PLANT_LABEL,
        instance_id="MON-1",
        tenant_key=TENANT,
        current_phase_key=None,
        slot_key=None,
    )
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    plant_repo.get_or_raise.return_value = plant

    return CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo,
        plant_repo=plant_repo,
        notification_propagation=NotificationPropagationService(notification_repo),
    )


def _seed_care_notification(repo: FakeNotificationRepo, *, due_date: datetime) -> Notification:
    """The live care note the user sees before the sequence starts."""
    return repo.create(
        Notification(
            tenant_key=TENANT,
            user_key=USER,
            notification_type=f"care.{ReminderType.WATERING.value}",
            title=PLANT_LABEL,
            body=f"{ReminderType.WATERING.value} due on {due_date.date().isoformat()}: {PLANT_LABEL}",
            data={"plant_key": PLANT_KEY, "due_date": due_date.isoformat()},
            group_key=CARE_GROUP_KEY,
            status=NotificationStatus.DELIVERED,
        )
    )


def _care_row(repo: FakeNotificationRepo) -> Notification:
    rows = [n for n in repo.all_rows() if n.group_key == CARE_GROUP_KEY]
    assert len(rows) == 1, f"expected exactly one care row, got {len(rows)}"
    return rows[0]


# ── the defect: the follow-up occurrence must reach the badge ───────────────


def test_confirmation_follow_up_notification_is_unread() -> None:
    """#769: confirming watering leaves the follow-up note *unread*.

    The sequence is the live one: ``on_care_confirmed`` closes the note (badge
    drops, correctly), then the newly created follow-up task is announced through
    the same ``group_key``. Reusing that row without clearing ``read_at`` produces
    a correctly-worded note the badge query can never return.
    """
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    notification_repo = FakeNotificationRepo()
    _seed_care_notification(notification_repo, due_date=today)
    task_repo = FakeTaskRepo([_due_watering_task()])
    service = _service(task_repo, notification_repo)

    service.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT, user_key=USER)

    # A follow-up task was scheduled — the note announces a *new* care date.
    follow_up = task_repo.open_care_tasks(ReminderType.WATERING)
    assert len(follow_up) == 1

    row = _care_row(notification_repo)
    assert row.read_at is None, "the follow-up care note must reach the unread badge"
    assert row.acted_at is None
    # …carrying the follow-up's data, not the confirmed occurrence's.
    assert follow_up[0].due_date is not None
    expected_due = follow_up[0].due_date.date().isoformat()
    assert expected_due in row.body
    assert row.title == PLANT_LABEL
    assert row.data["task_key"] == follow_up[0].key
    assert row.data["due_date"] == follow_up[0].due_date.isoformat()
    # …and the badge query actually returns it.
    assert [n.key for n in notification_repo.unread_for(USER, TENANT)] == [row.key]


def test_confirmation_without_follow_up_leaves_the_note_closed() -> None:
    """No follow-up task → nothing new to announce → the note stays done.

    Guards the fix against over-reach: opting out of auto-scheduling must not
    resurrect the note the confirmation just closed.
    """
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    notification_repo = FakeNotificationRepo()
    _seed_care_notification(notification_repo, due_date=today)
    task_repo = FakeTaskRepo([_due_watering_task()])
    service = _service(task_repo, notification_repo, profile=_profile(auto_create_watering_task=False))

    service.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT, user_key=USER)

    assert task_repo.open_care_tasks(ReminderType.WATERING) == []
    row = _care_row(notification_repo)
    assert row.read_at is not None
    assert row.acted_at is not None
    assert notification_repo.unread_for(USER, TENANT) == []


# ── the sibling path: an interval edit ──────────────────────────────────────


def test_interval_edit_retiming_a_pending_task_keeps_the_read_state() -> None:
    """An interval edit that only *moves* the pending occurrence never re-badges.

    The user already dealt with this note (read/confirmed ahead of schedule);
    editing the cadence shifts the same task's due date rather than announcing a
    new care event. Clearing ``read_at`` here would be #769's mirror-image
    defect — and it would diverge from the task path, where moving a task's due
    date (:meth:`sync_task_due_notification`) equally leaves the read state alone.
    """
    notification_repo = FakeNotificationRepo()
    seeded = _seed_care_notification(notification_repo, due_date=datetime.now(UTC) + timedelta(days=3))
    read_at = datetime(2026, 3, 1, tzinfo=UTC)
    seeded.read_at = read_at
    seeded.acted_at = read_at

    pending = _due_watering_task("task-pending")
    pending.due_date = datetime.now(UTC) + timedelta(days=3)
    task_repo = FakeTaskRepo([pending])
    service = _service(task_repo, notification_repo)

    service.update_profile(PLANT_KEY, {"watering_interval_days": 14}, user_key=USER)

    row = _care_row(notification_repo)
    assert row.read_at == read_at, "a retimed occurrence must not resurface in the badge"
    assert row.acted_at == read_at
    # The note still follows the new cycle — only the read state is untouched.
    rescheduled = task_repo.get_task("task-pending")
    assert rescheduled is not None
    assert rescheduled.due_date is not None
    assert rescheduled.due_date.date().isoformat() in row.body
    assert notification_repo.unread_for(USER, TENANT) == []


def test_interval_edit_creating_a_task_resets_the_read_state() -> None:
    """An interval edit with no open task *creates* one → same rule as a confirmation.

    Nothing is being retimed here: :meth:`ensure_next_watering_task` materialises
    a brand-new occurrence, so the reused row announces a care date the user has
    never seen and must reach the badge (#769).
    """
    notification_repo = FakeNotificationRepo()
    seeded = _seed_care_notification(notification_repo, due_date=datetime.now(UTC))
    seeded.read_at = datetime(2026, 3, 1, tzinfo=UTC)
    seeded.acted_at = seeded.read_at

    task_repo = FakeTaskRepo()  # no open watering task at all
    service = _service(task_repo, notification_repo)

    service.update_profile(PLANT_KEY, {"watering_interval_days": 14}, user_key=USER)

    created = task_repo.open_care_tasks(ReminderType.WATERING)
    assert len(created) == 1
    row = _care_row(notification_repo)
    assert row.read_at is None
    assert row.acted_at is None
    assert row.data["task_key"] == created[0].key
    assert [n.key for n in notification_repo.unread_for(USER, TENANT)] == [row.key]
