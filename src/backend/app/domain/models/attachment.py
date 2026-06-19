"""NFR-013 §2.2 — domain model for a stored attachment.

An ``Attachment`` is the catalog record that maps a logical upload (a diary
photo, an IPM image, an export archive, ...) to a physical object in the
configured storage backend (``storage_key``). The bytes live in object storage;
this document carries only the metadata needed for listing, deduplication
(``sha256``), DSGVO erasure lookups (``tenant_key`` + ``created_by``) and
serving (``mime_type`` / ``byte_size``).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import AttachmentCategory


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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
