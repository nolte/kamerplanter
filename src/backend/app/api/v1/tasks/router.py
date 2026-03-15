from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Response, UploadFile

from app.api.v1.tasks.schemas import (
    BatchAssignRequest,
    BatchDeleteRequest,
    BatchResponse,
    BatchResultItem,
    BatchStatusRequest,
    HSTValidateRequest,
    PhotoUploadResponse,
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
    WorkflowTemplateCreate,
    WorkflowTemplateResponse,
    WorkflowTemplateUpdate,
)
from app.common.dependencies import get_task_service
from app.config.settings import settings
from app.domain.models.task import Task, TaskTemplate, WorkflowTemplate

if TYPE_CHECKING:
    from app.domain.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _wf_response(wt: WorkflowTemplate) -> WorkflowTemplateResponse:
    return WorkflowTemplateResponse(key=wt.key or "", **wt.model_dump(exclude={"key"}))


def _tt_response(tt: TaskTemplate) -> TaskTemplateResponse:
    return TaskTemplateResponse(key=tt.key or "", **tt.model_dump(exclude={"key"}))


def _task_response(t: Task) -> TaskResponse:
    return TaskResponse(key=t.key or "", **t.model_dump(exclude={"key"}))


def _we_response(we) -> WorkflowExecutionResponse:
    return WorkflowExecutionResponse(key=we.key or "", **we.model_dump(exclude={"key"}))


# ── Workflow Templates ──


@router.get("/workflows", response_model=list[WorkflowTemplateResponse])
def list_workflows(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    species_key: str | None = Query(None),
    service: TaskService = Depends(get_task_service),
):
    templates, _ = service.list_workflow_templates(offset, limit, species_key=species_key)
    # Enrich with species names and plant counts
    wf_keys = [wt.key for wt in templates if wt.key]
    usage_map = service.get_workflow_usage_stats(wf_keys) if wf_keys else {}
    result = []
    for wt in templates:
        resp = _wf_response(wt)
        stats = usage_map.get(wt.key or "", {})
        resp.species_name = stats.get("species_name", "")
        resp.assigned_plant_count = stats.get("plant_count", 0)
        result.append(resp)
    return result


@router.post("/workflows", response_model=WorkflowTemplateResponse, status_code=201)
def create_workflow(body: WorkflowTemplateCreate, service: TaskService = Depends(get_task_service)):
    wt = WorkflowTemplate(**body.model_dump())
    created = service.create_workflow_template(wt)
    return _wf_response(created)


@router.get("/workflows/{key}", response_model=WorkflowTemplateResponse)
def get_workflow(key: str, service: TaskService = Depends(get_task_service)):
    return _wf_response(service.get_workflow_template(key))


@router.put("/workflows/{key}", response_model=WorkflowTemplateResponse)
def update_workflow(key: str, body: WorkflowTemplateUpdate, service: TaskService = Depends(get_task_service)):
    data = body.model_dump(exclude_none=True)
    updated = service.update_workflow_template(key, data)
    return _wf_response(updated)


@router.delete("/workflows/{key}", status_code=204)
def delete_workflow(key: str, service: TaskService = Depends(get_task_service)):
    service.delete_workflow_template(key)
    return Response(status_code=204)


@router.post("/workflows/{key}/duplicate", response_model=WorkflowTemplateResponse, status_code=201)
def duplicate_workflow(
    key: str,
    name: str = Query(..., min_length=1, max_length=200),
    service: TaskService = Depends(get_task_service),
):
    duplicated = service.duplicate_workflow_template(key, name)
    return _wf_response(duplicated)


@router.post("/workflows/{key}/instantiate", response_model=WorkflowExecutionResponse, status_code=201)
def instantiate_workflow(
    key: str,
    body: WorkflowInstantiateRequest,
    service: TaskService = Depends(get_task_service),
):
    execution = service.instantiate_workflow(key, body.plant_key)
    return _we_response(execution)


# ── Task Templates ──


@router.get("/workflows/{wf_key}/templates", response_model=list[TaskTemplateResponse])
def list_task_templates(wf_key: str, service: TaskService = Depends(get_task_service)):
    templates = service.get_task_templates(wf_key)
    return [_tt_response(tt) for tt in templates]


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


@router.post("/templates", response_model=TaskTemplateResponse, status_code=201)
def create_task_template(body: TaskTemplateCreate, service: TaskService = Depends(get_task_service)):
    data = body.model_dump()
    # Map ActivityCategory values to TaskCategory if needed
    cat = data.get("category", "")
    if cat in _ACTIVITY_TO_TASK_CATEGORY:
        data["category"] = _ACTIVITY_TO_TASK_CATEGORY[cat]
    tt = TaskTemplate(**data)
    created = service.create_task_template(tt)
    return _tt_response(created)


@router.get("/templates/{key}", response_model=TaskTemplateResponse)
def get_task_template(key: str, service: TaskService = Depends(get_task_service)):
    return _tt_response(service.get_task_template(key))


