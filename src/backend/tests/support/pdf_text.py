"""The text layer of a PDF as a client sees it (REQ-053 WP 9.10, #2750).

A test that claims a PDF does *not* carry something (a member's name without the assignment opt-in) has to read
the bytes the route returns, not the HTML they were rendered from: a template that hid a column with CSS would pass
an HTML assertion and still print the names. ``pypdf`` decodes the subset fonts through their ``ToUnicode`` maps.
"""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def pdf_pages_text(content: bytes) -> list[str]:
    """The extracted text of every page, in page order."""
    reader = PdfReader(BytesIO(content))
    return [page.extract_text() or "" for page in reader.pages]


def pdf_text(content: bytes) -> str:
    """The text of the whole document, pages joined by a newline."""
    return "\n".join(pdf_pages_text(content))
