"""Stateful in-memory task repository for care-reminder behaviour tests (#768).

The care paths compose *complete-then-schedule*: they close the plant's open care
task and then ask the single dedup helper
(:meth:`ITaskRepository.find_open_care_task`) whether a follow-up is still
needed. With a stateless mock that composition looks correct while the real AQL
returns the very task that was just completed — which is how #768 shipped: the
follow-up watering task was never created.

:class:`FakeTaskRepo` therefore models the repository's *state*: a completion is
visible to the very next lookup, exactly as in ArangoDB. It mirrors the AQL
predicate of ``ArangoTaskRepository.find_open_care_task``:

* tenant-scoped (``tenant_key``), entity-scoped (``entity_key``),
* care-reminder category with the ``"— {reminder_type}"`` name suffix,
* satisfied by ``PENDING``/``IN_PROGRESS`` — or, when
  ``include_completed_today``, by a task completed today,
* newest first (``due_date`` DESC, then insertion order DESC).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.models.task import Task

#: Sort floor for tasks without a due date (mirrors AQL's null-last ordering).
_NO_DUE_DATE = datetime.min.replace(tzinfo=UTC)

_OPEN_STATUSES = (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value)


def _as_aware_utc(value: datetime | None) -> datetime:
    """Normalise a (possibly naive) due date so mixed tasks stay sortable."""
    if value is None:
        return _NO_DUE_DATE
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class FakeTaskRepo:
    """In-memory ``ITaskRepository`` slice covering the care-task dedup surface."""

    def __init__(self, tasks: list[Task] | None = None) -> None:
        self.store: list[Task] = list(tasks or [])
        self.created: list[Task] = []
        self.updated: list[Task] = []
        self.lookups: list[dict] = []

    # ── the single care-task dedup predicate ──
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
            task
            for task in self.store
            if task.tenant_key == tenant_key
            and (task.entity_key or "") == entity_key
            and task.category == TaskCategory.CARE_REMINDER.value
            and (task.name or "").endswith(suffix)
            and (
                task.status in _OPEN_STATUSES
                or (
                    include_completed_today
                    and task.status == TaskStatus.COMPLETED.value
                    and task.completed_at is not None
                    and task.completed_at.date() >= today
                )
            )
        ]
        if not matches:
            return None
        newest = max(matches, key=lambda task: (_as_aware_utc(task.due_date), self.store.index(task)))
        # The repository materialises a fresh model per document; returning a copy
        # keeps a caller's in-place mutation invisible until ``update_task`` runs.
        return newest.model_copy(deep=True)

    # ── writes ──
    def create_task(self, task: Task) -> Task:
        stored = task.model_copy(deep=True)
        if not stored.key:
            stored.key = f"task-{len(self.store) + 1}"
        self.store.append(stored)
        self.created.append(stored)
        return stored.model_copy(deep=True)

    def update_task(self, key: str, task: Task) -> Task:
        for index, existing in enumerate(self.store):
            if existing.key == key:
                self.store[index] = task.model_copy(deep=True)
                self.updated.append(self.store[index])
                return self.store[index].model_copy(deep=True)
        raise AssertionError(f"update_task called for unknown task key {key!r}")

    def get_task(self, key: str) -> Task | None:
        for task in self.store:
            if task.key == key:
                return task.model_copy(deep=True)
        return None

    # ── assertions helpers ──
    def open_care_tasks(self, reminder_type: ReminderType) -> list[Task]:
        """Return the still-open tasks of *reminder_type* (test assertion helper)."""
        suffix = f"— {reminder_type.value}"
        return [task for task in self.store if (task.name or "").endswith(suffix) and task.status in _OPEN_STATUSES]

    def completed_care_tasks(self, reminder_type: ReminderType) -> list[Task]:
        """Return the completed tasks of *reminder_type* (test assertion helper)."""
        suffix = f"— {reminder_type.value}"
        return [
            task
            for task in self.store
            if (task.name or "").endswith(suffix) and task.status == TaskStatus.COMPLETED.value
        ]
