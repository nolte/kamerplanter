from abc import ABC, abstractmethod

from app.common.types import TaskKey, WorkflowExecutionKey, WorkflowTemplateKey
from app.domain.models.task import Task, TaskTemplate, WorkflowExecution, WorkflowTemplate


class ITaskRepository(ABC):
    # ── WorkflowTemplate CRUD ──
    @abstractmethod
    def get_all_workflow_templates(self, offset: int = 0, limit: int = 50) -> tuple[list[WorkflowTemplate], int]: ...

    @abstractmethod
    def get_workflow_template_by_key(self, key: WorkflowTemplateKey) -> WorkflowTemplate | None: ...

    @abstractmethod
    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate: ...

    # ── TaskTemplate CRUD ──
    @abstractmethod
    def get_task_templates_for_workflow(self, wf_key: WorkflowTemplateKey) -> list[TaskTemplate]: ...

    @abstractmethod
    def create_task_template(self, template: TaskTemplate) -> TaskTemplate: ...

    # ── Task CRUD ──
    @abstractmethod
    def get_all_tasks(
        self, offset: int = 0, limit: int = 50, filters: dict | None = None,
    ) -> tuple[list[Task], int]: ...

    @abstractmethod
    def get_task_by_key(self, key: TaskKey) -> Task | None: ...

    @abstractmethod
    def create_task(self, task: Task) -> Task: ...

    @abstractmethod
    def update_task(self, key: TaskKey, task: Task) -> Task: ...

    @abstractmethod
    def get_tasks_for_plant(self, plant_key: str, status: str | None = None) -> list[Task]: ...

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
        self, key: WorkflowExecutionKey, execution: WorkflowExecution,
    ) -> WorkflowExecution: ...
