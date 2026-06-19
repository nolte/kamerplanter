"""REQ-029-A §4 — Admin API to drive reference-image acquisition.

Platform-admin-only. Reference images / embeddings are a global resource (not
tenant-scoped), so these endpoints live under ``/admin/reference-images``.
Acquisition itself runs asynchronously via Celery; these endpoints dispatch the
tasks and expose the coverage report.
"""

import httpx
from fastapi import APIRouter, Depends

from app.api.v1.admin.reference_images.schemas import (
    AcquireResponse,
    CoverageEntry,
    CoverageReport,
    CurationImage,
    CurationImageList,
    SetImageActiveRequest,
    SetImageActiveResponse,
)
from app.common.auth import require_platform_admin
from app.common.dependencies import get_reference_image_repo, get_species_repo
from app.common.exceptions import NotFoundError
from app.config.settings import settings
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.models.user import User

router = APIRouter(prefix="/admin/reference-images", tags=["admin-reference-images"])


@router.post("/acquire", response_model=AcquireResponse, status_code=202)
def acquire_all(_user: User = Depends(require_platform_admin)) -> AcquireResponse:
    """Dispatch acquisition for every species (initial index build)."""
    from app.tasks.reference_image_tasks import acquire_all_reference_images_task

    task = acquire_all_reference_images_task.delay()
    return AcquireResponse(status="queued", scope="all", task_id=getattr(task, "id", None))


@router.post("/acquire/{species_key}", response_model=AcquireResponse, status_code=202)
def acquire_species(
    species_key: str,
    _user: User = Depends(require_platform_admin),
) -> AcquireResponse:
    """Dispatch (re-)acquisition for a single species."""
    from app.tasks.reference_image_tasks import acquire_reference_images_task

    species = get_species_repo().get_by_key(species_key)
    if species is None:
        raise NotFoundError("Species", species_key)

    task = acquire_reference_images_task.delay(species_key, species.scientific_name)
    return AcquireResponse(
        status="queued",
        scope="species",
        species_key=species_key,
        task_id=getattr(task, "id", None),
    )


@router.get("/coverage", response_model=CoverageReport)
def get_coverage(_user: User = Depends(require_platform_admin)) -> CoverageReport:
    """Return the reference-image coverage report across all species."""
    rows = get_reference_image_repo().coverage_report()
    entries = [CoverageEntry(**row) for row in rows]
    usable = sum(1 for e in entries if e.usable_for_recognition)
    return CoverageReport(total_species=len(entries), usable_species=usable, entries=entries)


@router.get("/{species_key}/images", response_model=CurationImageList)
def list_curation_images(
    species_key: str,
    _user: User = Depends(require_platform_admin),
) -> CurationImageList:
    """List ALL reference images for a species (incl. deselected) for curation."""
    species = get_species_repo().get_by_key(species_key)
    if species is None:
        raise NotFoundError("Species", species_key)

    client = InferenceServiceClient(settings.inference_service_url)
    rows = client.list_references(species_key, limit=200)
    images = [
        CurationImage(
            id=r["id"],
            source_url=r.get("source_url", ""),
            license=r.get("license"),
            attribution=r.get("attribution"),
            organ=r.get("organ"),
            source=r.get("source"),
            is_active=r.get("is_active", True),
            exclusion_reason=r.get("exclusion_reason"),
        )
        for r in rows
        if r.get("source_url") and r.get("id") is not None
    ]
    active_count = sum(1 for img in images if img.is_active)
    return CurationImageList(
        species_key=species_key,
        count=len(images),
        active_count=active_count,
        images=images,
    )


@router.patch("/{species_key}/images/{image_id}", response_model=SetImageActiveResponse)
def set_image_active(
    species_key: str,
    image_id: int,
    body: SetImageActiveRequest,
    _user: User = Depends(require_platform_admin),
) -> SetImageActiveResponse:
    """Deselect or re-include one reference image (manual visual-test curation).

    Deselected images are kept (audit trail) but filtered out of recognition.
    """
    client = InferenceServiceClient(settings.inference_service_url)
    try:
        client.set_reference_active(
            species_key,
            image_id,
            is_active=body.is_active,
            reason=body.reason,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError("ReferenceImage", str(image_id)) from exc
        raise
    return SetImageActiveResponse(
        species_key=species_key,
        id=image_id,
        is_active=body.is_active,
    )
