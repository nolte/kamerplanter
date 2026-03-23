from fastapi import APIRouter, Depends, Query

from app.api.v1.substrates.schemas import (
    BatchCreate,
    BatchResponse,
    MixComponentResponse,
    PreparationResponse,
    PreparationStep,
    ReusabilityResponse,
    SubstrateCreate,
    SubstrateMixRequest,
    SubstrateResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_substrate_service
from app.domain.models.substrate import MixComponent, Substrate, SubstrateBatch
from app.domain.services.substrate_service import SubstrateService

router = APIRouter(prefix="/substrates", tags=["substrates"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SubstrateResponse])
def list_substrates(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SubstrateService = Depends(get_substrate_service),
):
    items, total = service.list_substrates(offset, limit)
    return [SubstrateResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in items]


@router.post("", response_model=SubstrateResponse, status_code=201)
def create_substrate(body: SubstrateCreate, service: SubstrateService = Depends(get_substrate_service)):
    substrate = Substrate(**body.model_dump())
    created = service.create_substrate(substrate)
    return SubstrateResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/{key}", response_model=SubstrateResponse)
def get_substrate(key: str, service: SubstrateService = Depends(get_substrate_service)):
    s = service.get_substrate(key)
    return SubstrateResponse(key=s.key or "", **s.model_dump(exclude={"key"}))


@router.put("/{key}", response_model=SubstrateResponse)
def update_substrate(key: str, body: SubstrateCreate, service: SubstrateService = Depends(get_substrate_service)):
    substrate = Substrate(**body.model_dump())
    updated = service.update_substrate(key, substrate)
    return SubstrateResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/{key}", status_code=204)
def delete_substrate(key: str, service: SubstrateService = Depends(get_substrate_service)):
    service.delete_substrate(key)


@router.post("/mix", response_model=SubstrateResponse, status_code=201)
def create_mix(body: SubstrateMixRequest, service: SubstrateService = Depends(get_substrate_service)):
    components = [MixComponent(substrate_key=c.substrate_key, fraction=c.fraction) for c in body.components]
    created = service.create_mix(components, name_de=body.name_de, name_en=body.name_en)
    return SubstrateResponse(
        key=created.key or "",
        **created.model_dump(exclude={"key"}),
    )


@router.post("/preview-mix", response_model=SubstrateResponse)
def preview_mix(body: SubstrateMixRequest, service: SubstrateService = Depends(get_substrate_service)):
    components = [MixComponent(substrate_key=c.substrate_key, fraction=c.fraction) for c in body.components]
    props = service.preview_mix(components)
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
        cec_meq_per_100g=props["cec_meq_per_100g"],
        bulk_density_g_per_l=props["bulk_density_g_per_l"],
        irrigation_strategy=props["irrigation_strategy"],
    )


@router.get("/{substrate_key}/batches", response_model=list[BatchResponse])
def list_batches(substrate_key: str, service: SubstrateService = Depends(get_substrate_service)):
    batches = service.list_batches(substrate_key)
    return [BatchResponse(key=b.key or "", **b.model_dump(exclude={"key"})) for b in batches]


@router.post("/batches", response_model=BatchResponse, status_code=201)
def create_batch(body: BatchCreate, service: SubstrateService = Depends(get_substrate_service)):
    batch = SubstrateBatch(**body.model_dump())
    created = service.create_batch(batch)
    return BatchResponse(key=created.key or "", **created.model_dump(exclude={"key"}))


@router.get("/batches/{key}", response_model=BatchResponse)
def get_batch(key: str, service: SubstrateService = Depends(get_substrate_service)):
    b = service.get_batch(key)
    return BatchResponse(key=b.key or "", **b.model_dump(exclude={"key"}))


@router.put("/batches/{key}", response_model=BatchResponse)
def update_batch(key: str, body: BatchCreate, service: SubstrateService = Depends(get_substrate_service)):
    batch = SubstrateBatch(**body.model_dump())
    updated = service.update_batch(key, batch)
    return BatchResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))


@router.delete("/batches/{key}", status_code=204)
def delete_batch(key: str, service: SubstrateService = Depends(get_substrate_service)):
    service.delete_batch(key)


@router.post("/batches/{key}/check-reusability", response_model=ReusabilityResponse)
def check_reusability(key: str, service: SubstrateService = Depends(get_substrate_service)):
    can_reuse, issues, prep_steps, prep_time, ready_date = service.check_reusability(key)
    return ReusabilityResponse(
        can_reuse=can_reuse,
        treatments=issues,
        preparation_steps=[PreparationStep(**s) for s in prep_steps],
        estimated_prep_time_hours=prep_time,
        ready_date=ready_date,
    )


@router.post("/batches/{key}/prepare-reuse", response_model=PreparationResponse)
def prepare_reuse(key: str, service: SubstrateService = Depends(get_substrate_service)):
    result = service.prepare_reuse(key)
    return PreparationResponse(
        can_reuse=result["can_reuse"],
        issues=result["issues"],
        preparation_steps=[PreparationStep(**s) for s in result["preparation_steps"]],
        estimated_prep_time_hours=result["estimated_prep_time_hours"],
        ready_date=result["ready_date"],
    )


@router.post("/batches/{batch_key}/assign-slot/{slot_key}", status_code=201)
def assign_batch_to_slot(
    batch_key: str,
    slot_key: str,
    service: SubstrateService = Depends(get_substrate_service),
):
    service.assign_batch_to_slot(batch_key, slot_key)
    return {"status": "assigned", "batch_key": batch_key, "slot_key": slot_key}
