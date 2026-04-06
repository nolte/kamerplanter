from abc import ABC, abstractmethod

from app.common.types import TaskKey, WorkflowExecutionKey, WorkflowTemplateKey
from app.domain.models.task import (
    Task,
    TaskAuditEntry,
    TaskComment,
    TaskTemplate,
    WorkflowExecution,
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
    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate: ...

    @abstractmethod
    def update_workflow_template(self, key: WorkflowTemplateKey, template: WorkflowTemplate) -> WorkflowTemplate: ...

    @abstractmethod
    def delete_workflow_template(self, key: WorkflowTemplateKey) -> bool: ...

    # ── TaskTemplate CRUD ──
    @abstractmethod
    def get_task_templates_for_workflow(self, wf_key: WorkflowTemplateKey) -> list[TaskTemplate]: ...

    @abstractmethod
    def get_task_template_by_key(self, key: str) -> TaskTemplate | None: ...

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
    def create_task(self, task: Task) -> Task: ...

    @abstractmethod
    def update_task(self, key: TaskKey, task: Task) -> Task: ...

    @abstractmethod
    def delete_task(self, key: TaskKey) -> bool: ...

    @abstractmethod
    def get_tasks_for_plant(self, plant_key: str, status: str | None = None) -> list[Task]: ...

    @abstractmethod
    def get_tasks_for_entity(
        self,
        entity_type: str,
        entity_key: str,
        tenant_key: str,
        status: str | None = None,
    ) -> list[Task]: ...

    @abstractmethod
    def get_pending_tasks(self, offset: int = 0, limit: int = 50) -> tuple[list[Task], int]: ...

    @abstractmethod
    def get_overdue_tasks(self) -> list[Task]: ...

    @abstractmethod
    def get_blocking_tasks(self, task_key: TaskKey) -> list[dict]: ...

    # ── WorkflowExecution ──
    @abstractmethod
    def create_workflow_execution(self, execution: WorkflowExecution) -> WorkflowExecution: ...

    @abstractmethod
    def get_workflow_execution_by_key(self, key: WorkflowExecutionKey) -> WorkflowExecution | None: ...

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
    def get_comments_for_task(self, task_key: str) -> list[TaskComment]: ...

    @abstractmethod
    def get_comment_by_key(self, key: str) -> TaskComment | None: ...

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
    def get_auto_generated_workflow_for_species(self, species_key: str) -> WorkflowTemplate | None: ...

    @abstractmethod
    def delete_task_templates_for_workflow(self, wf_key: str) -> int: ...

    @abstractmethod
    def get_workflow_usage_stats(self, wf_keys: list[str]) -> dict[str, dict]: ...

    @abstractmethod
    def get_executions_for_template(self, template_key: str) -> list[dict]: ...

    # ── Batch ──
    @abstractmethod
    def batch_get_tasks(self, task_keys: list[str]) -> list[Task]: ...
