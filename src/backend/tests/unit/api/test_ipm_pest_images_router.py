"""REQ-010 — tenant-scoped pest-image router unit tests.

House style: the router functions are invoked directly with a fake service and
a hand-built ``TenantContext`` (no HTTP layer). We assert the response mapping
(fully-qualified tenant-scoped URIs, ``is_own``, thumbnail handling) and that a
foreign / unknown image id surfaces as a 404 on delete.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.v1.ipm import tenant_router
from app.common.enums import PestImageStatus
from app.common.exceptions import NotFoundError
from app.core.permissions import TenantRole
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.tenant_context import TenantContext
from app.domain.services.pest_image_service import PestImageView


def _ctx(tenant_slug: str = "my-garden", tenant_key: str = "t1", user_key: str = "u1") -> TenantContext:
    return TenantContext(
        tenant_key=tenant_key,
        tenant_slug=tenant_slug,
        user_key=user_key,
        role=TenantRole.GROWER,
    )


def _view(
    *,
    key: str = "pic1",
    pest_key: str = "p1",
    attachment_id: str = "att1",
    mime: str = "image/jpeg",
    renderable: bool = True,
    caption: str | None = "hi",
) -> PestImageView:
    contribution = PestImageContribution(
        _key=key,
        tenant_key="t1",
        pest_key=pest_key,
        attachment_id=attachment_id,
        contributed_by="u1",
        caption=caption,
        status=PestImageStatus.PRIVATE,
        created_at=datetime.now(UTC),
    )
    return PestImageView(contribution=contribution, mime_type=mime, has_thumbnail=renderable)


class _FakeService:
    def __init__(self, *, list_views=None, delete_result=True):
        self._list_views = list_views or []
        self._delete_result = delete_result
        self.delete_args: tuple | None = None

    def list_for_pest(self, tenant_key, pest_key):
        return list(self._list_views)

    async def delete(self, tenant_key, user_key, contribution_key):
        self.delete_args = (tenant_key, user_key, contribution_key)
        return self._delete_result


class TestResponseMapping:
    def test_list_builds_fully_qualified_uris(self):
        service = _FakeService(list_views=[_view()])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert len(resp) == 1
        item = resp[0]
        assert item.id == "pic1"
        assert item.pest_key == "p1"
        assert item.attachment_id == "att1"
        assert item.uri == "/api/v1/t/my-garden/attachments/att1"
        assert item.thumbnail_uri == "/api/v1/t/my-garden/attachments/att1/thumbnails/512"
        assert item.status == PestImageStatus.PRIVATE
        assert item.caption == "hi"
        assert item.contributed_by == "u1"
        assert item.is_own is True

    def test_non_renderable_attachment_has_no_thumbnail(self):
        service = _FakeService(list_views=[_view(mime="application/pdf", renderable=False)])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert resp[0].thumbnail_uri is None


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_returns_204_when_owned(self):
        service = _FakeService(delete_result=True)

        resp = await tenant_router.delete_pest_image("p1", "pic1", ctx=_ctx(), service=service)

        assert resp.status_code == 204
        # Scoped to the caller's tenant.
        assert service.delete_args == ("t1", "u1", "pic1")

    @pytest.mark.asyncio
    async def test_delete_foreign_or_missing_raises_404(self):
        service = _FakeService(delete_result=False)

        with pytest.raises(NotFoundError):
            await tenant_router.delete_pest_image("p1", "missing", ctx=_ctx(), service=service)
