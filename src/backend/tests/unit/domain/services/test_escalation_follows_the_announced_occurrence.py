"""#3135 — the overdue escalation follows the occurrence the care row announces.

The plant's ``care.watering:<plant>`` row is ONE row for every watering: a
confirmation closes it, the follow-up task re-opens it (``reset_read``, #769),
a retiming moves its due date. Before #3135 the escalation measured "overdue
for N days" from that row's ``created_at`` and never restarted its level, so:

* the follow-up occurrence — not due for a week — was escalated at the next run,
  because the row was as old as the plant's first reminder;
* the levels reached by the previous occurrence carried over (level 3: the next
  occurrence was never escalated at all);
* an escalation row (same ``group_key``, newer) was the row a retiming kept, and
  the reminder itself was pruned as its "duplicate".

Every step here runs through the real chain — :class:`CareReminderService`,
:class:`NotificationPropagationService`, :class:`NotificationEngine` — over the
stateful :class:`~tests.unit.domain.services.notification_fakes.EscalationNotificationRepo`,
whose overdue filter is held to the AQL by one case table
(``tests/support/overdue_watering_cases.py``). The clock is frozen per step, so
"overdue" is a property of the dates in the test, not of the day it runs.

Traces to issue #3135 (no TC-ID: service-chain unit tests).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from freezegun import freeze_time

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.notification import (
    WATERING_ESCALATION_TYPE,
    WATERING_REMINDER_TYPE,
    ChannelResult,
    Notification,
    NotificationPreferences,
    NotificationStatus,
)
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.notification_propagation_service import NotificationPropagationService
from app.domain.services.notification_service import NotificationService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo
from tests.unit.domain.services.notification_fakes import EscalationNotificationRepo

PLANT_KEY = "plant-1"
PLANT_LABEL = "Monstera"
TENANT = "tenant-A"
USER = "user-a"
INTERVAL_DAYS = 7
CARE_GROUP_KEY = f"care.{ReminderType.WATERING.value}:{PLANT_KEY}"

#: The first occurrence is due on this day (midnight UTC, as the producer stores it).
FIRST_DUE = datetime(2026, 11, 2, tzinfo=UTC)
#: The beat runs at 12:00 UTC.
BEAT = timedelta(hours=12)


def _member(user_key: str, tenant_key: str) -> bool:
    return bool(user_key and tenant_key)


class _Confirmations:
    """Stateful confirmation store: the follow-up is measured from the confirmation just written."""

    def __init__(self) -> None:
        self.rows: list[CareConfirmation] = []

    def create(self, confirmation: CareConfirmation, **_kwargs: object) -> CareConfirmation:
        stored = CareConfirmation(**{**confirmation.model_dump(), "_key": f"conf-{len(self.rows) + 1}"})
        self.rows.append(stored)
        return stored

    def last(self, _plant_key: str, _reminder_type: ReminderType) -> CareConfirmation | None:
        return self.rows[-1] if self.rows else None


def _world() -> SimpleNamespace:
    notifications = EscalationNotificationRepo()
    tasks = FakeTaskRepo(
        [
            Task(
                key="task-1",
                name=f"{PLANT_LABEL} — {ReminderType.WATERING.value}",
                instruction=f"Water {PLANT_LABEL} (every {INTERVAL_DAYS} days).",
                category=TaskCategory.CARE_REMINDER,
                entity_key=PLANT_KEY,
                entity_type="plant_instance",
                tenant_key=TENANT,
                status=TaskStatus.PENDING,
                due_date=FIRST_DUE,
            )
        ]
    )
    confirmations = _Confirmations()
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = CareProfile(
        _key="cp-1",
        plant_key=PLANT_KEY,
        watering_interval_days=INTERVAL_DAYS,
        winter_watering_multiplier=1.0,
        auto_create_watering_task=True,
        adaptive_learning_enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    care_repo.get_last_confirmation.side_effect = confirmations.last
    care_repo.create_confirmation.side_effect = confirmations.create
    care_repo.create_confirmation_logged.side_effect = confirmations.create
    plant = SimpleNamespace(
        key=PLANT_KEY,
        plant_name=PLANT_LABEL,
        instance_id="MON-1",
        tenant_key=TENANT,
        current_phase_key=None,
        slot_key=None,
        removed_on=None,
        species_key=None,
        cultivar_key=None,
    )
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    plant_repo.get_or_raise.return_value = plant
    propagation = NotificationPropagationService(notifications)
    care = CareReminderService(
        care_repo,
        CareReminderEngine(),
        tasks,
        plant_repo=plant_repo,
        notification_propagation=propagation,
    )

    preference_repo = MagicMock()
    preference_repo.get_by_user.return_value = NotificationPreferences(user_key=USER)
    redis = MagicMock()
    redis.get.return_value = None  # no Redis dedup: only the stored row may keep a run quiet
    engine = NotificationEngine(
        notification_repo=notifications,
        preference_repo=preference_repo,
        channel_registry=MagicMock(),
        redis_client=redis,
        user_repo=MagicMock(),
        propagation=propagation,
    )
    engine._is_quiet_hours = MagicMock(return_value=False)  # type: ignore[method-assign]
    engine._resolve_channels = MagicMock(return_value=[])  # type: ignore[method-assign]
    return SimpleNamespace(notifications=notifications, tasks=tasks, care=care, propagation=propagation, engine=engine)


def _announce(world: SimpleNamespace, due: datetime, *, task_key: str = "task-1", reset_read: bool = False) -> None:
    """The propagation owner's write for the plant's care row (create, new occurrence or retiming)."""
    world.propagation.sync_care_notification(
        tenant_key=TENANT,
        user_key=USER,
        plant_key=PLANT_KEY,
        plant_label=PLANT_LABEL,
        reminder_type=ReminderType.WATERING,
        due_date=due,
        task_key=task_key,
        reset_read=reset_read,
    )


def _escalate(world: SimpleNamespace, at: datetime) -> dict:
    with freeze_time(at):
        return asyncio.run(world.engine.escalate_overdue(TENANT, is_active_member=_member))


def _reminder(world: SimpleNamespace) -> Notification:
    rows = [
        row
        for row in world.notifications.all_rows()
        if row.group_key == CARE_GROUP_KEY and row.notification_type == WATERING_REMINDER_TYPE
    ]
    assert len(rows) == 1, f"expected exactly one care reminder row, got {len(rows)}"
    return rows[0]


# ── two consecutive occurrences ──────────────────────────────────────────────


def test_the_next_occurrence_is_not_escalated_before_it_is_overdue_and_then_from_level_one() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    reminder_key = _reminder(world).key
    created_at = _reminder(world).created_at

    # Occurrence 1 is three days overdue at the beat: level 1.
    assert _escalate(world, FIRST_DUE + timedelta(days=3) + BEAT) == {"escalated": 1}
    assert _reminder(world).escalation_level == 1

    # The user waters; the follow-up (due a week after the confirmation day) re-uses the row.
    confirmed_on = FIRST_DUE + timedelta(days=3)
    with freeze_time(confirmed_on + timedelta(hours=13)):
        world.care.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT, user_key=USER)
    follow_up = world.tasks.open_care_tasks(ReminderType.WATERING)
    assert len(follow_up) == 1
    second_due = follow_up[0].due_date
    assert second_due == confirmed_on + timedelta(days=INTERVAL_DAYS)

    reminder = _reminder(world)
    assert reminder.key == reminder_key, "the single care row is reused (#769)"
    assert reminder.created_at == created_at, "premise: the reused row keeps its creation time"
    assert reminder.data["due_date"] == second_due.isoformat()
    assert reminder.escalation_level == 0, "a new occurrence starts a new escalation cycle"
    # The finished cycle's escalation is closed, not left as an open "Overdue".
    assert all(row.acted_at is not None for row in world.notifications.escalations())

    # Every beat until the follow-up is two days overdue escalates nothing — the row
    # itself is older than every cutoff, which is what used to escalate it at once.
    day = confirmed_on + timedelta(days=1)
    while day + BEAT < second_due + timedelta(days=2):
        assert _escalate(world, day + BEAT) == {"escalated": 0}, f"escalated on {day.date()} before it was overdue"
        day += timedelta(days=1)
    assert len(world.notifications.escalations()) == 1

    # Two days overdue: escalated again, starting at level 1.
    assert _escalate(world, second_due + timedelta(days=2) + BEAT) == {"escalated": 1}
    assert _reminder(world).escalation_level == 1
    newest = max(world.notifications.escalations(), key=lambda row: row.created_at or datetime.min.replace(tzinfo=UTC))
    assert newest.escalation_level == 1
    assert newest.data["due_date"] == second_due.isoformat()


def test_a_row_retimed_into_the_future_is_not_escalated() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    later = FIRST_DUE + timedelta(days=38)

    # Ten days overdue, then retimed (dormancy ``minimal``: 7 → 38 days) before the beat.
    with freeze_time(FIRST_DUE + timedelta(days=10)):
        _announce(world, later)

    for offset in (10, 20, 39):
        assert _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT) == {"escalated": 0}, offset
    assert world.notifications.escalations() == []
    # The retimed occurrence escalates from its own due date.
    assert _escalate(world, later + timedelta(days=2) + BEAT) == {"escalated": 1}


def test_a_retiming_keeps_the_levels_already_sent_for_the_occurrence() -> None:
    """Retiming is the same occurrence: level 1 is not sent twice; the next level follows the new date."""
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    assert _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT) == {"escalated": 1}
    moved = FIRST_DUE + timedelta(days=5)
    with freeze_time(FIRST_DUE + timedelta(days=3)):
        _announce(world, moved)

    assert _reminder(world).escalation_level == 1
    assert _escalate(world, moved + timedelta(days=2) + BEAT) == {"escalated": 0}
    assert _escalate(world, moved + timedelta(days=4) + BEAT) == {"escalated": 1}
    assert _reminder(world).escalation_level == 2


# ── escalation rows in the reminder's group ─────────────────────────────────


def test_escalation_rows_are_never_escalated_themselves() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    reminder_key = _reminder(world).key

    for offset in (2, 4, 7, 9, 12, 20):
        _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT)

    assert [level for _key, level in world.notifications.claims] == [1, 2, 3]
    assert {key for key, _level in world.notifications.claims} == {reminder_key}
    assert {row.parent_notification_key for row in world.notifications.escalations()} == {reminder_key}


def test_a_retiming_after_an_escalation_keeps_the_reminder_and_leaves_the_escalation() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    reminder_key = _reminder(world).key
    _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT)
    (escalation,) = world.notifications.escalations()
    escalation_before = escalation.model_copy(deep=True)

    moved = FIRST_DUE + timedelta(days=20)
    with freeze_time(FIRST_DUE + timedelta(days=3)):
        _announce(world, moved)

    reminder = _reminder(world)
    assert reminder.key == reminder_key, "the reminder survives a retiming of its group"
    assert reminder.data["due_date"] == moved.isoformat()
    assert world.notifications.get(escalation.key or "") == escalation_before, "the escalation is an event row"
    assert world.notifications.updates == [reminder_key]


def test_a_new_occurrence_closes_the_open_escalations_of_the_previous_cycle() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT)
    _escalate(world, FIRST_DUE + timedelta(days=4) + BEAT)
    assert len(world.notifications.escalations()) == 2

    with freeze_time(FIRST_DUE + timedelta(days=5)):
        _announce(world, FIRST_DUE + timedelta(days=12), task_key="task-2", reset_read=True)

    assert all(row.read_at is not None and row.acted_at is not None for row in world.notifications.escalations())
    assert _reminder(world).escalation_level == 0
    assert [n.notification_type for n in world.notifications.unread_for(USER, TENANT)] == [WATERING_REMINDER_TYPE]


def test_an_escalation_row_is_no_recipient_for_a_missing_reminder() -> None:
    """#3135 / #2114: a group holding only escalation rows gets no reminder addressed from them.

    The pre-#3135 prune could leave such a group (the reminder deleted, the
    escalation kept). Its recipient may have left the tenant since, so a
    background retiming creates nothing; the escalation is no candidate either,
    so the group stays harmless until a user's own action creates the reminder.
    """
    world = _world()
    with freeze_time(FIRST_DUE + timedelta(days=3)):
        world.notifications.create(
            Notification(
                tenant_key=TENANT,
                user_key="former-member",
                notification_type=WATERING_ESCALATION_TYPE,
                title=PLANT_LABEL,
                body="Overdue: watering due on 2026-11-02: Monstera",
                data={"due_date": FIRST_DUE.isoformat()},
                group_key=CARE_GROUP_KEY,
                escalation_level=1,
                parent_notification_key="gone",
                status=NotificationStatus.DELIVERED,
            )
        )
        world.propagation.sync_care_notification(
            tenant_key=TENANT,
            user_key="",
            plant_key=PLANT_KEY,
            plant_label=PLANT_LABEL,
            reminder_type=ReminderType.WATERING,
            due_date=FIRST_DUE + timedelta(days=10),
            task_key="task-1",
        )
    assert [row.notification_type for row in world.notifications.all_rows()] == [WATERING_ESCALATION_TYPE]
    assert _escalate(world, FIRST_DUE + timedelta(days=20) + BEAT) == {"escalated": 0}

    # A user's own action addresses the reminder to that user.
    with freeze_time(FIRST_DUE + timedelta(days=4)):
        _announce(world, FIRST_DUE + timedelta(days=10))
    assert _reminder(world).user_key == USER


# ── the run's own bookkeeping ───────────────────────────────────────────────


def test_a_row_first_seen_long_overdue_moves_one_level_per_run() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)

    assert _escalate(world, FIRST_DUE + timedelta(days=10) + BEAT) == {"escalated": 1}
    assert _reminder(world).escalation_level == 1
    assert _escalate(world, FIRST_DUE + timedelta(days=11) + BEAT) == {"escalated": 1}
    assert _escalate(world, FIRST_DUE + timedelta(days=12) + BEAT) == {"escalated": 1}
    assert _escalate(world, FIRST_DUE + timedelta(days=13) + BEAT) == {"escalated": 0}
    assert [row.escalation_level for row in world.notifications.escalations()] == [1, 2, 3]


def test_a_deduplicated_send_is_not_counted_and_the_level_stays_claimed() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    world.engine._redis.get.return_value = b"1"  # the dedup key is set: notify sends and writes nothing

    assert _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT) == {"escalated": 0}
    assert world.notifications.escalations() == []
    assert _reminder(world).escalation_level == 1, "at most once per level (decision 2026-11-27): not retried"


def test_a_former_member_is_not_escalated_to() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)

    with freeze_time(FIRST_DUE + timedelta(days=2) + BEAT):
        result = asyncio.run(world.engine.escalate_overdue(TENANT, is_active_member=lambda _user, _tenant: False))

    assert result == {"escalated": 0}
    assert world.notifications.claims == []
    assert world.notifications.escalations() == []
    world.engine._preference_repo.get_by_user.assert_not_called()


# ── one chain per occurrence (SCR-001) ──────────────────────────────────────


def _dispatch_due_care(world: SimpleNamespace, due: datetime) -> None:
    """The 06:05 due-care dispatch for the plant, through the real service (rows ``care:<user>:watering``)."""
    service = NotificationService(
        engine=world.engine, notification_repo=world.notifications, preference_repo=MagicMock()
    )
    entry = {
        "user_key": USER,
        "plant_key": PLANT_KEY,
        "plant_name": PLANT_LABEL,
        "reminder_type": ReminderType.WATERING.value,
        "urgency": "due_today",
        "due_date": due.isoformat(),
    }
    with freeze_time(due + timedelta(hours=6)):
        asyncio.run(service.send_care_notifications(TENANT, [entry]))


def test_an_occurrence_delivered_by_the_dispatch_escalates_in_one_chain() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    _dispatch_due_care(world, FIRST_DUE)
    dispatched = [row for row in world.notifications.all_rows() if row.group_key == f"care:{USER}:watering"]
    assert len(dispatched) == 1, "premise: the dispatch wrote its own care.watering row"

    for offset in (2, 4, 7):
        assert _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT) == {"escalated": 1}

    assert {row.parent_notification_key for row in world.notifications.escalations()} == {_reminder(world).key}
    assert world.notifications.get(dispatched[0].key or "").escalation_level == 0


def test_nothing_escalates_after_the_plant_was_watered() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    _dispatch_due_care(world, FIRST_DUE)
    with freeze_time(FIRST_DUE + timedelta(hours=9)):
        world.care.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT, user_key=USER)

    for offset in (2, 3, 4, 5, 6):
        assert _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT) == {"escalated": 0}, offset
    assert world.notifications.escalations() == []


def test_a_task_the_beat_creates_is_announced_on_the_reminder_row() -> None:
    """The daily producer reuses the row as a new occurrence, like every other creator (#3135)."""
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    for offset in (2, 4, 7):
        _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT)
    assert _reminder(world).escalation_level == 3
    # The user deletes the stale task; its reminder row is closed with it.
    (task,) = world.tasks.open_care_tasks(ReminderType.WATERING)
    world.tasks.store.remove(next(t for t in world.tasks.store if t.key == task.key))
    world.propagation.on_task_deleted(task)
    assert _reminder(world).acted_at is not None, "a deleted occurrence does not keep escalating"

    with freeze_time(FIRST_DUE + timedelta(days=8, hours=6)):
        created = world.care.ensure_and_announce_next_watering_task(
            world.care._repo.get_profile_by_plant_key(PLANT_KEY), phase_watering_interval=None, tenant_key=TENANT
        )
    assert created is not None
    reminder = _reminder(world)
    assert reminder.data["task_key"] == created.key
    assert reminder.data["due_date"] == created.due_date.isoformat()
    assert reminder.escalation_level == 0
    assert reminder.read_at is None and reminder.acted_at is None
    assert all(row.acted_at is not None for row in world.notifications.escalations())


