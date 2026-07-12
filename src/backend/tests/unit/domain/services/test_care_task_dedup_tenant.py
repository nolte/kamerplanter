"""Cross-tenant isolation for the single care-task dedup helper (#509).

The care-reminder idempotency check used to scan ``find_by_field("entity_key",
…)`` which is tenant-blind, while the created task is stamped with the plant's
tenant. These tests prove the two dedup surfaces are now strictly tenant-scoped:

* the **creation path** (``CareReminderService._ensure_care_task`` → the single
  ``find_open_care_task`` helper) never lets a task in tenant B suppress the
  creation of the equivalent task in tenant A — and still dedups within a tenant;
* the **read-time safety net** (``TaskService._deduplicate_care_tasks``) never
  collapses two tenants' identically named care tasks into one.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService, build_care_reminder_task
from app.domain.services.task_service import TaskService


class _FakeTaskRepo:
    """In-memory task repo with a faithful tenant-scoped ``find_open_care_task``.

    Mirrors the ArangoDB helper's dedup key — ``(tenant_key, entity_key,
    reminder-type name suffix)`` restricted to still-open tasks — so a behavioural
    test can prove tenant isolation end-to-end without a live database.
    """

    def __init__(self) -> None:
        self.store: list[Task] = []

    def find_open_care_task(
        self,
        entity_key: str,
        reminder_type: ReminderType,
        tenant_key: str,
        *,
        include_completed_today: bool = True,
    ) -> Task | None:
        suffix = f"— {reminder_type.value}"
        matches = [
            task
            for task in self.store
            if task.tenant_key == tenant_key
            and (task.entity_key or "") == entity_key
            and task.category == TaskCategory.CARE_REMINDER.value
            and (task.name or "").endswith(suffix)
            and task.status in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)
        ]
        return matches[-1] if matches else None

    def create_task(self, task: Task) -> Task:
        self.store.append(task)
        return task


def _plant(entity_key: str, tenant_key: str):  # noqa: ANN202 — PlantInstance stand-in
    return SimpleNamespace(
        key=entity_key,
        plant_name="Basil",
        instance_id="i1",
        tenant_key=tenant_key,
    )


def _seed_care_task(repo: _FakeTaskRepo, *, tenant_key: str, reminder_type: ReminderType) -> None:
    repo.store.append(
        build_care_reminder_task(
            plant_key="plant-shared",
            plant_label="Basil",
            tenant_key=tenant_key,
            reminder_type=reminder_type,
            due_date=datetime(2026, 6, 14, tzinfo=UTC),
        )
    )


def test_ensure_care_task_never_dedups_across_tenants() -> None:
    """A tenant-B care task must not suppress the equivalent tenant-A creation."""
    repo = _FakeTaskRepo()
    _seed_care_task(repo, tenant_key="tenant-B", reminder_type=ReminderType.PEST_CHECK)
    service = CareReminderService(MagicMock(), CareReminderEngine(), task_repo=repo)

    created = service._ensure_care_task(_plant("plant-shared", "tenant-A"), ReminderType.PEST_CHECK)

    assert created is not None
    assert created.tenant_key == "tenant-A"
    # tenant-B's task is untouched; each tenant now owns exactly one task.
    assert sum(t.tenant_key == "tenant-B" for t in repo.store) == 1
    assert sum(t.tenant_key == "tenant-A" for t in repo.store) == 1


def test_ensure_care_task_dedups_within_the_same_tenant() -> None:
    """Within one tenant the helper still keeps a single open task (no drift)."""
    repo = _FakeTaskRepo()
    service = CareReminderService(MagicMock(), CareReminderEngine(), task_repo=repo)

    first = service._ensure_care_task(_plant("plant-shared", "tenant-A"), ReminderType.PEST_CHECK)
    second = service._ensure_care_task(_plant("plant-shared", "tenant-A"), ReminderType.PEST_CHECK)

    assert first is not None
    assert second is None
    assert len(repo.store) == 1


def _care_task(*, name: str, tenant_key: str, due_date: datetime) -> Task:
    return Task(
        name=name,
        instruction="care",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-shared",
        entity_type="plant_instance",
        tenant_key=tenant_key,
        due_date=due_date,
        status=TaskStatus.PENDING,
    )


def test_deduplicate_care_tasks_is_tenant_scoped() -> None:
    """Two tenants' identically named care tasks are never collapsed (#509)."""
    task_a = _care_task(name="Basil — watering", tenant_key="tenant-A", due_date=datetime(2026, 6, 14, tzinfo=UTC))
    task_b = _care_task(name="Basil — watering", tenant_key="tenant-B", due_date=datetime(2026, 6, 14, tzinfo=UTC))

    result = TaskService._deduplicate_care_tasks([task_a, task_b])

    assert len(result) == 2
    assert {t.tenant_key for t in result} == {"tenant-A", "tenant-B"}


def test_deduplicate_care_tasks_collapses_same_tenant_duplicates() -> None:
    """Same tenant + same name still collapses to the newest task (behaviour kept)."""
    older = _care_task(name="Basil — watering", tenant_key="tenant-A", due_date=datetime(2026, 6, 10, tzinfo=UTC))
    newer = _care_task(name="Basil — watering", tenant_key="tenant-A", due_date=datetime(2026, 6, 14, tzinfo=UTC))

    result = TaskService._deduplicate_care_tasks([older, newer])

    assert len(result) == 1
    assert result[0].due_date == datetime(2026, 6, 14, tzinfo=UTC)
