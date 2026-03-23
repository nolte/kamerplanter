from fastapi import APIRouter, Depends, Query

from app.api.v1.ipm.schemas import (
    DiseaseCreate,
    DiseaseResponse,
    DiseaseUpdate,
    InspectionResponse,
    PestCreate,
    PestResponse,
    PestUpdate,
    TreatmentApplicationResponse,
    TreatmentCreate,
    TreatmentResponse,
    TreatmentUpdate,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_ipm_service
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)
from app.domain.services.ipm_service import IpmService

router = APIRouter(prefix="/ipm", tags=["ipm"], dependencies=[Depends(get_current_user)])


def _pest_response(p: Pest) -> PestResponse:
    return PestResponse(key=p.key or "", **p.model_dump(exclude={"key"}))


def _disease_response(d: Disease) -> DiseaseResponse:
    return DiseaseResponse(key=d.key or "", **d.model_dump(exclude={"key"}))


def _treatment_response(t: Treatment) -> TreatmentResponse:
    return TreatmentResponse(key=t.key or "", **t.model_dump(exclude={"key"}))


def _inspection_response(i: Inspection) -> InspectionResponse:
    return InspectionResponse(key=i.key or "", **i.model_dump(exclude={"key"}))


def _application_response(a: TreatmentApplication) -> TreatmentApplicationResponse:
    return TreatmentApplicationResponse(key=a.key or "", **a.model_dump(exclude={"key"}))


# -- Pests --


@router.get("/pests", response_model=list[PestResponse])
def list_pests(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: IpmService = Depends(get_ipm_service),
):
    pests, _ = service.list_pests(offset, limit)
    return [_pest_response(p) for p in pests]


@router.post("/pests", response_model=PestResponse, status_code=201)
def create_pest(body: PestCreate, service: IpmService = Depends(get_ipm_service)):
    pest = Pest(**body.model_dump())
    created = service.create_pest(pest)
    return _pest_response(created)


@router.get("/pests/{key}", response_model=PestResponse)
def get_pest(key: str, service: IpmService = Depends(get_ipm_service)):
    return _pest_response(service.get_pest(key))


@router.put("/pests/{key}", response_model=PestResponse)
def update_pest(key: str, body: PestUpdate, service: IpmService = Depends(get_ipm_service)):
    data = body.model_dump(exclude_none=True)
    updated = service.update_pest(key, data)
    return _pest_response(updated)


@router.delete("/pests/{key}", status_code=204)
def delete_pest(key: str, service: IpmService = Depends(get_ipm_service)):
    service.delete_pest(key)


# -- Diseases --


@router.get("/diseases", response_model=list[DiseaseResponse])
def list_diseases(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: IpmService = Depends(get_ipm_service),
):
    diseases, _ = service.list_diseases(offset, limit)
    return [_disease_response(d) for d in diseases]


@router.post("/diseases", response_model=DiseaseResponse, status_code=201)
def create_disease(body: DiseaseCreate, service: IpmService = Depends(get_ipm_service)):
    disease = Disease(**body.model_dump())
    created = service.create_disease(disease)
    return _disease_response(created)


@router.get("/diseases/{key}", response_model=DiseaseResponse)
def get_disease(key: str, service: IpmService = Depends(get_ipm_service)):
    return _disease_response(service.get_disease(key))


@router.put("/diseases/{key}", response_model=DiseaseResponse)
def update_disease(key: str, body: DiseaseUpdate, service: IpmService = Depends(get_ipm_service)):
    data = body.model_dump(exclude_none=True)
    updated = service.update_disease(key, data)
    return _disease_response(updated)


@router.delete("/diseases/{key}", status_code=204)
def delete_disease(key: str, service: IpmService = Depends(get_ipm_service)):
    service.delete_disease(key)


# -- Treatments --


@router.get("/treatments", response_model=list[TreatmentResponse])
def list_treatments(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: IpmService = Depends(get_ipm_service),
):
    treatments, _ = service.list_treatments(offset, limit)
    return [_treatment_response(t) for t in treatments]


@router.post("/treatments", response_model=TreatmentResponse, status_code=201)
def create_treatment(body: TreatmentCreate, service: IpmService = Depends(get_ipm_service)):
    treatment = Treatment(**body.model_dump())
    created = service.create_treatment(treatment)
    return _treatment_response(created)


@router.get("/treatments/{key}", response_model=TreatmentResponse)
def get_treatment(key: str, service: IpmService = Depends(get_ipm_service)):
    return _treatment_response(service.get_treatment(key))


@router.put("/treatments/{key}", response_model=TreatmentResponse)
def update_treatment(key: str, body: TreatmentUpdate, service: IpmService = Depends(get_ipm_service)):
    data = body.model_dump(exclude_none=True)
    updated = service.update_treatment(key, data)
    return _treatment_response(updated)


@router.delete("/treatments/{key}", status_code=204)
def delete_treatment(key: str, service: IpmService = Depends(get_ipm_service)):
    service.delete_treatment(key)
