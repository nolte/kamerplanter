"""REQ-017 §3 — tenant-scoped propagation / lineage endpoints.

Mounted under ``/t/{tenant_slug}`` by the tenant-scoped parent router, so the
paths declared here are already tenant-scoped. Reads use ``get_current_tenant``;
state-changing writes require at least the ``grower`` role, while protocol and
phenotype-note deletion require the ``admin`` role (``require_tenant_role``). All
persistence and lineage logic
live in :class:`PropagationService` / :class:`LineageEngine`. Cross-tenant or
unknown resources surface as 404 (no existence oracle).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.propagation.schemas import (
    BatchFinalizeRequest,
    DescendantsResponse,
    GraftCompatibilityResponse,
    LineageNode,
    LineageResponse,
    MotherDesignateRequest,
    MotherHealthRequest,
    MotherResponse,
    MotherRetireRequest,
    PhenotypeNoteCreate,
    PhenotypeNoteResponse,
    PropagationBatchCreate,
    PropagationBatchResponse,
    PropagationBatchUpdate,
    PropagationEventCreate,
    PropagationEventOutcomeRequest,
    PropagationEventProgressRequest,
    PropagationEventResponse,
    PropagationStatRow,
    ProtocolStatsResponse,
    RootingProtocolCreate,
    RootingProtocolResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_propagation_service
from app.common.enums import TenantRole
from app.common.pagination import PaginationParams, get_pagination
from app.domain.engines.lineage_engine import GraftCompatibilityResult
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.propagation import (
    PhenotypeNote,
    PropagationBatch,
    PropagationEvent,
    RootingProtocol,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.propagation_service import PropagationService

router = APIRouter(tags=["propagation"])


# ── Mapping helpers ───────────────────────────────────────────────────────────


def _event_response(event: PropagationEvent) -> PropagationEventResponse:
    return PropagationEventResponse(**event.model_dump(by_alias=True))


def _batch_response(batch: PropagationBatch) -> PropagationBatchResponse:
    return PropagationBatchResponse(**batch.model_dump(by_alias=True))


def _protocol_response(protocol: RootingProtocol) -> RootingProtocolResponse:
    data = protocol.model_dump(by_alias=True)
    return RootingProtocolResponse(**data, is_global=(protocol.tenant_key == ""))


def _phenotype_response(note: PhenotypeNote) -> PhenotypeNoteResponse:
    return PhenotypeNoteResponse(**note.model_dump(by_alias=True))


def _lineage_node(plant: PlantInstance) -> LineageNode:
    return LineageNode(
        key=plant.key,
        instance_id=plant.instance_id,
        plant_name=plant.plant_name,
        species_key=plant.species_key,
    )


# ── Events ────────────────────────────────────────────────────────────────────


@router.post("/propagation/events", response_model=PropagationEventResponse, status_code=201)
def create_event(
    body: PropagationEventCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    event = PropagationEvent(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_event(event)
    return _event_response(created)


@router.get("/propagation/events", response_model=list[PropagationEventResponse])
def list_events(
    method: str | None = Query(default=None),
    status: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    items, _total = service.list_events(
        ctx.tenant_key, method=method, status=status, offset=pagination.offset, limit=pagination.limit
    )
    return [_event_response(e) for e in items]


@router.get("/propagation/events/{event_key}", response_model=PropagationEventResponse)
def get_event(
    event_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return _event_response(service.get_event(event_key, ctx.tenant_key))


@router.patch("/propagation/events/{event_key}/outcome", response_model=PropagationEventResponse)
def update_event_outcome(
    event_key: str,
    body: PropagationEventOutcomeRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    updated = service.update_outcome(
        event_key, ctx.tenant_key, survived_count=body.survived_count, failure_reasons=body.failure_reasons
    )
    return _event_response(updated)


@router.patch("/propagation/events/{event_key}/progress", response_model=PropagationEventResponse)
def update_event_progress(
    event_key: str,
    body: PropagationEventProgressRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    updated = service.update_progress(
        event_key,
        ctx.tenant_key,
        callus_observed_at=body.callus_observed_at,
        roots_observed_at=body.roots_observed_at,
        transplant_ready_at=body.transplant_ready_at,
    )
    return _event_response(updated)


# ── Batches ───────────────────────────────────────────────────────────────────


@router.post("/propagation/batches", response_model=PropagationBatchResponse, status_code=201)
def create_batch(
    body: PropagationBatchCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    batch = PropagationBatch(**body.model_dump(), tenant_key=ctx.tenant_key)
    return _batch_response(service.create_batch(batch))


@router.get("/propagation/batches", response_model=list[PropagationBatchResponse])
def list_batches(
    status: str | None = Query(default=None),
    method: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    items, _total = service.list_batches(
        ctx.tenant_key, status=status, method=method, offset=pagination.offset, limit=pagination.limit
    )
    return [_batch_response(b) for b in items]


@router.get("/propagation/batches/{batch_key}", response_model=PropagationBatchResponse)
def get_batch(
    batch_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return _batch_response(service.get_batch(batch_key, ctx.tenant_key))


@router.get("/propagation/batches/{batch_key}/events", response_model=list[PropagationEventResponse])
def get_batch_events(
    batch_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return [_event_response(e) for e in service.get_batch_events(batch_key, ctx.tenant_key)]


@router.patch("/propagation/batches/{batch_key}", response_model=PropagationBatchResponse)
def update_batch(
    batch_key: str,
    body: PropagationBatchUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    updated = service.update_batch(
        batch_key, ctx.tenant_key, status=body.status, completed_at=body.completed_at, notes=body.notes
    )
    return _batch_response(updated)


@router.post("/propagation/batches/{batch_key}/finalize", response_model=PropagationBatchResponse)
def finalize_batch(
    batch_key: str,
    body: BatchFinalizeRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    updated = service.finalize_batch(batch_key, ctx.tenant_key, body.target_planting_run_key)
    return _batch_response(updated)


# ── Protocols ─────────────────────────────────────────────────────────────────


@router.post("/propagation/protocols", response_model=RootingProtocolResponse, status_code=201)
def create_protocol(
    body: RootingProtocolCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    protocol = RootingProtocol(**body.model_dump(), tenant_key=ctx.tenant_key, author=ctx.user_key)
    return _protocol_response(service.create_protocol(protocol))


@router.get("/propagation/protocols", response_model=list[RootingProtocolResponse])
def list_protocols(
    method: str | None = Query(default=None),
    is_template: bool | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    items, _total = service.list_protocols(
        ctx.tenant_key,
        method=method,
        is_template=is_template,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return [_protocol_response(p) for p in items]


@router.get("/propagation/protocols/{protocol_key}", response_model=RootingProtocolResponse)
def get_protocol(
    protocol_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return _protocol_response(service.get_protocol(protocol_key, ctx.tenant_key))


@router.get("/propagation/protocols/{protocol_key}/stats", response_model=ProtocolStatsResponse)
def get_protocol_stats(
    protocol_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return ProtocolStatsResponse(**service.protocol_stats(protocol_key, ctx.tenant_key))


@router.put("/propagation/protocols/{protocol_key}", response_model=RootingProtocolResponse)
def update_protocol(
    protocol_key: str,
    body: RootingProtocolCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    protocol = RootingProtocol(**body.model_dump(), tenant_key=ctx.tenant_key, author=ctx.user_key)
    return _protocol_response(service.update_protocol(protocol_key, ctx.tenant_key, protocol))


@router.delete("/propagation/protocols/{protocol_key}", status_code=204)
def delete_protocol(
    protocol_key: str,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: PropagationService = Depends(get_propagation_service),
):
    service.delete_protocol(protocol_key, ctx.tenant_key)


# ── Mothers ───────────────────────────────────────────────────────────────────


@router.get("/propagation/mothers", response_model=list[MotherResponse])
def list_mothers(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    docs = service.list_mothers(ctx.tenant_key, pagination.offset, pagination.limit)
    return [MotherResponse(**doc) for doc in docs]


@router.get("/propagation/mothers/{plant_key}", response_model=MotherResponse)
def get_mother(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return MotherResponse(**service.get_mother(plant_key, ctx.tenant_key))


@router.patch("/propagation/mothers/{plant_key}/designate", response_model=MotherResponse)
def designate_mother(
    plant_key: str,
    body: MotherDesignateRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    return MotherResponse(**service.designate_mother(plant_key, ctx.tenant_key, priority=body.priority))


@router.patch("/propagation/mothers/{plant_key}/retire", response_model=MotherResponse)
def retire_mother(
    plant_key: str,
    body: MotherRetireRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    return MotherResponse(**service.retire_mother(plant_key, ctx.tenant_key, reason=body.reason))


@router.patch("/propagation/mothers/{plant_key}/health", response_model=MotherResponse)
def update_mother_health(
    plant_key: str,
    body: MotherHealthRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    return MotherResponse(**service.update_mother_health(plant_key, ctx.tenant_key, health_score=body.health_score))


# ── Lineage ───────────────────────────────────────────────────────────────────


@router.get("/plant-instances/{plant_key}/lineage", response_model=LineageResponse)
def get_lineage(
    plant_key: str,
    max_depth: int = Query(default=10, ge=1, le=25),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    result = service.get_lineage(plant_key, ctx.tenant_key, max_depth)
    return LineageResponse(
        plant_key=result["plant_key"],
        paths=result["paths"],
        ancestors=[_lineage_node(p) for p in result["ancestors"]],
    )


@router.get("/plant-instances/{plant_key}/descendants", response_model=DescendantsResponse)
def get_descendants(
    plant_key: str,
    max_depth: int = Query(default=10, ge=1, le=25),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    descendants = service.get_descendants(plant_key, ctx.tenant_key, max_depth)
    return DescendantsResponse(plant_key=plant_key, descendants=[_lineage_node(p) for p in descendants])


@router.get("/propagation/graft-compatibility", response_model=GraftCompatibilityResponse)
def check_graft_compatibility(
    scion_key: str = Query(...),
    rootstock_key: str = Query(...),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    result: GraftCompatibilityResult = service.check_graft_compatibility(scion_key, rootstock_key, ctx.tenant_key)
    return GraftCompatibilityResponse(
        scion_key=scion_key,
        rootstock_key=rootstock_key,
        scion_species_key=result.scion_species_key,
        rootstock_species_key=result.rootstock_species_key,
        compatible=result.compatible,
        level=result.level,
        same_genus=result.same_genus,
        same_family=result.same_family,
        message=result.message,
    )


# ── Phenotype notes ───────────────────────────────────────────────────────────


@router.post("/plant-instances/{plant_key}/phenotypes", response_model=PhenotypeNoteResponse, status_code=201)
def add_phenotype(
    plant_key: str,
    body: PhenotypeNoteCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PropagationService = Depends(get_propagation_service),
):
    note = PhenotypeNote(**body.model_dump(), plant_key=plant_key, tenant_key=ctx.tenant_key)
    return _phenotype_response(service.add_phenotype(note, ctx.tenant_key))


@router.get("/plant-instances/{plant_key}/phenotypes", response_model=list[PhenotypeNoteResponse])
def list_phenotypes(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return [_phenotype_response(n) for n in service.list_phenotypes(plant_key, ctx.tenant_key)]


@router.delete("/plant-instances/{plant_key}/phenotypes/{note_key}", status_code=204)
def delete_phenotype(
    plant_key: str,
    note_key: str,
    # Phenotype notes are destructive, tenant-shared breeding records: deletion is
    # admin-only, mirroring protocol deletion (SEC-B4 least-privilege).
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: PropagationService = Depends(get_propagation_service),
):
    service.delete_phenotype(plant_key, note_key, ctx.tenant_key)


# ── Statistics ────────────────────────────────────────────────────────────────


@router.get("/propagation/stats", response_model=list[PropagationStatRow])
def get_stats(
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return [PropagationStatRow(**row) for row in service.stats(ctx.tenant_key, "method")]


@router.get("/propagation/stats/by-cultivar", response_model=list[PropagationStatRow])
def get_stats_by_cultivar(
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return [PropagationStatRow(**row) for row in service.stats(ctx.tenant_key, "cultivar")]


@router.get("/propagation/stats/by-protocol", response_model=list[PropagationStatRow])
def get_stats_by_protocol(
    ctx: TenantContext = Depends(get_current_tenant),
    service: PropagationService = Depends(get_propagation_service),
):
    return [PropagationStatRow(**row) for row in service.stats(ctx.tenant_key, "protocol")]