@router.put("/templates/{key}", response_model=TaskTemplateResponse)
def update_task_template(key: str, body: TaskTemplateUpdate, service: TaskService = Depends(get_task_service)):
    data = body.model_dump(exclude_none=True)
    updated = service.update_task_template(key, data)
    return _tt_response(updated)


@router.delete("/templates/{key}", status_code=204)
def delete_task_template(key: str, service: TaskService = Depends(get_task_service)):
    service.delete_task_template(key)
    return Response(status_code=204)


# ── Tasks ──


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    plant_key: str | None = None,
    category: str | None = None,
    service: TaskService = Depends(get_task_service),
):
    filters: dict[str, str] = {}
    if status:
        filters["status"] = status
    if plant_key:
        filters["plant_key"] = plant_key
    if category:
        filters["category"] = category
    tasks, _ = service.list_tasks(offset, limit, filters or None)
    return [_task_response(t) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate, service: TaskService = Depends(get_task_service)):
    task = Task(**body.model_dump())
    created = service.create_task(task)
    return _task_response(created)


@router.get("/queue", response_model=list[TaskResponse])
def get_task_queue(
    plant_key: str | None = None,
    service: TaskService = Depends(get_task_service),
):
    tasks = service.get_task_queue(plant_key)
    return [_task_response(t) for t in tasks]


@router.post("/generate-care-reminders")
def generate_care_reminders_now():
    """Manually trigger care reminder task generation (same as daily Celery beat)."""
    from app.tasks.care_tasks import generate_due_care_reminders

    result = generate_due_care_reminders()
    return result


@router.get("/overdue", response_model=list[TaskResponse])
def get_overdue_tasks(service: TaskService = Depends(get_task_service)):
    tasks = service.get_overdue_tasks()
    return [_task_response(t) for t in tasks]


@router.get("/plants/{plant_key}", response_model=list[TaskResponse])
def get_tasks_for_plant(
    plant_key: str,
    status: str | None = None,
    service: TaskService = Depends(get_task_service),
):
    tasks = service.get_tasks_for_plant(plant_key, status)
    return [_task_response(t) for t in tasks]


@router.post("/validate-hst")
def validate_hst(body: HSTValidateRequest, service: TaskService = Depends(get_task_service)):
    return service.validate_hst(body.task_name, body.current_phase, body.recent_hst_tasks, body.species_name)


# ── Batch Operations (MUST be before /{key} to avoid path collision) ──


@router.post("/batch/status", response_model=BatchResponse)
def batch_status_change(body: BatchStatusRequest, service: TaskService = Depends(get_task_service)):
    succeeded, failed = service.batch_status_change(body.task_keys, body.action, body.completion_notes)
    return BatchResponse(
        succeeded=succeeded,
        failed=[BatchResultItem(key=f["key"], error=f["error"]) for f in failed],
    )


@router.post("/batch/delete", response_model=BatchResponse)
def batch_delete(body: BatchDeleteRequest, service: TaskService = Depends(get_task_service)):
    succeeded, failed = service.batch_delete(body.task_keys)
    return BatchResponse(
        succeeded=succeeded,
        failed=[BatchResultItem(key=f["key"], error=f["error"]) for f in failed],
    )


@router.post("/batch/assign", response_model=BatchResponse)
def batch_assign(body: BatchAssignRequest, service: TaskService = Depends(get_task_service)):
    succeeded, failed = service.batch_assign(body.task_keys, body.assigned_to_user_key)
    return BatchResponse(
        succeeded=succeeded,
        failed=[BatchResultItem(key=f["key"], error=f["error"]) for f in failed],
    )


@router.get("/{key}", response_model=TaskResponse)
def get_task(key: str, service: TaskService = Depends(get_task_service)):
    return _task_response(service.get_task(key))


@router.delete("/{key}", status_code=204)
def delete_task(key: str, service: TaskService = Depends(get_task_service)):
    service.delete_task(key)
    return Response(status_code=204)


@router.put("/{key}", response_model=TaskResponse)
def update_task(key: str, body: TaskUpdate, service: TaskService = Depends(get_task_service)):
    task = service.get_task(key)
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(task, field, value)
    updated = service._repo.update_task(key, task)
    return _task_response(updated)


@router.post("/{key}/start", response_model=TaskResponse)
def start_task(key: str, service: TaskService = Depends(get_task_service)):
    return _task_response(service.start_task(key))


@router.post("/{key}/photos", response_model=PhotoUploadResponse, status_code=201)
async def upload_task_photo(key: str, file: UploadFile, service: TaskService = Depends(get_task_service)):
    service.get_task(key)  # ensure task exists
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{key}_{file.filename}"
    file_path = upload_dir / safe_name
    content = await file.read()
    file_path.write_bytes(content)
    url = f"/uploads/tasks/{safe_name}"
    service.add_photo_ref(key, url)
    return PhotoUploadResponse(url=url, filename=safe_name, size_bytes=len(content))


