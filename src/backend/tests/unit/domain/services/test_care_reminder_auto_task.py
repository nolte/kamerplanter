"""Tests for CareReminderService.ensure_next_watering_task."""

from datetime import UTC, datetime, time, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.datetimes import today_utc
from app.common.enums import ConfirmAction, ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo


def _today_utc() -> datetime:
    """Midnight UTC of the current day (care tasks are day-granular)."""
    now = datetime.now(UTC)
    return datetime(now.year, now.month, now.day, tzinfo=UTC)


@pytest.fixture
def mock_care_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_task_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_plant_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_by_key.return_value = None
    return repo


@pytest.fixture
def engine() -> CareReminderEngine:
    return CareReminderEngine()


@pytest.fixture
def service(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_task_repo: MagicMock,
    mock_plant_repo: MagicMock,
) -> CareReminderService:
    return CareReminderService(mock_care_repo, engine, mock_task_repo, plant_repo=mock_plant_repo)


def _profile(auto_create: bool = True, plant_key: str = "plant-1") -> CareProfile:
    return CareProfile(
        watering_interval_days=7,
        winter_watering_multiplier=1.5,
        plant_key=plant_key,
        auto_create_watering_task=auto_create,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _watering_task(
    status: TaskStatus,
    completed_at: datetime | None = None,
    name: str = "plant-1 — watering",
) -> Task:
    """Build a persisted-style watering care-reminder Task as the repository returns it.

    The repository wraps ArangoDB documents into Pydantic ``Task`` models, so the
    dedup logic must operate on attribute access, not ``dict.get`` (regression #456).
    """
    return Task(
        name=name,
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status=status,
        completed_at=completed_at,
    )


def test_creates_task_when_no_pending_exists(
    service: CareReminderService,
    mock_task_repo: MagicMock,
    mock_care_repo: MagicMock,
) -> None:
    profile = _profile()
    mock_task_repo.find_open_care_task.return_value = None
    mock_care_repo.get_last_confirmation.return_value = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    mock_task_repo.create_task.return_value = Task(
        name="plant-1 \u2014 watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status=TaskStatus.PENDING,
    )

    result = service.ensure_next_watering_task(profile)

    assert result is not None
    mock_task_repo.create_task.assert_called_once()
    created = mock_task_repo.create_task.call_args[0][0]
    assert created.category == TaskCategory.CARE_REMINDER
    assert created.entity_key == "plant-1"
    assert created.entity_type == "plant_instance"
    assert "watering" in created.name
    assert "Water" in created.instruction
    assert "care:" not in created.instruction


def test_skips_when_pending_task_exists(
    service: CareReminderService,
    mock_task_repo: MagicMock,
) -> None:
    """When the tenant-aware dedup helper reports an open task, no new one is created.

    The dedup decision now lives in ``ITaskRepository.find_open_care_task`` (#509);
    the service only reacts to its ``Task | None`` result.
    """
    profile = _profile()
    mock_task_repo.find_open_care_task.return_value = _watering_task(TaskStatus.PENDING)

    result = service.ensure_next_watering_task(profile)

    assert result is None
    mock_task_repo.create_task.assert_not_called()


def test_skips_when_task_completed_today_exists(
    service: CareReminderService,
    mock_task_repo: MagicMock,
) -> None:
    """A watering task completed today counts as recent and blocks re-materialization.

    The recency rule ("completed today counts as satisfied") now lives in the
    tenant-aware helper; here the helper reports the recent task, so the service skips.
    """
    profile = _profile()
    # The UTC day, like the module's own ``_today_utc()`` helper and the
    # day-granular dedup in ``task_repository``. Combining the *local* date with
    # a UTC offset produced a "completed today" fixture that is yesterday in UTC
    # for part of every day on a non-UTC host (§12a, #858).
    completed_today = datetime.combine(today_utc(), time(12, 0), tzinfo=UTC)
    mock_task_repo.find_open_care_task.return_value = _watering_task(TaskStatus.COMPLETED, completed_at=completed_today)

    result = service.ensure_next_watering_task(profile)

    assert result is None
    mock_task_repo.create_task.assert_not_called()


def test_creates_task_when_prior_task_completed_yesterday(
    service: CareReminderService,
    mock_task_repo: MagicMock,
    mock_care_repo: MagicMock,
) -> None:
    """A watering task completed before today no longer blocks the next materialization.

    The tenant-aware helper only reports today-or-open tasks, so a task completed
    yesterday yields ``None`` and the service creates the next occurrence.
    """
    profile = _profile()
    mock_task_repo.find_open_care_task.return_value = None
    mock_care_repo.get_last_confirmation.return_value = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    mock_task_repo.create_task.return_value = _watering_task(TaskStatus.PENDING)

    result = service.ensure_next_watering_task(profile)

    assert result is not None
    mock_task_repo.create_task.assert_called_once()


def test_scopes_dedup_lookup_by_plant_tenant(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_task_repo: MagicMock,
) -> None:
    """The dedup lookup is issued with the plant's own tenant_key (#509).

    Proves the service never asks the repository for a tenant-blind scan: the
    ``find_open_care_task`` call carries the resolved ``tenant_key`` so a task in
    another tenant can never be matched.
    """
    plant_repo = MagicMock()
    plant = MagicMock()
    plant.plant_name = "Monstera"
    plant.instance_id = "PI-1"
    plant.tenant_key = "tenant-A"
    plant_repo.get_by_key.return_value = plant
    service = CareReminderService(mock_care_repo, engine, mock_task_repo, plant_repo=plant_repo)

    profile = _profile()
    mock_task_repo.find_open_care_task.return_value = None
    mock_care_repo.get_last_confirmation.return_value = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    mock_task_repo.create_task.return_value = _watering_task(TaskStatus.PENDING)

    service.ensure_next_watering_task(profile)

    args, kwargs = mock_task_repo.find_open_care_task.call_args
    assert args[0] == "plant-1"
    assert args[1] == ReminderType.WATERING
    assert args[2] == "tenant-A"


def test_creates_task_regardless_of_auto_create_flag(
    service: CareReminderService,
    mock_task_repo: MagicMock,
    mock_care_repo: MagicMock,
) -> None:
    """Watering tasks are always created, auto_create_watering_task flag is ignored."""
    profile = _profile(auto_create=False)
    mock_task_repo.find_open_care_task.return_value = None
    mock_care_repo.get_last_confirmation.return_value = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    mock_task_repo.create_task.return_value = Task(
        name="plant-1 — watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status=TaskStatus.PENDING,
    )

    result = service.ensure_next_watering_task(profile)

    assert result is not None
    mock_task_repo.create_task.assert_called_once()


def test_skips_when_no_task_repo(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
) -> None:
    service = CareReminderService(mock_care_repo, engine, task_repo=None)
    profile = _profile()

    result = service.ensure_next_watering_task(profile)

    assert result is None


def test_due_date_calculated_from_last_confirmation(
    service: CareReminderService,
    mock_task_repo: MagicMock,
    mock_care_repo: MagicMock,
) -> None:
    profile = _profile()
    last = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 5, tzinfo=UTC),
    )
    mock_task_repo.find_open_care_task.return_value = None
    mock_task_repo.create_task.return_value = Task(
        name="plant-1 — watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status=TaskStatus.PENDING,
    )

    service.ensure_next_watering_task(profile, last_confirmation=last)

    created = mock_task_repo.create_task.call_args[0][0]
    # 7 days after March 5 = March 12
    assert created.due_date == datetime(2026, 3, 12, tzinfo=UTC)


