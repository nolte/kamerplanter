"""The HTTP side of a CSV download (REQ-053 GP-FR-104, GP-FR-145; WP 8.4, WP 8.25).

:mod:`app.common.csv_export` writes the file; this module is what every route that offers ``format=csv`` shares around
it, so the care log and the bed list cannot drift apart:

* :data:`CsvDelimiter` / :data:`CSV_DELIMITERS` - the ``delimiter`` query parameter (``semicolon`` is the Excel variant
  with a decimal comma);
* :func:`csv_not_requested` - the ``exempt_when`` of an export budget: only ``format=csv`` is counted, the JSON form of
  the same list never;
* :func:`csv_download` - the response: an attachment with a dated file name, never sniffed, never cached (a download
  may name members).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from typing import Literal

from fastapi import Request
from fastapi.responses import Response

from app.common.csv_export import encode_csv

#: The ``delimiter`` query parameter of a CSV download.
CsvDelimiter = Literal["comma", "semicolon"]

CSV_DELIMITERS: dict[str, str] = {"comma": ",", "semicolon": ";"}

#: The headers of every CSV download besides its ``Content-Disposition``.
CSV_DOWNLOAD_HEADERS: dict[str, str] = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}


def csv_not_requested(request: Request) -> bool:
    """``exempt_when`` of an export budget: ``True`` (exempt) unless the request asks for ``format=csv``."""
    return request.query_params.get("format") != "csv"


def csv_download(
    header: Sequence[str],
    rows: Iterable[Sequence[str]],
    *,
    delimiter: CsvDelimiter,
    filename_stem: str,
) -> Response:
    """The file as a download named ``<filename_stem>-YYYYMMDD.csv`` (UTC day); cells must already be neutralised."""
    body = encode_csv(header, rows, delimiter=CSV_DELIMITERS[delimiter])
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={**CSV_DOWNLOAD_HEADERS, "Content-Disposition": f'attachment; filename="{filename_stem}-{stamp}.csv"'},
    )
