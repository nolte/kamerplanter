from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.plant_instances.schemas import ActiveChannelResponse
from app.api.v1.planting_runs.diary_schemas import (
    DiaryEntryCreateRequest,
    DiaryEntryResponse,
    DiaryEntryUpdateRequest,
    RunDiaryEntryResponse,
)
from app.api.v1.planting_runs.schemas import (
    AdoptPlantsRequest,
    AdoptPlantsResponse,
    BatchCreatePlantsResponse,
    BatchRemoveRequest,
    BatchRemoveResponse,
    BatchUpdatePhaseDatesRequest,
    BatchUpdatePhaseDatesResponse,
    DetachPlantRequest,
    DetachPlantResponse,
    EntryCreate,
    EntryResponse,
    EntryUpdate,
    NutrientPlanAssignRequest,
    NutrientPlanAssignResponse,
    PhaseSummary,
    PlantingRunCreate,
    PlantingRunResponse,
    PlantingRunUpdate,
    PlantInRunResponse,
    RunTransitionRequest,
    RunTransitionResponse,
    WateringScheduleCalendarResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_nutrient_plan_service,
    get_plant_diary_service,
    get_planting_run_service,
    get_species_repo,
)
from app.common.enums import PlantingRunStatus
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.plant_diary_entry import PlantDiaryEntry
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.plant_diary_service import PlantDiaryService
from app.domain.services.planting_run_service import PlantingRunService

router = APIRouter(prefix="/planting-runs", tags=["planting-runs"])


def _run_response(r: PlantingRun, phase_summary: dict | None = None) -> PlantingRunResponse:
    ps = PhaseSummary(**phase_summary) if phase_summary else None
    return PlantingRunResponse(key=r.key or "", phase_summary=ps, **r.model_dump(exclude={"key"}))


def _entry_response(e: PlantingRunEntry) -> EntryResponse:
    return EntryResponse(key=e.key or "", **e.model_dump(exclude={"key"}))


@router.get("", response_model=list[PlantingRunResponse])
def list_runs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    run_type: str | None = None,
    location_key: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    filters: dict[str, str] = {}
    if status:
        filters["status"] = status
    if run_type:
        filters["run_type"] = run_type
    if location_key:
        filters["location_key"] = location_key
    items, _total = service.list_runs(offset, limit, filters or None, tenant_key=ctx.tenant_key)
    active_keys = [r.key for r in items if r.key and r.status != PlantingRunStatus.PLANNED]
    summaries = service.get_batch_phase_summaries(active_keys) if active_keys else {}
    return [_run_response(r, summaries.get(r.key)) for r in items]


