from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Standard offset/limit pagination query parameters (DUP-B5).

    The single source of truth for the offset/limit pair that was previously
    copied across ~40 list endpoints.  Consumed through :func:`get_pagination`
    so the individual ``offset``/``limit`` query parameters (and their
    ``ge``/``le`` constraints) stay byte-identical in the OpenAPI schema.
    """

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


#: Backwards-compatible alias for the original (previously unused) name.
PaginatedRequest = PaginationParams


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    offset: int
    limit: int


def get_pagination(
    offset: int = Query(0, ge=0, description="Number of items to skip from the start of the result set."),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return (1-200)."),
) -> PaginationParams:
    """FastAPI dependency yielding the shared offset/limit pagination params.

    Declaring ``offset``/``limit`` as explicit ``Query`` parameters keeps the
    generated OpenAPI contract unchanged (same names, types and constraints)
    while collapsing the 39×/43× duplicated declarations into one place.
    """

    return PaginationParams(offset=offset, limit=limit)
