"""REQ-029 — tenant-scoped plant-identification endpoints.

Mounted under /api/v1/t/{tenant_slug}/identification/. All endpoints require
authentication and tenant membership via ``get_current_tenant``. ``/identify``
additionally enforces the ``plant_identification`` consent inside the service
(REQ-029-A §0.1.1 point 2) before any photo leaves the instance.
"""

import io

from fastapi import APIRouter, Depends, Form, Query, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.api.v1.recognition.schemas import (
    HistoryEntryResponse,
    IdentifyResponse,
    ReferenceContributionResponse,
    SelectResultResponse,
    SuggestionResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_identification_service, get_reference_image_service
from app.common.enums import TenantRole
from app.common.exceptions import (
    AdapterNotAvailableError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from app.config.settings import settings
from app.domain.interfaces.plant_identification_adapter import PlantOrgan
from app.domain.models.tenant_context import TenantContext
from app.domain.services.identification_service import IdentificationService
from app.domain.services.image_processing import is_supported_image
from app.domain.services.reference_image_service import ReferenceImageService

router = APIRouter(prefix="/identification", tags=["identification"])

_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})

# Chunk size for the bounded streaming upload read (1 MiB).
_UPLOAD_CHUNK_SIZE = 1024 * 1024

# SEC-004 — decompression-bomb guard: reject images whose pixel count is
# implausible for a plant photo even when the encoded bytes are tiny.
_MAX_IMAGE_PIXELS = 40_000_000  # ~6300 x 6300 px


def _parse_organ(value: str) -> PlantOrgan:
    try:
        return PlantOrgan(value)
    except ValueError as exc:
        raise UnsupportedMediaTypeError(value, [o.value for o in PlantOrgan]) from exc


def _parse_content_length(request: Request) -> int | None:
    """Return the request ``Content-Length`` as an int, or ``None`` if absent/invalid."""
    raw = request.headers.get("content-length")
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)


async def _read_upload_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Read an ``UploadFile`` in bounded chunks, capping memory at ``max_bytes``.

    Raises :class:`PayloadTooLargeError` as soon as the running byte count
    exceeds ``max_bytes`` — without buffering the rest of the body (SEC-004).
    """
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


def _validate_reference_image(image_data: bytes, max_bytes: int) -> None:
    """Validate reference-upload bytes before any embedding work (SEC-004).

    Enforces the size cap, the JPEG/PNG magic-byte allow-list, real decodability
    and a decompression-bomb guard. A corrupt/undecodable image is a 422, an
    oversized/pixel-bomb image a 413, a wrong type a 415 — never a 500.
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


@router.post("/identify", response_model=IdentifyResponse)
async def identify_plant(
    image: UploadFile,
    organ: str = Form("auto", description="leaf, flower, fruit, bark, habit, auto"),
    language: str = Form("de"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> IdentifyResponse:
    """Identify a plant from an uploaded image (JPEG/PNG, max 5 MB).

    Consent ``plant_identification`` is a hard precondition: the photo is sent
    to Pl@ntNet (Phase-1 primary), EXIF-stripped and normalized beforehand, and
    is never persisted. Returns rank-sorted suggestions for explicit selection.
    """
    content_type = (image.content_type or "").lower().strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(_ALLOWED_CONTENT_TYPES))

    image_data = await image.read()
    parsed_organ = _parse_organ(organ)

    result = service.identify_plant(
        image_data,
        organ=parsed_organ,
        language=language,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
    )
    return IdentifyResponse(**result)


@router.post("/reference", response_model=ReferenceContributionResponse, status_code=202)
async def contribute_reference(
    request: Request,
    image: UploadFile,
    species_key: str = Form(..., description="Resolved species key to attach the reference to"),
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ReferenceImageService = Depends(get_reference_image_service),
) -> ReferenceContributionResponse:
    """Reuse an identification photo as a DINOv2 few-shot recognition reference.

    Issue #447 — opt-in step of the "reuse identification photo" flow. Only
    available when the self-hosted DINOv2 adapter is configured
    (``inference_service_enabled``); the external Pl@ntNet path has no local
    reference index, so the frontend hides the toggle there.

    Security (SEC-001..006 review):

    * The contribution is written **quarantined** (``is_active=False``,
      ``source="user_contributed"``) — it does NOT affect the active, global
      recognition index until a platform admin activates it in the reference-
      image curation view. A cross-tenant contribution therefore cannot silently
      change what other tenants' identifications return.
    * At least the ``grower`` role is required — a ``viewer`` cannot contribute.
    * ``species_key`` is validated server-side and the scientific name is derived
      from the master record (any client-supplied name is ignored). A per-user
      daily quota, image dedup, upload size/type/decode/bomb validation and
      contributor provenance are enforced in the service / here.

    The photo is embedded locally; only the embedding + provenance are indexed —
    the original image is never persisted (REQ-029-A §4.4) and no third-party
    egress happens on this self-hosted path.
    """
    if not settings.inference_service_enabled:
        raise AdapterNotAvailableError(
            "local_embedding",
            "the self-hosted DINOv2 inference-service is not enabled",
        )

    content_type = (image.content_type or "").lower().strip()
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(_ALLOWED_CONTENT_TYPES))

    # SEC-004 — reject oversized uploads before buffering, then bound the read
    # and fully validate the bytes (magic/decode/bomb) before any embedding.
    max_bytes = settings.identification_max_image_size_mb * 1024 * 1024
    content_length = _parse_content_length(request)
    if content_length is not None and content_length > max_bytes:
        raise PayloadTooLargeError(max_bytes)
    image_data = await _read_upload_bounded(image, max_bytes)
    _validate_reference_image(image_data, max_bytes)

    result = service.contribute_user_reference(
        species_key,
        image_data,
        user_key=ctx.user_key,
        tenant_key=ctx.tenant_key,
    )
    return ReferenceContributionResponse(
        accepted=bool(result.get("accepted", True)),
        pending_review=bool(result.get("pending_review", True)),
        species_key=species_key,
        dim=result.get("dim"),
    )


@router.post("/{request_key}/select", response_model=SelectResultResponse)
def select_result(
    request_key: str,
    selected_rank: int = Query(..., ge=1, le=10),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> SelectResultResponse:
    """Persist the user's explicit candidate choice (REQ-029-A §0.1.1 point 3).

    The returned ``matched_species_key`` / scientific name drives the
    'create plant' step (PlantInstance + species link). No silent auto-create.
    """
    result = service.select_result(
        request_key,
        selected_rank,
        tenant_key=ctx.tenant_key,
    )
    return SelectResultResponse(**result)


@router.get("/history", response_model=list[HistoryEntryResponse])
def identification_history(
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IdentificationService = Depends(get_identification_service),
) -> list[HistoryEntryResponse]:
    """Return the current user's recent identification requests (no images)."""
    entries = service.get_history(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        limit=limit,
    )
    return [
        HistoryEntryResponse(
            key=e.get("key"),
            adapter_key=e["adapter_key"],
            request_type=e["request_type"],
            image_organ=e["image_organ"],
            status=e["status"],
            results=[SuggestionResponse(**r) for r in e.get("results", [])],
            selected_result_rank=e.get("selected_result_rank"),
            created_at=str(e["created_at"]) if e.get("created_at") else None,
        )
        for e in entries
    ]