def test_a_retiming_that_announces_another_task_is_a_new_occurrence() -> None:
    """SCR-004: the row says which task it announces; a different one is new whatever the caller's flag."""
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE, task_key="task-1")
    for offset in (2, 4, 7):
        _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT)
    world.notifications.mark_read(_reminder(world).key or "", FIRST_DUE + timedelta(days=7))

    second_due = FIRST_DUE + timedelta(days=12)
    with freeze_time(FIRST_DUE + timedelta(days=9)):
        _announce(world, second_due, task_key="task-2", reset_read=False)  # e.g. an interval edit

    reminder = _reminder(world)
    assert reminder.escalation_level == 0
    assert reminder.read_at is None
    assert all(row.acted_at is not None for row in world.notifications.escalations())
    assert _escalate(world, second_due + timedelta(days=2) + BEAT) == {"escalated": 1}


def test_deleting_a_task_the_row_no_longer_announces_leaves_the_row_open() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE, task_key="task-2")
    stale = Task(
        key="task-1",
        name=f"{PLANT_LABEL} — {ReminderType.WATERING.value}",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=TaskStatus.PENDING,
        due_date=FIRST_DUE,
    )

    world.propagation.on_task_deleted(stale)

    assert _reminder(world).acted_at is None


# ── at most once per level, under concurrency and dedup (SCR-002/-003) ─────


