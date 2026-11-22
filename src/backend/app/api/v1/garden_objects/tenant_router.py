"""Single-resource CRUD of garden objects (REQ-053 §21.2, GP-API-013).

The batch (``POST /sites/{key}/plan/batch``) is the main way to change the plan; these routes are the
one-object shortcut and run through the same rules as a one-operation batch: containment (V-03), the lock
(GP-FR-032), the quota, the revision bump. Ownership is resolved in the service through the object's site
(§22.3 T-01/T-04) — ``site_key`` is the path's or the stored document's, never the body's.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.garden_objects.schemas import (
    GardenObjectCreate,
    GardenObjectResponse,
    garden_object_to_response,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_garden_resource_service
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)
from app.core.permissions import Action, ResourceType
from app.domain.models.garden_plan import CreateGardenObjectData, GardenObjectPatch
from app.domain.models.tenant_context import TenantContext
from app.domain.services.garden_resource_service import GardenResourceService

router = APIRouter(tags=["garden-objects"], responses=NOT_FOUND_RESPONSE)

_SITE_KEY = Annotated[str, Path(description="Document key of the site.")]
_OBJECT_KEY = Annotated[str, Path(description="Document key of the garden object.")]


@router.get("/sites/{key}/garden-objects", response_model=list[GardenObjectResponse])
def list_garden_objects(
    key: _SITE_KEY,
    ctx: TenantContext = Depends(get_current_tenant),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> list[GardenObjectResponse]:
    """Every garden object of a site, in drawing order (GP-API-013)."""
    return [garden_object_to_response(item) for item in service.list_garden_objects(key, tenant_key=ctx.tenant_key)]


@router.post(
    "/sites/{key}/garden-objects",
    response_model=GardenObjectResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
def create_garden_object(
    key: _SITE_KEY,
    body: GardenObjectCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.GARDEN_OBJECT, Action.CREATE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> GardenObjectResponse:
    """Create an object on the site (GP-API-013). Raises the site's ``plan_revision``.

    422 ``geometry.outside_parent`` (V-03) when it lies outside its parent or the garden boundary and is not
    ``off_site``; 422 ``reference.not_found`` for an unknown ``parent_location_key``.
    """
    data = CreateGardenObjectData(
        object_type=body.object_type,
        label=body.label,
        geometry=body.geometry,
        props=body.props.model_dump(mode="json"),
        parent_location_key=body.parent_location_key,
        off_site=body.off_site,
        locked=body.locked,
        z_order=body.z_order,
        notes=body.notes,
    )
    created = service.create_garden_object(
        key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role, data=data
    )
    return garden_object_to_response(created)


@router.get("/garden-objects/{key}", response_model=GardenObjectResponse)
def get_garden_object(
    key: _OBJECT_KEY,
    ctx: TenantContext = Depends(get_current_tenant),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> GardenObjectResponse:
    """One garden object (GP-API-013)."""
    return garden_object_to_response(service.get_garden_object(key, tenant_key=ctx.tenant_key))


@router.patch(
    "/garden-objects/{key}",
    response_model=GardenObjectResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
def patch_garden_object(
    key: _OBJECT_KEY,
    body: GardenObjectPatch,
    ctx: TenantContext = Depends(require_permission(ResourceType.GARDEN_OBJECT, Action.UPDATE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> GardenObjectResponse:
    """Change the fields present: geometry, label, notes, props, ``off_site``, lock, drawing order (GP-API-013).

    A structural change: raises the site's ``plan_revision``. A locked object cannot be moved (422
    ``object.locked``).
    """
    updated = service.patch_garden_object(
        key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role, patch=body
    )
    return garden_object_to_response(updated)


@router.delete(
    "/garden-objects/{key}",
    status_code=204,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE},
)
def delete_garden_object(
    key: _OBJECT_KEY,
    ctx: TenantContext = Depends(require_permission(ResourceType.GARDEN_OBJECT, Action.DELETE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> None:
    """Delete a garden object (lead only, GP-API-013). Audited; raises the site's ``plan_revision``."""
    service.delete_garden_object(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)
