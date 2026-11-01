"""#2545 item 1 - a deleted site's underlay picture goes with it, unless another carrier still names it.

The aerial photo of a garden plan (REQ-053 GP-FR-033, §26: it can reveal where someone lives) used to outlive the
site and went only with the tenant erasure. ``SiteService.delete_site`` now hands the picture the delete
transaction read to the underlay service's own discard (B3: the attachment goes only when no other site, gallery
or task names it); the predicate is that service's, not a copy.
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from app.common import dependencies
from app.common.enums import AttachmentCategory
from app.common.exceptions import NotFoundError, PlanError
from app.domain.interfaces.site_repository import SiteDeletion
from app.domain.models.site import Site, SitePlan, SiteUnderlay
from app.domain.services.garden_plan_underlay_service import GardenPlanUnderlayService
from app.domain.services.site_service import SiteService
from tests.support.underlay_fakes import FakeUnderlayAttachments

TENANT, OTHER = "t-own", "t-other"


def _underlay(attachment_key: str) -> SiteUnderlay:
    return SiteUnderlay.model_validate(
        {"attachment_key": attachment_key, "calibration": {"p1_px": [0, 0], "p2_px": [100, 0], "distance_m": 2.0}}
    )


def _site(key: str, *, tenant: str = TENANT, underlay: str | None = None) -> Site:
    plan = SitePlan(underlay=_underlay(underlay)) if underlay else SitePlan()
    return Site(_key=key, tenant_key=tenant, name=key, type="outdoor", plan=plan)


class _Rig:
    def __init__(self, *sites: Site) -> None:
        self.sites = {site.key: site for site in sites}
        self.attachments = FakeUnderlayAttachments(self.sites)
        self.repo = MagicMock()
        self.repo.get_site_or_raise.side_effect = self._get
        self.repo.delete_site.side_effect = self._delete
        underlay = GardenPlanUnderlayService(
            MagicMock(),
            MagicMock(),
            self.attachments,
            self.attachments.as_service(),  # type: ignore[arg-type]
        )
        self.service = SiteService(self.repo, underlay=lambda: underlay)

        #: The thread each synchronous repository call ran on (#2545 review LOW-1).
        self.threads: dict[str, int] = {}

    def _get(self, key: str) -> Site:
        self.threads["get_site_or_raise"] = threading.get_ident()
        if key not in self.sites:
            raise NotFoundError("Site", key)
        return self.sites[key]

    def _delete(self, key: str, *, tenant_key: str, user_key: str) -> SiteDeletion:
        self.threads["delete_site"] = threading.get_ident()
        removed = self.sites.pop(key)
        underlay = removed.plan.underlay if removed.plan is not None else None
        return SiteDeletion(underlay_attachment_key=underlay.attachment_key if underlay else None)


class TestTheUnderlayGoesWithTheSite:
    async def test_the_picture_only_this_site_named_is_deleted(self) -> None:
        rig = _Rig(_site("site-a", underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=TENANT)

        assert await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own") is True

        assert rig.attachments.deleted == [("att_1", TENANT)]
        assert "att_1" not in rig.attachments.rows

    async def test_a_picture_another_site_still_names_stays(self) -> None:
        rig = _Rig(_site("site-a", underlay="att_1"), _site("site-b", underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=TENANT)

        await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own")

        assert rig.attachments.deleted == []
        assert "att_1" in rig.attachments.rows

    async def test_an_attachment_of_another_category_is_never_deleted_by_the_site_delete(self) -> None:
        rig = _Rig(_site("site-a", underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=TENANT, category=AttachmentCategory.PLANT)

        await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own")

        assert rig.attachments.deleted == [] and "att_1" in rig.attachments.rows

    async def test_a_site_without_an_underlay_deletes_no_attachment(self) -> None:
        rig = _Rig(_site("site-a"))
        rig.attachments.add("att_1", tenant_key=TENANT)

        await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own")

        assert rig.attachments.deleted == [] and "att_1" in rig.attachments.rows

    async def test_a_refused_delete_discards_nothing(self) -> None:
        rig = _Rig(_site("site-a", underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=TENANT)
        rig.repo.delete_site.side_effect = PlanError("site.has_active_plants", "busy", status_code=409)

        with pytest.raises(PlanError):
            await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own")

        assert rig.attachments.deleted == [] and "att_1" in rig.attachments.rows

    async def test_a_foreign_site_is_not_found_and_nothing_is_deleted(self) -> None:
        rig = _Rig(_site("site-f", tenant=OTHER, underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=OTHER)

        with pytest.raises(NotFoundError):
            await rig.service.delete_site("site-f", tenant_key=TENANT, user_key="u-own")

        rig.repo.delete_site.assert_not_called()
        assert rig.attachments.deleted == []


class TestTheCommittedDeleteStaysSuccessful:
    """#2545 review MEDIUM-3: the site is gone once the transaction commits; the picture's discard cannot 500 it."""

    async def test_a_failing_discard_is_logged_and_the_delete_still_succeeds(self, monkeypatch) -> None:
        rig = _Rig(_site("site-a", underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=TENANT)

        async def failing(attachment_id: str, tenant_key: str) -> bool:
            raise TimeoutError("storage unreachable")

        monkeypatch.setattr(rig.attachments, "delete_if_unreferenced", failing)

        with capture_logs() as logs:
            assert await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own") is True

        assert "site-a" not in rig.sites
        [warning] = [entry for entry in logs if entry["event"] == "site.underlay_discard_failed"]
        assert warning["log_level"] == "warning"
        assert warning["site_key"] == "site-a" and warning["attachment_id"] == "att_1"
        assert warning["error_type"] == "TimeoutError"
        assert TENANT not in warning.values() and "u-own" not in warning.values()


class TestTheDeleteDoesNotBlockTheEventLoop:
    """#2545 review LOW-1: the route is ``async``; the synchronous Arango calls run in a worker thread."""

    async def test_the_repository_calls_run_off_the_event_loop_thread(self) -> None:
        rig = _Rig(_site("site-a", underlay="att_1"))
        rig.attachments.add("att_1", tenant_key=TENANT)
        attachment_get = rig.attachments.get

        def recording_get(key: str, tenant_key: str):  # type: ignore[no-untyped-def]
            rig.threads["attachment_get"] = threading.get_ident()
            return attachment_get(key, tenant_key)

        rig.attachments.get = recording_get  # type: ignore[method-assign]
        loop_thread = threading.get_ident()

        await rig.service.delete_site("site-a", tenant_key=TENANT, user_key="u-own")

        assert set(rig.threads) == {"get_site_or_raise", "delete_site", "attachment_get"}
        assert loop_thread not in rig.threads.values()


def test_the_request_wiring_hands_the_site_service_the_underlay_service(monkeypatch) -> None:
    """Production builds the underlay service only when a delete has a picture to discard (a provider)."""
    monkeypatch.setattr(dependencies, "get_site_repo", MagicMock)
    monkeypatch.setattr(dependencies, "get_tank_repo", MagicMock)

    service = dependencies.get_site_service()

    assert service._underlay is dependencies.get_garden_plan_underlay_service
