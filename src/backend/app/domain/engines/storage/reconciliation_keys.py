"""Which attachment-record keys can hold a stored object key (#1834).

The reconciliation walks the object store and asks the ``attachments`` catalogue
whether anything still holds what it finds. An *original* is held by a record
whose ``storage_key`` is that key. A *rendition* (a WebP preview, NFR-013 §8.2)
has no record of its own: it is held by whatever holds the original it was
rendered from, and the original's extension is not part of the rendition's key.

A rendition is therefore mapped to every original key it could have been rendered
from — one per renderable extension — and counts as held when any of them is.
Over-matching is the safe direction for a job that deletes: it can only keep an
object, never remove one a record still needs.
"""

from __future__ import annotations

import re

from app.domain.engines.storage.storage_key_builder import MIME_TO_EXTENSION
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, can_render

#: The tenant namespace this reconciliation covers (``t/{tenant}/…``). Everything
#: outside it — GDPR export bundles under ``privacy/exports/`` — has its own
#: lifecycle and its own record (``data_exports``) and is never touched here.
TENANT_NAMESPACE = "t/"

_RENDITION = re.compile(r"^(?P<stem>.+)_t(?P<size>\d+)\.webp$")

#: Extensions an original can have whose MIME type the generator renders.
_RENDERABLE_EXTENSIONS: tuple[str, ...] = tuple(
    sorted({ext for mime, ext in MIME_TO_EXTENSION.items() if can_render(mime)})
)


def holder_candidates(storage_key: str) -> set[str]:
    """Every ``attachments.storage_key`` value that would hold *storage_key*.

    Always includes the key itself. A key shaped like a rendition adds the
    originals it may have been rendered from.
    """
    candidates = {storage_key}
    match = _RENDITION.match(storage_key)
    if match is not None and int(match.group("size")) in THUMBNAIL_SIZES:
        stem = match.group("stem")
        candidates.update(f"{stem}.{ext}" for ext in _RENDERABLE_EXTENSIONS)
    return candidates


def is_reconcilable(storage_key: str) -> bool:
    """Whether *storage_key* is an object this reconciliation may judge.

    Only tenant-namespace objects in canonical form: not a directory marker an
    S3-compatible backend lists for an empty "folder", and not a name the local-fs
    adapter would resolve to a *different* file than the one listed (a backslash,
    an empty or dot segment). The application never writes such a key; one that
    appears came from outside, and judging it could end in deleting another object.
    """
    if not storage_key.startswith(TENANT_NAMESPACE) or storage_key.endswith("/") or "\\" in storage_key:
        return False
    return all(segment not in ("", ".", "..") for segment in storage_key.split("/"))