def test_fixed_interval_next_due_routes_through_recurrence_engine(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_task_repo: MagicMock,
    mock_plant_repo: MagicMock,
) -> None:
    """#510: the fixed-interval watering cadence is advanced by the shared
    RecurrenceEngine, not by hand-rolled date arithmetic.

    The care engine remains the interval authority (it computes ``7``); the next
    due date is produced by ``RecurrenceEngine.next_occurrence`` with a
    ``FREQ=DAILY;INTERVAL=7`` rule — proving the care path and the generic
    recurring-task path share one recurrence implementation. The resulting cadence
    (March 5 + 7 days = March 12) is identical to the previous behaviour.
    """
    from app.domain.engines.recurrence_engine import RecurrenceEngine

    recurrence = RecurrenceEngine()
    spy = MagicMock(wraps=recurrence.next_occurrence)
    recurrence.next_occurrence = spy  # type: ignore[method-assign]
    service = CareReminderService(
        mock_care_repo,
        engine,
        mock_task_repo,
        plant_repo=mock_plant_repo,
        recurrence=recurrence,
    )

    profile = _profile()
    last = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 5, tzinfo=UTC),
    )
    mock_task_repo.find_open_care_task.return_value = None
    mock_task_repo.create_task.side_effect = lambda task: task

    result = service.ensure_next_watering_task(profile, last_confirmation=last)

    # The shared recurrence engine was consulted with a fixed-interval RRULE...
    spy.assert_called_once()
    rule_arg, base_arg = spy.call_args[0]
    assert rule_arg == "FREQ=DAILY;INTERVAL=7"
    assert base_arg == datetime(2026, 3, 5, tzinfo=UTC)
    # ...and the produced cadence is unchanged (7 days after March 5).
    assert result is not None
    assert result.due_date == datetime(2026, 3, 12, tzinfo=UTC)


