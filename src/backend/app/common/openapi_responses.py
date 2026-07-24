"""Reusable OpenAPI ``responses=`` maps for the global error envelope.

Documentation-only module (spec/project/api-documentation/): routers compose
these maps into ``APIRouter(responses=...)`` so every actually-returned error
status code is documented per operation. The envelope shape itself is owned by
the global handlers in :mod:`app.common.error_handlers` — ``ErrorResponse``
mirrors it for schema generation and must be kept in sync with them.
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Global error envelope emitted by the exception handlers."""

    error_id: str = Field(description="Unique reference id for support and log correlation.")
    error_code: str = Field(description="Machine-readable error code, e.g. NOT_FOUND or VALIDATION_ERROR.")
    message: str = Field(description="Human-readable error message.")
    details: list[dict[str, Any]] = Field(default_factory=list, description="Optional structured error details.")
    timestamp: str = Field(description="ISO-8601 timestamp of the error.")
    path: str = Field(description="Request path that produced the error.")
    method: str = Field(description="HTTP method of the failing request.")


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


UNAUTHORIZED_RESPONSE: dict[int | str, dict[str, Any]] = {
    401: _error("Missing, invalid, or expired credentials."),
}

FORBIDDEN_RESPONSE: dict[int | str, dict[str, Any]] = {
    403: _error("Authenticated, but not allowed to access this resource."),
}

NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    404: _error("The requested resource does not exist."),
}

CONFLICT_RESPONSE: dict[int | str, dict[str, Any]] = {
    409: _error("A conflicting resource already exists (duplicate key or unique constraint)."),
}

VALIDATION_RESPONSE: dict[int | str, dict[str, Any]] = {
    422: _error("The input data is invalid (field-level details in `details`)."),
}

# Composed profiles for the common router shapes.
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    **UNAUTHORIZED_RESPONSE,
    **FORBIDDEN_RESPONSE,
}

CRUD_RESPONSES: dict[int | str, dict[str, Any]] = {
    **NOT_FOUND_RESPONSE,
    **CONFLICT_RESPONSE,
}

AUTH_CRUD_RESPONSES: dict[int | str, dict[str, Any]] = {
    **AUTH_RESPONSES,
    **CRUD_RESPONSES,
}
