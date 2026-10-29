"""Bed templates (REQ-053 §20.12, §21.7, §21.8 "Beetvorlage"; WP 7.8, #2474).

``GET /bed-templates`` answers the system templates and the tenant's own. The gate decides the caller's rank only
(read all roles, create and change from grower, delete lead only); whose row it is - the tenant's, a system one
(platform admin only) or another tenant's (404) - is decided in the service (§22.3 T-01..T-03).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.bed_templates.schemas import (
    BedTemplateCreate,
    BedTemplateResponse,
    BedTemplateUpdate,
    bed_template_to_response,
)
from app.common.auth import get_current_tenant, get_is_platform_admin, require_permission
from app.common.dependencies import get_bed_template_service
from app.common.openapi_responses import (
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)
from app.common.pagination import PaginationParams, get_pagination
from app.core.permissions import Action, ResourceType
from app.domain.models.tenant_context import TenantContext
from app.domain.services.bed_template_service import BedTemplateService

router = APIRouter(tags=["bed-templates"], responses=NOT_FOUND_RESPONSE)

_TEMPLATE_KEY = Annotated[str, Path(description="Document key of the bed template.")]


@router.get("/bed-templates", response_model=list[BedTemplateResponse])
def list_bed_templates(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> list[BedTemplateResponse]:
    """The system templates (standard sizes) and the tenant's own, by name (GP-FR-044, GP-FR-045)."""
    templates = service.list_templates(tenant_key=ctx.tenant_key, offset=pagination.offset, limit=pagination.limit)
    return [bed_template_to_response(template) for template in templates]


@router.post(
    "/bed-templates",
    response_model=BedTemplateResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def create_bed_template(
    body: BedTemplateCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.CREATE)),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> BedTemplateResponse:
    """Create a template of the tenant (from grower).

    `default_geometry` is in the bed frame (rect, circle or polygon; the anchor of the shape at the origin).
    422 `reference.not_found` when `location_type_key` or a `recurring_task_templates` key does not exist for the
    tenant, 422 `bed_template.not_a_bed_type` for a location type that is no bed type, 422
    `bed_template.quota_exceeded` at the tenant's ceiling.
    """
    created = service.create_template(tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role, data=body)
    return bed_template_to_response(created)


@router.patch(
    "/bed-templates/{key}",
    response_model=BedTemplateResponse,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def patch_bed_template(
    key: _TEMPLATE_KEY,
    body: BedTemplateUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.UPDATE)),
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> BedTemplateResponse:
    """Change the fields present (from grower); `height_m: null` clears the height.

    A system template can be changed by a platform admin only (403 for everybody else); another tenant's template
    answers 404.
    """
    updated = service.patch_template(
        key, tenant_key=ctx.tenant_key, role=ctx.role, patch=body, is_platform_admin=is_platform_admin
    )
    return bed_template_to_response(updated)


@router.delete(
    "/bed-templates/{key}",
    status_code=204,
    responses=FORBIDDEN_RESPONSE,
)
def delete_bed_template(
    key: _TEMPLATE_KEY,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.DELETE)),
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> None:
    """Delete a template (lead only). Beds placed from it keep their copy of the fields; their `template_key` is
    unset, since it would name nothing. A system template can be deleted by a platform admin only."""
    service.delete_template(key, tenant_key=ctx.tenant_key, role=ctx.role, is_platform_admin=is_platform_admin)
