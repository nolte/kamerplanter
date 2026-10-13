"""Review follow-up to #2030 — only the duplicate refusal is absorbed when creating a seed-identity index.

``ensure_unique_index_when_clean`` read every ``IndexCreateError`` as "duplicates block
it" and returned ``False``. A permission or server fault then left the collection
without its concurrency guard and was logged as if rows were duplicated.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.exceptions import IndexCreateError

from app.data_access.arango.collections import ensure_unique_index_when_clean


def _error(code: int) -> IndexCreateError:
    error = IndexCreateError.__new__(IndexCreateError)
    error.error_code = code
    error.error_message = "injected"
    return error


class _Collection:
    def __init__(self, code: int) -> None:
        self._code = code

    def indexes(self) -> list[dict[str, Any]]:
        return []

    def add_persistent_index(self, **_kwargs: Any) -> None:
        raise _error(self._code)


def test_duplicates_leave_the_collection_unconstrained_and_report_it() -> None:
    assert ensure_unique_index_when_clean(_Collection(1210), ["a"]) is False  # type: ignore[arg-type]


@pytest.mark.parametrize("code", [11, 1004, 1203])  # forbidden, read-only, collection not found
def test_any_other_index_failure_is_raised(code: int) -> None:
    with pytest.raises(IndexCreateError):
        ensure_unique_index_when_clean(_Collection(code), ["a"])  # type: ignore[arg-type]
