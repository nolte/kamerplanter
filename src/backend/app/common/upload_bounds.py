"""Early ``Content-Length`` reject for multipart uploads (SEC-004, SEC-005, #2144).

Every upload route refuses an oversized body twice: once from the declared
``Content-Length`` before a byte is read, and again while the file is streamed
in bounded chunks. The two checks measure different things. The bounded read
counts FILE bytes and is the exact limit. ``Content-Length`` declares the whole
multipart BODY — the file plus its boundaries, part headers (file name, content
type) and the small form fields beside it.

Comparing the declared body with the file limit refused a file of exactly the
allowed size with 413 before it was read (#2144). The early reject therefore
allows :data:`MULTIPART_ENVELOPE_BYTES` on top of the file limit: generous for
the envelope of every upload route here (a few hundred bytes in practice), and
far below the edge proxy's 1 MiB headroom, so a body between the two still gets
the backend's typed 413 instead of nginx's.
"""

from __future__ import annotations

from fastapi import Request

#: Allowance for the multipart envelope around the file in the early
#: ``Content-Length`` reject. It never widens the file limit itself — the
#: bounded read still refuses one byte more than the file limit.
MULTIPART_ENVELOPE_BYTES = 64 * 1024


def declared_content_length(request: Request) -> int | None:
    """Return the request ``Content-Length`` as an int, or ``None`` if absent/invalid."""
    raw = request.headers.get("content-length")
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)


def declared_body_exceeds(request: Request, max_file_bytes: int) -> bool:
    """Whether the declared body cannot carry a file of at most ``max_file_bytes``.

    ``True`` only when ``Content-Length`` is present and larger than the file
    limit plus :data:`MULTIPART_ENVELOPE_BYTES`. A missing or invalid header is
    ``False``: the bounded read then enforces the limit on the bytes themselves.
    """
    declared = declared_content_length(request)
    return declared is not None and declared > max_file_bytes + MULTIPART_ENVELOPE_BYTES
