"""REQ-010 — global (cross-tenant) promoted pest-image content router tests.

House style: router functions invoked directly with a fake service. The central
guarantee under test is the SECURITY contract — the global content endpoint must
serve ONLY promoted images and 404 everything else (private / unknown), so a
private (own or foreign) image can never leak through the un-gated global path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.responses import StreamingResponse

from app.api.v1.ipm import pest_images_router
from app.common.enums import PestImageStatus
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.attachment import Attachment
from app.domain.models.pest_image import PestImageContribution
from app.domain.services.pest_image_service import PestImageContent


def _attachment(key: str = "att1", mime: str = "image/jpeg") -> Attachment:
    return Attachment(
        _key=key,
        tenant_key="t1",
        mime_type=mime,
        byte_size=10,
        sha256="a" * 64,
        original_filename="a.jpg",
        created_by="u1",
        category="pest_reference",  # type: ignore[arg-type]
        storage_key=f"t1/{key}",
        created_at=datetime.now(UTC),
    )


def _content(*, status=PestImageStatus.PROMOTED, mime="image/jpeg") -> PestImageContent:
    contribution = PestImageContribution(
        _key="pic1",
        tenant_key="t1",
        pest_key="p1",
        attachment_id="att1",
        contributed_by="u1",
        status=status,
    )
    return PestImageContent(contribution=contribution, attachment=_attachment(mime=mime))


class _FakeService:
    """Mimics the slice of PestImageService the global router calls."""

    def __init__(self, *, content: PestImageContent | None, thumbnail_missing: bool = False):
        self._content = content
        self._thumbnail_missing = thumbnail_missing

    def resolve_promoted_content(self, contribution_id):
        return self._content

    async def open_content_stream(self, content):
        async def _gen():
            yield b"bytes"

        return _gen()

    async def open_content_thumbnail_stream(self, content, size):
        if self._thumbnail_missing:
            raise NotFoundError("thumbnail", str(size))

        async def _gen():
            yield b"thumb"

        return _gen()


class TestGlobalContentSecurity:
    @pytest.mark.asyncio
    async def test_promoted_image_streams_200(self):
        service = _FakeService(content=_content())

        resp = await pest_images_router.get_promoted_pest_image("pic1", _user=None, service=service)

        assert isinstance(resp, StreamingResponse)
        assert resp.media_type == "image/jpeg"
        assert resp.headers.get("ETag") == '"' + "a" * 64 + '"'

    @pytest.mark.asyncio
    async def test_private_image_is_404(self):
        # The service resolves a private image to None — the router must 404 it.
        service = _FakeService(content=None)

        with pytest.raises(NotFoundError):
            await pest_images_router.get_promoted_pest_image("pic-private", _user=None, service=service)

    @pytest.mark.asyncio
    async def test_unknown_image_is_404(self):
        service = _FakeService(content=None)

        with pytest.raises(NotFoundError):
            await pest_images_router.get_promoted_pest_image("missing", _user=None, service=service)


class TestGlobalThumbnail:
    @pytest.mark.asyncio
    async def test_promoted_thumbnail_streams_200(self):
        service = _FakeService(content=_content())

        resp = await pest_images_router.get_promoted_pest_image_thumbnail("pic1", 512, _user=None, service=service)

        assert isinstance(resp, StreamingResponse)
        assert resp.media_type == "image/webp"

    @pytest.mark.asyncio
    async def test_private_thumbnail_is_404(self):
        service = _FakeService(content=None)

        with pytest.raises(NotFoundError):
            await pest_images_router.get_promoted_pest_image_thumbnail("pic1", 512, _user=None, service=service)

    @pytest.mark.asyncio
    async def test_invalid_size_is_validation_error(self):
        service = _FakeService(content=_content())

        with pytest.raises(ValidationError):
            await pest_images_router.get_promoted_pest_image_thumbnail("pic1", 999, _user=None, service=service)

    @pytest.mark.asyncio
    async def test_missing_rendition_returns_202(self):
        service = _FakeService(content=_content(), thumbnail_missing=True)

        with patch("app.tasks.storage_tasks.generate_thumbnails.delay") as delay:
            resp = await pest_images_router.get_promoted_pest_image_thumbnail("pic1", 512, _user=None, service=service)

        assert resp.status_code == 202
        # Lazy regeneration enqueued against the OWNING tenant.
        delay.assert_called_once_with("att1", "t1")
