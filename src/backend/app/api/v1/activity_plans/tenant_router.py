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

``POST /generate`` joined them here for #1003. The plan a caller reads is no
longer the same object for everybody: the generated plan stays a shared
template, and a tenant's first write materialises a private copy they work on
from then on. The lookup behind this route therefore has to know *whose* plan to
answer with, which a global route cannot tell it. ``POST /apply`` stays on the
global router — it takes its tenant from the request body, which is #1000's
defect and a separate change.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from app.api.v1.activity_plans.mapping import activity_plan_response, task_template_response
from app.api.v1.activity_plans.schemas import (
    ActivityPlanGenerateRequest,
    ActivityPlanResponse,
    TaskTemplateResponse,
    TaskTemplateUpdateRequest,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_activity_plan_service, get_task_repo, get_task_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.tenant_context import TenantContext
from app.domain.services.activity_plan_service import ActivityPlanService
from app.domain.services.task_service import TaskService

router = APIRouter(
    prefix="/activity-plans",
    tags=["activity-plans"],
    responses=NOT_FOUND_RESPONSE,
)


@router.post("/generate", response_model=ActivityPlanResponse)
def generate_plan(
    body: ActivityPlanGenerateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActivityPlanService = Depends(get_activity_plan_service),
    task_repo=Depends(get_task_repo),
) -> ActivityPlanResponse:
    """Return the caller's activity plan for a species, generating it if needed.

    Answers the caller's **private copy** once they have edited the plan, and the
    globally generated **shared template** until then (#1003) — the response's
    ``is_shared_template`` says which of the two arrived.

    ``force_regenerate`` always produces a plan owned by the caller's tenant: it
    is a write, and rebuilding the shared template in place would discard every
    other tenant's plan along with the caller's.
    """
    if body.force_regenerate:
        workflow = service.regenerate_for_species(
            species_key=body.species_key,
            lifecycle_key=body.lifecycle_key,
            growth_system=body.growth_system,
            skill_level=body.skill_level,
            tenant_key=ctx.tenant_key,
        )
    else:
        workflow = service.get_or_generate_for_species(
            species_key=body.species_key,
            lifecycle_key=body.lifecycle_key,
            growth_system=body.growth_system,
            skill_level=body.skill_level,
            tenant_key=ctx.tenant_key,
        )
    return activity_plan_response(workflow, task_repo=task_repo)


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
