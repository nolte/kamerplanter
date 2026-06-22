"""REQ-010 — user-contributed pest reference images.

A :class:`PestImageContribution` links a (tenant-private) uploaded attachment
to a *global* pest record (``pests`` are global reference data). A contribution
is uploaded ``PRIVATE`` (visible only to its tenant); a platform admin may
``PROMOTE`` it, after which its pixels are served globally (cross-tenant) via a
dedicated read-only content endpoint. ``promoted_at`` / ``promoted_by`` record
the moderation decision.

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
    # PRIVATE on upload; a platform admin may PROMOTE it to global visibility
    # (Phase 2 curation). Promotion is the gate for cross-tenant pixel access.
    status: PestImageStatus = PestImageStatus.PRIVATE
    # REQ-010 curation — a platform admin may *deselect* (hide) an image instead
    # of deleting it. Deselected images stay catalogued (audit / re-include) but
    # are excluded from the default gallery for everyone. Backward compatible:
    # documents written before this field default to ``True`` (Pydantic default),
    # so an existing contribution remains visible.
    is_active: bool = True
    # Promotion audit (set on PRIVATE → PROMOTED, cleared on demotion). Records
    # the platform-admin user_key and the moment of the global release.
    promoted_at: datetime | None = None
    promoted_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
