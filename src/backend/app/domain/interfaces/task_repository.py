from abc import ABC, abstractmethod

from app.common.enums import ReminderType
from app.common.types import TaskKey, WorkflowExecutionKey, WorkflowTemplateKey
from app.domain.models.task import (
    Task,
    TaskAuditEntry,
    TaskComment,
    TaskTemplate,
    WorkflowExecution,
    WorkflowPhase,
    WorkflowTemplate,
)


class ITaskRepository(ABC):
    # ── WorkflowTemplate CRUD ──
    @abstractmethod
    def get_all_workflow_templates(
        self,
        offset: int = 0,
        limit: int = 50,
        species_key: str | None = None,
        target_entity_type: str | None = None,
    ) -> tuple[list[WorkflowTemplate], int]: ...

    @abstractmethod
    def get_workflow_template_by_key(self, key: WorkflowTemplateKey) -> WorkflowTemplate | None: ...

    @abstractmethod
    def get_workflow_template_or_raise(self, key: WorkflowTemplateKey) -> WorkflowTemplate: ...

    @abstractmethod
    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate: ...

    @abstractmethod
    def update_workflow_template(self, key: WorkflowTemplateKey, template: WorkflowTemplate) -> WorkflowTemplate: ...

    @abstractmethod
    def delete_workflow_template(self, key: WorkflowTemplateKey) -> bool: ...

    # ── WorkflowPhase CRUD ──
    @abstractmethod
    def get_phases_for_workflow(self, wf_key: WorkflowTemplateKey) -> list[WorkflowPhase]: ...

    @abstractmethod
    def get_phase_by_key(self, key: str) -> WorkflowPhase | None: ...

    @abstractmethod
    def get_phase_or_raise(self, key: str) -> WorkflowPhase: ...

    @abstractmethod
    def create_phase(self, phase: WorkflowPhase) -> WorkflowPhase: ...

    @abstractmethod
    def update_phase(self, key: str, phase: WorkflowPhase) -> WorkflowPhase: ...

    @abstractmethod
    def delete_phase(self, key: str) -> bool: ...

    @abstractmethod
    def reorder_phases(self, phase_orders: list[dict]) -> list[WorkflowPhase]: ...

    @abstractmethod
    def get_phase_suggestions(self) -> list[dict]: ...

    # ── TaskTemplate CRUD ──
    @abstractmethod
    def get_task_templates_for_workflow(self, wf_key: WorkflowTemplateKey) -> list[TaskTemplate]: ...

    @abstractmethod
    def get_task_template_by_key(self, key: str) -> TaskTemplate | None: ...

    @abstractmethod
    def get_task_template_or_raise(self, key: str) -> TaskTemplate: ...

    @abstractmethod
    def create_task_template(self, template: TaskTemplate) -> TaskTemplate: ...

    @abstractmethod
    def update_task_template(self, key: str, template: TaskTemplate) -> TaskTemplate: ...

    @abstractmethod
    def delete_task_template(self, key: str) -> bool: ...

    # ── Task CRUD ──
    @abstractmethod
    def get_all_tasks(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
    ) -> tuple[list[Task], int]: ...

    @abstractmethod
    def get_task_by_key(self, key: TaskKey) -> Task | None: ...

    @abstractmethod
    def get_task_or_raise(self, key: TaskKey) -> Task: ...

    @abstractmethod
    def create_task(self, task: Task) -> Task: ...

    @abstractmethod
    def find_task_by_external_ref(self, *, tenant_key: str, source: str, external_ref: str) -> Task | None:
        """Tenant+source-scoped FreeStyle idempotency lookup (#1082 AC-3).

        Returns the newest task matching ``(tenant_key, source, external_ref)`` or
        ``None``. Anchored on ``tenant_key`` AND ``source`` so it is never a
        cross-tenant existence oracle and two producers cannot collide on the same
        ``external_ref``. All three are keyword-only.
        """
        ...

    @abstractmethod
    def update_task(self, key: TaskKey, task: Task) -> Task: ...

    @abstractmethod
    def delete_task(self, key: TaskKey) -> bool: ...

    @abstractmethod
    def get_tasks_for_plant(self, plant_key: str, status: str | None = None, *, tenant_key: str) -> list[Task]:
        """Return a plant's tasks inside ``tenant_key`` (#927).

        ``tenant_key`` is required and keyword-only; ``plant_key`` alone selects
        across every tenant and arrives from the URL.
        """
        ...

    @abstractmethod
    def get_tasks_for_run(self, run_key: str, status: str | None = None, *, tenant_key: str) -> list[Task]:
        """A run's tasks inside ``tenant_key`` (#952)."""
        ...

    @abstractmethod
    def get_tasks_for_entity(
        self,
        entity_type: str,
        entity_key: str,
        tenant_key: str,
        status: str | None = None,
    ) -> list[Task]: ...

    @abstractmethod
    def get_pending_tasks(self, offset: int = 0, limit: int = 50, *, tenant_key: str) -> tuple[list[Task], int]: ...

    @abstractmethod
    def get_overdue_tasks(self, *, tenant_key: str) -> list[Task]: ...

    @abstractmethod
    def find_open_care_task(
        self,
        entity_key: str,
        reminder_type: ReminderType,
        tenant_key: str,
        *,
        include_completed_today: bool = True,
    ) -> Task | None:
        """Single tenant-scoped care-reminder idempotency lookup (#509).

        Returns the newest care-reminder task that still "satisfies" the
        reminder for ``(tenant_key, entity_key, reminder_type)``, or ``None``.
        The only care-task dedup predicate — see the ArangoDB implementation.
        """
        ...

    @abstractmethod
    def get_blocking_tasks(self, task_key: TaskKey) -> list[dict]: ...

    # ── WorkflowExecution ──
    @abstractmethod
    def create_workflow_execution(self, execution: WorkflowExecution) -> WorkflowExecution: ...

    @abstractmethod
    def get_workflow_execution_by_key(self, key: WorkflowExecutionKey) -> WorkflowExecution | None: ...

    @abstractmethod
    def get_workflow_execution_or_raise(self, key: WorkflowExecutionKey) -> WorkflowExecution: ...

    @abstractmethod
    def update_workflow_execution(
        self,
        key: WorkflowExecutionKey,
        execution: WorkflowExecution,
    ) -> WorkflowExecution: ...

    # ── Comments ──
    @abstractmethod
    def create_comment(self, comment: TaskComment) -> TaskComment: ...

    @abstractmethod
    def get_comments_for_task(self, task_key: str, *, tenant_key: str) -> list[TaskComment]:
        """Return a task's comments, scoped by the parent task's tenant (#927)."""
        ...

    @abstractmethod
    def get_comment_by_key(self, key: str) -> TaskComment | None: ...

    @abstractmethod
    def get_comment_or_raise(self, key: str) -> TaskComment: ...

    @abstractmethod
    def update_comment(self, key: str, comment: TaskComment) -> TaskComment: ...

    @abstractmethod
    def delete_comment(self, key: str) -> bool: ...

    @abstractmethod
    def delete_comments_for_task(self, task_key: str) -> int: ...

    # ── Audit ──
    @abstractmethod
    def create_audit_entry(self, entry: TaskAuditEntry) -> TaskAuditEntry: ...

    @abstractmethod
    def get_audit_entries_for_task(self, task_key: str) -> list[TaskAuditEntry]: ...

    # ── Dormant ──
    @abstractmethod
    def get_dormant_tasks_for_phase(self, plant_key: str, phase_name: str) -> list[Task]: ...

    # ── Activity edge ──
    @abstractmethod
    def create_task_activity_edge(self, task_key: str, activity_key: str) -> None: ...

    # ── Auto-generated workflow lookup ──
    @abstractmethod
    def get_auto_generated_workflow_for_species(
        self,
        species_key: str,
        tenant_key: str = "",
    ) -> WorkflowTemplate | None:
        """Return ``tenant_key``'s private copy of the generated plan, else the shared template.

        A union, not an equality — see the implementation's docstring for why a
        strict tenant predicate matches nothing here (#1003, #324).
        """
        ...

    @abstractmethod
    def delete_task_templates_for_workflow(self, wf_key: str) -> int: ...

    @abstractmethod
    def get_workflow_usage_stats(self, wf_keys: list[str]) -> dict[str, dict]: ...

    @abstractmethod
    def get_executions_for_template(self, template_key: str) -> list[dict]: ...

    # ── Batch ──
    @abstractmethod
    def batch_get_tasks(self, task_keys: list[str]) -> list[Task]: ...
