from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.substrates.schemas import (
    BatchCreate,
    BatchResponse,
    BatchSlotAssignmentResponse,
    MixComponentResponse,
    PreparationResponse,
    PreparationStep,
    ReusabilityResponse,
    SubstrateCreate,
    SubstrateMixRequest,
    SubstrateResponse,
)
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_substrate_service
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.substrate import MixComponent, Substrate, SubstrateBatch
from app.domain.models.tenant_context import TenantContext
from app.domain.services.substrate_service import SubstrateService

#: Substrates are a **global-but-tenant-aware** surface since #1195 — the same
#: shape as species and botanical families, and resolved by the same
#: ``X-Active-Tenant`` mechanism (#1091 / ADR-009 / REQ-049 §2.11) rather than by
#: moving the routes under ``/t/{slug}/``, which would break every client for no
#: gain.
#:
#: Before #1195 this router carried exactly one dependency — ``get_current_user``
#: — across all 15 routes. No tenant context, no ``require_permission``, no
#: platform-admin check. Every authenticated user of the instance could read,
#: edit and delete every tenant's batches and the shared catalogue.
router = APIRouter(
    prefix="/substrates",
    tags=["substrates"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES},
)


@router.get("", response_model=list[SubstrateResponse])
def list_substrates(
    pagination: PaginationParams = Depends(get_pagination),
    query: Annotated[
        str | None,
        Query(description="Case-insensitive filter over the German/English name and the brand."),
    ] = None,
    service: SubstrateService = Depends(get_substrate_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the substrate catalogue (paginated), optionally filtered by name or brand.

    Hybrid catalogue (#1195): the seeded base media plus the active tenant's own
    mixes, never a foreign tenant's.
    """
    items, total = service.list_substrates(pagination.offset, pagination.limit, query, tenant_key=tenant_key)
    return [to_response(s, SubstrateResponse) for s in items]


@router.post("", response_model=SubstrateResponse, status_code=201)
def create_substrate(
    body: SubstrateCreate,
    service: SubstrateService = Depends(get_substrate_service),
    creating_tenant_key: str = Depends(get_creating_tenant_key),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Create a substrate master record — stamped with the active tenant (#1195).

    The stamp is server-side and never taken from the body: a client that could
    name its own ``tenant_key`` could write into another tenant's catalogue, which
    is the ownership-smuggling vector #1000 closes for every other resource.
    """
    substrate = Substrate(**body.model_dump())
    substrate.tenant_key = creating_tenant_key
    created = service.create_substrate(substrate, caller_role=ctx.role, is_platform_admin=is_platform_admin)
    return to_response(created, SubstrateResponse)


@router.get("/{key}", response_model=SubstrateResponse)
def get_substrate(
    key: Annotated[str, Path(description="Document key of the substrate.")],
    service: SubstrateService = Depends(get_substrate_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Return a single substrate by key — a foreign tenant's mix answers 404 (#1195)."""
    s = service.get_substrate(key, tenant_key=tenant_key)
    return to_response(s, SubstrateResponse)


@router.put("/{key}", response_model=SubstrateResponse)
def update_substrate(
    key: Annotated[str, Path(description="Document key of the substrate.")],
    body: SubstrateCreate,
    service: SubstrateService = Depends(get_substrate_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Update a substrate master record.

    Four-way gate (#1195): a *foreign* mix answers 404, the *global* base
    catalogue is platform-admin only (the #1120 rule), an *own* mix needs a
    writing role.
    """
    substrate = Substrate(**body.model_dump())
    updated = service.update_substrate(
        key, substrate, tenant_key=ctx.tenant_key, caller_role=ctx.role, is_platform_admin=is_platform_admin
    )
    return to_response(updated, SubstrateResponse)


@router.delete("/{key}", status_code=204)
def delete_substrate(
    key: Annotated[str, Path(description="Document key of the substrate.")],
    service: SubstrateService = Depends(get_substrate_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Delete a substrate master record — lead only for an own mix, platform admin for a global one."""
    service.delete_substrate(key, tenant_key=ctx.tenant_key, caller_role=ctx.role, is_platform_admin=is_platform_admin)


@router.post("/mix", response_model=SubstrateResponse, status_code=201)
def create_mix(
    body: SubstrateMixRequest,
    service: SubstrateService = Depends(get_substrate_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Create and persist a substrate mix from weighted components.

    Owned by the active tenant (#1195/#1098): a mix a garden blends for itself
    stays in its own catalogue rather than the shared one.
    """
    components = [MixComponent(substrate_key=c.substrate_key, fraction=c.fraction) for c in body.components]
    created = service.create_mix(
        components,
        name_de=body.name_de,
        name_en=body.name_en,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
    return to_response(created, SubstrateResponse)


@router.post("/preview-mix", response_model=SubstrateResponse)
def preview_mix(
    body: SubstrateMixRequest,
    service: SubstrateService = Depends(get_substrate_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Compute the resulting properties of a substrate mix without persisting it.

    Scoped although it writes nothing: an unscoped preview would report a foreign
    tenant's medium properties back to the caller (#1195).
    """
    components = [MixComponent(substrate_key=c.substrate_key, fraction=c.fraction) for c in body.components]
    props = service.preview_mix(components, tenant_key=tenant_key)
    return SubstrateResponse(
        key="",
        name_de=body.name_de,
        name_en=body.name_en,
        brand=None,
        is_mix=True,
        mix_components=[MixComponentResponse(substrate_key=c.substrate_key, fraction=c.fraction) for c in components],
        type=props["type"],
        ph_base=props["ph_base"],
        ec_base_ms=props["ec_base_ms"],
        water_retention=props["water_retention"],
        air_porosity_percent=props["air_porosity_percent"],
        composition=props["composition"],
        buffer_capacity=props["buffer_capacity"],
        reusable=props["reusable"],
        max_reuse_cycles=props["max_reuse_cycles"],
        water_holding_capacity_percent=props["water_holding_capacity_percent"],
        easily_available_water_percent=props["easily_available_water_percent"],
        cec_meq_per_100cm3=props["cec_meq_per_100cm3"],
        bulk_density_g_per_l=props["bulk_density_g_per_l"],
        irrigation_strategy=props["irrigation_strategy"],
    )


@router.get("/{substrate_key}/batches", response_model=list[BatchResponse])
def list_batches(
    substrate_key: Annotated[str, Path(description="Document key of the substrate.")],
    service: SubstrateService = Depends(get_substrate_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the mixed batches of a substrate — the active tenant's only (#1195).

    Strict, not the catalogue's union: a batch has exactly one owner and there is
    no global batch to share. Before #1195 this returned every tenant's batches.
    """
    batches = service.list_batches(substrate_key, tenant_key=tenant_key)
    return [to_response(b, BatchResponse) for b in batches]


@router.post("/batches", response_model=BatchResponse, status_code=201)
def create_batch(
    body: BatchCreate,
    service: SubstrateService = Depends(get_substrate_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Create a substrate batch, stamped with the active tenant (#1195)."""
    batch = SubstrateBatch(**body.model_dump())
    created = service.create_batch(
        batch, tenant_key=ctx.tenant_key, caller_role=ctx.role, is_platform_admin=is_platform_admin
    )
    return to_response(created, BatchResponse)


@router.get("/batches/{key}", response_model=BatchResponse)
def get_batch(
    key: Annotated[str, Path(description="Document key of the substrate batch.")],
    service: SubstrateService = Depends(get_substrate_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Return a single substrate batch — a foreign one answers 404, never 403 (#1195)."""
    b = service.get_batch(key, tenant_key=tenant_key)
    return to_response(b, BatchResponse)


@router.put("/batches/{key}", response_model=BatchResponse)
def update_batch(
    key: Annotated[str, Path(description="Document key of the substrate batch.")],
    body: BatchCreate,
    service: SubstrateService = Depends(get_substrate_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Update a substrate batch — a foreign one answers 404 before the role gate runs."""
    batch = SubstrateBatch(**body.model_dump())
    updated = service.update_batch(
        key, batch, tenant_key=ctx.tenant_key, caller_role=ctx.role, is_platform_admin=is_platform_admin
    )
    return to_response(updated, BatchResponse)


@router.delete("/batches/{key}", status_code=204)
def delete_batch(
    key: Annotated[str, Path(description="Document key of the substrate batch.")],
    service: SubstrateService = Depends(get_substrate_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Delete a substrate batch — lead only (REQ-049 §2.3)."""
    service.delete_batch(key, tenant_key=ctx.tenant_key, caller_role=ctx.role, is_platform_admin=is_platform_admin)


@router.post("/batches/{key}/check-reusability", response_model=ReusabilityResponse)
def check_reusability(
    key: Annotated[str, Path(description="Document key of the substrate batch.")],
    service: SubstrateService = Depends(get_substrate_service),
):
    """Assess whether a substrate batch can be reused and which treatments it needs."""
    can_reuse, issues, prep_steps, prep_time, ready_date = service.check_reusability(key)
    return ReusabilityResponse(
        can_reuse=can_reuse,
        treatments=issues,
        preparation_steps=[PreparationStep(**s) for s in prep_steps],
        estimated_prep_time_hours=prep_time,
        ready_date=ready_date,
    )


@router.post("/batches/{key}/prepare-reuse", response_model=PreparationResponse)
def prepare_reuse(
    key: Annotated[str, Path(description="Document key of the substrate batch.")],
    service: SubstrateService = Depends(get_substrate_service),
):
    """Run the reuse preparation for a substrate batch and return its steps."""
    result = service.prepare_reuse(key)
    return PreparationResponse(
        can_reuse=result["can_reuse"],
        issues=result["issues"],
        preparation_steps=[PreparationStep(**s) for s in result["preparation_steps"]],
        estimated_prep_time_hours=result["estimated_prep_time_hours"],
        ready_date=result["ready_date"],
    )


@router.post(
    "/batches/{batch_key}/assign-slot/{slot_key}",
    response_model=BatchSlotAssignmentResponse,
    status_code=201,
)
def assign_batch_to_slot(
    batch_key: Annotated[str, Path(description="Document key of the substrate batch.")],
    slot_key: Annotated[str, Path(description="Document key of the slot to assign the batch to.")],
    service: SubstrateService = Depends(get_substrate_service),
):
    """Assign a substrate batch to a slot."""
    service.assign_batch_to_slot(batch_key, slot_key)
    return {"status": "assigned", "batch_key": batch_key, "slot_key": slot_key}
