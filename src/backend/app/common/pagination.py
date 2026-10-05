"""Shared list pagination: offset/limit, and a keyset cursor for the heavy lists.

Every route that answers with a ``list[...]`` reads a bounded window: it depends
on :func:`get_pagination` or :func:`get_cursor_pagination`, or it is classified
in the exemption table of ``tests/unit/guards/test_list_routes_are_bounded.py``
with the reason its result cannot grow with tenant data (MT-035, #2131).

The response stays a plain JSON array — no envelope, no total. A client pages
until a page comes back shorter than ``limit`` (offset) or empty (cursor).
"""

from fastapi import Query
from pydantic import BaseModel, Field

from app.common.exceptions import ValidationError


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
    """An ``items``/``total`` envelope. Not used by any route (MT-035, #2131).

    The list routes deliberately keep their array shape: wrapping them would break
    every client, and a ``total`` costs a second scan of the filtered set on every
    page. Kept for a future envelope-shaped route, not as a pending migration.
    """

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


#: The ArangoDB document-key alphabet (``_key`` may hold nothing else) and its
#: length bound. A cursor outside it cannot name a row, so it is refused at the
#: boundary instead of being bound into a query that can only return nothing.
ARANGO_KEY_PATTERN = r"^[A-Za-z0-9_\-:.@()+,=;$!*'%]{1,254}$"


class CursorPaginationParams(PaginationParams):
    """Offset/limit plus an optional keyset cursor (MT-035, #2131).

    ``after`` is the ``key`` of the last row of the previous page. A route that
    accepts it lists in ascending ``_key`` order and reads ``FILTER doc._key >
    @after SORT doc._key LIMIT @limit``: no row before the cursor is counted off,
    where ``LIMIT @offset, @limit`` walks and discards every row before
    ``offset``. ``offset`` and ``after`` are mutually exclusive.
    """

    after: str | None = Field(default=None, pattern=ARANGO_KEY_PATTERN)


def get_cursor_pagination(
    offset: int = Query(
        0,
        ge=0,
        description="Number of items to skip from the start of the result set. Must be 0 when `after` is set.",
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return (1-200)."),
    after: str | None = Query(
        None,
        pattern=ARANGO_KEY_PATTERN,
        description=(
            "Keyset cursor: return only items whose `key` sorts after this value. Pass the `key` of the "
            "last item of the previous page; an empty page ends the list. Cannot be combined with `offset`."
        ),
    ),
) -> CursorPaginationParams:
    """FastAPI dependency for the list routes that also page by keyset (MT-035, #2131).

    The ``offset``/``limit`` pair is declared exactly like :func:`get_pagination`,
    so a client that never sends ``after`` sees the same contract. The list-bound
    guard accepts either dependency as the bound of a ``list[...]`` route.

    Raises:
        ValidationError: ``offset`` and ``after`` were both given — a keyset
            page has no row position to skip from.
    """
    if after is not None and offset:
        raise ValidationError(
            "offset and after cannot be combined",
            details=[{"field": "offset", "reason": "must be 0 when after is set"}],
        )
    return CursorPaginationParams(offset=offset, limit=limit, after=after)


#: Every dependency that bounds a ``list[...]`` route; the list-bound guard reads this tuple.
PAGINATION_DEPENDENCIES = (get_pagination, get_cursor_pagination)
