"""Unit tests for the shared pagination dependency (AP-17 / DUP-B5).

The offset/limit pair was previously copied across ~40 list endpoints. These
tests pin the constraints (``ge``/``le``) and the pass-through behaviour of the
``get_pagination`` FastAPI dependency so the collapsed declaration stays
contract-identical.
"""

import pytest
from pydantic import ValidationError

from app.common.pagination import PaginatedRequest, PaginationParams, get_pagination


def test_defaults_match_previous_query_defaults():
    params = PaginationParams()
    assert params.offset == 0
    assert params.limit == 50


def test_get_pagination_passes_values_through():
    params = get_pagination(offset=10, limit=5)
    assert isinstance(params, PaginationParams)
    assert params.offset == 10
    assert params.limit == 5


def test_paginated_request_is_backwards_compatible_alias():
    assert PaginatedRequest is PaginationParams


def test_negative_offset_rejected():
    with pytest.raises(ValidationError):
        PaginationParams(offset=-1)


def test_limit_above_maximum_rejected():
    with pytest.raises(ValidationError):
        PaginationParams(limit=201)


def test_limit_zero_rejected():
    with pytest.raises(ValidationError):
        PaginationParams(limit=0)


# ── keyset cursor (MT-035, #2131) ────────────────────────────────────────────


def test_cursor_pagination_passes_the_cursor_through():
    from app.common.pagination import CursorPaginationParams, get_cursor_pagination

    params = get_cursor_pagination(offset=0, limit=7, after="12345")
    assert isinstance(params, CursorPaginationParams)
    assert (params.offset, params.limit, params.after) == (0, 7, "12345")


def test_cursor_pagination_without_a_cursor_is_plain_offset_paging():
    from app.common.pagination import get_cursor_pagination

    params = get_cursor_pagination(offset=40, limit=20, after=None)
    assert (params.offset, params.limit, params.after) == (40, 20, None)


def test_cursor_and_offset_cannot_be_combined():
    from app.common.exceptions import ValidationError as DomainValidationError
    from app.common.pagination import get_cursor_pagination

    with pytest.raises(DomainValidationError) as raised:
        get_cursor_pagination(offset=1, limit=5, after="12345")
    assert raised.value.status_code == 422


@pytest.mark.parametrize("after", ["", "has space", "slash/inside", "x" * 255, 'quote"'])
def test_a_cursor_outside_the_key_alphabet_is_refused(after):
    from app.common.pagination import CursorPaginationParams

    with pytest.raises(ValidationError):
        CursorPaginationParams(after=after)


@pytest.mark.parametrize("after", ["12345", "plant_a-1", "a:b.c@d(e)+f,g=h;i$j!k*l'm%n", "x" * 254])
def test_every_arango_key_spelling_is_a_valid_cursor(after):
    from app.common.pagination import CursorPaginationParams

    assert CursorPaginationParams(after=after).after == after
