"""REQ-053 WP 8.18 (#2661) - the photos of deleted beds go with them, unless another carrier still names them.

Five paths delete a bed: ``DELETE /locations/{key}`` (``GardenResourceService.delete_bed``), a plan batch with a
``delete`` operation (``GardenPlanService.apply_batch_async``), the site delete (``SiteService.delete_site``), and a
``replace`` plan import and a snapshot restore (``GardenPlanImportService.release_photos``).
Each hands the photo ids its transaction read to ``LocationPhotoService.discard_released`` after the commit; the
service tests cover the first two over the in-memory plan repository, this file the site delete and the wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common import dependencies
from app.common.exceptions import NotFoundError
from app.domain.interfaces.site_repository import SiteDeletion
from app.domain.models.site import Site
from app.domain.services.site_service import SiteService

TENANT = "t-own"


class _Discard:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    async def discard_released(self, attachment_ids, *, tenant_key: str) -> int:  # type: ignore[no-untyped-def]
        self.calls.append((list(attachment_ids), tenant_key))
        return len(self.calls[-1][0])


def _service(deletion: SiteDeletion) -> tuple[SiteService, _Discard, MagicMock]:
    repo = MagicMock()
    repo.get_site_or_raise.return_value = Site(_key="site-a", tenant_key=TENANT, name="A", type="outdoor")
    repo.delete_site.return_value = deletion
    discard = _Discard()
    return SiteService(repo, photos=lambda: discard), discard, repo


async def test_the_site_delete_hands_the_photos_of_its_beds_to_the_discard() -> None:
    service, discard, _repo = _service(SiteDeletion(location_photo_refs=("p1", "p2")))

    assert await service.delete_site("site-a", tenant_key=TENANT, user_key="u-own") is True

    assert discard.calls == [(["p1", "p2"], TENANT)]


async def test_a_site_whose_beds_had_no_photos_builds_no_discard() -> None:
    repo = MagicMock()
    repo.get_site_or_raise.return_value = Site(_key="site-a", tenant_key=TENANT, name="A", type="outdoor")
    repo.delete_site.return_value = SiteDeletion()

    def provider() -> _Discard:
        raise AssertionError("the attachment side is built only when a photo was released")

    await SiteService(repo, photos=provider).delete_site("site-a", tenant_key=TENANT, user_key="u-own")


async def test_a_foreign_site_releases_nothing() -> None:
    service, discard, repo = _service(SiteDeletion(location_photo_refs=("p1",)))
    repo.get_site_or_raise.return_value = Site(_key="site-a", tenant_key="t-other", name="A", type="outdoor")

    with pytest.raises(NotFoundError):
        await service.delete_site("site-a", tenant_key=TENANT, user_key="u-own")

    repo.delete_site.assert_not_called()
    assert discard.calls == []


def test_the_request_wiring_hands_every_bed_delete_path_the_photo_service(monkeypatch) -> None:
    """Production: every bed-delete path gets the photo service as a provider (built only when needed)."""
    for name in ("get_site_repo", "get_tank_repo", "get_garden_plan_repo", "get_db"):
        monkeypatch.setattr(dependencies, name, MagicMock)

    assert dependencies.get_site_service()._photos is dependencies.get_location_photo_service
    assert dependencies.get_garden_plan_service()._photos is dependencies.get_location_photo_service
    assert dependencies.get_garden_resource_service()._photos is dependencies.get_location_photo_service
    # a ``replace`` import and a snapshot restore delete beds too (#2661 follow-up)
    assert dependencies.get_garden_plan_import_service()._photos is dependencies.get_location_photo_service
