"""The text layer of a PDF as a client sees it (REQ-053 WP 9.10, #2750).

A test that claims a PDF does *not* carry something (a member's name without the assignment opt-in) has to read
the bytes the route returns, not the HTML they were rendered from: a template that hid a column with CSS would pass
an HTML assertion and still print the names. ``pypdf`` decodes the subset fonts through their ``ToUnicode`` maps.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject


def pdf_pages_text(content: bytes) -> list[str]:
    """The extracted text of every page, in page order."""
    reader = PdfReader(BytesIO(content))
    return [page.extract_text() or "" for page in reader.pages]


def pdf_text(content: bytes) -> str:
    """The text of the whole document, pages joined by a newline."""
    return "\n".join(pdf_pages_text(content))


@dataclass(frozen=True)
class PdfAccessibility:
    """What a reader of a tagged PDF relies on (REQ-032 §8, REQ-053 GP-NFR-029), read from the PDF catalog.

    ``structure`` lists the structure elements depth-first - document order, the reading order - as
    ``(role, alternative text)``; it is empty for an untagged PDF.
    """

    tagged: bool
    marked: bool
    lang: str | None
    title: str | None
    display_doc_title: bool
    structure: list[tuple[str, str | None]]


def _walk(node: Any, out: list[tuple[str, str | None]]) -> None:
    node = node.get_object()
    if isinstance(node, ArrayObject):
        for child in node:
            _walk(child, out)
        return
    if not isinstance(node, DictionaryObject):
        return  # a marked-content id: content, not structure
    if "/S" in node:
        alt = node.get("/Alt")
        out.append((str(node["/S"]), str(alt) if alt is not None else None))
    if "/K" in node:
        _walk(node["/K"], out)


def pdf_accessibility(content: bytes) -> PdfAccessibility:
    """The tagging facts of a PDF: structure tree, ``/MarkInfo``, ``/Lang``, the title and ``DisplayDocTitle``."""
    reader = PdfReader(BytesIO(content))
    root = reader.trailer["/Root"].get_object()
    structure: list[tuple[str, str | None]] = []
    tree = root.get("/StructTreeRoot")
    if tree is not None:
        _walk(tree.get_object().get("/K", ArrayObject()), structure)
    mark_info = root.get("/MarkInfo")
    preferences = root.get("/ViewerPreferences")
    metadata = reader.metadata
    return PdfAccessibility(
        tagged=tree is not None,
        marked=bool(mark_info is not None and mark_info.get_object().get("/Marked")),
        lang=str(root["/Lang"]) if "/Lang" in root else None,
        title=metadata.title if metadata is not None else None,
        display_doc_title=bool(preferences is not None and preferences.get_object().get("/DisplayDocTitle")),
        structure=structure,
    )
