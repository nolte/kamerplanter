from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, Field

from app.api.mapping import to_response
from app.api.v1.species.schemas import (
    ReferenceImageEntry,
    SpeciesCreate,
    SpeciesListResponse,
    SpeciesReferenceImagesResponse,
    SpeciesResponse,
)
from app.common.auth import (
    get_active_tenant_context,
    get_active_tenant_key,
    get_creating_tenant_key,
    get_current_user,
    get_is_platform_admin,
)
from app.common.dependencies import get_family_repo, get_species_service
from app.common.enums import DataOrigin
from app.common.exceptions import ValidationError
from app.common.openapi_responses import CRUD_RESPONSES, UNAUTHORIZED_RESPONSE
from app.config.settings import settings
from app.data_access.arango.botanical_family_repository import ArangoBotanicalFamilyRepository
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.models.species import Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.species_service import SpeciesService

router = APIRouter(
    prefix="/species",
    tags=["species"],
    dependencies=[Depends(get_current_user)],
    responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES},
)


def _species_response(s: Species, family_repo: ArangoBotanicalFamilyRepository) -> SpeciesResponse:
    family_name = None
    if s.family_key:
        fam = family_repo.get_by_key(s.family_key)
        if fam:
            family_name = fam.name
    return to_response(s, SpeciesResponse, family_name=family_name)


