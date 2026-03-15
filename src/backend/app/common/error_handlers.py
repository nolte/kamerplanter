import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError

    from app.common.exceptions import KamerplanterError

logger = structlog.get_logger()


async def app_error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    """Handler for all KamerplanterError subclasses."""
    logger.warning(
        "app_error",
        error_id=exc.error_id,
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_id": exc.error_id,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(UTC).isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for Pydantic validation errors."""
    error_id = f"err_{uuid.uuid4()}"
    details = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "reason": err["msg"],
            "code": err["type"],
        }
        for err in exc.errors()
    ]
    logger.warning(
        "validation_error",
        error_id=error_id,
        path=request.url.path,
        method=request.method,
        detail_count=len(details),
    )
    return JSONResponse(
        status_code=422,
        content={
            "error_id": error_id,
            "error_code": "VALIDATION_ERROR",
            "message": "The input data is invalid.",
            "details": details,
            "timestamp": datetime.now(UTC).isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected errors - never expose internal details."""
    error_id = f"err_{uuid.uuid4()}"
    logger.error(
        "unhandled_error",
        error_id=error_id,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_id": error_id,
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred. Please contact support with the reference ID.",
            "details": [],
            "timestamp": datetime.now(UTC).isoformat(),
            "path": request.url.path,
            "method": request.method,
        },
    )
