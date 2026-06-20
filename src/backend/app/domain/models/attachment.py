"""NFR-013 §2.2 — domain model for a stored attachment.

An ``Attachment`` is the catalog record that maps a logical upload (a diary
photo, an IPM image, an export archive, ...) to a physical object in the
configured storage backend (``storage_key``). The bytes live in object storage;
this document carries only the metadata needed for listing, deduplication
(``sha256``), DSGVO erasure lookups (``tenant_key`` + ``created_by``) and
serving (``mime_type`` / ``byte_size``).
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import AttachmentCategory

# REQ-034 §2.1 — upper bound for the user-editable gallery photo caption.
CAPTION_MAX_LENGTH = 500


class Attachment(BaseModel):
    """A catalog record for one object in the storage backend."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    mime_type: str
    byte_size: int
    sha256: str
    original_filename: str
    created_by: str
    category: AttachmentCategory
    storage_key: str
    # REQ-034 §2.1 v1.2 — generic, user-editable photo metadata. Populated for
    # gallery photos (``category == plant``); every other category leaves them
    # ``None``. ``caption`` is a free-text note (<= 500 chars); ``taken_on`` is
    # the capture date the user may override (default/fallback: the upload
    # ``created_at``; the display fallback lives in the frontend). EXIF capture
    # time is unavailable here because EXIF is stripped on upload (NFR-013 §6.4).
    caption: str | None = None
    taken_on: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
