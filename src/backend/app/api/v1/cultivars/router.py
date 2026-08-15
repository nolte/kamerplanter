from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field

from app.api.mapping import to_response
from app.api.v1.cultivars.schemas import CultivarCreate, CultivarResponse
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_species_service
from app.common.enums import DataOrigin
from app.common.exceptions import ValidationError
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
from app.config.settings import settings
from app.domain.models.species import Cultivar
from app.domain.models.tenant_context import TenantContext
from app.domain.services.species_service import SpeciesService

router = APIRouter(
    prefix="/species/{species_key}/cultivars",
    tags=["cultivars"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES},
)


@router.get("", response_model=list[CultivarResponse])
def list_cultivars(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the cultivars registered for a species.

    Tenant-aware (C-3, #1090): returns the global cultivar catalogue
    (``tenant_key == ""``) plus the caller's own cultivars, and never a foreign
    tenant's. The active tenant is resolved by
    :func:`~app.common.auth.get_active_tenant_key`; an anonymous/light-mode caller
    resolves to ``""`` and sees exactly the global catalogue. A *foreign* tenant's
    species answers 404 rather than an empty list (operator decision Q3).
    """
    cultivars = service.list_cultivars(species_key, tenant_key=tenant_key)
    return [to_response(c, CultivarResponse) for c in cultivars]


@router.post("", response_model=CultivarResponse, status_code=201)
def create_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    body: CultivarCreate,
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_creating_tenant_key),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Create a tenant-owned cultivar for a species.

    The parent species is resolved **tenant-scoped** (C-4, #1090): a cultivar may
    only be attached to the caller's own or a global species. Attaching one to a
    *foreign* tenant's species answers 404 — it would otherwise confirm that
    species key exists and write a ``has_cultivar`` edge into a foreign graph.

    Role-gated in the service since SEC-005 (#1113), mirroring the update/delete
    wiring and the species create: a viewer of the active tenant is refused with
    403, a grower or lead may create, a platform admin may curate regardless of
    domain rank. The parent-species 404 is decided first, so the refusal for an
    unreachable species does not vary with the caller's role.

    ``tenant_key`` stays the **ownership stamp** (and the C-4 co-scoping input);
    ``ctx`` supplies only the **role**. Both resolve through the one
    ``_resolve_active_tenant``, so they cannot disagree — and the stamp keeps
    reading the F-3 back-compat alias rather than ``ctx.tenant_key``, so that
    dependency does not silently become inert.
    """
    # SEC-004 pendant (#1090): in full mode a tenant-owned create with no resolvable
    # active tenant must NOT be stamped global. Without this guard an authenticated
    # caller who has no personal tenant would resolve ``tenant_key == ""`` and inject
    # an ``origin=TENANT`` cultivar straight into the shared seed catalogue every
    # tenant sees. Reject it as 422 instead. Light mode (REQ-027) is single-tenant, so
    # the empty key there is the legitimate global operator context — never blocked.
    #
    # Ordering vs the SEC-005 (#1113) role gate: this 422 wins, for the reason the
    # species create route records — a request that names no tenant fails on its
    # precondition, before a role that is only a fail-safe default is judged.
    if settings.kamerplanter_mode == "full" and not tenant_key:
        raise ValidationError("Cannot create a tenant-owned cultivar without an active tenant.")
    # User-created cultivars are tenant-owned (editable); seeded ones stay 'system'.
    #
    # tenant_key is resolved from the authenticated caller (their personal tenant),
    # never from the request body (#1000, #1090) — ``CultivarCreate`` carries no
    # tenant field, so ``body.model_dump()`` cannot smuggle one in. It carries no
    # ``species_key`` either since #1114: the parent is the path segment, and the
    # previous ``exclude={"species_key"}`` existed only to drop a field the schema
    # required and this route never wanted. This binds a
    # newly created cultivar to its owner so the tenant-aware read predicate can keep
    # it out of foreign tenants while the global seed catalogue (tenant_key == "")
    # stays visible to all. Mirrors the species create path.
    cultivar = Cultivar(
        species_key=species_key,
        origin=DataOrigin.TENANT,
        tenant_key=tenant_key,
        **body.model_dump(),
    )
    created = service.create_cultivar(
        cultivar,
        tenant_key=tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
    return to_response(created, CultivarResponse)


@router.get("/{cultivar_key}", response_model=CultivarResponse)
def get_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Return a single cultivar of a species by key.

    Tenant-aware (C-3, #1090): the caller's active tenant is threaded into
    :meth:`SpeciesService.get_cultivar`, so the global catalogue and the caller's
    own cultivars resolve, but a *foreign* tenant's cultivar answers 404 — never a
    403, so the by-key endpoint is not an enumerable cross-tenant oracle.

    Species-bound (SEC-007, C-10, #1090): the ``species_key`` path segment is
    threaded in as well. A cultivar addressed under a species that is not its own
    answers 404 — the same signal the list route gives for a foreign species (Q3).
    Before C-10 the segment was accepted and ignored, so every cultivar resolved
    under every species key.
    """
    c = service.get_cultivar(cultivar_key, species_key=species_key, tenant_key=tenant_key)
    return to_response(c, CultivarResponse)


@router.put("/{cultivar_key}", response_model=CultivarResponse)
def update_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    body: CultivarCreate,
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Update an existing cultivar of a species.

    Ownership and role are enforced in the service (C-4, #1090): a *foreign*
    tenant's cultivar answers 404, the *global* seed catalogue is editable only by
    a platform admin, and the caller's *own* cultivar requires a writing domain
    role (a viewer is refused).

    Species-bound (SEC-007, C-10, #1090): updating a cultivar under a species that
    is not its own answers 404 and writes nothing. Previously the path value was
    written straight into the model, so a PUT to the wrong URL silently re-parented
    the document while its ``has_cultivar`` edge stayed on the original species.
    """
    # The model built here carries the *default* ``tenant_key == ""`` — the edit form
    # never submits ownership (#1090). The service restores the stored owner before
    # writing, so this full-replace update cannot move a tenant-owned cultivar into
    # the shared global catalogue. It restores the stored ``species_key`` the same
    # way (C-10), so neither the path segment below nor the body's ignored
    # ``species_key`` can move the row between species.
    cultivar = Cultivar(species_key=species_key, **body.model_dump(exclude={"species_key"}))
    updated = service.update_cultivar(
        cultivar_key,
        cultivar,
        species_key=species_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
    return to_response(updated, CultivarResponse)


@router.delete("/{cultivar_key}", status_code=204)
def delete_cultivar(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Delete a cultivar of a species.

    Same three-way gate as update (C-4, #1090), with the stricter delete role
    boundary: a *foreign* cultivar answers 404, a *global* seed row is deletable
    only by a platform admin, and deleting an *own* cultivar requires a lead
    (the irreversibility boundary, REQ-049 §2.3).

    Species-bound (SEC-007, C-10, #1090): deleting a cultivar under a species that
    is not its own answers 404 and removes nothing.
    """
    service.delete_cultivar(
        cultivar_key,
        species_key=species_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


class CultivarGrantRequest(BaseModel):
    """Which tenant a cultivar is being shared with (#1092).

    The field is ``grantee_tenant_key``, not ``tenant_key``: a body field of the
    latter name reads as "the tenant of this request" and is the ownership-
    smuggling vector #1000 blocks. This one names a *different* tenant — the
    recipient — which the caller genuinely has to supply, because no path segment
    carries it.
    """

    grantee_tenant_key: str = Field(min_length=1, description="Key of the tenant to grant read access to.")


@router.get("/{cultivar_key}/grants", response_model=list[str])
def list_cultivar_grants(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """List the tenants this cultivar has been shared with. Owner only (#1092).

    Not readable by a grantee: that would turn a share into a directory of which
    tenants exist.
    """
    return service.list_cultivar_grants(
        cultivar_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


@router.post("/{cultivar_key}/grants", status_code=204)
def grant_cultivar_access(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    body: CultivarGrantRequest,
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Share one of this tenant's own cultivars with another tenant (REQ-001 v4.0, #1092).

    The case #1092 was decided on: a community garden shares a cultivar it
    maintains with a member tenant, without that row becoming global. Read-only —
    the grantee sees the cultivar, the owner keeps update and delete.

    Gated exactly like the edit path: a *foreign* cultivar answers 404 (never a
    403, which would confirm it exists), the *global* catalogue is platform-admin
    only, and sharing an *own* cultivar needs a writing role.
    """
    service.grant_cultivar_access(
        cultivar_key,
        to_tenant_key=body.grantee_tenant_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


@router.delete("/{cultivar_key}/grants/{grantee_key}", status_code=204)
def revoke_cultivar_access(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    cultivar_key: Annotated[str, Path(description="Document key of the cultivar.")],
    grantee_key: Annotated[str, Path(description="Key of the tenant whose access is withdrawn.")],
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Withdraw a cultivar grant (#1092).

    Shipped together with the grant, deliberately: a share that cannot be taken
    back is a permanent one wearing a revocable label. Idempotent — revoking a
    grant that is not there answers 204, because the caller's intent ("this tenant
    must not see it") is satisfied either way.
    """
    service.revoke_cultivar_access(
        cultivar_key,
        from_tenant_key=grantee_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
