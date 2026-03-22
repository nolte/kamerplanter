"""HTTP middleware components (NFR-007)."""

import uuid

import structlog
from fastapi import Request, Response


async def request_id_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    """Assign a unique request ID to every request for end-to-end tracing.

    If the client sends a valid ``X-Request-ID`` header (UUID4 format), it is
    reused.  Otherwise a new UUID4 is generated.  The ID is bound to structlog
    contextvars so it appears in every log line, and returned as a response
    header for client-side correlation.
    """
    incoming_id = request.headers.get("X-Request-ID")
    if incoming_id:
        try:
            # Validate that the incoming value is a proper UUID
            parsed = uuid.UUID(incoming_id, version=4)
            request_id = str(parsed)
        except (ValueError, AttributeError):
            request_id = str(uuid.uuid4())
    else:
        request_id = str(uuid.uuid4())

    structlog.contextvars.bind_contextvars(request_id=request_id)
    try:
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        structlog.contextvars.clear_contextvars()