class _Redis:
    """A Redis slice with real TTLs on the frozen clock: what the engine's dedup reads."""

    def __init__(self) -> None:
        self.keys: dict[str, datetime] = {}

    def get(self, key: str) -> bytes | None:
        expires = self.keys.get(key)
        return b"1" if expires is not None and datetime.now(UTC) < expires else None

    def set(self, key: str, _value: str, ex: int) -> None:
        self.keys[key] = datetime.now(UTC) + timedelta(seconds=ex)


def _with_dedup(world: SimpleNamespace) -> None:
    """A stateful Redis and one channel that delivers: only a delivered send sets the dedup key."""
    world.engine._redis = _Redis()
    world.engine._resolve_channels = MagicMock(return_value=["push"])  # type: ignore[method-assign]
    world.engine._send_to_channel = AsyncMock(  # type: ignore[method-assign]
        return_value=ChannelResult(channel_key="push", success=True)
    )


def test_each_level_is_sent_when_the_next_run_comes_within_24_hours() -> None:
    """Level n+1 must not meet level n's live dedup key — or it is claimed and never sent."""
    world = _world()
    _with_dedup(world)
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)

    # Long overdue, one level per run; each run is earlier in the day than the one before.
    runs = (
        FIRST_DUE + timedelta(days=10, hours=18),
        FIRST_DUE + timedelta(days=11, hours=9),
        FIRST_DUE + timedelta(days=12, hours=1),
    )
    results = [_escalate(world, at) for at in runs]

    assert results == [{"escalated": 1}] * 3
    assert [row.escalation_level for row in world.notifications.escalations()] == [1, 2, 3]
    assert world.engine._send_to_channel.await_count == 3, "every level reached the channel"


