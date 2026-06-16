"""REQ-029-A §4 — Admin API to drive reference-image acquisition.

Platform-admin-only. Reference images / embeddings are a global resource (not
tenant-scoped), so these endpoints live under ``/admin/reference-images``.
Acquisition itself runs asynchronously via Celery; these endpoints dispatch the
tasks and expose the coverage report.
"""

from fastapi import APIRouter, Depends

from app.api.v1.admin.reference_images.schemas import (
    AcquireResponse,
    CoverageEntry,
    CoverageReport,
)
from app.common.auth import require_platform_admin
from app.common.dependencies import get_reference_image_repo, get_species_repo
from app.common.exceptions import NotFoundError
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
