from fastapi import APIRouter, Depends, Query

from app.api.v1.enrichment.schemas import (
    AcceptFieldsRequest,
    EnrichmentResponse,
    ExternalSearchRequest,
    ExternalSpeciesResponse,
    FieldMappingResponse,
    RejectFieldsRequest,
    SourceHealthResponse,
    SourceResponse,
    SyncRunResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from app.common.dependencies import get_enrichment_service
from app.domain.services.enrichment_service import EnrichmentService

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.get("/sources", response_model=list[SourceResponse])
def list_sources(service: EnrichmentService = Depends(get_enrichment_service)):
    sources = service.list_sources()
    return [
        SourceResponse(key=s.key or "", **s.model_dump(exclude={"key", "created_at", "updated_at"}))
        for s in sources
    ]


@router.get("/sources/{source_key}", response_model=SourceResponse)
def get_source(source_key: str, service: EnrichmentService = Depends(get_enrichment_service)):
    s = service.get_source(source_key)
    return SourceResponse(key=s.key or "", **s.model_dump(exclude={"key", "created_at", "updated_at"}))


@router.post("/sources/{source_key}/sync", response_model=SyncTriggerResponse, status_code=202)
def trigger_sync(
    source_key: str,
    body: SyncTriggerRequest | None = None,
    service: EnrichmentService = Depends(get_enrichment_service),
):
    full_sync = body.full_sync if body else False
    run = service.trigger_sync(source_key, full_sync=full_sync)
    return SyncTriggerResponse(
        key=run.key or "",
        source_key=run.source_key,
        status=run.status,
        triggered_by=run.triggered_by,
        full_sync=run.full_sync,
        started_at=run.started_at,
    )


@router.get("/sources/{source_key}/history", response_model=list[SyncRunResponse])
def get_sync_history(
    source_key: str,
    limit: int = Query(20, ge=1, le=100),
    service: EnrichmentService = Depends(get_enrichment_service),
):
    runs = service.get_sync_history(source_key, limit=limit)
    return [
        SyncRunResponse(key=r.key or "", **r.model_dump(exclude={"key", "created_at", "updated_at"}))
        for r in runs
    ]


@router.get("/species/{species_key}/enrichments", response_model=list[EnrichmentResponse])
def get_species_enrichments(species_key: str, service: EnrichmentService = Depends(get_enrichment_service)):
    mappings = service.get_species_enrichments(species_key)
    return [
        EnrichmentResponse(
            key=m.key or "",
            internal_collection=m.internal_collection,
            internal_key=m.internal_key,
            source_key=m.source_key,
            external_id=m.external_id,
            field_mappings={
                k: FieldMappingResponse(**v.model_dump()) for k, v in m.field_mappings.items()
            },
        )
        for m in mappings
    ]


@router.post("/species/{species_key}/enrichments/{source_key}/accept", response_model=EnrichmentResponse)
def accept_enrichment(
    species_key: str,
    source_key: str,
    body: AcceptFieldsRequest,
    service: EnrichmentService = Depends(get_enrichment_service),
):
    m = service.accept_enrichment(species_key, source_key, body.fields)
    return EnrichmentResponse(
        key=m.key or "",
        internal_collection=m.internal_collection,
        internal_key=m.internal_key,
        source_key=m.source_key,
        external_id=m.external_id,
        field_mappings={k: FieldMappingResponse(**v.model_dump()) for k, v in m.field_mappings.items()},
    )


@router.post("/species/{species_key}/enrichments/{source_key}/reject", response_model=EnrichmentResponse)
def reject_enrichment(
    species_key: str,
    source_key: str,
    body: RejectFieldsRequest,
    service: EnrichmentService = Depends(get_enrichment_service),
):
    m = service.reject_enrichment(species_key, source_key, body.fields)
    return EnrichmentResponse(
        key=m.key or "",
        internal_collection=m.internal_collection,
        internal_key=m.internal_key,
        source_key=m.source_key,
        external_id=m.external_id,
        field_mappings={k: FieldMappingResponse(**v.model_dump()) for k, v in m.field_mappings.items()},
    )


@router.post("/search", response_model=list[ExternalSpeciesResponse])
def search_external(body: ExternalSearchRequest, service: EnrichmentService = Depends(get_enrichment_service)):
    results = service.search_external(body.source_key, body.query)
    return [
        ExternalSpeciesResponse(**r.model_dump(exclude={"sunlight", "watering", "cycle"}))
        for r in results
    ]


@router.get("/health", response_model=list[SourceHealthResponse])
def get_health(service: EnrichmentService = Depends(get_enrichment_service)):
    health = service.get_source_health()
    return [SourceHealthResponse(source_key=k, healthy=v) for k, v in health.items()]