def test_the_same_level_of_the_next_occurrence_is_not_deduplicated() -> None:
    world = _world()
    _with_dedup(world)
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE, task_key="task-1")
    assert _escalate(world, FIRST_DUE + timedelta(days=2, hours=23)) == {"escalated": 1}
    with freeze_time(FIRST_DUE + timedelta(days=2, hours=23, minutes=30)):
        _announce(world, FIRST_DUE + timedelta(days=1), task_key="task-2", reset_read=True)

    # The next occurrence is two days overdue an hour later: its level 1 is its own event.
    assert _escalate(world, FIRST_DUE + timedelta(days=3, hours=1)) == {"escalated": 1}


def test_a_claim_landing_between_a_refresh_and_its_write_is_not_undone() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)
    key = _reminder(world).key or ""
    real_update = world.notifications.update

    def update_after_a_concurrent_claim(update_key: str, notification: Notification) -> Notification:
        # The overlapping beat claims level 1 after the refresh read the row at level 0.
        world.notifications.claim_escalation_level(
            key, tenant_key=TENANT, escalation_level=1, due_date=FIRST_DUE.isoformat()
        )
        world.notifications.update = real_update  # type: ignore[method-assign]
        return real_update(update_key, notification)

    world.notifications.update = update_after_a_concurrent_claim  # type: ignore[method-assign]
    with freeze_time(FIRST_DUE + timedelta(days=2)):
        _announce(world, FIRST_DUE)  # a retiming to the same date: the refresh still writes the row

    assert _reminder(world).escalation_level == 1
    # Level 1 counts as sent: the next run goes on with level 2, not level 1 again.
    assert _escalate(world, FIRST_DUE + timedelta(days=4) + BEAT) == {"escalated": 1}
    assert [level for _key, level in world.notifications.claims] == [1, 2]


