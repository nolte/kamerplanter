"""Tests for CareReminderService.ensure_next_watering_task."""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import ConfirmAction, ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService


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


def test_creates_task_when_no_pending_exists(
    service: CareReminderService,
    mock_task_repo: MagicMock,
    mock_care_repo: MagicMock,
) -> None:
    profile = _profile()
    mock_task_repo.find_by_field.return_value = []
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
        plant_key="plant-1",
        status=TaskStatus.PENDING,
    )

    result = service.ensure_next_watering_task(profile)

    assert result is not None
    mock_task_repo.create_task.assert_called_once()
    created = mock_task_repo.create_task.call_args[0][0]
    assert created.category == TaskCategory.CARE_REMINDER
    assert created.plant_key == "plant-1"
    assert "watering" in created.name
    assert "Water" in created.instruction
    assert "care:" not in created.instruction


def test_skips_when_pending_task_exists(
    service: CareReminderService,
    mock_task_repo: MagicMock,
) -> None:
    profile = _profile()
    mock_task_repo.find_by_field.return_value = [
        {
            "category": "care_reminder",
            "name": "plant-1 \u2014 watering",
            "status": "pending",
        },
    ]

    result = service.ensure_next_watering_task(profile)

    assert result is None
    mock_task_repo.create_task.assert_not_called()


def test_creates_task_regardless_of_auto_create_flag(
    service: CareReminderService,
    mock_task_repo: MagicMock,
    mock_care_repo: MagicMock,
) -> None:
    """Watering tasks are always created, auto_create_watering_task flag is ignored."""
    profile = _profile(auto_create=False)
    mock_task_repo.find_by_field.return_value = []
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
        plant_key="plant-1",
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
    mock_task_repo.find_by_field.return_value = []
    mock_task_repo.create_task.return_value = Task(
        name="plant-1 — watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        plant_key="plant-1",
        status=TaskStatus.PENDING,
    )

    service.ensure_next_watering_task(profile, last_confirmation=last)

    created = mock_task_repo.create_task.call_args[0][0]
    # 7 days after March 5 = March 12
    assert created.due_date == datetime(2026, 3, 12, tzinfo=UTC)


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
    mock_task_repo.find_by_field.return_value = []
    mock_task_repo.create_task.return_value = Task(
        name="plant-1 — watering",
        instruction="Water plant-1 (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        plant_key="plant-1",
        status=TaskStatus.PENDING,
    )

    service.confirm_reminder("plant-1", ReminderType.WATERING)

    mock_task_repo.create_task.assert_called_once()


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
    mock_plant_repo.get_by_key.return_value = plant_mock

    service = CareReminderService(mock_care_repo, engine, mock_task_repo, plant_repo=mock_plant_repo)

    profile = _profile()
    mock_task_repo.find_by_field.return_value = []
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
        plant_key="plant-1",
        status=TaskStatus.PENDING,
    )

    result = service.ensure_next_watering_task(profile)

    assert result is not None
    created = mock_task_repo.create_task.call_args[0][0]
    assert created.name == "Monstera \u2014 watering"
    assert "Water Monstera" in created.instruction
