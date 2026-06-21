"""REQ-044 — admin API for the few-shot pest-recognition index.

Coverage per taxonomy class, a per-class gallery of the indexed reference images
(provenance + attribution, no embeddings), manual curation, and a UI-startable
acquisition job. Platform-admin only; in light mode the sole system user is the
admin (see require_platform_admin).
"""

from fastapi import APIRouter, Depends

from app.api.v1.admin.pests.schemas import (
    PestAcquireResponse,
    PestCoverageEntry,
    PestCurationImage,
    PestCurationImageList,
    PestRecognitionStatusResponse,
    SetPestImageActiveRequest,
    SetPestImageActiveResponse,
)
from app.common.auth import require_platform_admin
from app.config.settings import settings
from app.data_access.external.pest_inference_client import PestDetectionInferenceClient
from app.domain.models.pest_taxonomy import PEST_TAXONOMY
from app.domain.models.user import User

router = APIRouter(prefix="/admin/pests", tags=["admin-pests"])


def _client() -> PestDetectionInferenceClient:
    return PestDetectionInferenceClient(settings.inference_service_url)


@router.get("/status", response_model=PestRecognitionStatusResponse)
def get_pest_recognition_status(_user: User = Depends(require_platform_admin)) -> PestRecognitionStatusResponse:
    """Aggregated coverage of the few-shot pest index, per taxonomy class."""
    client = _client()
    coverage_rows = client.coverage() if settings.pest_detection_enabled else []
    by_label = {row["label"]: row for row in coverage_rows}

    target = settings.pest_reference_min_usable
    classes: list[PestCoverageEntry] = []
    index_count = 0
    for taxon in PEST_TAXONOMY:
        row = by_label.get(taxon.slug, {})
        total = int(row.get("total", 0))
        active = int(row.get("active", 0))
        index_count += total
        classes.append(
            PestCoverageEntry(
                label=taxon.slug,
                common_name=taxon.common_name_de,
                category=taxon.category.value,
                scientific_name=taxon.scientific_name,
                gbif_taxon_key=taxon.gbif_taxon_key,
                total=total,
                active=active,
                target=target,
                usable=active >= target,
            )
        )

    service_ready = client.is_ready() if settings.pest_detection_enabled else False
    return PestRecognitionStatusResponse(
        feature_enabled=settings.pest_detection_enabled,
        service_ready=service_ready,
        index_count=index_count,
        target_per_class=target,
        classes=classes,
    )


@router.post("/acquire", response_model=PestAcquireResponse, status_code=202)
def start_pest_acquisition(_user: User = Depends(require_platform_admin)) -> PestAcquireResponse:
    """Dispatch the cold-start acquisition job for all classes (from the UI)."""
    from app.tasks.pest_dataset_tasks import acquire_pest_dataset_task

    task = acquire_pest_dataset_task.delay()
    return PestAcquireResponse(status="queued", task_id=getattr(task, "id", None))


@router.get("/{label}/images", response_model=PestCurationImageList)
def list_pest_images(label: str, _user: User = Depends(require_platform_admin)) -> PestCurationImageList:
    """List the indexed reference images for a class (gallery + curation source)."""
    payload = _client().list_prototypes(label, limit=200, active_only=False)
    images = [PestCurationImage(**img) for img in payload.get("images", [])]
    return PestCurationImageList(
        label=label,
        count=payload.get("count", len(images)),
        active_count=payload.get("active_count", sum(1 for i in images if i.is_active)),
        images=images,
    )


@router.patch("/{label}/images/{image_id}", response_model=SetPestImageActiveResponse)
def set_pest_image_active(
    label: str,
    image_id: int,
    body: SetPestImageActiveRequest,
    _user: User = Depends(require_platform_admin),
) -> SetPestImageActiveResponse:
    """Activate/deactivate one reference image (manual curation)."""
    _client().set_prototype_active(label, image_id, is_active=body.is_active, reason=body.reason)
    return SetPestImageActiveResponse(label=label, id=image_id, is_active=body.is_active)
