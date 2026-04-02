from datetime import UTC, datetime, timedelta

from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.models.task import (
    ChecklistItem,
    Task,
    TaskAuditEntry,
    TaskComment,
    TaskTemplate,
    WorkflowExecution,
    WorkflowTemplate,
)


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

    def list_workflow_templates(
        self,
        offset: int = 0,
        limit: int = 50,
        species_key: str | None = None,
        tenant_key: str = "",
        target_entity_type: str | None = None,
    ) -> tuple[list[WorkflowTemplate], int]:
        return self._repo.get_all_workflow_templates(
            offset,
            limit,
            species_key=species_key,
            tenant_key=tenant_key,
            target_entity_type=target_entity_type,
        )

    def get_workflow_usage_stats(self, wf_keys: list[str]) -> dict[str, dict]:
        """Return species_name and assigned plant count per workflow key."""
        return self._repo.get_workflow_usage_stats(wf_keys)

    def get_workflow_template(self, key: str, tenant_key: str = "") -> WorkflowTemplate:
        wt = self._repo.get_workflow_template_by_key(key)
        if not wt:
            raise NotFoundError("WorkflowTemplate", key)
        if tenant_key:
            verify_tenant_ownership(wt, tenant_key, "WorkflowTemplate")
        return wt

    def create_workflow_template(self, template: WorkflowTemplate) -> WorkflowTemplate:
        return self._repo.create_workflow_template(template)

    def update_workflow_template(self, key: str, data: dict) -> WorkflowTemplate:
        wt = self.get_workflow_template(key)
        for field, value in data.items():
            setattr(wt, field, value)
        return self._repo.update_workflow_template(key, wt)

    def delete_workflow_template(self, key: str) -> bool:
        wt = self.get_workflow_template(key)
        if wt.is_system:
            raise ValidationError("Cannot delete system workflow templates.")
        return self._repo.delete_workflow_template(key)

    def duplicate_workflow_template(self, key: str, new_name: str) -> WorkflowTemplate:
        """Duplicate a workflow template including all its task templates."""
        source = self.get_workflow_template(key)
        clone = WorkflowTemplate(
            name=new_name,
            description=source.description,
            species_compatible=list(source.species_compatible),
            species_key=source.species_key,
            lifecycle_key=source.lifecycle_key,
            growth_system=source.growth_system,
            difficulty_level=source.difficulty_level,
            category=source.category,
            tags=list(source.tags),
            auto_generated=False,
            total_duration_days=source.total_duration_days,
            skill_level_filter=source.skill_level_filter,
            target_entity_types=list(source.target_entity_types),
        )
        created_wf = self._repo.create_workflow_template(clone)

        templates = self._repo.get_task_templates_for_workflow(key)
        for tt in templates:
            tt.key = None
            tt.workflow_template_key = created_wf.key or ""
            tt.created_at = None
            tt.updated_at = None
            self._repo.create_task_template(tt)

        return created_wf

    # ── Task Templates ──

    def get_task_templates(self, wf_key: str) -> list[TaskTemplate]:
        return self._repo.get_task_templates_for_workflow(wf_key)

    def get_task_template(self, key: str) -> TaskTemplate:
        tt = self._repo.get_task_template_by_key(key)
        if not tt:
            raise NotFoundError("TaskTemplate", key)
        return tt

    def create_task_template(self, template: TaskTemplate) -> TaskTemplate:
        return self._repo.create_task_template(template)

    def update_task_template(self, key: str, data: dict) -> TaskTemplate:
        tt = self.get_task_template(key)
        for field, value in data.items():
            setattr(tt, field, value)
        return self._repo.update_task_template(key, tt)

    def delete_task_template(self, key: str) -> bool:
        self.get_task_template(key)  # ensure exists
        return self._repo.delete_task_template(key)

    # ── Workflow Instantiation ──

    def instantiate_workflow(
        self,
        template_key: str,
        entity_key: str,
        entity_type: str,
    ) -> WorkflowExecution:
        """Generate tasks from a workflow template for a specific entity.

        Tasks whose trigger_phase does not match the current phase are created
        with status 'dormant' for plant_instance entities and 'pending' for
        all other entity types (which have no phase concept).
        """
        wt = self.get_workflow_template(template_key)
        templates = self._repo.get_task_templates_for_workflow(template_key)

        if not templates:
            raise ValidationError(f"Workflow '{wt.name}' has no task templates.")

        execution = WorkflowExecution(
            workflow_template_key=template_key,
            entity_key=entity_key,
            entity_type=entity_type,
        )
        execution = self._repo.create_workflow_execution(execution)

        now = datetime.now(UTC)
        for tt in templates:
            checklist = [ChecklistItem(text=item.text, done=False, order=item.order) for item in tt.default_checklist]

            status = "pending"
            due_date = now + timedelta(days=tt.days_offset) if tt.days_offset else None
            # Only plant_instance entities support phase-based dormant tasks
            if (
                entity_type == "plant_instance"
                and tt.trigger_phase
                and tt.trigger_type in ("phase_entry", "days_after_phase")
            ):
                status = "dormant"
                due_date = None

            task = Task(
                name=tt.name,
                name_de=tt.name_de,
                instruction=tt.instruction,
                instruction_de=tt.instruction_de,
                category=tt.category,
                entity_key=entity_key,
                entity_type=entity_type,
                due_date=due_date,
                status=status,
                priority="medium",
                skill_level=tt.skill_level,
                stress_level=tt.stress_level,
                estimated_duration_minutes=tt.estimated_duration_minutes,
                requires_photo=tt.requires_photo,
                timer_duration_seconds=tt.timer_duration_seconds,
                timer_label=tt.timer_label,
                checklist=checklist,
                trigger_phase=tt.trigger_phase,
                template_key=tt.key,
                workflow_execution_key=execution.key,
                activity_key=tt.activity_key,
            )
            created_task = self._repo.create_task(task)

            if tt.activity_key and created_task.key:
                self._repo.create_task_activity_edge(
                    created_task.key,
                    tt.activity_key,
                )

        return execution

    # ── Task CRUD ──

    def list_tasks(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str = "",
    ) -> tuple[list[Task], int]:
        return self._repo.get_all_tasks(offset, limit, filters, tenant_key=tenant_key)

    def get_task(self, key: str, tenant_key: str = "") -> Task:
        task = self._repo.get_task_by_key(key)
        if not task:
            raise NotFoundError("Task", key)
        if tenant_key:
            verify_tenant_ownership(task, tenant_key, "Task")
        return task

    def create_task(self, task: Task) -> Task:
        return self._repo.create_task(task)

    def delete_task(self, key: str) -> bool:
        task = self.get_task(key)
        allowed = {"pending", "skipped", "cancelled", "dormant"}
        if task.status not in allowed:
            raise ValidationError(
                f"Cannot delete task in status '{task.status}'. "
                f"Only {', '.join(sorted(allowed))} tasks can be deleted.",
            )
        return self._repo.delete_task(key)

    def add_photo_ref(self, key: str, url: str) -> Task:
        task = self.get_task(key)
        task.photo_refs.append(url)
        return self._repo.update_task(key, task)

    def start_task(self, key: str) -> Task:
        task = self.get_task(key)
        if task.status != "pending":
            raise ValidationError(f"Cannot start task in status '{task.status}'.")
        task.status = "in_progress"
        task.started_at = datetime.now(UTC)
        return self._repo.update_task(key, task)

    def complete_task(
        self,
        key: str,
        completion_notes: str | None = None,
        actual_minutes: int | None = None,
        photo_refs: list[str] | None = None,
        difficulty_rating: int | None = None,
        quality_rating: int | None = None,
    ) -> Task:
        task = self.get_task(key)
        if task.status not in ("pending", "in_progress"):
            raise ValidationError(f"Cannot complete task in status '{task.status}'.")

        if task.requires_photo and not task.photo_refs and not photo_refs:
            raise ValidationError("This task requires at least one photo before completion.")

        if photo_refs:
            task.photo_refs.extend(photo_refs)

        task.status = "completed"
        task.completed_at = datetime.now(UTC)
        if completion_notes:
            task.completion_notes = completion_notes
        if actual_minutes is not None:
            task.actual_duration_minutes = actual_minutes
        if difficulty_rating is not None:
            task.difficulty_rating = difficulty_rating
        if quality_rating is not None:
            task.quality_rating = quality_rating

        updated = self._repo.update_task(key, task)

        # Reschedule dependents if late
        if task.due_date and task.completed_at and task.completed_at > task.due_date:
            self._reschedule_dependents(key, task)

        # Create next recurring task if applicable
        if task.recurrence_rule:
            self._create_next_recurring_task(updated)

        return updated

    def _reschedule_dependents(self, key: str, task: Task) -> None:
        if task.entity_key and task.entity_type:
            all_tasks = self._repo.get_tasks_for_entity(
                task.entity_type,
                task.entity_key,
                task.tenant_key,
            )
        else:
            all_tasks = []
        deps = self._repo.get_blocking_tasks(key)
        task_dicts = [
            {"key": t.key, "status": t.status, "priority": t.priority, "due_date": t.due_date} for t in all_tasks
        ]
        dep_dicts = [{"from_key": key, "to_key": d["key"]} for d in deps]
        rescheduled = self._deps.reschedule_dependents(
            key,
            task.completed_at,
            task.due_date,
            task_dicts,
            dep_dicts,
        )
        for r in rescheduled:
            dep_task = self._repo.get_task_by_key(r["task_key"])
            if dep_task:
                dep_task.due_date = datetime.fromisoformat(r["new_due_date"])
                self._repo.update_task(r["task_key"], dep_task)

    def _create_next_recurring_task(self, completed_task: Task) -> Task | None:
        """Create the next instance of a recurring task after completion."""
        if not completed_task.recurrence_rule:
            return None

        # Check end date
        if completed_task.recurrence_end_date and datetime.now(UTC) >= completed_task.recurrence_end_date:
            return None

        # Parse cron and compute next due date
        try:
            from croniter import croniter

            cron = croniter(completed_task.recurrence_rule, datetime.now(UTC))
            next_dt = cron.get_next(datetime)
        except Exception:
            return None

        new_task = Task(
            tenant_key=completed_task.tenant_key,
            name=completed_task.name,
            name_de=completed_task.name_de,
            instruction=completed_task.instruction,
            instruction_de=completed_task.instruction_de,
            category=completed_task.category,
            entity_key=completed_task.entity_key,
            entity_type=completed_task.entity_type,
            due_date=next_dt,
            scheduled_time=completed_task.scheduled_time,
            status="pending",
            priority=completed_task.priority,
            skill_level=completed_task.skill_level,
            stress_level=completed_task.stress_level,
            estimated_duration_minutes=completed_task.estimated_duration_minutes,
            requires_photo=completed_task.requires_photo,
            timer_duration_seconds=completed_task.timer_duration_seconds,
            timer_label=completed_task.timer_label,
            tags=list(completed_task.tags),
            checklist=[
                ChecklistItem(text=item.text, done=False, order=item.order) for item in completed_task.checklist
            ],
            assigned_to_user_key=completed_task.assigned_to_user_key,
            recurrence_rule=completed_task.recurrence_rule,
            recurrence_end_date=completed_task.recurrence_end_date,
            parent_recurring_task_key=completed_task.key,
        )
        return self._repo.create_task(new_task)

    def skip_task(self, key: str) -> Task:
        task = self.get_task(key)
        if task.status not in ("pending", "in_progress"):
            raise ValidationError(f"Cannot skip task in status '{task.status}'.")
        task.status = "skipped"
        task.completed_at = datetime.now(UTC)
        return self._repo.update_task(key, task)

    # ── Clone ──

    def clone_task(
        self,
        key: str,
        due_date_offset_days: int | None = None,
        target_entity_key: str | None = None,
        target_entity_type: str | None = None,
    ) -> Task:
        source = self.get_task(key)
        due_date = None
        if due_date_offset_days is not None:
            due_date = datetime.now(UTC) + timedelta(days=due_date_offset_days)

        entity_key = target_entity_key or source.entity_key
        entity_type = target_entity_type or source.entity_type

        new_task = Task(
            tenant_key=source.tenant_key,
            name=source.name,
            name_de=source.name_de,
            instruction=source.instruction,
            instruction_de=source.instruction_de,
            category=source.category,
            entity_key=entity_key,
            entity_type=entity_type,
            due_date=due_date,
            status="pending",
            priority=source.priority,
            skill_level=source.skill_level,
            stress_level=source.stress_level,
            estimated_duration_minutes=source.estimated_duration_minutes,
            requires_photo=source.requires_photo,
            timer_duration_seconds=source.timer_duration_seconds,
            timer_label=source.timer_label,
            tags=list(source.tags),
            checklist=[ChecklistItem(text=item.text, done=False, order=item.order) for item in source.checklist],
        )
        return self._repo.create_task(new_task)

    # ── Reopen ──

    def reopen_task(self, key: str) -> Task:
        task = self.get_task(key)
        if task.status not in ("completed", "skipped"):
            raise ValidationError(
                f"Cannot reopen task in status '{task.status}'. Only completed or skipped tasks can be reopened.",
            )
        task.reopened_from_status = task.status
        task.reopened_at = datetime.now(UTC)
        task.status = "pending"
        task.completed_at = None
        task.actual_duration_minutes = None
        task.completion_notes = None
        task.difficulty_rating = None
        task.quality_rating = None
        return self._repo.update_task(key, task)

    # ── Batch Operations ──

    def batch_status_change(
        self,
        task_keys: list[str],
        action: str,
        completion_notes: str | None = None,
    ) -> tuple[list[str], list[dict]]:
        succeeded: list[str] = []
        failed: list[dict] = []
        for tk in task_keys:
            try:
                if action == "start":
                    self.start_task(tk)
                elif action == "complete":
                    self.complete_task(tk, completion_notes=completion_notes)
                elif action == "skip":
                    self.skip_task(tk)
                else:
                    failed.append({"key": tk, "error": f"Unknown action: {action}"})
                    continue
                succeeded.append(tk)
            except (NotFoundError, ValidationError) as e:
                failed.append({"key": tk, "error": str(e)})
        return succeeded, failed

    def batch_delete(self, task_keys: list[str]) -> tuple[list[str], list[dict]]:
        succeeded: list[str] = []
        failed: list[dict] = []
        for tk in task_keys:
            try:
                self.delete_task(tk)
                succeeded.append(tk)
            except (NotFoundError, ValidationError) as e:
                failed.append({"key": tk, "error": str(e)})
        return succeeded, failed

    def batch_assign(
        self,
        task_keys: list[str],
        assigned_to_user_key: str,
    ) -> tuple[list[str], list[dict]]:
        succeeded: list[str] = []
        failed: list[dict] = []
        for tk in task_keys:
            try:
                task = self.get_task(tk)
                task.assigned_to_user_key = assigned_to_user_key
                self._repo.update_task(tk, task)
                succeeded.append(tk)
            except (NotFoundError, ValidationError) as e:
                failed.append({"key": tk, "error": str(e)})
        return succeeded, failed

    # ── Comments ──

    def list_comments(self, task_key: str) -> list[TaskComment]:
        self.get_task(task_key)  # ensure task exists
        return self._repo.get_comments_for_task(task_key)

    def create_comment(self, task_key: str, text: str, created_by: str) -> TaskComment:
        self.get_task(task_key)  # ensure task exists
        comment = TaskComment(
            task_key=task_key,
            comment_text=text,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        return self._repo.create_comment(comment)

    def update_comment(self, task_key: str, comment_key: str, text: str) -> TaskComment:
        self.get_task(task_key)  # ensure task exists
        comment = self._repo.get_comment_by_key(comment_key)
        if not comment:
            raise NotFoundError("TaskComment", comment_key)
        if comment.task_key != task_key:
            raise ValidationError("Comment does not belong to this task.")
        comment.comment_text = text
        comment.updated_at = datetime.now(UTC)
        return self._repo.update_comment(comment_key, comment)

    def delete_comment(self, task_key: str, comment_key: str) -> bool:
        self.get_task(task_key)  # ensure task exists
        comment = self._repo.get_comment_by_key(comment_key)
        if not comment:
            raise NotFoundError("TaskComment", comment_key)
        if comment.task_key != task_key:
            raise ValidationError("Comment does not belong to this task.")
        return self._repo.delete_comment(comment_key)

    # ── Audit / History ──

    def get_task_history(self, task_key: str) -> list[TaskAuditEntry]:
        self.get_task(task_key)  # ensure task exists
        return self._repo.get_audit_entries_for_task(task_key)

    def _record_audit(
        self,
        task_key: str,
        action: str,
        changed_by: str = "system",
        field: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> TaskAuditEntry:
        entry = TaskAuditEntry(
            task_key=task_key,
            changed_at=datetime.now(UTC),
            changed_by=changed_by,
            action=action,
            field=field,
            old_value=old_value,
            new_value=new_value,
        )
        return self._repo.create_audit_entry(entry)

    # ── Dormant Task Activation ──

    def activate_dormant_tasks_for_phase(self, plant_key: str, phase_name: str) -> list[Task]:
        """Activate dormant tasks whose trigger_phase matches the new phase."""
        dormant_tasks = self._repo.get_dormant_tasks_for_phase(plant_key, phase_name)
        activated: list[Task] = []
        now = datetime.now(UTC)
        for task in dormant_tasks:
            task.status = "pending"
            if task.trigger_phase and task.trigger_phase == phase_name:
                # For phase_entry triggers: due now
                # For days_after_phase: offset from now
                tt = self._repo.get_task_template_by_key(task.template_key or "")
                if tt and tt.trigger_type == "days_after_phase" and tt.days_offset:
                    task.due_date = now + timedelta(days=tt.days_offset)
                else:
                    task.due_date = now
            else:
                task.due_date = now
            updated = self._repo.update_task(task.key or "", task)
            activated.append(updated)
        return activated

    # ── Add Task to Workflow Execution ──

    def add_task_to_workflow_execution(self, execution_key: str, task: Task) -> Task:
        execution = self.get_workflow_execution(execution_key)
        task.workflow_execution_key = execution_key
        task.entity_key = task.entity_key or execution.entity_key
        task.entity_type = task.entity_type or execution.entity_type
        return self._repo.create_task(task)

    # ── Task Queue ──

    def get_task_queue(self, plant_key: str | None = None) -> list[Task]:
        if plant_key:
            tasks = self._repo.get_tasks_for_plant(plant_key, "pending")
        else:
            tasks, _ = self._repo.get_pending_tasks(0, 200)

        task_dicts = [
            {
                "key": t.key,
                "status": t.status,
                "priority": t.priority,
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
        """Convenience method for plant-specific task queries."""
        return self._repo.get_tasks_for_plant(plant_key, status)

    def get_tasks_for_entity(
        self,
        entity_type: str,
        entity_key: str,
        tenant_key: str,
        status: str | None = None,
    ) -> list[Task]:
        return self._repo.get_tasks_for_entity(entity_type, entity_key, tenant_key, status)

    # ── HST Validation ──

    def validate_hst(
        self,
        task_name: str,
        current_phase: str,
        recent_hst_tasks: list[dict],
        species_name: str = "",
    ) -> dict:
        return self._hst.validate(
            task_name,
            current_phase,
            recent_hst_tasks,
            species_name,
        )

    # ── Workflow Execution ──

    def get_workflow_execution(self, key: str) -> WorkflowExecution:
        we = self._repo.get_workflow_execution_by_key(key)
        if not we:
            raise NotFoundError("WorkflowExecution", key)
        return we

    def get_executions_for_template(self, template_key: str) -> list[dict]:
        return self._repo.get_executions_for_template(template_key)
