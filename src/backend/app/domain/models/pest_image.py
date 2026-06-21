"""REQ-010 — user-contributed pest reference images.

A :class:`PestImageContribution` links a (tenant-private) uploaded attachment
to a *global* pest record (``pests`` are global reference data). Phase 1 keeps
every contribution scoped to the contributing tenant; the ``status`` field is
already modelled so the later global-promotion phase needs no migration.

The binary image itself lives in object storage and is catalogued as an
``Attachment`` (NFR-013); this document only references it via ``attachment_id``.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import PestImageStatus


class PestImageContribution(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    # Owning tenant — the isolation boundary. A contribution is only ever
    # visible to / deletable by its own tenant in Phase 1.
    tenant_key: str = Field(min_length=1)
    # Global pest this image documents (``pests`` collection key).
    pest_key: str = Field(min_length=1)
    # NFR-013 attachment catalog key for the stored (EXIF-stripped) image.
    attachment_id: str = Field(min_length=1)
    # User who contributed the image (for "is_own" display + DSGVO lookup).
    contributed_by: str = Field(min_length=1)
    caption: str | None = Field(default=None, max_length=500)
    # Phase 1 always PRIVATE; PROMOTED is reserved for global curation (Phase 2).
    status: PestImageStatus = PestImageStatus.PRIVATE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