@router.post("", response_model=PlantingRunResponse, status_code=201)
def create_run(
    body: PlantingRunCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    run = PlantingRun(**body.model_dump(exclude={"entries"}), tenant_key=ctx.tenant_key)
    entries = None
    if body.entries:
        entries = [PlantingRunEntry(**e.model_dump()) for e in body.entries]
    created = service.create_run(run, entries)
    return _run_response(created)


@router.get("/{key}", response_model=PlantingRunResponse)
def get_run(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    r = service.get_run(key, tenant_key=ctx.tenant_key)
    ps = service.get_phase_summary(key) if r.status != PlantingRunStatus.PLANNED else None
    return _run_response(r, ps)


@router.put("/{key}", response_model=PlantingRunResponse)
def update_run(
    key: str,
    body: PlantingRunUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_run(key, data)
    return _run_response(updated)


@router.delete("/{key}", status_code=204)
def delete_run(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    service.delete_run(key)


@router.get("/{key}/entries", response_model=list[EntryResponse])
def list_entries(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    entries = service.list_entries(key)
    return [_entry_response(e) for e in entries]


@router.post("/{key}/entries", response_model=EntryResponse, status_code=201)
def add_entry(
    key: str,
    body: EntryCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    entry = PlantingRunEntry(**body.model_dump())
    created = service.add_entry(key, entry)
    return _entry_response(created)


@router.put("/{key}/entries/{entry_key}", response_model=EntryResponse)
def update_entry(
    key: str,
    entry_key: str,
    body: EntryUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
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
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    service.delete_entry(key, entry_key)


@router.post("/{key}/create-plants", response_model=BatchCreatePlantsResponse, status_code=201)
def batch_create_plants(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.create_plants(key)
    return BatchCreatePlantsResponse(**result)


@router.post("/{key}/adopt-plants", response_model=AdoptPlantsResponse)
def adopt_plants(
    key: str,
    body: AdoptPlantsRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.adopt_plants(key, body.plant_keys)
    return AdoptPlantsResponse(**result)


@router.get("/{key}/phase-timeline")
def get_phase_timeline(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    species_repo: ISpeciesRepository = Depends(get_species_repo),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    timelines = service.get_phase_timeline(key)
    for tl in timelines:
        sp = species_repo.get_by_key(tl["species_key"])
        if sp:
            tl["species_name"] = sp.scientific_name
    return timelines


@router.post("/{key}/transition", response_model=RunTransitionResponse)
def transition_run(
    key: str,
    body: RunTransitionRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.transition(key, body.target_phase_key, body.target_phase_name)
    return RunTransitionResponse(**result)


@router.patch("/{key}/batch-update-phase-dates", response_model=BatchUpdatePhaseDatesResponse)
def batch_update_phase_dates(
    key: str,
    body: BatchUpdatePhaseDatesRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    if body.entered_at is None and body.exited_at is None:
        raise HTTPException(status_code=422, detail="At least one of entered_at or exited_at must be provided")
    try:
        result = service.batch_update_phase_dates(key, body.phase_key, body.entered_at, body.exited_at)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return BatchUpdatePhaseDatesResponse(**result)


@router.post("/{key}/batch-remove", response_model=BatchRemoveResponse)
def batch_remove(
    key: str,
    body: BatchRemoveRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.batch_remove(key, body.reason, body.target_status)
    return BatchRemoveResponse(**result)


@router.get("/{key}/plants", response_model=list[PlantInRunResponse])
def list_plants(
    key: str,
    include_detached: bool = Query(False),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
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


@router.post("/{key}/plants/{plant_key}/detach", response_model=DetachPlantResponse)
def detach_plant(
    key: str,
    plant_key: str,
    body: DetachPlantRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.detach_plant(key, plant_key, body.reason)
    return DetachPlantResponse(**result)


@router.post("/{key}/nutrient-plan", response_model=NutrientPlanAssignResponse, status_code=201)
def assign_nutrient_plan(
    key: str,
    body: NutrientPlanAssignRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.assign_nutrient_plan(key, body.plan_key, body.assigned_by)
    return NutrientPlanAssignResponse(**result)


@router.get("/{key}/nutrient-plan")
def get_nutrient_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    plan = service.get_nutrient_plan(key)
    if plan is None:
        return {"plan": None}
    return {"plan": plan}


@router.delete("/{key}/nutrient-plan", status_code=204)
def remove_nutrient_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    service.remove_nutrient_plan(key)


@router.get("/{key}/active-channels", response_model=list[ActiveChannelResponse])
def get_active_channels(
    key: str,
    current_week: int | None = Query(default=None, ge=1),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    plan_service: NutrientPlanService = Depends(get_nutrient_plan_service),
):
    run = service.get_run(key, tenant_key=ctx.tenant_key)
    plan_key = service._repo.get_run_nutrient_plan_key(key)
    if plan_key is None:
        return []
    summary = service.get_phase_summary(key)
    dominant_phase = summary.get("dominant_phase")
    if not dominant_phase:
        return []
    if current_week is None:
        from datetime import date, datetime

        started = run.started_at
        if started is None:
            current_week = 1
        else:
            if isinstance(started, datetime):
                started_date = started.date() if started.tzinfo else started.replace(tzinfo=UTC).date()
            else:
                started_date = started
            delta_days = (date.today() - started_date).days
            current_week = max(1, delta_days // 7 + 1)
    channels = plan_service.get_active_channels_for_plan(plan_key, dominant_phase, current_week)
    return channels


@router.get("/{key}/watering-schedule", response_model=WateringScheduleCalendarResponse)
def get_watering_schedule(
    key: str,
    days_ahead: int = Query(14, ge=1, le=90),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    result = service.get_watering_schedule(key, days_ahead)
    return WateringScheduleCalendarResponse(**result)


# ── Plant diary endpoints ────────────────────────────────────────────


def _diary_response(entry: PlantDiaryEntry) -> DiaryEntryResponse:
    return DiaryEntryResponse(
        key=entry.key or "",
        plant_key=entry.plant_key,
        entry_type=entry.entry_type,
        title=entry.title,
        text=entry.text,
        photo_refs=entry.photo_refs,
        tags=entry.tags,
        measurements=entry.measurements,
        created_by=entry.created_by,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get(
    "/{key}/plants/{plant_key}/diary",
    response_model=list[DiaryEntryResponse],
)
def list_plant_diary_entries(
    key: str,
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    entries, _total = diary_service.list_entries_for_plant(plant_key, offset, limit)
    return [_diary_response(e) for e in entries]


@router.post(
    "/{key}/plants/{plant_key}/diary",
    response_model=DiaryEntryResponse,
    status_code=201,
)
def create_plant_diary_entry(
    key: str,
    plant_key: str,
    body: DiaryEntryCreateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    entry = PlantDiaryEntry(
        tenant_key=ctx.tenant_key,
        created_by=ctx.user_key,
        **body.model_dump(),
    )
    created = diary_service.create_entry(plant_key, entry, run_key=key)
    return _diary_response(created)


@router.get(
    "/{key}/plants/{plant_key}/diary/{entry_key}",
    response_model=DiaryEntryResponse,
)
def get_plant_diary_entry(
    key: str,
    plant_key: str,
    entry_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    entry = diary_service.get_entry(entry_key)
    return _diary_response(entry)


@router.put(
    "/{key}/plants/{plant_key}/diary/{entry_key}",
    response_model=DiaryEntryResponse,
)
def update_plant_diary_entry(
    key: str,
    plant_key: str,
    entry_key: str,
    body: DiaryEntryUpdateRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = diary_service.update_entry(entry_key, data)
    return _diary_response(updated)


@router.delete(
    "/{key}/plants/{plant_key}/diary/{entry_key}",
    status_code=204,
)
def delete_plant_diary_entry(
    key: str,
    plant_key: str,
    entry_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    diary_service.delete_entry(entry_key)


@router.get(
    "/{key}/diary",
    response_model=list[RunDiaryEntryResponse],
)
def list_run_diary_entries(
    key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingRunService = Depends(get_planting_run_service),
    diary_service: PlantDiaryService = Depends(get_plant_diary_service),
):
    service.get_run(key, tenant_key=ctx.tenant_key)
    entries, _total = diary_service.list_entries_for_run(key, offset, limit)
    results = []
    for item in entries:
        diary_data = item.get("diary_entry", {})
        diary_resp = DiaryEntryResponse(
            key=diary_data.get("_key", diary_data.get("key", "")),
            plant_key=diary_data.get("plant_key", ""),
            entry_type=diary_data.get("entry_type", "note"),
            title=diary_data.get("title"),
            text=diary_data.get("text", ""),
            photo_refs=diary_data.get("photo_refs", []),
            tags=diary_data.get("tags", []),
            measurements=diary_data.get("measurements"),
            created_by=diary_data.get("created_by", ""),
            created_at=diary_data.get("created_at"),
            updated_at=diary_data.get("updated_at"),
        )
        results.append(
            RunDiaryEntryResponse(
                plant_key=item.get("plant_key", ""),
                plant_id=item.get("plant_id", ""),
                plant_name=item.get("plant_name"),
                diary_entry=diary_resp,
            )
        )
    return results