@router.get("", response_model=SpeciesListResponse)
def list_species(
    offset: int = Query(0, ge=0, description="Number of species to skip (pagination offset)."),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of species to return."),
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """List the species catalogue (paginated).

    Tenant-aware on this global route (F-5, #808): returns the global seed
    catalogue (``tenant_key == ""``) plus the caller's own-tenant species, and
    never a foreign tenant's. The active tenant is resolved by
    :func:`~app.common.auth.get_active_tenant_key`; an anonymous/light-mode caller
    resolves to ``""`` and sees only the global catalogue.
    """
    items, total = service.list_species(offset, limit, tenant_key=tenant_key)
    # Build family name cache to avoid N+1 queries
    family_keys = {s.family_key for s in items if s.family_key}
    family_map: dict[str, str] = {}
    for fk in family_keys:
        fam = family_repo.get_by_key(fk)
        if fam:
            family_map[fk] = fam.name
    return SpeciesListResponse(
        items=[to_response(s, SpeciesResponse, family_name=family_map.get(s.family_key or "")) for s in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{key}", response_model=SpeciesResponse)
def get_species(
    key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Return a single species by key.

    Tenant-aware (SEC-001, #808): the caller's active tenant is threaded into
    :meth:`SpeciesService.get_species`, so the global seed catalogue and the
    caller's own species resolve, but a *foreign* tenant's species answers 404 —
    the by-key endpoint is no longer an enumerable cross-tenant oracle.
    """
    s = service.get_species(key, tenant_key=tenant_key)
    return _species_response(s, family_repo)


@router.get("/{key}/reference-images", response_model=SpeciesReferenceImagesResponse)
def get_species_reference_images(
    key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    tenant_key: str = Depends(get_active_tenant_key),
):
    """Reference-image gallery for a species (REQ-029-A §4).

    Proxies the inference-service; returns an empty gallery when the service is
    disabled/unreachable or the index has no images for this species yet.
    """
    # 404 if the species does not exist OR belongs to a foreign tenant — this
    # gallery shares the by-key read root, so it inherits SEC-001's scoping.
    service.get_species(key, tenant_key=tenant_key)
    client = InferenceServiceClient(settings.inference_service_url)
    # Public gallery: never show images an admin has deselected.
    rows = client.list_references(key, active_only=True)
    images = [
        ReferenceImageEntry(
            source_url=r.get("source_url", ""),
            license=r.get("license"),
            attribution=r.get("attribution"),
            organ=r.get("organ"),
            source=r.get("source"),
        )
        for r in rows
        if r.get("source_url")
    ]
    return SpeciesReferenceImagesResponse(species_key=key, count=len(images), images=images)


@router.post("", response_model=SpeciesResponse, status_code=201)
def create_species(
    body: SpeciesCreate,
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    tenant_key: str = Depends(get_creating_tenant_key),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Create a tenant-owned species master record.

    Role-gated in the service since SEC-005 (#1113), mirroring the update/delete
    wiring: a viewer of the active tenant is refused with 403, a grower or lead may
    create, and a platform admin may curate regardless of domain rank.

    Two tenant-bearing dependencies on purpose, and they answer different
    questions. ``tenant_key`` (:func:`~app.common.auth.get_creating_tenant_key`) is
    the **ownership stamp**; ``ctx`` supplies only the caller's **role** in that same
    tenant. They cannot disagree — both come from the one
    ``_resolve_active_tenant`` — and keeping the stamp on the alias is what stops
    the F-3 back-compat dependency (and the tests overriding it) from quietly
    becoming inert.
    """
    # SEC-004 (#808): in full mode a tenant-owned create with no resolvable active
    # tenant must NOT be stamped global. Without this guard an authenticated caller
    # who has no personal tenant would resolve ``tenant_key == ""`` and inject an
    # ``origin=TENANT`` species straight into the shared seed catalogue every tenant
    # sees. Reject it as 422 instead. Light mode (REQ-027) is single-tenant, so the
    # empty key there is the legitimate global operator context — never blocked.
    #
    # Ordering vs the SEC-005 (#1113) role gate below: this 422 wins. It is a
    # request-precondition failure — the request names no tenant to create in — and
    # with no resolvable tenant ``ctx.role`` is the fail-safe VIEWER default rather
    # than a standing the caller actually holds, so answering 403 would report a
    # role nobody assigned them. It is also the order the wiring produces (route
    # body before service call), so SEC-004's shipped answer is unchanged.
    if settings.kamerplanter_mode == "full" and not tenant_key:
        raise ValidationError("Cannot create a tenant-owned species without an active tenant.")
    # User-created master data is tenant-owned (editable); seeded species default
    # to 'system' (read-only). Provenance is server-set, never from the form body.
    #
    # tenant_key is resolved from the authenticated caller (their personal tenant),
    # never from the request body (#1000, F-3/#808) — ``SpeciesCreate`` carries no
    # tenant field, so ``body.model_dump()`` cannot smuggle one in. This binds a
    # newly created species to its owner so F-5's read predicate can keep it out of
    # foreign tenants while the global seed catalogue (tenant_key == "") stays
    # visible to all.
    species = Species(**body.model_dump(), origin=DataOrigin.TENANT, tenant_key=tenant_key)
    created = service.create_species(species, caller_role=ctx.role, is_platform_admin=is_platform_admin)
    return _species_response(created, family_repo)


@router.put("/{key}", response_model=SpeciesResponse)
def update_species(
    key: Annotated[str, Path(description="Document key of the species.")],
    body: SpeciesCreate,
    service: SpeciesService = Depends(get_species_service),
    family_repo: ArangoBotanicalFamilyRepository = Depends(get_family_repo),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Update an existing species master record.

    Ownership and role are enforced in the service (SEC-002, #808): a *foreign*
    tenant's species answers 404, the *global* seed catalogue is editable only by
    a platform admin, and the caller's *own* species requires a writing domain
    role (a viewer is refused).
    """
    species = Species(**body.model_dump())
    updated = service.update_species(
        key,
        species,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
    return _species_response(updated, family_repo)


class SpeciesGrantRequest(BaseModel):
    """Which tenant a species is being shared with (#1092).

    The field is ``grantee_tenant_key``, not ``tenant_key``, and the distinction is
    the one #1000 draws: a body field named ``tenant_key`` reads as "the tenant of
    this request" and is the ownership-smuggling vector the guard exists to block.
    This names a *different* tenant — the recipient — which the caller genuinely
    has to supply, because no path segment can carry it.
    """

    grantee_tenant_key: str = Field(min_length=1, description="Key of the tenant to grant read access to.")


@router.get("/{key}/grants", response_model=list[str])
def list_species_grants(
    key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """List the tenants this species has been shared with. Owner only (#1092).

    Not readable by a grantee: that would turn a share into a directory of which
    tenants exist.
    """
    return service.list_species_grants(
        key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


@router.post("/{key}/grants", status_code=204)
def grant_species_access(
    key: Annotated[str, Path(description="Document key of the species.")],
    body: SpeciesGrantRequest,
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Share one of this tenant's own species with another tenant (REQ-001 v4.0, #1092).

    The community-garden case: a shared cultivar reaches a member tenant without
    becoming global. Read-only — the grantee sees the row, the owner keeps update
    and delete.

    Gated exactly like the edit path: a *foreign* species answers 404 (never a 403,
    which would confirm it exists), the *global* catalogue is platform-admin only,
    and sharing an *own* species needs a writing role.
    """
    service.grant_species_access(
        key,
        to_tenant_key=body.grantee_tenant_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


@router.delete("/{key}/grants/{grantee_key}", status_code=204)
def revoke_species_access(
    key: Annotated[str, Path(description="Document key of the species.")],
    grantee_key: Annotated[str, Path(description="Key of the tenant whose access is withdrawn.")],
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Withdraw a grant (#1092).

    Shipped together with the grant, deliberately: a share that cannot be taken
    back is a permanent one wearing a revocable label. Idempotent — revoking a
    grant that is not there answers 204, because the caller's intent ("this tenant
    must not see it") is satisfied either way.
    """
    service.revoke_species_access(
        key,
        from_tenant_key=grantee_key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


@router.delete("/{key}", status_code=204)
def delete_species(
    key: Annotated[str, Path(description="Document key of the species.")],
    service: SpeciesService = Depends(get_species_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Delete a species master record.

    Same three-way gate as update (SEC-002, #808), with the stricter delete role
    boundary: a *foreign* species answers 404, a *global* seed row is deletable
    only by a platform admin, and deleting an *own* species requires a lead
    (the irreversibility boundary, REQ-049 §2.3).
    """
    service.delete_species(
        key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
