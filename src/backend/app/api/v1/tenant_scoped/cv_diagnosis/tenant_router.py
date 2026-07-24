"""REQ-038 §6 — tenant-scoped CV disease-diagnosis endpoints.

Mounted under ``/t/{tenant_slug}`` by the tenant-scoped parent router. Reads use
``get_current_tenant`` (membership); writes (``/diagnose``, ``/confirm``) require
at least the ``grower`` role (``require_tenant_role``), consistent with the
weather/recognition writers. ``/diagnose`` enforces the ``plant_diagnosis``
consent inside the service before any processing, hardens the upload
(size/type/decode/decompression-bomb) and never persists the image. ``/confirm``
creates an IPM inspection *suggestion* only — never a treatment (§0), so the
Karenz gate is not engaged. Cross-tenant access fails closed with 404 (no oracle).
"""

import io
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Query, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.api.v1.tenant_scoped.cv_diagnosis.schemas import (
    ConfirmDiagnosisRequest,
    ConfirmDiagnosisResponse,
    CvDiagnosisResponse,
    CvDiagnosisStatusResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_cv_diagnosis_service
from app.common.enums import TenantRole
from app.common.exceptions import (
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.config.settings import settings
from app.domain.models.tenant_context import TenantContext
from app.domain.services.cv_diagnosis_service import CvDiagnosisService
from app.domain.services.image_processing import is_supported_image

router = APIRouter(prefix="/cv-diagnosis", tags=["cv-diagnosis"], responses=NOT_FOUND_RESPONSE)

_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})
_UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MiB bounded-read chunk
# SEC-004 decompression-bomb guard — reject implausibly large pixel counts even
# when the encoded bytes are tiny.
_MAX_IMAGE_PIXELS = 40_000_000  # ~6300 x 6300 px


def _parse_content_length(request: Request) -> int | None:
    raw = request.headers.get("content-length")
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)


async def _read_upload_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Read an ``UploadFile`` in bounded chunks, capping memory at ``max_bytes``."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise PayloadTooLargeError(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)


def _validate_image_bytes(image_data: bytes, max_bytes: int) -> None:
    """Validate upload bytes before any inference (SEC-004).

    Oversized/pixel-bomb → 413, wrong type → 415, undecodable → 422 — never a 500.
    """
    if len(image_data) > max_bytes:
        raise PayloadTooLargeError(max_bytes)
    if not is_supported_image(image_data):
        raise UnsupportedMediaTypeError("unknown", ["image/jpeg", "image/png"])
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            width, height = img.size
            if width * height > _MAX_IMAGE_PIXELS:
                raise PayloadTooLargeError(max_bytes)
            img.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationError(
            "The uploaded image could not be decoded.",
            details=[{"field": "image", "reason": "Undecodable image.", "code": "INVALID_IMAGE"}],
        ) from exc


@router.get("/status", response_model=CvDiagnosisStatusResponse)
def cv_diagnosis_status(
    ctx: TenantContext = Depends(get_current_tenant),
    service: CvDiagnosisService = Depends(get_cv_diagnosis_service),
) -> CvDiagnosisStatusResponse:
    """Report whether CV diagnosis is available (feature off → button hidden)."""
    return CvDiagnosisStatusResponse(**service.get_status())


@router.post("/diagnose", response_model=CvDiagnosisResponse)
async def diagnose(
    request: Request,
    image: UploadFile,
    plant_key: str | None = Form(default=None, description="Optional plant instance to bind the diagnosis to"),
    phenotype: bool = Query(default=False, description="Also compute PlantCV phenotype metrics"),
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: CvDiagnosisService = Depends(get_cv_diagnosis_service),
) -> CvDiagnosisResponse:
    """Diagnose disease/deficiency from an uploaded photo (JPEG/PNG, max 5 MB).

    Consent ``plant_diagnosis`` is a hard precondition. EXIF is stripped
    server-side and the image is never persisted. The result always carries a
    non-empty disclaimer and is never an accepted diagnosis — only a hypothesis.
    """
    content_type = (image.content_type or "").lower().strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(_ALLOWED_CONTENT_TYPES))

    max_bytes = settings.cv_diagnosis_max_image_size_mb * 1024 * 1024
    content_length = _parse_content_length(request)
    if content_length is not None and content_length > max_bytes:
        raise PayloadTooLargeError(max_bytes)
    image_data = await _read_upload_bounded(image, max_bytes)
    _validate_image_bytes(image_data, max_bytes)

    result = service.diagnose(
        image_data,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        plant_instance_key=plant_key,
        with_phenotype=phenotype,
    )
    return CvDiagnosisResponse(**result)


@router.post("/diagnose/{request_key}/confirm", response_model=ConfirmDiagnosisResponse, status_code=201)
def confirm_diagnosis(
    request_key: Annotated[str, Path(description="Document key of the diagnosis request.")],
    body: ConfirmDiagnosisRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: CvDiagnosisService = Depends(get_cv_diagnosis_service),
) -> ConfirmDiagnosisResponse:
    """Confirm a diagnosis into an IPM inspection suggestion. Never a treatment (§0).

    Cross-tenant fail-closed: an unknown/foreign request → 404 (no oracle).
    """
    result = service.confirm(
        request_key,
        tenant_key=ctx.tenant_key,
        plant_key=body.plant_key,
        confirmed_labels=body.confirmed_labels,
    )
    return ConfirmDiagnosisResponse(**result)


@router.get("/history", response_model=list[CvDiagnosisResponse])
def diagnosis_history(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of history entries to return."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: CvDiagnosisService = Depends(get_cv_diagnosis_service),
) -> list[CvDiagnosisResponse]:
    """Return the current user's recent diagnosis requests (no images retained)."""
    entries = service.get_history(tenant_key=ctx.tenant_key, user_key=ctx.user_key, limit=limit)
    return [CvDiagnosisResponse(**e) for e in entries]
