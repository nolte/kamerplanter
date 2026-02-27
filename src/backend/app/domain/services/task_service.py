from datetime import UTC, datetime, timedelta

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.task import Task, WorkflowExecution, WorkflowTemplate


class TaskService:
    def __init__(
        self,
        repo: ITaskRepository,
        hst_validator: HSTValidator,
        dependency_resolver: DependencyResolver,
    ) -> None:
        self._repo = repo
        self._hst = hst_validator
        self._deps = dependency_resolver

    # ── Workflow Templates ──

    def list_workflow_templates(self, offset: int = 0, limit: int = 50) -> tuple[list[WorkflowTemplate], int]:
        return self._repo.get_all_workflow_templates(offset, limit)

    def get_workflow_template(self, key: str) -> WorkflowTemplate:
        wt = self._repo.get_workflow_template_by_key(key)
        if not wt:
            raise NotFoundError("WorkflowTemplate", key)
        return wt

    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        return self._repo.create_workflow_template(template)

    # ── Task Templates ──

    def get_task_templates(self, wf_key: str) -> list:
        return self._repo.get_task_templates_for_workflow(wf_key)

    def create_task_template(self, template) -> object:
        return self._repo.create_task_template(template)

    # ── Workflow Instantiation ──

    def instantiate_workflow(self, template_key: str, plant_key: str) -> WorkflowExecution:
        """Generate tasks from a workflow template for a specific plant."""
        wt = self.get_workflow_template(template_key)
        templates = self._repo.get_task_templates_for_workflow(template_key)

        if not templates:
            raise ValidationError(f"Workflow '{wt.name}' has no task templates.")

        execution = WorkflowExecution(
            workflow_template_key=template_key,
            plant_key=plant_key,
        )
        execution = self._repo.create_workflow_execution(execution)

        now = datetime.now(UTC)
        for tt in templates:
            due_date = now + timedelta(days=tt.days_offset) if tt.days_offset else None
            task = Task(
                name=tt.name,
                instruction=tt.instruction,
                category=tt.category,
                plant_key=plant_key,
                due_date=due_date,
                priority="medium",
                estimated_duration_minutes=tt.estimated_duration_minutes,
                requires_photo=tt.requires_photo,
                template_key=tt.key,
                workflow_execution_key=execution.key,
            )
            self._repo.create_task(task)

        return execution

    # ── Task CRUD ──

    def list_tasks(self, offset: int = 0, limit: int = 50, filters: dict | None = None) -> tuple[list[Task], int]:
        return self._repo.get_all_tasks(offset, limit, filters)

    def get_task(self, key: str) -> Task:
        task = self._repo.get_task_by_key(key)
        if not task:
            raise NotFoundError("Task", key)
        return task

    def create_task(self, task: Task) -> Task:
        return self._repo.create_task(task)

    def start_task(self, key: str) -> Task:
        task = self.get_task(key)
        if task.status != "pending":
            raise ValidationError(f"Cannot start task in status '{task.status}'.")
        task.status = "in_progress"
        task.started_at = datetime.now(UTC)
        return self._repo.update_task(key, task)

    def complete_task(self, key: str, completion_notes: str | None = None, actual_minutes: int | None = None) -> Task:
        task = self.get_task(key)
        if task.status not in ("pending", "in_progress"):
            raise ValidationError(f"Cannot complete task in status '{task.status}'.")

        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        if completion_notes:
            task.completion_notes = completion_notes
        if actual_minutes is not None:
            task.actual_duration_minutes = actual_minutes

        updated = self._repo.update_task(key, task)

        # Reschedule dependents if late
        if task.due_date and task.completed_at and task.completed_at > task.due_date:
            all_tasks = self._repo.get_tasks_for_plant(task.plant_key or "")
            deps = self._repo.get_blocking_tasks(key)
            task_dicts = [
                {"key": t.key, "status": t.status, "priority": t.priority, "due_date": t.due_date}
                for t in all_tasks
            ]
            dep_dicts = [{"from_key": key, "to_key": d["key"]} for d in deps]
            rescheduled = self._deps.reschedule_dependents(
                key, task.completed_at, task.due_date, task_dicts, dep_dicts,
            )
            for r in rescheduled:
                dep_task = self._repo.get_task_by_key(r["task_key"])
                if dep_task:
                    dep_task.due_date = datetime.fromisoformat(r["new_due_date"])
                    self._repo.update_task(r["task_key"], dep_task)

        return updated

    def skip_task(self, key: str) -> Task:
        task = self.get_task(key)
        if task.status not in ("pending", "in_progress"):
            raise ValidationError(f"Cannot skip task in status '{task.status}'.")
        task.status = "skipped"
        task.completed_at = datetime.now(UTC)
        return self._repo.update_task(key, task)

    # ── Task Queue ──

    def get_task_queue(self, plant_key: str | None = None) -> list[Task]:
        if plant_key:
            tasks = self._repo.get_tasks_for_plant(plant_key, "pending")
        else:
            tasks, _ = self._repo.get_pending_tasks(0, 200)

        task_dicts = [
            {
                "key": t.key, "status": t.status, "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in tasks
        ]
        deps: list[dict] = []
        for t in tasks:
            blocking = self._repo.get_blocking_tasks(t.key or "")
            for b in blocking:
                deps.append({"from_key": b["key"], "to_key": t.key})

        ready_dicts = self._deps.get_ready_tasks(task_dicts, deps)
        ready_keys = {d["key"] for d in ready_dicts}
        return [t for t in tasks if t.key in ready_keys]

    def get_overdue_tasks(self) -> list[Task]:
        return self._repo.get_overdue_tasks()

    def get_tasks_for_plant(self, plant_key: str, status: str | None = None) -> list[Task]:
        return self._repo.get_tasks_for_plant(plant_key, status)

    # ── HST Validation ──

    def validate_hst(
        self, task_name: str, current_phase: str,
        recent_hst_tasks: list[dict], species_name: str = "",
    ) -> dict:
        return self._hst.validate(
            task_name, current_phase, recent_hst_tasks, species_name,
        )

    # ── Workflow Execution ──

    def get_workflow_execution(self, key: str) -> WorkflowExecution:
        we = self._repo.get_workflow_execution_by_key(key)
        if not we:
            raise NotFoundError("WorkflowExecution", key)
        return we
