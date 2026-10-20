"""Doubles for the garden-plan underlay (REQ-053 WP 7.14): an attachment repository and the slice of
``AttachmentService`` the underlay uses (``get_attachment``, ``open_stream``, ``delete``)."""

from __future__ import annotations

import io
from typing import cast

from PIL import Image

from app.common.enums import AttachmentCategory
from app.common.exceptions import AttachmentNotFoundError, NotFoundError
from app.domain.models.attachment import Attachment
from app.domain.services.attachment_service import AttachmentService


def png_bytes(width: int = 800, height: int = 400, colour: tuple[int, int, int] = (200, 220, 180)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="PNG")
    return buffer.getvalue()


class FakeUnderlayAttachments:
    """Repository and service in one: ``get`` is tenant-scoped, ``delete`` records what it was asked to remove."""

    def __init__(self, sites: dict | None = None) -> None:
        #: The sites whose ``plan.underlay`` names an attachment: the reference scan of the real service.
        self._sites = sites if sites is not None else {}
        self.rows: dict[str, Attachment] = {}
        self.bodies: dict[str, bytes] = {}
        self.deleted: list[tuple[str, str]] = []
        #: Attachment ids whose record exists but whose stored object is gone.
        self.lost_objects: set[str] = set()

    def add(
        self,
        key: str,
        *,
        tenant_key: str,
        category: AttachmentCategory = AttachmentCategory.GARDEN_PLAN_UNDERLAY,
        body: bytes | None = None,
        storage_key: str | None = None,
    ) -> None:
        self.rows[key] = Attachment(
            _key=key,
            tenant_key=tenant_key,
            mime_type="image/png",
            byte_size=10,
            sha256="0" * 64,
            original_filename="plan.png",
            created_by="u_sabine",
            category=category,
            storage_key=storage_key or f"t/{tenant_key}/{category.value}/{key}.png",
        )
        self.bodies[key] = body if body is not None else png_bytes()

    # repository ------------------------------------------------------------
    def get(self, key: str, tenant_key: str) -> Attachment | None:
        row = self.rows.get(key)
        return row if row is not None and row.tenant_key == tenant_key else None

    # service ----------------------------------------------------------------
    def get_attachment(self, attachment_id: str, tenant_key: str) -> Attachment:
        row = self.get(attachment_id, tenant_key)
        if row is None:
            raise AttachmentNotFoundError(attachment_id)
        return row

    async def open_stream(self, attachment: Attachment):
        if attachment.key in self.lost_objects:
            raise NotFoundError("StoredObject", attachment.storage_key)
        body = self.bodies[attachment.key or ""]

        async def chunks():
            yield body

        return chunks()

    async def delete(self, attachment_id: str, tenant_key: str) -> bool:
        self.deleted.append((attachment_id, tenant_key))
        return self.rows.pop(attachment_id, None) is not None

    async def delete_if_unreferenced(self, attachment_id: str, tenant_key: str) -> bool:
        """Like the real one: a picture some site still names stays."""
        for site in self._sites.values():
            if (
                site.plan is not None
                and site.plan.underlay is not None
                and site.plan.underlay.attachment_key == attachment_id
            ):
                return False
        return await self.delete(attachment_id, tenant_key)

    def as_service(self) -> AttachmentService:
        return cast("AttachmentService", self)
