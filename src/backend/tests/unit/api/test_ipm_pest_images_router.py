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
from app.domain.services.pest_image_service import (
    PestImageView,
    PestInspectionImageView,
    PestRecognitionImageView,
)


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
    is_own: bool = True,
    tenant_key: str = "t1",
    contributed_by: str = "u1",
    status: PestImageStatus = PestImageStatus.PRIVATE,
) -> PestImageView:
    contribution = PestImageContribution(
        _key=key,
        tenant_key=tenant_key,
        pest_key=pest_key,
        attachment_id=attachment_id,
        contributed_by=contributed_by,
        caption=caption,
        status=status,
        created_at=datetime.now(UTC),
    )
    return PestImageView(contribution=contribution, mime_type=mime, has_thumbnail=renderable, is_own=is_own)


def _inspection_view(*, attachment_id: str = "att-i1", renderable: bool = True) -> PestInspectionImageView:
    return PestInspectionImageView(
        attachment_id=attachment_id,
        mime_type="image/jpeg" if renderable else "application/pdf",
        has_thumbnail=renderable,
    )


def _recognition_view(
    *,
    prototype_id: int = 7,
    source_url: str = "https://example.org/ref/7.jpg",
    attribution: str | None = "Jane Doe / iNaturalist",
    license_: str | None = "CC-BY 4.0",
) -> PestRecognitionImageView:
    return PestRecognitionImageView(
        prototype_id=prototype_id,
        source_url=source_url,
        attribution=attribution,
        license=license_,
    )


class _FakeService:
    def __init__(self, *, list_views=None, inspection_views=None, recognition_views=None, delete_result=True):
        self._list_views = list_views or []
        self._inspection_views = inspection_views or []
        self._recognition_views = recognition_views or []
        self._delete_result = delete_result
        self.delete_args: tuple | None = None

    def list_for_pest(self, tenant_key, pest_key):
        return list(self._list_views)

    def list_inspection_images_for_pest(self, tenant_key, pest_key):
        return list(self._inspection_views)

    def list_recognition_images_for_pest(self, pest_key):
        return list(self._recognition_views)

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
        assert item.source == "contribution"

    def test_non_renderable_attachment_has_no_thumbnail(self):
        service = _FakeService(list_views=[_view(mime="application/pdf", renderable=False)])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert resp[0].thumbnail_uri is None

    def test_own_contribution_exposes_contributor(self):
        """SEC-002 — the caller's own contribution keeps ``contributed_by`` set."""
        service = _FakeService(list_views=[_view(is_own=True, contributed_by="u1")])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert resp[0].is_own is True
        assert resp[0].contributed_by == "u1"

    def test_foreign_promoted_contribution_hides_contributor(self):
        """SEC-002 — a foreign promoted image must not disclose the contributor (PII)."""
        foreign = _view(
            key="pic-foreign",
            is_own=False,
            tenant_key="t-other",
            contributed_by="u-other",
            status=PestImageStatus.PROMOTED,
        )
        service = _FakeService(list_views=[foreign])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert resp[0].is_own is False
        assert resp[0].contributed_by is None
        # The global content URI is still returned so the image renders.
        assert resp[0].uri == "/api/v1/ipm/pest-images/pic-foreign"


class TestInspectionImages:
    """REQ-010 — inspection photos appended read-only to the gallery."""

    def test_inspection_photo_mapped_as_read_only_source(self):
        service = _FakeService(inspection_views=[_inspection_view(attachment_id="att-i1")])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert len(resp) == 1
        item = resp[0]
        assert item.source == "inspection"
        assert item.is_own is True
        # The attachment id doubles as the stable client key; no contribution id.
        assert item.id == "att-i1"
        assert item.attachment_id == "att-i1"
        assert item.uri == "/api/v1/t/my-garden/attachments/att-i1"
        assert item.thumbnail_uri == "/api/v1/t/my-garden/attachments/att-i1/thumbnails/512"
        # Read-only: no contribution lifecycle / contributor provenance.
        assert item.status is None
        assert item.contributed_by is None

    def test_contributions_precede_inspection_photos(self):
        service = _FakeService(
            list_views=[_view(attachment_id="att-c1")],
            inspection_views=[_inspection_view(attachment_id="att-i1")],
        )

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert [(r.source, r.attachment_id) for r in resp] == [
            ("contribution", "att-c1"),
            ("inspection", "att-i1"),
        ]

    def test_attachment_already_contributed_not_duplicated(self):
        """An attachment surfaced as a contribution is not repeated as an inspection tile."""
        service = _FakeService(
            list_views=[_view(attachment_id="att-shared")],
            inspection_views=[_inspection_view(attachment_id="att-shared")],
        )

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert len(resp) == 1
        assert resp[0].source == "contribution"

    def test_inspection_non_renderable_has_no_thumbnail(self):
        service = _FakeService(inspection_views=[_inspection_view(attachment_id="att-i1", renderable=False)])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert resp[0].thumbnail_uri is None


class TestRecognitionImages:
    """REQ-010 / REQ-044 — global recognition reference images appended read-only."""

    def test_recognition_image_mapped_as_external_read_only_source(self):
        service = _FakeService(recognition_views=[_recognition_view(prototype_id=7)])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert len(resp) == 1
        item = resp[0]
        assert item.source == "recognition"
        # Stable, namespaced client key — disjoint from contribution/attachment ids.
        assert item.id == "recognition:7"
        # The external CC-licensed URL is the uri; no local pixel, no thumbnail.
        assert item.uri == "https://example.org/ref/7.jpg"
        assert item.thumbnail_uri is None
        assert item.attachment_id == ""
        # Global, read-only: not own, no contribution lifecycle / contributor.
        assert item.is_own is False
        assert item.status is None
        assert item.contributed_by is None
        # CC-BY attribution / license travel with the tile.
        assert item.attribution == "Jane Doe / iNaturalist"
        assert item.license == "CC-BY 4.0"

    def test_recognition_appended_after_contributions_and_inspections(self):
        service = _FakeService(
            list_views=[_view(attachment_id="att-c1")],
            inspection_views=[_inspection_view(attachment_id="att-i1")],
            recognition_views=[_recognition_view(prototype_id=9)],
        )

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert [(r.source, r.id) for r in resp] == [
            ("contribution", "pic1"),
            ("inspection", "att-i1"),
            ("recognition", "recognition:9"),
        ]

    def test_recognition_without_license_is_still_mapped(self):
        service = _FakeService(recognition_views=[_recognition_view(prototype_id=5, attribution=None, license_=None)])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert resp[0].attribution is None
        assert resp[0].license is None

    def test_no_recognition_images_when_service_returns_none(self):
        # Mirrors a pest without detection_slug / a disabled feature / an outage:
        # the service yields an empty list and only the other sources remain.
        service = _FakeService(list_views=[_view(attachment_id="att-c1")], recognition_views=[])

        resp = tenant_router.list_pest_images("p1", ctx=_ctx(), service=service)

        assert [r.source for r in resp] == ["contribution"]


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
