from fastapi import APIRouter, Depends, Query

from app.api.v1.planting_runs.schemas import (
    BatchCreatePlantsResponse,
    BatchRemoveRequest,
    BatchRemoveResponse,
    BatchTransitionRequest,
    BatchTransitionResponse,
    DetachPlantRequest,
    EntryCreate,
    EntryResponse,
    EntryUpdate,
    PlantingRunCreate,
    PlantingRunResponse,
    PlantingRunUpdate,
    PlantInRunResponse,
)
from app.common.dependencies import get_planting_run_service
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.planting_run_service import PlantingRunService

router = APIRouter(prefix="/planting-runs", tags=["planting-runs"])


def _run_response(r: PlantingRun) -> PlantingRunResponse:
    return PlantingRunResponse(key=r.key or "", **r.model_dump(exclude={"key"}))


def _entry_response(e: PlantingRunEntry) -> EntryResponse:
    return EntryResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


# ── Run CRUD ──────────────────────────────────────────────────────────

@router.get("", response_model=list[PlantingRunResponse])
def list_runs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    run_type: str | None = None,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    filters: dict[str, str] = {}
    if status:
        filters["status"] = status
    if run_type:
        filters["run_type"] = run_type
    items, _total = service.list_runs(offset, limit, filters or None)
    return [_run_response(r) for r in items]


@router.post("", response_model=PlantingRunResponse, status_code=201)
def create_run(
    body: PlantingRunCreate,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    run = PlantingRun(**body.model_dump(exclude={"entries"}))
    entries = None
    if body.entries:
        entries = [PlantingRunEntry(**e.model_dump()) for e in body.entries]
    created = service.create_run(run, entries)
    return _run_response(created)


@router.get("/{key}", response_model=PlantingRunResponse)
def get_run(key: str, service: PlantingRunService = Depends(get_planting_run_service)):
    r = service.get_run(key)
    return _run_response(r)


@router.put("/{key}", response_model=PlantingRunResponse)
def update_run(
    key: str,
    body: PlantingRunUpdate,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    data = body.model_dump(exclude_none=True)
    updated = service.update_run(key, data)
    return _run_response(updated)


@router.delete("/{key}", status_code=204)
def delete_run(key: str, service: PlantingRunService = Depends(get_planting_run_service)):
    service.delete_run(key)


# ── Entry management ──────────────────────────────────────────────────

@router.get("/{key}/entries", response_model=list[EntryResponse])
def list_entries(key: str, service: PlantingRunService = Depends(get_planting_run_service)):
    entries = service.list_entries(key)
    return [_entry_response(e) for e in entries]


@router.post("/{key}/entries", response_model=EntryResponse, status_code=201)
def add_entry(
    key: str,
    body: EntryCreate,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    entry = PlantingRunEntry(**body.model_dump())
    created = service.add_entry(key, entry)
    return _entry_response(created)


@router.put("/{key}/entries/{entry_key}", response_model=EntryResponse)
def update_entry(
    key: str,
    entry_key: str,
    body: EntryUpdate,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    data = body.model_dump(exclude_none=True)
    entry = PlantingRunEntry(
        species_key=data.get("species_key", "placeholder"),
        quantity=data.get("quantity", 1),
        id_prefix=data.get("id_prefix", "XX"),
        **{k: v for k, v in data.items() if k not in ("species_key", "quantity", "id_prefix")},
    )
    updated = service.update_entry(key, entry_key, entry)
    return _entry_response(updated)


@router.delete("/{key}/entries/{entry_key}", status_code=204)
def delete_entry(
    key: str,
    entry_key: str,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.delete_entry(key, entry_key)


# ── Batch operations ──────────────────────────────────────────────────

@router.post("/{key}/create-plants", response_model=BatchCreatePlantsResponse, status_code=201)
def batch_create_plants(
    key: str,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    result = service.create_plants(key)
    return BatchCreatePlantsResponse(**result)


@router.post("/{key}/batch-transition", response_model=BatchTransitionResponse)
def batch_transition(
    key: str,
    body: BatchTransitionRequest,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    exclude = set(body.exclude_keys) if body.exclude_keys else None
    result = service.batch_transition(key, body.target_phase_key, body.target_phase_name, exclude)
    return BatchTransitionResponse(**result)


@router.post("/{key}/batch-remove", response_model=BatchRemoveResponse)
def batch_remove(
    key: str,
    body: BatchRemoveRequest,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    result = service.batch_remove(key, body.reason)
    return BatchRemoveResponse(**result)


# ── Plant management ──────────────────────────────────────────────────

@router.get("/{key}/plants", response_model=list[PlantInRunResponse])
def list_plants(
    key: str,
    include_detached: bool = Query(False),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    plants = service.get_plants(key, include_detached)
    return [
        PlantInRunResponse(
            key=p.get("_key", ""),
            instance_id=p.get("instance_id", ""),
            species_key=p.get("species_key", ""),
            cultivar_key=p.get("cultivar_key"),
            plant_name=p.get("plant_name"),
            planted_on=p.get("planted_on", "1970-01-01"),
            removed_on=p.get("removed_on"),
            current_phase=p.get("current_phase", ""),
            detached_at=p.get("_edge_detached_at"),
            detach_reason=p.get("_edge_detach_reason"),
        )
        for p in plants
    ]


@router.post("/{key}/plants/{plant_key}/detach", status_code=204)
def detach_plant(
    key: str,
    plant_key: str,
    body: DetachPlantRequest,
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.detach_plant(key, plant_key, body.reason)