@router.post("/{key}/complete", response_model=TaskResponse)
def complete_task(key: str, body: TaskCompleteRequest, service: TaskService = Depends(get_task_service)):
    completed = service.complete_task(
        key,
        body.completion_notes,
        body.actual_duration_minutes,
        body.photo_refs or None,
        body.difficulty_rating,
        body.quality_rating,
    )

    # Auto-create next watering task if this was a care:watering task
    if (
        completed.category == "care_reminder"
        and completed.name
        and completed.name.startswith("care:watering")
        and completed.plant_key
    ):
        from app.common.dependencies import get_care_reminder_service

        care_service = get_care_reminder_service()
        profile = care_service._repo.get_profile_by_plant_key(completed.plant_key)
        if profile is not None and profile.auto_create_watering_task:
            care_service.ensure_next_watering_task(profile)

    return _task_response(completed)


@router.post("/{key}/skip", response_model=TaskResponse)
def skip_task(key: str, service: TaskService = Depends(get_task_service)):
    skipped = service.skip_task(key)

    # Record a CareConfirmation so the reminder interval resets from today
    if skipped.category == "care_reminder" and skipped.plant_key:
        from datetime import UTC, datetime

        from app.common.dependencies import get_care_reminder_service
        from app.common.enums import ConfirmAction, ReminderType
        from app.domain.models.care_reminder import CareConfirmation

        care_service = get_care_reminder_service()
        profile = care_service._repo.get_profile_by_plant_key(skipped.plant_key)
        if profile is not None:
            # Derive reminder type from task name suffix ("… — fertilizing")
            rt_match = None
            for rt in ReminderType:
                if skipped.name and skipped.name.endswith(f"\u2014 {rt.value}"):
                    rt_match = rt
                    break
            if rt_match is not None:
                confirmation = CareConfirmation(
                    plant_key=skipped.plant_key,
                    care_profile_key=profile.key or "",
                    reminder_type=rt_match,
                    action=ConfirmAction.SKIPPED,
                    confirmed_at=datetime.now(UTC),
                    task_key=skipped.key,
                    interval_at_time=care_service._engine._get_interval_days(profile, rt_match),
                )
                created_conf = care_service._repo.create_confirmation(confirmation)
                if created_conf.key and profile.key:
                    care_service._repo.create_confirmation_edges(
                        created_conf.key,
                        profile.key,
                        skipped.plant_key,
                    )

    return _task_response(skipped)


@router.post("/{key}/clone", response_model=TaskResponse, status_code=201)
def clone_task(key: str, body: TaskCloneRequest, service: TaskService = Depends(get_task_service)):
    cloned = service.clone_task(key, body.target_plant_key, body.due_date_offset_days)
    return _task_response(cloned)


@router.post("/{key}/reopen", response_model=TaskResponse)
def reopen_task(key: str, body: TaskReopenRequest | None = None, service: TaskService = Depends(get_task_service)):
    return _task_response(service.reopen_task(key))


# ── Comments ──


@router.get("/{task_key}/comments", response_model=list[TaskCommentResponse])
def list_task_comments(task_key: str, service: TaskService = Depends(get_task_service)):
    comments = service.list_comments(task_key)
    return [TaskCommentResponse(key=c.key or "", **c.model_dump(exclude={"key"})) for c in comments]


@router.post("/{task_key}/comments", response_model=TaskCommentResponse, status_code=201)
def create_task_comment(
    task_key: str,
    body: TaskCommentCreate,
    service: TaskService = Depends(get_task_service),
):
    comment = service.create_comment(task_key, body.comment_text, created_by="system")
    return TaskCommentResponse(key=comment.key or "", **comment.model_dump(exclude={"key"}))


@router.put("/{task_key}/comments/{comment_key}", response_model=TaskCommentResponse)
def update_task_comment(
    task_key: str,
    comment_key: str,
    body: TaskCommentUpdate,
    service: TaskService = Depends(get_task_service),
):
    comment = service.update_comment(task_key, comment_key, body.comment_text)
    return TaskCommentResponse(key=comment.key or "", **comment.model_dump(exclude={"key"}))


@router.delete("/{task_key}/comments/{comment_key}", status_code=204)
def delete_task_comment(
    task_key: str,
    comment_key: str,
    service: TaskService = Depends(get_task_service),
):
    service.delete_comment(task_key, comment_key)
    return Response(status_code=204)


# ── Audit / History ──


@router.get("/{task_key}/history", response_model=list[TaskAuditEntryResponse])
def get_task_history(task_key: str, service: TaskService = Depends(get_task_service)):
    entries = service.get_task_history(task_key)
    return [TaskAuditEntryResponse(key=e.key or "", **e.model_dump(exclude={"key"})) for e in entries]


# ── Workflow Executions ──


@router.get("/executions/{key}", response_model=WorkflowExecutionResponse)
def get_workflow_execution(key: str, service: TaskService = Depends(get_task_service)):
    return _we_response(service.get_workflow_execution(key))


@router.post("/executions/{key}/tasks", response_model=TaskResponse, status_code=201)
def add_task_to_workflow(
    key: str,
    body: WorkflowAddTaskRequest,
    service: TaskService = Depends(get_task_service),
):
    task = Task(**body.model_dump())
    created = service.add_task_to_workflow_execution(key, task)
    return _task_response(created)
