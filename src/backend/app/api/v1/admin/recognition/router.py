"""REQ-029-A — Admin API for the DINOv2 recognition status view.

Aggregates feature flag, primary adapter, inference-service liveness + model
metadata, reference-index coverage and non-secret config into one call for the
admin UI. Platform-admin only; global (recognition is a system-wide concern).
"""

from fastapi import APIRouter, Depends

from app.api.v1.admin.recognition.schemas import (
    AcquisitionStartResponse,
    CoverageSummary,
    InferenceServiceStatus,
    RecognitionConfig,
    RecognitionStatusResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_reference_image_repo, get_species_repo
from app.common.openapi_responses import UNAUTHORIZED_RESPONSE
from app.config.settings import settings
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.domain.models.user import User

router = APIRouter(prefix="/admin/recognition", tags=["admin-recognition"], responses=UNAUTHORIZED_RESPONSE)


@router.get("/status", response_model=RecognitionStatusResponse)
def get_recognition_status(_user: User = Depends(get_current_user)) -> RecognitionStatusResponse:
    """Aggregated status of the self-hosted DINOv2 recognition feature."""
    client = InferenceServiceClient(settings.inference_service_url)
    ready = client.is_ready() if settings.inference_service_enabled else False
    info = client.modelinfo() if ready else None

    rows = get_reference_image_repo().coverage_report()
    usable = sum(1 for r in rows if r.get("usable_for_recognition"))
    # Total = all species in the system (not just those already acquired), so the
    # coverage reads "0 of 210" before the first acquisition run, not "0 of 0".
    _, total_species = get_species_repo().get_all(offset=0, limit=1)

    # Is the local DINOv2 adapter registered and configured?
    from app.domain.services.identification_registry import IdentificationAdapterRegistry

    try:
        local = IdentificationAdapterRegistry.get("local_embedding")
        local_available = local.is_configured()
    except KeyError:
        local_available = False

    return RecognitionStatusResponse(
        feature_enabled=settings.inference_service_enabled,
        local_adapter_available=local_available,
        inference_service=InferenceServiceStatus(
            enabled=settings.inference_service_enabled,
            url=settings.inference_service_url,
            ready=ready,
            model=(info or {}).get("model"),
            dim=(info or {}).get("dim"),
            license=(info or {}).get("license"),
        ),
        coverage=CoverageSummary(
            total_species=total_species,
            processed_species=len(rows),
            usable_species=usable,
        ),
        config=RecognitionConfig(
            primary_adapter=settings.identification_primary_adapter,
            confidence_auto_accept=settings.identification_confidence_auto_accept,
            confidence_min_show=settings.identification_confidence_min_show,
            reference_image_min_usable=settings.reference_image_min_usable,
            use_wikimedia=settings.reference_image_use_wikimedia,
        ),
    )


@router.post("/acquire", response_model=AcquisitionStartResponse, status_code=202)
def start_acquisition(_user: User = Depends(get_current_user)) -> AcquisitionStartResponse:
    """Dispatch a reference-image acquisition run for all species (from the UI).

    UI-facing counterpart to the platform-admin ``/admin/reference-images/acquire``
    endpoint: get_current_user-gated and available in light + full mode, so the
    "start acquisition" button in the settings card works in both.
    """
    from app.tasks.reference_image_tasks import acquire_all_reference_images_task

    task = acquire_all_reference_images_task.delay()
    return AcquisitionStartResponse(status="queued", task_id=getattr(task, "id", None))
