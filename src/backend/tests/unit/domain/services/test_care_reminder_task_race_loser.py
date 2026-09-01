"""The loser of the care-task creation race is resolved, not surfaced (#1301).

The unique index on ``tasks`` rejects the second of two overlapping care-task
inserts. That is only half a fix: if the rejection reached the caller, a
``POST /t/{slug}/tasks/generate-care-reminders`` that happened to overlap with the
06:00 beat would answer 409 instead of succeeding, and the Celery producer would
abort the rest of a tenant's run. :func:`create_care_reminder_task` turns it back
into the answer the loser was asking for — "an equivalent task already exists" —
which is ``None``.

Solitary tests: the *behaviour under a rejected insert* is what is under test, so
a repository double raising :class:`DuplicateError` is the right instrument. That
the database actually raises it, and that it does so exactly for two concurrent
producers, is asserted against a real ArangoDB in
``tests/integration/test_care_task_dedup_concurrency.py`` — neither half certifies
anything on its own.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType
from app.common.exceptions import DuplicateError, ValidationError
from app.domain.services.care_reminder_service import build_care_reminder_task, create_care_reminder_task


def _task():
    return build_care_reminder_task(
        plant_key="plant-1",
        plant_label="Basil",
        tenant_key="tenant-a",
        reminder_type=ReminderType.WATERING,
        due_date=datetime(2026, 6, 14, tzinfo=UTC),
    )


def test_uncontended_create_returns_the_created_task():
    repo = MagicMock()
    created = SimpleNamespace(key="task-1")
    repo.create_task.return_value = created

    assert create_care_reminder_task(repo, _task()) is created
    repo.create_task.assert_called_once()


def test_rejected_insert_resolves_to_none_instead_of_raising():
    """The 409-shaped rejection becomes the same outcome as "the lookup found one"."""
    repo = MagicMock()
    repo.create_task.side_effect = DuplicateError("tasks", "care_dedup_key", "")

    assert create_care_reminder_task(repo, _task()) is None


def test_unrelated_repository_errors_still_propagate():
    """Only the duplicate answer is absorbed — a real failure must not read as "exists"."""
    repo = MagicMock()
    repo.create_task.side_effect = ValidationError("nope")

    with pytest.raises(ValidationError):
        create_care_reminder_task(repo, _task())


def test_service_watering_path_returns_none_when_it_loses_the_race():
    """``ensure_next_watering_task`` keeps its ``Task | None`` contract under a rejection.

    Its callers (the dashboard confirmation, the watering log, the task queue) all
    read ``None`` as "nothing to schedule". A raised ``DuplicateError`` here would
    instead abort the whole watering-log write that had already been committed.
    """
    from app.domain.engines.care_reminder_engine import CareReminderEngine
    from app.domain.models.care_reminder import CareProfile
    from app.domain.services.care_reminder_service import CareReminderService

    care_repo = MagicMock()
    care_repo.get_last_confirmation.return_value = None

    task_repo = MagicMock()
    task_repo.find_open_care_task.return_value = None  # the racing read: "none open"
    task_repo.create_task.side_effect = DuplicateError("tasks", "care_dedup_key", "")

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = SimpleNamespace(
        plant_name="Basil",
        instance_id="P-1",
        tenant_key="tenant-a",
    )

    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo=task_repo,
        plant_repo=plant_repo,
    )
    profile = CareProfile(plant_key="plant-1", watering_interval_days=3)

    assert service.ensure_next_watering_task(profile) is None
    task_repo.create_task.assert_called_once()
