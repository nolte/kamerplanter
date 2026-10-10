"""#2144 — the early Content-Length reject allows the multipart envelope, not more.

The API tests (``tests/api/test_attachments_router.py``,
``tests/api/test_cv_diagnosis_router.py``) send a file of exactly the limit
through the real routes; this file pins the boundary of the shared predicate
itself, so every route that calls it shares the same edge.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.common.upload_bounds import (
    MULTIPART_ENVELOPE_BYTES,
    declared_body_exceeds,
    declared_content_length,
)

_LIMIT = 5 * 1024 * 1024


def _request(content_length: str | None) -> Any:
    headers = {} if content_length is None else {"content-length": content_length}
    return SimpleNamespace(headers=headers)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("123", 123), (" 42 ", 42), (None, None), ("", None), ("-1", None), ("12abc", None)],
)
def test_declared_content_length_reads_only_a_plain_number(raw: str | None, expected: int | None) -> None:
    assert declared_content_length(_request(raw)) == expected


def test_a_body_carrying_a_file_of_exactly_the_limit_and_its_envelope_passes() -> None:
    assert not declared_body_exceeds(_request(str(_LIMIT + MULTIPART_ENVELOPE_BYTES)), _LIMIT)


def test_a_body_one_byte_beyond_limit_and_envelope_is_refused() -> None:
    assert declared_body_exceeds(_request(str(_LIMIT + MULTIPART_ENVELOPE_BYTES + 1)), _LIMIT)


@pytest.mark.parametrize("raw", [None, "not-a-number"])
def test_an_absent_or_invalid_header_leaves_the_decision_to_the_bounded_read(raw: str | None) -> None:
    assert not declared_body_exceeds(_request(raw), _LIMIT)


def test_the_envelope_stays_below_the_edge_proxy_headroom() -> None:
    # nginx allows file limit + 1 MiB (test_proxy_body_limit.py); a body between
    # the backend bound and the proxy bound must reach the backend's typed 413.
    assert 0 < MULTIPART_ENVELOPE_BYTES < 1024 * 1024