def test_snoozed_last_confirmation_keeps_engine_interval_authority(
    service: CareReminderService,
    mock_task_repo: MagicMock,
) -> None:
    """A snoozed last confirmation cannot be a static RRULE, so it stays on the
    care engine (documented #510 boundary): due = snooze base + snooze days."""
    profile = _profile()
    snoozed = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.SNOOZED,
        snooze_days=3,
        confirmed_at=datetime(2026, 3, 5, tzinfo=UTC),
    )
    mock_task_repo.find_open_care_task.return_value = None
    mock_task_repo.create_task.side_effect = lambda task: task

    result = service.ensure_next_watering_task(profile, last_confirmation=snoozed)

    assert result is not None
    # 3-day snooze after March 5 = March 8 (interval is ignored while snoozed).
    assert result.due_date == datetime(2026, 3, 8, tzinfo=UTC)


def test_confirm_triggers_next_task_creation(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    profile = _profile()
    mock_care_repo.get_profile_by_plant_key.return_value = profile
    mock_care_repo.create_confirmation.return_value = CareConfirmation(
        key="conf-1",
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 9, tzinfo=UTC),
    )
    mock_care_repo.get_confirmations_by_plant.return_value = []
    mock_task_repo.find_open_care_task.return_value = None
    mock_task_repo.create_task.return_value = Task(
        name="plant-1 — watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status=TaskStatus.PENDING,
    )

    service.confirm_reminder("plant-1", ReminderType.WATERING)

    mock_task_repo.create_task.assert_called_once()


def test_confirm_with_open_task_completes_it_and_schedules_follow_up(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
) -> None:
    """#768 — confirming with an open task must yield completion *and* a follow-up.

    The dashboard/API/MCP confirmation path shares the complete-then-schedule
    composition with the Gießprotokoll path. Against real repository state the
    follow-up lookup would otherwise return the very task the confirmation just
    completed, ending the reminder chain. Driven through the stateful
    :class:`FakeTaskRepo`, which a stateless mock cannot expose.
    """
    plant_repo = MagicMock()
    plant = MagicMock()
    plant.key = "plant-1"
    plant.plant_name = "Monstera"
    plant.instance_id = "PI-001"
    plant.tenant_key = "tenant-1"
    plant.current_phase_key = None
    plant.slot_key = None
    plant_repo.get_by_key.return_value = plant

    open_task = Task(
        key="task-open",
        name="Monstera — watering",
        instruction="Water Monstera (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        tenant_key="tenant-1",
        status=TaskStatus.PENDING,
        due_date=_today_utc(),
    )
    task_repo = FakeTaskRepo([open_task])

    profile = _profile()
    mock_care_repo.get_profile_by_plant_key.return_value = profile
    mock_care_repo.create_confirmation.side_effect = lambda c: CareConfirmation(**{**c.model_dump(), "_key": "conf-1"})
    mock_care_repo.get_last_confirmation.return_value = None
    mock_care_repo.get_confirmations_by_plant.return_value = []

    service = CareReminderService(mock_care_repo, engine, task_repo, plant_repo=plant_repo)

    service.confirm_reminder("plant-1", ReminderType.WATERING)

    completed = task_repo.completed_care_tasks(ReminderType.WATERING)
    pending = task_repo.open_care_tasks(ReminderType.WATERING)
    assert [t.key for t in completed] == ["task-open"]
    assert len(pending) == 1, "the confirmation must schedule exactly one follow-up"
    assert pending[0].due_date == _today_utc() + timedelta(days=7)
    assert pending[0].tenant_key == "tenant-1"


def test_confirm_non_watering_does_not_trigger_task(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    profile = _profile()
    mock_care_repo.get_profile_by_plant_key.return_value = profile
    mock_care_repo.create_confirmation.return_value = CareConfirmation(
        key="conf-1",
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.FERTILIZING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 9, tzinfo=UTC),
    )
    mock_care_repo.get_confirmations_by_plant.return_value = []
    mock_task_repo.find_open_care_task.return_value = None

    service.confirm_reminder("plant-1", ReminderType.FERTILIZING)

    mock_task_repo.create_task.assert_not_called()


def test_resolves_plant_name_for_task_display(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_task_repo: MagicMock,
) -> None:
    """When plant_repo is available, task name should use the plant's name."""
    mock_plant_repo = MagicMock()
    plant_mock = MagicMock()
    plant_mock.plant_name = "Monstera"
    plant_mock.instance_id = "PI-001"
    plant_mock.tenant_key = "tenant-1"
    mock_plant_repo.get_by_key.return_value = plant_mock

    service = CareReminderService(mock_care_repo, engine, mock_task_repo, plant_repo=mock_plant_repo)

    profile = _profile()
    mock_task_repo.find_open_care_task.return_value = None
    mock_care_repo.get_last_confirmation.return_value = CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    mock_task_repo.create_task.return_value = Task(
        name="Monstera — watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status=TaskStatus.PENDING,
    )

    result = service.ensure_next_watering_task(profile)

    assert result is not None
    created = mock_task_repo.create_task.call_args[0][0]
    assert created.name == "Monstera \u2014 watering"
    assert "Water Monstera" in created.instruction