def test_overdue_counts_utc_calendar_days_not_hours_from_the_due_time() -> None:
    """SCR-009: due at 18:00 on day D is two days overdue at the 12:00 beat of day D+2 — not on D+3."""
    world = _world()
    due = FIRST_DUE + timedelta(hours=18)
    with freeze_time(due):
        _announce(world, due)

    assert _escalate(world, FIRST_DUE + timedelta(days=1) + BEAT) == {"escalated": 0}
    assert _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT) == {"escalated": 1}


# ── the claim is for the occurrence that was selected ───────────────────────


def _between_select_and_claim(world: SimpleNamespace, action) -> None:  # noqa: ANN001 - a callback
    """Run *action* after the overdue read returned its rows and before any claim."""
    real_find = world.notifications.find_overdue_watering
    done: list[bool] = []

    def find(overdue_since: datetime, escalation_level: int, *, tenant_key: str) -> list[Notification]:
        rows = real_find(overdue_since, escalation_level, tenant_key=tenant_key)
        if rows and not done:
            done.append(True)
            action()
        return rows

    world.notifications.find_overdue_watering = find  # type: ignore[method-assign]


def test_a_plant_watered_between_select_and_claim_gets_no_overdue() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE)

    def water() -> None:
        world.care.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT, user_key=USER)

    _between_select_and_claim(world, water)

    assert _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT) == {"escalated": 0}
    assert world.notifications.claims == []
    assert world.notifications.escalations() == []


