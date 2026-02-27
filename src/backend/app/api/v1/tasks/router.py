from fastapi import APIRouter, Depends, Query

from app.api.v1.tasks.schemas import (
    HSTValidateRequest,
    TaskCompleteRequest,
    TaskCreate,
    TaskResponse,
    TaskTemplateCreate,
    TaskTemplateResponse,
    TaskUpdate,
    WorkflowExecutionResponse,
    WorkflowInstantiateRequest,
    WorkflowTemplateCreate,
    WorkflowTemplateResponse,
)
from app.common.dependencies import get_task_service
from app.domain.models.task import Task, TaskTemplate, WorkflowTemplate
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
    service: TaskService = Depends(get_task_service),
):
    templates, _ = service.list_workflow_templates(offset, limit)
    return [_wf_response(wt) for wt in templates]


@router.post("/workflows", response_model=WorkflowTemplateResponse, status_code=201)
def create_workflow(body: WorkflowTemplateCreate, service: TaskService = Depends(get_task_service)):
    wt = WorkflowTemplate(**body.model_dump())
    created = service.create_workflow_template(wt)
    return _wf_response(created)


@router.get("/workflows/{key}", response_model=WorkflowTemplateResponse)
def get_workflow(key: str, service: TaskService = Depends(get_task_service)):
    return _wf_response(service.get_workflow_template(key))


@router.post("/workflows/{key}/instantiate", response_model=WorkflowExecutionResponse, status_code=201)
def instantiate_workflow(
    key: str, body: WorkflowInstantiateRequest, service: TaskService = Depends(get_task_service),
):
    execution = service.instantiate_workflow(key, body.plant_key)
    return _we_response(execution)


# ── Task Templates ──


@router.get("/workflows/{wf_key}/templates", response_model=list[TaskTemplateResponse])
def list_task_templates(wf_key: str, service: TaskService = Depends(get_task_service)):
    templates = service.get_task_templates(wf_key)
    return [_tt_response(tt) for tt in templates]


@router.post("/templates", response_model=TaskTemplateResponse, status_code=201)
def create_task_template(body: TaskTemplateCreate, service: TaskService = Depends(get_task_service)):
    tt = TaskTemplate(**body.model_dump())
    created = service.create_task_template(tt)
    return _tt_response(created)


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


@router.get("/{key}", response_model=TaskResponse)
def get_task(key: str, service: TaskService = Depends(get_task_service)):
    return _task_response(service.get_task(key))


@router.put("/{key}", response_model=TaskResponse)
def update_task(key: str, body: TaskUpdate, service: TaskService = Depends(get_task_service)):
    task = service.get_task(key)
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(task, field, value)
    from app.common.dependencies import get_task_repo
    updated = get_task_repo().update_task(key, task)
    return _task_response(updated)


@router.post("/{key}/start", response_model=TaskResponse)
def start_task(key: str, service: TaskService = Depends(get_task_service)):
    return _task_response(service.start_task(key))


@router.post("/{key}/complete", response_model=TaskResponse)
def complete_task(key: str, body: TaskCompleteRequest, service: TaskService = Depends(get_task_service)):
    return _task_response(service.complete_task(key, body.completion_notes, body.actual_duration_minutes))


@router.post("/{key}/skip", response_model=TaskResponse)
def skip_task(key: str, service: TaskService = Depends(get_task_service)):
    return _task_response(service.skip_task(key))


# ── Workflow Executions ──


@router.get("/executions/{key}", response_model=WorkflowExecutionResponse)
def get_workflow_execution(key: str, service: TaskService = Depends(get_task_service)):
    return _we_response(service.get_workflow_execution(key))
