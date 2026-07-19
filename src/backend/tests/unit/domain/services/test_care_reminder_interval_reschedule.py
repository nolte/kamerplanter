"""Regression tests for #622 — editing a care interval reschedules the pending task.

When a user edits ``watering_interval_days`` (or fertilizing/pest/humidity/
repotting) on the Pflege tab, ``CareReminderService.update_profile`` must
re-terminate the corresponding **pending** care task: recompute its ``due_date``
from the new interval and refresh its "every N days" instruction. Only pending
tasks are touched; completed/skipped history is never revived, no duplicates are
created, and ``auto_create_watering_task=false`` is respected.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import ConfirmAction, ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService


@pytest.fixture
def mock_care_repo() -> MagicMock:
    repo = MagicMock()
    # The service reschedules against the persisted (post-edit) profile: echo the
    # constructed CareProfile back so `saved` carries the new interval + reset.
    repo.update_profile.side_effect = lambda _key, profile: profile
    return repo


@pytest.fixture
def mock_task_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_plant_repo() -> MagicMock:
    repo = MagicMock()
    plant = MagicMock()
    plant.plant_name = "Dahlie"
    plant.instance_id = "DAHLI-0710-3LN"
    plant.tenant_key = "tenant-A"
    plant.current_phase_key = None  # no phase override → profile interval wins
    plant.slot_key = None
    repo.get_by_key.return_value = plant
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


def _profile(
    *,
    watering_interval_days: int = 7,
    fertilizing_interval_days: int = 14,
    pest_check_interval_days: int = 14,
    auto_create_watering_task: bool = True,
    watering_interval_learned: int | None = None,
    fertilizing_interval_learned: int | None = None,
    plant_key: str = "plant-1",
) -> CareProfile:
    return CareProfile(
        key="cp-1",
        watering_interval_days=watering_interval_days,
        # Neutral multiplier keeps the due-date deterministic regardless of the
        # season the test runs in (the watering interval is season-adjusted).
        winter_watering_multiplier=1.0,
        fertilizing_interval_days=fertilizing_interval_days,
        pest_check_interval_days=pest_check_interval_days,
        auto_create_watering_task=auto_create_watering_task,
        watering_interval_learned=watering_interval_learned,
        fertilizing_interval_learned=fertilizing_interval_learned,
        plant_key=plant_key,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _pending_task(
    reminder_value: str = "watering",
    *,
    status: TaskStatus = TaskStatus.PENDING,
    instruction: str = "Water Dahlie (every 7 days).",
) -> Task:
    return Task(
        key="task-1",
        name=f"Dahlie — {reminder_value}",
        instruction=instruction,
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        tenant_key="tenant-A",
        due_date=datetime(2026, 3, 12, tzinfo=UTC),
        status=status,
    )


def _confirmation(reminder_type: ReminderType) -> CareConfirmation:
    return CareConfirmation(
        plant_key="plant-1",
        care_profile_key="cp-1",
        reminder_type=reminder_type,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 3, 5, tzinfo=UTC),
    )


def test_watering_interval_change_reschedules_pending_task(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """Shortening the watering interval moves the pending task's due date + text."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(watering_interval_days=7)
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.WATERING)
    mock_task_repo.find_open_care_task.return_value = _pending_task()

    service.update_profile("plant-1", {"watering_interval_days": 3})

    # Only pending tasks are considered — completed/skipped are excluded.
    _args, kwargs = mock_task_repo.find_open_care_task.call_args
    assert kwargs["include_completed_today"] is False

    mock_task_repo.update_task.assert_called_once()
    updated_task = mock_task_repo.update_task.call_args[0][1]
    # 3 days after the last confirmation (March 5) = March 8.
    assert updated_task.due_date == datetime(2026, 3, 8, tzinfo=UTC)
    assert "every 3 days" in updated_task.instruction
    # No duplicate is materialised while a pending task already exists.
    mock_task_repo.create_task.assert_not_called()


def test_lengthening_watering_interval_pushes_due_date_out(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(watering_interval_days=7)
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.WATERING)
    mock_task_repo.find_open_care_task.return_value = _pending_task()

    service.update_profile("plant-1", {"watering_interval_days": 14})

    updated_task = mock_task_repo.update_task.call_args[0][1]
    # 14 days after March 5 = March 19.
    assert updated_task.due_date == datetime(2026, 3, 19, tzinfo=UTC)
    assert "every 14 days" in updated_task.instruction


def test_unchanged_interval_is_noop(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """Writing the same interval value must not touch any task."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(watering_interval_days=7)

    service.update_profile("plant-1", {"watering_interval_days": 7})

    mock_task_repo.find_open_care_task.assert_not_called()
    mock_task_repo.update_task.assert_not_called()
    mock_task_repo.create_task.assert_not_called()
    # The profile itself is still persisted.
    mock_care_repo.update_profile.assert_called_once()


def test_no_pending_task_creates_when_watering_autocreate_on(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """No pending watering task + auto-create on → the next occurrence is created."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(auto_create_watering_task=True)
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.WATERING)
    mock_task_repo.find_open_care_task.return_value = None
    mock_task_repo.create_task.side_effect = lambda task: task

    service.update_profile("plant-1", {"watering_interval_days": 3})

    mock_task_repo.update_task.assert_not_called()
    mock_task_repo.create_task.assert_called_once()