def test_a_new_occurrence_between_select_and_claim_is_not_claimed_for_the_old_one() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE, task_key="task-1")
    next_due = FIRST_DUE + timedelta(days=9)

    _between_select_and_claim(world, lambda: _announce(world, next_due, task_key="task-2", reset_read=True))

    assert _escalate(world, FIRST_DUE + timedelta(days=2) + BEAT) == {"escalated": 0}
    assert world.notifications.claims == []
    assert _reminder(world).escalation_level == 0, "the new occurrence starts at level 0"
    assert _escalate(world, next_due + timedelta(days=2) + BEAT) == {"escalated": 1}


# ── a lost beat announcement is caught up ───────────────────────────────────


def test_the_next_beat_announces_an_open_task_whose_announcement_was_lost() -> None:
    world = _world()
    with freeze_time(FIRST_DUE):
        _announce(world, FIRST_DUE, task_key="task-old")
    for offset in (2, 4, 7):
        _escalate(world, FIRST_DUE + timedelta(days=offset) + BEAT)
    world.tasks.store.clear()  # the old task is gone; the row is still open at level 3
    profile = world.care._repo.get_profile_by_plant_key(PLANT_KEY)

    # Run 1 creates the next task and dies before announcing it.
    with freeze_time(FIRST_DUE + timedelta(days=8, hours=6)):
        created = world.care.ensure_next_watering_task(profile, tenant_key=TENANT)
    assert created is not None and created.key != "task-old"
    assert _reminder(world).data["task_key"] == "task-old"

    # Run 2 finds it open, creates nothing — and catches the row up.
    with freeze_time(FIRST_DUE + timedelta(days=9, hours=6)):
        again = world.care.ensure_and_announce_next_watering_task(
            profile, phase_watering_interval=None, tenant_key=TENANT
        )
    assert again is None
    reminder = _reminder(world)
    assert reminder.data["task_key"] == created.key
    assert reminder.escalation_level == 0
    assert reminder.read_at is None and reminder.acted_at is None

    # Run 3: the row is on the open task already — nothing is written.
    updates_before = list(world.notifications.updates)
    with freeze_time(FIRST_DUE + timedelta(days=10, hours=6)):
        world.care.ensure_and_announce_next_watering_task(profile, phase_watering_interval=None, tenant_key=TENANT)
    assert world.notifications.updates == updates_before
