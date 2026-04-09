from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.tasks.schemas import (
    BatchAssignRequest,
    BatchDeleteRequest,
    BatchResponse,
    BatchResultItem,
    BatchStatusRequest,
    HSTValidateRequest,
    PhaseReorderRequest,
    TaskAuditEntryResponse,
    TaskCloneRequest,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskCommentUpdate,
    TaskCompleteRequest,
    TaskCreate,
    TaskReopenRequest,
    TaskResponse,
    TaskTemplateCreate,
    TaskTemplateResponse,
    TaskTemplateUpdate,
    TaskUpdate,
    WorkflowAddTaskRequest,
    WorkflowExecutionResponse,
    WorkflowInstantiateRequest,
    WorkflowPhaseCreate,
    WorkflowPhaseResponse,
    WorkflowPhaseSuggestion,
    WorkflowPhaseUpdate,
    WorkflowTemplateCreate,
    WorkflowTemplateResponse,
    WorkflowTemplateUpdate,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_task_service
from app.domain.models.task import Task, TaskTemplate, WorkflowPhase, WorkflowTemplate
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _wf_response(wt: WorkflowTemplate) -> WorkflowTemplateResponse:
    return WorkflowTemplateResponse(key=wt.key or "", **wt.model_dump(exclude={"key"}))


def _tt_response(tt: TaskTemplate) -> TaskTemplateResponse:
    return TaskTemplateResponse(key=tt.key or "", **tt.model_dump(exclude={"key"}))


def _phase_response(p: WorkflowPhase) -> WorkflowPhaseResponse:
    return WorkflowPhaseResponse(key=p.key or "", **p.model_dump(exclude={"key"}))


def _task_response(t: Task) -> TaskResponse:
    return TaskResponse(key=t.key or "", **t.model_dump(exclude={"key"}))


def _we_response(we) -> WorkflowExecutionResponse:
    return WorkflowExecutionResponse(key=we.key or "", **we.model_dump(exclude={"key"}))


_ACTIVITY_TO_TASK_CATEGORY: dict[str, str] = {
    "training_hst": "training",
    "training_lst": "training",
    "pruning": "pruning",
    "ausgeizen": "ausgeizen",
    "transplant": "transplant",
    "harvest_prep": "harvest",
    "propagation": "maintenance",
    "inspection": "observation",
    "general": "maintenance",
}


# ── Workflow Templates ──


@router.get("/workflows", response_model=list[WorkflowTemplateResponse])
def list_workflows(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    species_key: str | None = Query(None),
    target_entity_type: str | None = Query(None),
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    templates, _ = service.list_workflow_templates(
        offset,
        limit,
        species_key=species_key,
        tenant_key=ctx.tenant_key,
        target_entity_type=target_entity_type,
    )
    wf_keys = [wt.key for wt in templates if wt.key]
    usage_map = service.get_workflow_usage_stats(wf_keys) if wf_keys else {}
    result = []
    for wt in templates:
        resp = _wf_response(wt)
        stats = usage_map.get(wt.key or "", {})
        resp.species_name = stats.get("species_name", "")
        resp.assigned_entity_count = stats.get("entity_count", 0)
        result.append(resp)
    return result


@router.post("/workflows", response_model=WorkflowTemplateResponse, status_code=201)
def create_workflow(
    body: WorkflowTemplateCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    wt = WorkflowTemplate(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_workflow_template(wt)
    return _wf_response(created)


@router.get("/workflows/{key}", response_model=WorkflowTemplateResponse)
def get_workflow(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return _wf_response(service.get_workflow_template(key, tenant_key=ctx.tenant_key))


@router.put("/workflows/{key}", response_model=WorkflowTemplateResponse)
def update_workflow(
    key: str,
    body: WorkflowTemplateUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_workflow_template(key, data)
    return _wf_response(updated)


@router.delete("/workflows/{key}", status_code=204)
def delete_workflow(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(key, tenant_key=ctx.tenant_key)
    service.delete_workflow_template(key)
    return Response(status_code=204)


@router.post("/workflows/{key}/duplicate", response_model=WorkflowTemplateResponse, status_code=201)
def duplicate_workflow(
    key: str,
    name: str = Query(..., min_length=1, max_length=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(key, tenant_key=ctx.tenant_key)
    duplicated = service.duplicate_workflow_template(key, name)
    return _wf_response(duplicated)


@router.get("/workflows/{key}/executions")
def list_workflow_executions(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(key, tenant_key=ctx.tenant_key)
    return service.get_executions_for_template(key)


@router.post("/workflows/{key}/instantiate", response_model=WorkflowExecutionResponse, status_code=201)
def instantiate_workflow(
    key: str,
    body: WorkflowInstantiateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(key, tenant_key=ctx.tenant_key)
    execution = service.instantiate_workflow(
        key,
        entity_key=body.entity_key,
        entity_type=body.entity_type,
    )
    return _we_response(execution)


# ── Workflow Phases ──


@router.get("/workflows/{wf_key}/phases", response_model=list[WorkflowPhaseResponse])
def list_workflow_phases(
    wf_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(wf_key, tenant_key=ctx.tenant_key)
    return [_phase_response(p) for p in service.get_workflow_phases(wf_key)]


@router.post("/workflows/{wf_key}/phases", response_model=WorkflowPhaseResponse, status_code=201)
def create_workflow_phase(
    wf_key: str,
    body: WorkflowPhaseCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(wf_key, tenant_key=ctx.tenant_key)
    phase = WorkflowPhase(**body.model_dump(), workflow_template_key=wf_key)
    return _phase_response(service.create_workflow_phase(phase))


@router.get("/phases/suggestions", response_model=list[WorkflowPhaseSuggestion])
def list_phase_suggestions(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return service.get_phase_suggestions()


@router.put("/phases/reorder", response_model=list[WorkflowPhaseResponse])
def reorder_phases(
    body: PhaseReorderRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return [_phase_response(p) for p in service.reorder_workflow_phases([item.model_dump() for item in body.phases])]


@router.put("/phases/{key}", response_model=WorkflowPhaseResponse)
def update_workflow_phase(
    key: str,
    body: WorkflowPhaseUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    phase = service.get_workflow_phase(key)
    service.get_workflow_template(phase.workflow_template_key, tenant_key=ctx.tenant_key)
    return _phase_response(service.update_workflow_phase(key, body.model_dump(exclude_none=True)))


@router.delete("/phases/{key}", status_code=204)
def delete_workflow_phase(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    phase = service.get_workflow_phase(key)
    service.get_workflow_template(phase.workflow_template_key, tenant_key=ctx.tenant_key)
    service.delete_workflow_phase(key)
    return Response(status_code=204)


# ── Task Templates ──


@router.get("/workflows/{wf_key}/templates", response_model=list[TaskTemplateResponse])
def list_task_templates(
    wf_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_workflow_template(wf_key, tenant_key=ctx.tenant_key)
    templates = service.get_task_templates(wf_key)
    return [_tt_response(tt) for tt in templates]


@router.post("/templates", response_model=TaskTemplateResponse, status_code=201)
def create_task_template(
    body: TaskTemplateCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    data = body.model_dump()
    cat = data.get("category", "")
    if cat in _ACTIVITY_TO_TASK_CATEGORY:
        data["category"] = _ACTIVITY_TO_TASK_CATEGORY[cat]
    tt = TaskTemplate(**data)
    created = service.create_task_template(tt)
    return _tt_response(created)


@router.get("/templates/{key}", response_model=TaskTemplateResponse)
def get_task_template(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return _tt_response(service.get_task_template(key))


@router.put("/templates/{key}", response_model=TaskTemplateResponse)
def update_task_template(
    key: str,
    body: TaskTemplateUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_task_template(key, data)
    return _tt_response(updated)


@router.delete("/templates/{key}", status_code=204)
def delete_task_template(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.delete_task_template(key)
    return Response(status_code=204)


# ── Tasks ──


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    category: str | None = None,
    entity_type: str | None = None,
    entity_key: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    filters: dict[str, str] = {}
    if status:
        filters["status"] = status
    if category:
        filters["category"] = category
    if entity_type:
        filters["entity_type"] = entity_type
    if entity_key:
        filters["entity_key"] = entity_key
    tasks, _ = service.list_tasks(offset, limit, filters or None, tenant_key=ctx.tenant_key)
    return [_task_response(t) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    body: TaskCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    task = Task(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_task(task)
    return _task_response(created)


@router.get("/queue", response_model=list[TaskResponse])
def get_task_queue(
    plant_key: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    tasks = service.get_task_queue(plant_key)
    return [_task_response(t) for t in tasks]


@router.post("/generate-care-reminders")
def generate_care_reminders_now(
    ctx: TenantContext = Depends(get_current_tenant),
):
    """Manually trigger care reminder task generation (same as daily Celery beat)."""
    from app.tasks.care_tasks import generate_due_care_reminders

    result = generate_due_care_reminders()
    return result


@router.get("/overdue", response_model=list[TaskResponse])
def get_overdue_tasks(
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    tasks = service.get_overdue_tasks()
    return [_task_response(t) for t in tasks]


@router.get("/plants/{plant_key}", response_model=list[TaskResponse])
def get_tasks_for_plant(
    plant_key: str,
    status: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    tasks = service.get_tasks_for_plant(plant_key, status)
    return [_task_response(t) for t in tasks]


@router.post("/validate-hst")
def validate_hst(
    body: HSTValidateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return service.validate_hst(body.task_name, body.current_phase, body.recent_hst_tasks, body.species_name)


@router.post("/batch/status", response_model=BatchResponse)
def batch_status_change(
    body: BatchStatusRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    succeeded, failed = service.batch_status_change(body.task_keys, body.action, body.completion_notes)
    return BatchResponse(succeeded=succeeded, failed=[BatchResultItem(key=f["key"], error=f["error"]) for f in failed])


@router.post("/batch/delete", response_model=BatchResponse)
def batch_delete(
    body: BatchDeleteRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    succeeded, failed = service.batch_delete(body.task_keys)
    return BatchResponse(succeeded=succeeded, failed=[BatchResultItem(key=f["key"], error=f["error"]) for f in failed])


@router.post("/batch/assign", response_model=BatchResponse)
def batch_assign(
    body: BatchAssignRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    succeeded, failed = service.batch_assign(body.task_keys, body.assigned_to_user_key)
    return BatchResponse(succeeded=succeeded, failed=[BatchResultItem(key=f["key"], error=f["error"]) for f in failed])


@router.get("/{key}", response_model=TaskResponse)
def get_task(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return _task_response(service.get_task(key, tenant_key=ctx.tenant_key))


@router.delete("/{key}", status_code=204)
def delete_task(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(key, tenant_key=ctx.tenant_key)
    service.delete_task(key)
    return Response(status_code=204)


@router.put("/{key}", response_model=TaskResponse)
def update_task(
    key: str,
    body: TaskUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    task = service.get_task(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(task, field, value)
    updated = service._repo.update_task(key, task)
    return _task_response(updated)


@router.post("/{key}/start", response_model=TaskResponse)
def start_task(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(key, tenant_key=ctx.tenant_key)
    return _task_response(service.start_task(key))


@router.post("/{key}/complete", response_model=TaskResponse)
def complete_task(
    key: str,
    body: TaskCompleteRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(key, tenant_key=ctx.tenant_key)
    completed = service.complete_task(
        key,
        body.completion_notes,
        body.actual_duration_minutes,
        body.photo_refs or None,
        body.difficulty_rating,
        body.quality_rating,
    )
    if completed.category == "care_reminder" and completed.entity_type == "plant_instance" and completed.entity_key:
        from datetime import UTC, datetime

        from app.common.dependencies import get_care_reminder_service
        from app.common.enums import ConfirmAction, ReminderType
        from app.domain.models.care_reminder import CareConfirmation

        care_service = get_care_reminder_service()
        profile = care_service._repo.get_profile_by_plant_key(completed.entity_key)
        if profile is not None:
            rt_match = None
            for rt in ReminderType:
                if completed.name and completed.name.endswith(f"\u2014 {rt.value}"):
                    rt_match = rt
                    break
            if rt_match is not None:
                confirmation = CareConfirmation(
                    plant_key=completed.entity_key,
                    care_profile_key=profile.key or "",
                    reminder_type=rt_match,
                    action=ConfirmAction.CONFIRMED,
                    confirmed_at=datetime.now(UTC),
                    task_key=completed.key,
                    notes=completed.completion_notes,
                    interval_at_time=care_service._engine._get_interval_days(profile, rt_match),
                )
                created_conf = care_service._repo.create_confirmation(confirmation)
                if created_conf.key and profile.key:
                    care_service._repo.create_confirmation_edges(
                        created_conf.key,
                        profile.key,
                        completed.entity_key,
                    )
                care_service.complete_care_task_with_log(
                    completed.key or "",
                    completed.entity_key,
                    rt_match,
                )
            if rt_match == ReminderType.WATERING and profile.auto_create_watering_task:
                phase_interval = care_service._get_phase_watering_interval(completed.entity_key)
                care_service.ensure_next_watering_task(profile, phase_watering_interval=phase_interval)
    return _task_response(completed)


@router.post("/{key}/skip", response_model=TaskResponse)
def skip_task(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(key, tenant_key=ctx.tenant_key)
    skipped = service.skip_task(key)
    if skipped.category == "care_reminder" and skipped.entity_type == "plant_instance" and skipped.entity_key:
        from datetime import UTC, datetime

        from app.common.dependencies import get_care_reminder_service
        from app.common.enums import ConfirmAction, ReminderType
        from app.domain.models.care_reminder import CareConfirmation

        care_service = get_care_reminder_service()
        profile = care_service._repo.get_profile_by_plant_key(skipped.entity_key)
        if profile is not None:
            rt_match = None
            for rt in ReminderType:
                if skipped.name and skipped.name.endswith(f"\u2014 {rt.value}"):
                    rt_match = rt
                    break
            if rt_match is not None:
                confirmation = CareConfirmation(
                    plant_key=skipped.entity_key,
                    care_profile_key=profile.key or "",
                    reminder_type=rt_match,
                    action=ConfirmAction.SKIPPED,
                    confirmed_at=datetime.now(UTC),
                    task_key=skipped.key,
                    interval_at_time=care_service._engine._get_interval_days(profile, rt_match),
                )
                created_conf = care_service._repo.create_confirmation(confirmation)
                if created_conf.key and profile.key:
                    care_service._repo.create_confirmation_edges(created_conf.key, profile.key, skipped.entity_key)
    return _task_response(skipped)


@router.post("/{key}/clone", response_model=TaskResponse, status_code=201)
def clone_task(
    key: str,
    body: TaskCloneRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(key, tenant_key=ctx.tenant_key)
    cloned = service.clone_task(
        key,
        due_date_offset_days=body.due_date_offset_days,
        target_entity_key=body.target_entity_key,
        target_entity_type=body.target_entity_type,
    )
    return _task_response(cloned)


@router.post("/{key}/reopen", response_model=TaskResponse)
def reopen_task(
    key: str,
    body: TaskReopenRequest | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(key, tenant_key=ctx.tenant_key)
    return _task_response(service.reopen_task(key))


@router.get("/{task_key}/comments", response_model=list[TaskCommentResponse])
def list_task_comments(
    task_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(task_key, tenant_key=ctx.tenant_key)
    comments = service.list_comments(task_key)
    return [TaskCommentResponse(key=c.key or "", **c.model_dump(exclude={"key"})) for c in comments]


@router.post("/{task_key}/comments", response_model=TaskCommentResponse, status_code=201)
def create_task_comment(
    task_key: str,
    body: TaskCommentCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(task_key, tenant_key=ctx.tenant_key)
    comment = service.create_comment(task_key, body.comment_text, created_by=ctx.user_key)
    return TaskCommentResponse(key=comment.key or "", **comment.model_dump(exclude={"key"}))


@router.put("/{task_key}/comments/{comment_key}", response_model=TaskCommentResponse)
def update_task_comment(
    task_key: str,
    comment_key: str,
    body: TaskCommentUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(task_key, tenant_key=ctx.tenant_key)
    comment = service.update_comment(task_key, comment_key, body.comment_text)
    return TaskCommentResponse(key=comment.key or "", **comment.model_dump(exclude={"key"}))


@router.delete("/{task_key}/comments/{comment_key}", status_code=204)
def delete_task_comment(
    task_key: str,
    comment_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(task_key, tenant_key=ctx.tenant_key)
    service.delete_comment(task_key, comment_key)
    return Response(status_code=204)


@router.get("/{task_key}/history", response_model=list[TaskAuditEntryResponse])
def get_task_history(
    task_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    service.get_task(task_key, tenant_key=ctx.tenant_key)
    entries = service.get_task_history(task_key)
    return [TaskAuditEntryResponse(key=e.key or "", **e.model_dump(exclude={"key"})) for e in entries]


@router.get("/executions/{key}", response_model=WorkflowExecutionResponse)
def get_workflow_execution(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    return _we_response(service.get_workflow_execution(key))


@router.post("/executions/{key}/tasks", response_model=TaskResponse, status_code=201)
def add_task_to_workflow(
    key: str,
    body: WorkflowAddTaskRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
):
    task = Task(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.add_task_to_workflow_execution(key, task)
    return _task_response(created)
