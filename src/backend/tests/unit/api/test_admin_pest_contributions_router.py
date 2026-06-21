"""REQ-010 — admin pest-image moderation router tests (global promotion).

House style: router functions invoked directly with a fake service and a
hand-built admin ``User``. Covers the moderation listing (global content URIs +
provenance), and promote/demote mapping incl. the 404 on an unknown id.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.v1.admin.pests import router as admin_pests_router
from app.api.v1.admin.pests.schemas import PromotePestContributionRequest
from app.common.enums import PestImageStatus
from app.common.exceptions import NotFoundError
from app.domain.models.pest_image import PestImageContribution
from app.domain.models.user import User
from app.domain.services.pest_image_service import PestImageView


def _admin() -> User:
    return User(_key="admin1", email="admin@example.com", display_name="Admin")


def _view(
    *,
    key: str = "pic1",
    tenant_key: str = "t1",
    status: PestImageStatus = PestImageStatus.PRIVATE,
    promoted_by: str | None = None,
    promoted_at: datetime | None = None,
    renderable: bool = True,
) -> PestImageView:
    contribution = PestImageContribution(
        _key=key,
        tenant_key=tenant_key,
        pest_key="p1",
        attachment_id="att1",
        contributed_by="u1",
        status=status,
        promoted_by=promoted_by,
        promoted_at=promoted_at,
        created_at=datetime.now(UTC),
    )
    return PestImageView(contribution=contribution, mime_type="image/jpeg", has_thumbnail=renderable, is_own=False)


class _FakeService:
    def __init__(self, *, list_views=None, promote_view="__unset__"):
        self._list_views = list_views or []
        self._promote_view = promote_view
        self.promote_args = None

    def list_all_for_pest(self, pest_key):
        return list(self._list_views)

    def set_promotion(self, *, contribution_key, promote, admin_user_key):
        self.promote_args = (contribution_key, promote, admin_user_key)
        if self._promote_view == "__unset__":
            return None
        return self._promote_view


class TestListContributions:
    def test_lists_with_global_content_uris_and_provenance(self):
        promoted = _view(
            key="pic2",
            tenant_key="t2",
            status=PestImageStatus.PROMOTED,
            promoted_by="admin1",
            promoted_at=datetime.now(UTC),
        )
        service = _FakeService(list_views=[_view(), promoted])

        resp = admin_pests_router.list_pest_contributions("p1", _user=_admin(), service=service)

        assert resp.pest_key == "p1"
        assert resp.count == 2
        assert resp.promoted_count == 1
        first = resp.images[0]
        assert first.content_uri == "/api/v1/ipm/pest-images/pic1"
        assert first.thumbnail_uri == "/api/v1/ipm/pest-images/pic1/thumbnails/512"
        assert first.tenant_key == "t1"
        assert first.contributed_by == "u1"
        # Promoted row carries the audit fields.
        promoted_row = resp.images[1]
        assert promoted_row.status == PestImageStatus.PROMOTED
        assert promoted_row.promoted_by == "admin1"
        assert promoted_row.promoted_at is not None

    def test_non_renderable_has_no_thumbnail(self):
        service = _FakeService(list_views=[_view(renderable=False)])

        resp = admin_pests_router.list_pest_contributions("p1", _user=_admin(), service=service)

        assert resp.images[0].thumbnail_uri is None


class TestSetPromotion:
    def test_promote_returns_audit(self):
        view = _view(
            status=PestImageStatus.PROMOTED,
            promoted_by="admin1",
            promoted_at=datetime.now(UTC),
        )
        service = _FakeService(promote_view=view)

        resp = admin_pests_router.set_pest_contribution_promotion(
            "p1",
            "pic1",
            PromotePestContributionRequest(promote=True),
            user=_admin(),
            service=service,
        )

        assert resp.id == "pic1"
        assert resp.status == PestImageStatus.PROMOTED
        assert resp.promoted_by == "admin1"
        assert service.promote_args == ("pic1", True, "admin1")

    def test_unknown_contribution_raises_404(self):
        service = _FakeService(promote_view="__unset__")

        with pytest.raises(NotFoundError):
            admin_pests_router.set_pest_contribution_promotion(
                "p1",
                "missing",
                PromotePestContributionRequest(promote=True),
                user=_admin(),
                service=service,
            )
