"""Wiring tests: care mutations fan out to notification propagation (#742).

Verify that editing a care interval reschedules *and* upserts the plant's care
notification, and that confirming a reminder closes it. The propagation collaborator
is a ``MagicMock``; the propagation behaviour itself lives in
test_notification_propagation_service.py.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService


@pytest.fixture
def care_repo() -> MagicMock:
    repo = MagicMock()
    repo.update_profile.side_effect = lambda _key, profile: profile
    repo.get_last_confirmation.return_value = None
    repo.create_confirmation.side_effect = lambda conf: conf
    return repo


@pytest.fixture
def task_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def plant_repo() -> MagicMock:
    repo = MagicMock()
    plant = MagicMock()
    plant.plant_name = "Monstera"
    plant.instance_id = "MON-1"
    plant.tenant_key = "tenant-A"
    plant.current_phase_key = None
    plant.slot_key = None
    plant.key = "plant-1"
    repo.get_by_key.return_value = plant
    repo.get_or_raise.return_value = plant
    return repo


@pytest.fixture
def propagation() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(care_repo, task_repo, plant_repo, propagation) -> CareReminderService:
    return CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo,
        plant_repo=plant_repo,
        notification_propagation=propagation,
    )


def _profile(**kwargs) -> CareProfile:
    defaults = {
        "key": "cp-1",
        "plant_key": "plant-1",
        "watering_interval_days": 7,
        "winter_watering_multiplier": 1.0,
        "auto_create_watering_task": True,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return CareProfile(**defaults)


def _pending_task() -> Task:
    return Task(
        key="task-1",
        name="Monstera — watering",
        instruction="Water Monstera (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        tenant_key="tenant-A",
        due_date=datetime(2026, 3, 12, tzinfo=UTC),
        status=TaskStatus.PENDING,
    )


def test_interval_change_upserts_care_notification(service, care_repo, task_repo, propagation):
    care_repo.get_profile_by_plant_key.return_value = _profile()
    task_repo.find_open_care_task.return_value = _pending_task()

    service.update_profile("plant-1", {"watering_interval_days": 14}, user_key="user-a")

    propagation.sync_care_notification.assert_called_once()
    _, kwargs = propagation.sync_care_notification.call_args
    assert kwargs["tenant_key"] == "tenant-A"
    assert kwargs["user_key"] == "user-a"
    assert kwargs["plant_key"] == "plant-1"
    assert kwargs["reminder_type"] == ReminderType.WATERING


def test_no_interval_change_does_not_propagate(service, care_repo, task_repo, propagation):
    care_repo.get_profile_by_plant_key.return_value = _profile()
    task_repo.find_open_care_task.return_value = _pending_task()

    # Editing an unrelated field is not an interval change → no reschedule.
    service.update_profile("plant-1", {"notes": "hi"}, user_key="user-a")

    propagation.sync_care_notification.assert_not_called()


def test_confirm_reminder_closes_care_notification(service, care_repo, task_repo, propagation):
    care_repo.get_profile_by_plant_key.return_value = _profile(auto_create_watering_task=False)
    task_repo.find_open_care_task.return_value = None

    service.confirm_reminder("plant-1", ReminderType.WATERING, tenant_key="tenant-A", user_key="user-a")

    propagation.on_care_confirmed.assert_called_once_with(
        tenant_key="tenant-A",
        plant_key="plant-1",
        reminder_type=ReminderType.WATERING,
    )


def test_service_without_propagation_is_safe(care_repo, task_repo, plant_repo):
    service = CareReminderService(care_repo, CareReminderEngine(), task_repo, plant_repo=plant_repo)
    care_repo.get_profile_by_plant_key.return_value = _profile()
    task_repo.find_open_care_task.return_value = _pending_task()
    # Must not crash without the coupling wired.
    service.update_profile("plant-1", {"watering_interval_days": 14})
