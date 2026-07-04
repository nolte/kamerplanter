from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.ipm.schemas import (
    BeneficialResponse,
    DiseaseCreate,
    DiseaseResponse,
    DiseaseUpdate,
    InspectionResponse,
    PestCreate,
    PestDetailResponse,
    PestResponse,
    PestUpdate,
    TreatmentApplicationResponse,
    TreatmentCreate,
    TreatmentDetailResponse,
    TreatmentResponse,
    TreatmentTargetRef,
    TreatmentUpdate,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_ipm_service, get_pest_inference_client
from app.common.pagination import PaginationParams, get_pagination
from app.config.settings import settings
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import (
    Disease,
    Inspection,
    Pest,
    Treatment,
    TreatmentApplication,
)
from app.domain.services.ipm_service import IpmService

router = APIRouter(prefix="/ipm", tags=["ipm"], dependencies=[Depends(get_current_user)])


def _reference_image_counts() -> dict[str, int]:
    """Bundle the few-shot reference-image coverage per ``detection_slug``.

    REQ-044 — returns a ``{detection_slug: active_prototype_count}`` map loaded in
    a SINGLE call to the inference service (no N+1 over the pest list). The map is
    keyed by the recognition class slug (``PestTaxon.slug``), which a pest links
    to via its ``detection_slug``. Returns ``{}`` while pest detection is disabled
    (Default-Privacy master switch) or the service is unreachable — in both cases
    every pest reports ``has_reference_images=False``.
    """
    if not settings.pest_detection_enabled:
        return {}
    coverage_rows = get_pest_inference_client().coverage()
    counts: dict[str, int] = {}
    for row in coverage_rows:
        label = row.get("label")
        if not label:
            continue
        # "active" = curated, recognition-usable prototypes; fall back to the
        # total only if the service omits the active count.
        counts[label] = int(row.get("active", row.get("total", 0)))
    return counts


def _pest_response(p: Pest, ref_counts: dict[str, int] | None = None) -> PestResponse:
    count = 0
    if ref_counts and p.detection_slug:
        count = ref_counts.get(p.detection_slug, 0)
    return to_response(
        p,
        PestResponse,
        has_reference_images=count > 0,
        reference_image_count=count,
    )


def _disease_response(d: Disease) -> DiseaseResponse:
    return to_response(d, DiseaseResponse)


def _treatment_response(t: Treatment) -> TreatmentResponse:
    return to_response(t, TreatmentResponse)


def _inspection_response(i: Inspection) -> InspectionResponse:
    return to_response(i, InspectionResponse)


def _application_response(a: TreatmentApplication) -> TreatmentApplicationResponse:
    return to_response(a, TreatmentApplicationResponse)


def _beneficial_response(b: Beneficial) -> BeneficialResponse:
    return BeneficialResponse(
        key=b.key or "",
        slug=b.slug,
        common_name=b.common_name,
        scientific_name=b.scientific_name,
        description=b.description,
        preys_on=b.preys_on,
    )


# -- Pests --


@router.get("/pests", response_model=list[PestResponse])
def list_pests(
    pagination: PaginationParams = Depends(get_pagination),
    service: IpmService = Depends(get_ipm_service),
):
    pests, _ = service.list_pests(pagination.offset, pagination.limit)
    ref_counts = _reference_image_counts()
    return [_pest_response(p, ref_counts) for p in pests]


@router.post("/pests", response_model=PestResponse, status_code=201)
def create_pest(body: PestCreate, service: IpmService = Depends(get_ipm_service)):
    pest = Pest(**body.model_dump())
    created = service.create_pest(pest)
    return _pest_response(created)


@router.get("/pests/{key}/detail", response_model=PestDetailResponse)
def get_pest_detail(key: str, service: IpmService = Depends(get_ipm_service)):
    detail = service.get_pest_detail(key)
    return PestDetailResponse(
        pest=_pest_response(detail["pest"], _reference_image_counts()),
        treatments=[_treatment_response(t) for t in detail["treatments"]],
        beneficials=[_beneficial_response(b) for b in detail["beneficials"]],
        detection_symptom_hint=detail["detection_symptom_hint"],
    )


@router.get("/pests/{key}", response_model=PestResponse)
def get_pest(key: str, service: IpmService = Depends(get_ipm_service)):
    return _pest_response(service.get_pest(key), _reference_image_counts())


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
    pagination: PaginationParams = Depends(get_pagination),
    service: IpmService = Depends(get_ipm_service),
):
    diseases, _ = service.list_diseases(pagination.offset, pagination.limit)
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
    pagination: PaginationParams = Depends(get_pagination),
    service: IpmService = Depends(get_ipm_service),
):
    treatments, _ = service.list_treatments(pagination.offset, pagination.limit)
    return [_treatment_response(t) for t in treatments]


@router.post("/treatments", response_model=TreatmentResponse, status_code=201)
def create_treatment(body: TreatmentCreate, service: IpmService = Depends(get_ipm_service)):
    treatment = Treatment(**body.model_dump())
    created = service.create_treatment(treatment)
    return _treatment_response(created)


@router.get("/treatments/{key}/detail", response_model=TreatmentDetailResponse)
def get_treatment_detail(key: str, service: IpmService = Depends(get_ipm_service)):
    detail = service.get_treatment_detail(key)
    return TreatmentDetailResponse(
        treatment=_treatment_response(detail["treatment"]),
        targeted_pests=[
            TreatmentTargetRef(
                key=p.key or "",
                common_name=p.common_name,
                common_name_de=p.common_name_de,
                scientific_name=p.scientific_name,
            )
            for p in detail["targeted_pests"]
        ],
        targeted_diseases=[
            TreatmentTargetRef(key=d.key or "", common_name=d.common_name, scientific_name=d.scientific_name)
            for d in detail["targeted_diseases"]
        ],
    )


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
