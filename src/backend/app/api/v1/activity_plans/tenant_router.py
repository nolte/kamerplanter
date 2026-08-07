"""Tenant-scoped write routes for the task templates of an activity plan (#992).

These two routes used to live on the *global* ``/activity-plans`` router, behind
nothing but ``Depends(get_current_user)``, and edited the repository directly
from the API layer. The document key was the entire authorisation: any
authenticated user of any tenant could retime, disable or delete any other
tenant's task template — and the seeded templates of a system workflow, where a
delete removes them for every tenant.

They are mounted under ``/t/{tenant_slug}/`` so a ``TenantContext`` exists to
anchor against at all, and they go through ``TaskService`` rather than the
repository, which restores the 5-layer boundary (NFR-001) the old version broke.
Ownership itself is resolved in the service, on the parent ``WorkflowTemplate``
— see ``TaskService._resolve_task_template_for_tenant_write`` for why that is the
only available anchor and what each refusal status means.

``POST /activity-plans/generate`` and ``/apply`` stay on the global router: they
are read-mostly plan generation over the global catalogue, and their own tenant
handling is a separate question from this one.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from app.api.v1.activity_plans.mapping import task_template_response
from app.api.v1.activity_plans.schemas import TaskTemplateResponse, TaskTemplateUpdateRequest
from app.common.auth import get_current_tenant
from app.common.dependencies import get_task_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService

router = APIRouter(
    prefix="/activity-plans",
    tags=["activity-plans"],
    responses=NOT_FOUND_RESPONSE,
)


@router.patch("/templates/{key}", response_model=TaskTemplateResponse)
def update_task_template(
    key: Annotated[str, Path(description="Document key of the task template.")],
    body: TaskTemplateUpdateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
) -> TaskTemplateResponse:
    """Update a single task template of a generated activity plan.

    Answers 404 when the template's parent workflow belongs to another tenant or
    does not exist, and 422 when it is a globally seeded system workflow.
    """
    updated = service.update_activity_plan_task_template(
        key,
        body.model_dump(exclude_none=True),
        tenant_key=ctx.tenant_key,
    )
    return task_template_response(updated)


@router.delete("/templates/{key}", status_code=204)
def delete_task_template(
    key: Annotated[str, Path(description="Document key of the task template.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: TaskService = Depends(get_task_service),
) -> Response:
    """Delete a single task template of a generated activity plan.

    Same refusals as the PATCH above: 404 for a foreign or unknown parent
    workflow, 422 for a system workflow whose templates every tenant shares.
    """
    service.delete_activity_plan_task_template(key, tenant_key=ctx.tenant_key)
    return Response(status_code=204)
