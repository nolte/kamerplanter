"""A task-repository double that also holds task templates (REQ-053 GP-FR-087, #2897).

``place-template`` with ``create_recurring_tasks`` reads task templates by key and writes the tasks in one
transaction. ``TemplateTaskRepo`` extends the completion double with exactly that: a template store keyed like
``task_templates``, a switch that makes the atomic write fail (all or none, like the stream transaction), and the
activity edges it was asked for. Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from app.common.exceptions import NotFoundError
from app.domain.models.task import TaskTemplate
from tests.support.task_completion_fakes import FakeTaskRepo


class TemplateTaskRepo(FakeTaskRepo):
    def __init__(self, *templates: TaskTemplate) -> None:
        super().__init__()
        self.task_templates: dict[str, TaskTemplate] = {t.key or "": t for t in templates}
        self.activity_edges: list[tuple[str, str]] = []
        #: Raise from ``create_tasks_atomic`` before anything is stored (a failed transaction).
        self.fail_atomic = False

    def get_task_template_or_raise(self, key: str) -> TaskTemplate:
        if key not in self.task_templates:
            raise NotFoundError("TaskTemplate", key)
        return self.task_templates[key].model_copy(deep=True)

    def create_tasks_atomic(self, tasks, *, tenant_key):
        if self.fail_atomic:
            raise ConnectionError("the transaction was aborted")
        return super().create_tasks_atomic(tasks, tenant_key=tenant_key)

    def create_task_activity_edge(self, task_key: str, activity_key: str) -> None:
        self.activity_edges.append((task_key, activity_key))


def task_template(key: str, tenant_key: str, **overrides) -> TaskTemplate:
    """A task template of ``tenant_key`` (``""`` = a global one)."""
    return TaskTemplate(**{"_key": key, "tenant_key": tenant_key, "name": f"Task {key}", **overrides})
