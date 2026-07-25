"""Faithful in-memory model of the single care-task dedup helper (#509).

Shared by the care-reminder service tests that need the *real* semantics of
:meth:`ArangoTaskRepository.find_open_care_task` instead of a hand-wired mock.
Hand-wiring that lookup per call is how #761 stayed invisible: a mock answered
``None`` for the ``include_completed_today=True`` lookup while answering the
``False`` lookup with an open task — an impossible pair, because the two form a
**superset relation** in the real AQL (whatever the ``False`` lookup matches, the
``True`` lookup matches as well).

The predicate mirrored here — pinned by
``tests/unit/data_access/arango/test_find_open_care_task_repo.py`` — is:

* scoped to ``(tenant_key, entity_key, care_reminder category, "— {type}" name
  suffix)``;
* a task satisfies the reminder while it is ``PENDING``/``IN_PROGRESS``, or —
  only when ``include_completed_today`` — once it is ``COMPLETED`` with a
  ``completed_at`` of today or later (the recency rule);
* newest first (``due_date`` then insertion order), ``LIMIT 1``.

The recency rule is evaluated against the **UTC** clock, the same clock the
service stamps ``completed_at`` with, so tests are independent of the runner's
local timezone (in deployment the container clock is UTC, where the query's
``date.today()`` and UTC coincide).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.models.task import Task

_OLDEST = datetime.min.replace(tzinfo=UTC)


class FakeCareTaskRepo:
    """In-memory task repository whose care-dedup lookup mirrors the real AQL."""

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self.store: list[Task] = list(tasks or [])
        #: Every dedup lookup, for asserting the flag each caller passes.
        self.lookups: list[dict[str, Any]] = []
        self._created = 0

    # ── the dedup predicate ──

    def find_open_care_task(
        self,
        entity_key: str,
        reminder_type: ReminderType,
        tenant_key: str,
        *,
        include_completed_today: bool = True,
    ) -> Task | None:
        self.lookups.append(
            {
                "entity_key": entity_key,
                "reminder_type": reminder_type,
                "tenant_key": tenant_key,
                "include_completed_today": include_completed_today,
            }
        )
        suffix = f"— {reminder_type.value}"
        today = datetime.now(UTC).date()
        matches = [
            (index, task)
            for index, task in enumerate(self.store)
            if task.tenant_key == tenant_key
            and (task.entity_key or "") == entity_key
            and task.category == TaskCategory.CARE_REMINDER
            and (task.name or "").endswith(suffix)
            and (
                task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
                or (
                    include_completed_today
                    and task.status == TaskStatus.COMPLETED
                    and task.completed_at is not None
                    and task.completed_at.astimezone(UTC).date() >= today
                )
            )
        ]
        if not matches:
            return None
        matches.sort(key=lambda pair: (pair[1].due_date or _OLDEST, pair[0]), reverse=True)
        return matches[0][1]

    # ── writes ──

    def update_task(self, key: str, task: Task) -> Task:
        for index, stored in enumerate(self.store):
            if stored.key == key:
                self.store[index] = task
                return task
        self.store.append(task)
        return task

    def create_task(self, task: Task) -> Task:
        self._created += 1
        task.key = task.key or f"task-created-{self._created}"
        self.store.append(task)
        return task

    # ── assertions helpers ──

    def pending_care_tasks(self, reminder_type: ReminderType) -> list[Task]:
        """All tasks of that reminder type still awaiting the user."""
        suffix = f"— {reminder_type.value}"
        return [
            task
            for task in self.store
            if (task.name or "").endswith(suffix) and task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        ]
