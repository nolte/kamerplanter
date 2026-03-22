from fastapi import APIRouter, Depends, Form, Query, Response, UploadFile

from app.api.v1.imports.schemas import ImportJobResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_import_service
from app.common.enums import DuplicateStrategy, EntityType
from app.common.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError
from app.domain.models.import_job import ImportJob
from app.domain.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(get_current_user)])

# SEC-M-008: Upload security constants
MAX_UPLOAD_SIZE_BYTES = 10_485_760  # 10 MB
ALLOWED_MIME_TYPES = frozenset({
    "text/csv",
    "text/plain",
    "application/csv",
    "application/vnd.ms-excel",
})


def _job_response(job: ImportJob) -> ImportJobResponse:
    return ImportJobResponse(
        key=job.key or "",
        entity_type=job.entity_type.value,
        status=job.status.value,
        filename=job.filename,
        row_count=job.row_count,
        duplicate_strategy=job.duplicate_strategy.value,
        preview_rows=[
            {
                "row_number": r.row_number,
                "data": r.data,
                "status": r.status.value,
                "errors": [e.model_dump() for e in r.errors],
                "duplicate_key": r.duplicate_key,
            }
            for r in job.preview_rows
        ],
        result=job.result.model_dump() if job.result else None,
        error_message=job.error_message,
        uploaded_by=job.uploaded_by,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/upload", response_model=ImportJobResponse, status_code=202)
async def upload_csv(
    file: UploadFile,
    entity_type: EntityType = Form(...),
    duplicate_strategy: DuplicateStrategy = Form(DuplicateStrategy.SKIP),
    service: ImportService = Depends(get_import_service),
):
    # SEC-M-008: Validate MIME type
    content_type = (file.content_type or "").lower().strip()
    if content_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(ALLOWED_MIME_TYPES))

    content = await file.read()

    # SEC-M-008: Validate file size
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise PayloadTooLargeError(MAX_UPLOAD_SIZE_BYTES)

    job = service.upload(content, entity_type, file.filename or "upload.csv", duplicate_strategy)
    return _job_response(job)


@router.post("/jobs/{key}/confirm", response_model=ImportJobResponse)
def confirm_import(
    key: str,
    service: ImportService = Depends(get_import_service),
):
    job = service.confirm(key)
    return _job_response(job)


@router.get("/jobs/{key}", response_model=ImportJobResponse)
def get_job(
    key: str,
    service: ImportService = Depends(get_import_service),
):
    job = service.get_job(key)
    return _job_response(job)


@router.get("/jobs", response_model=list[ImportJobResponse])
def list_jobs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ImportService = Depends(get_import_service),
):
    items, _total = service.list_jobs(offset, limit)
    return [_job_response(j) for j in items]


@router.delete("/jobs/{key}", status_code=204)
def delete_job(
    key: str,
    service: ImportService = Depends(get_import_service),
):
    service.delete_job(key)


@router.get("/templates/{entity_type}")
def get_template(
    entity_type: EntityType,
    service: ImportService = Depends(get_import_service),
):
    csv_content = service.get_template(entity_type)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_type.value}_template.csv"},
    )
