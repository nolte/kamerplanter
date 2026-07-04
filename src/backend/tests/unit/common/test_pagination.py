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
