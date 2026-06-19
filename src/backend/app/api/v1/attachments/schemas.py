"""NFR-013 — request/response schemas for the attachment API.

Responses reference an attachment *only* by its ``attachment_id`` and stable,
tenant-scoped API URIs (``/api/v1/t/{tenant_slug}/attachments/...``). No bucket
name, storage key, backend type, or presign target is ever exposed (NFR-013
AC-04).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.enums import AttachmentCategory


class ThumbnailUris(BaseModel):
    """Stable, tenant-scoped thumbnail URIs keyed by longest-edge size."""

    small: str = Field(description="128 px longest edge")
    medium: str = Field(description="512 px longest edge")
    large: str = Field(description="1280 px longest edge")


class AttachmentResponse(BaseModel):
    """A single attachment as exposed to the client (NFR-013 AC-04)."""

    attachment_id: str
    category: AttachmentCategory
    mime_type: str
    byte_size: int
    original_filename: str
    uri: str = Field(description="Stable download URI for the original object.")
    thumbnail_uris: ThumbnailUris | None = Field(
        default=None,
        description="Present only for image attachments (renditions may still be generating).",
    )
    created_at: str | None = None


class AttachmentListResponse(BaseModel):
    """Paginated attachment listing."""

    items: list[AttachmentResponse]
    total: int
    offset: int
    limit: int


class PresignUploadRequest(BaseModel):
    """Request a direct-to-storage presigned upload URL."""

    category: AttachmentCategory
    mime_type: str


class PresignUploadResponse(BaseModel):
    """A presigned upload URL (only when the backend supports it)."""

    upload_url: str


class PresignDownloadResponse(BaseModel):
    """An explicit presign/token download URL."""

    download_url: str
