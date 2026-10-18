"""In-memory doubles of the task-completion transition's collaborators (REQ-053 WP 4.3, #2413).

``FakeCompletionRepo`` is all-or-nothing like the transaction (every task is checked before any is changed) and
records what it was handed, so a test asserts both what the service decided and that a refusal wrote nothing.
Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from app.common.enums import TaskCategory, TaskStatus
from app.common.exceptions import KarenzViolationError, NotFoundError, ValidationError
from app.domain.interfaces.task_completion_repository import ITaskCompletionRepository
from app.domain.models.care_event import CareEvent
from app.domain.models.task import Task
from app.domain.models.task_completion import CompletedTask, CompletionWrite, UndoWrite
from tests.support.garden_plan_fakes import TENANT


class FakeTaskRepo:
    """The slice of ``ITaskRepository`` a completion and a reopen read and write."""

    def __init__(self, *tasks: Task) -> None:
        self.store = {task.key: task for task in tasks}
        self.created: list[Task] = []
        self.cleared_parked: list[str] = []

    def get_task_or_raise(self, key: str) -> Task:
        if key not in self.store:
            raise NotFoundError("Task", key)
        return self.store[key].model_copy(deep=True)

    def update_task(self, key: str, task: Task) -> Task:
        self.store[key] = task.model_copy(deep=True)
        return self.store[key].model_copy(deep=True)

    def clear_parked_recurrence(self, key: str) -> None:
        self.cleared_parked.append(key)

    def get_tasks_for_entity(self, *_args, **_kwargs) -> list[Task]:
        return []

    def get_blocking_tasks(self, _key: str) -> list[dict]:
        return []

    def create_task(self, task: Task) -> Task:
        self.created.append(task)
        return task


class FakeCompletionRepo(ITaskCompletionRepository):
    """All-or-nothing like the transaction: every task is checked before any is changed."""

    def __init__(self, tasks: FakeTaskRepo, plants: dict[str, tuple[str, str]]) -> None:
        self._tasks = tasks
        self.plants = plants
        self.completed: list[CompletionWrite] = []
        self.calls = 0
        self.reopened: list[UndoWrite] = []
        self.open_event: CareEvent | None = None
        self.fail_with: Exception | None = None

    def plant_location(self, plant_key, *, tenant_key):
        owner, location = self.plants.get(plant_key, (None, None))
        return location if owner == tenant_key else None

    def plants_in_locations(self, location_keys, *, tenant_key):
        return sorted(k for k, (t, loc) in self.plants.items() if t == tenant_key and loc in location_keys)

    def task_event(self, task_key, *, tenant_key):
        return self.open_event if self.open_event and self.open_event.task_key == task_key else None

    def complete(self, writes, *, tenant_key):
        self.calls += 1
        if self.fail_with is not None:
            raise self.fail_with
        for write in writes:
            stored = self._tasks.store.get(write.task_key)
            if stored is None or stored.tenant_key != tenant_key:
                raise NotFoundError("Task", write.task_key)
            if stored.status not in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                raise ValidationError(f"Cannot complete task in status '{stored.status}'.")
        for write in writes:
            stored = self._tasks.store[write.task_key]
            self._tasks.store[write.task_key] = stored.model_copy(update={"status": TaskStatus.COMPLETED})
            self.completed.append(write)
        return [CompletedTask(w.task_key, "ce_x" if w.event else None, None) for w in writes]

    def reopen(self, write, *, tenant_key):
        if self.fail_with is not None:
            raise self.fail_with
        self.reopened.append(write)
        stored = self._tasks.store[write.task_key]
        self._tasks.store[write.task_key] = stored.model_copy(update={"status": TaskStatus.PENDING})


class FakeHarvests:
    def __init__(self) -> None:
        self.refuse = False
        self.checked: list[list[str]] = []

    def require_karenz_clear(self, plant_keys, harvest_date, *, tenant_key):
        self.checked.append(list(plant_keys))
        if self.refuse:
            raise KarenzViolationError("pyrethrum", 3)

    def next_batch_id(self, plant_key, harvest_date, *, tenant_key, taken=None):
        taken = taken if taken is not None else set()
        candidate = f"HARVEST-{plant_key or 'unassigned'}-{len(taken) + 1}"
        taken.add(candidate)
        return candidate


def bed_task(key: str = "t1", category: TaskCategory = TaskCategory.WATERING, **overrides) -> Task:
    data = {
        "_key": key,
        "tenant_key": TENANT,
        "name": "Bed 3",
        "category": category,
        "entity_type": "location",
        "entity_key": "bed",
        "status": TaskStatus.PENDING,
    }
    return Task(**{**data, **overrides})