def test_no_pending_task_respects_watering_autocreate_off(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """No pending watering task + auto-create off → nothing is created."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(auto_create_watering_task=False)
    mock_task_repo.find_open_care_task.return_value = None

    service.update_profile("plant-1", {"watering_interval_days": 3})

    mock_task_repo.update_task.assert_not_called()
    mock_task_repo.create_task.assert_not_called()


def test_in_progress_task_is_not_rescheduled(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """An in-progress task is being worked on — leave it untouched, create no dup."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile()
    mock_task_repo.find_open_care_task.return_value = _pending_task(status=TaskStatus.IN_PROGRESS)

    service.update_profile("plant-1", {"watering_interval_days": 3})

    mock_task_repo.update_task.assert_not_called()
    mock_task_repo.create_task.assert_not_called()


def test_completed_history_is_not_revived_for_non_watering(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """No open pest-check task (completed excluded) → nothing is touched or created."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(pest_check_interval_days=14)
    mock_task_repo.find_open_care_task.return_value = None

    service.update_profile("plant-1", {"pest_check_interval_days": 7})

    mock_task_repo.update_task.assert_not_called()
    mock_task_repo.create_task.assert_not_called()


def test_explicit_edit_resets_learned_interval_and_drives_schedule(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """An explicit interval edit resets the adaptive-learned value and wins."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(
        watering_interval_days=7,
        watering_interval_learned=10,
    )
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.WATERING)
    mock_task_repo.find_open_care_task.return_value = _pending_task()

    service.update_profile("plant-1", {"watering_interval_days": 3})

    # The persisted profile drops the stale learned value.
    saved_profile = mock_care_repo.update_profile.call_args[0][1]
    assert saved_profile.watering_interval_learned is None
    assert saved_profile.watering_interval_days == 3

    # The reschedule uses the edited base (3), not the old learned value (10).
    updated_task = mock_task_repo.update_task.call_args[0][1]
    assert updated_task.due_date == datetime(2026, 3, 8, tzinfo=UTC)
    assert "every 3 days" in updated_task.instruction


def test_caller_supplied_learned_value_is_preserved(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """When the same request sets the learned value, the edit must not clobber it."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(watering_interval_days=7)
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.WATERING)
    mock_task_repo.find_open_care_task.return_value = _pending_task()

    service.update_profile(
        "plant-1",
        {"watering_interval_days": 3, "watering_interval_learned": 4},
    )

    saved_profile = mock_care_repo.update_profile.call_args[0][1]
    assert saved_profile.watering_interval_learned == 4


def test_fertilizing_interval_change_reschedules_pending_task(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """The same reschedule wiring covers fertilizing (engine-owned cadence)."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(fertilizing_interval_days=14)
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.FERTILIZING)
    mock_task_repo.find_open_care_task.return_value = _pending_task(
        "fertilizing",
        instruction="Fertilize Dahlie according to care profile.",
    )

    service.update_profile("plant-1", {"fertilizing_interval_days": 10})

    args, _kwargs = mock_task_repo.find_open_care_task.call_args
    assert args[1] == ReminderType.FERTILIZING
    mock_task_repo.update_task.assert_called_once()
    updated_task = mock_task_repo.update_task.call_args[0][1]
    # 10 days after March 5 = March 15.
    assert updated_task.due_date == datetime(2026, 3, 15, tzinfo=UTC)
    mock_task_repo.create_task.assert_not_called()


def test_pest_check_interval_change_reschedules_pending_task(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    mock_care_repo.get_profile_by_plant_key.return_value = _profile(pest_check_interval_days=14)
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.PEST_CHECK)
    mock_task_repo.find_open_care_task.return_value = _pending_task(
        "pest_check",
        instruction="Inspect Dahlie for pests and diseases.",
    )

    service.update_profile("plant-1", {"pest_check_interval_days": 7})

    args, _kwargs = mock_task_repo.find_open_care_task.call_args
    assert args[1] == ReminderType.PEST_CHECK
    updated_task = mock_task_repo.update_task.call_args[0][1]
    # 7 days after March 5 = March 12.
    assert updated_task.due_date == datetime(2026, 3, 12, tzinfo=UTC)


def test_reschedule_lookup_is_tenant_scoped(
    service: CareReminderService,
    mock_care_repo: MagicMock,
    mock_task_repo: MagicMock,
) -> None:
    """The pending-task lookup carries the plant's own tenant_key (#509 dedup)."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile()
    mock_care_repo.get_last_confirmation.return_value = _confirmation(ReminderType.WATERING)
    mock_task_repo.find_open_care_task.return_value = _pending_task()

    service.update_profile("plant-1", {"watering_interval_days": 3})

    args, _kwargs = mock_task_repo.find_open_care_task.call_args
    assert args[0] == "plant-1"
    assert args[2] == "tenant-A"


def test_no_task_repo_is_safe(
    mock_care_repo: MagicMock,
    engine: CareReminderEngine,
    mock_plant_repo: MagicMock,
) -> None:
    """Without a task repository the interval edit persists but reschedules nothing."""
    mock_care_repo.get_profile_by_plant_key.return_value = _profile()
    service = CareReminderService(mock_care_repo, engine, task_repo=None, plant_repo=mock_plant_repo)

    result = service.update_profile("plant-1", {"watering_interval_days": 3})

    assert result.watering_interval_days == 3
