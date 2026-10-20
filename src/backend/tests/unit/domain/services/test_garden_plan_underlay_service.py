"""REQ-053 WP 7.14 (#2480) - the background picture of a plan: storage, ownership, export and print.

* **Ownership** - a foreign, absent, wrong-category or out-of-namespace attachment answers one 422
  ``reference.not_found`` (GP-NFR-058); a foreign site answers 404 before any attachment is read.
* **One per site** - replacing deletes the superseded attachment through the holder-asking delete.
* **Never exported** (GP-FR-140) - the JSON backup has no underlay; the PDF has it only when the caller supplies it.
* **Print** (GP-NFR-052 (f)) - the picture enters the PDF as a ``data:`` URI and the fetcher sees nothing else.
"""

from __future__ import annotations

import pytest

from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.models.site import SitePlan, SiteUnderlay
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_plan_underlay_service import GardenPlanUnderlayService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.underlay_fakes import FakeUnderlayAttachments

FOREIGN_SITE = "site_foreign"


def _underlay(attachment_key: str = "att_1", **overrides) -> SiteUnderlay:
    data = {
        "attachment_key": attachment_key,
        "calibration": {"p1_px": [100, 200], "p2_px": [500, 200], "distance_m": 4.0},
        "origin": [1.0, 5.0],
        "rotation_deg": 0.0,
        "opacity": 0.5,
        **overrides,
    }
    return SiteUnderlay.model_validate(data)


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0}, plan_revision=3
    )
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": FOREIGN_SITE})
    repository = FakePlanRepo(FakeSites(site, foreign))
    repository.locations["b1"] = make_location("b1", "Beet 1", geometry=rect(1, 1, 2, 1))
    return repository


@pytest.fixture
def attachments() -> FakeUnderlayAttachments:
    fake = FakeUnderlayAttachments()
    fake.add("att_1", tenant_key=TENANT)
    fake.add("att_2", tenant_key=TENANT)
    return fake


@pytest.fixture
def service(repo: FakePlanRepo, attachments: FakeUnderlayAttachments) -> GardenPlanUnderlayService:
    return GardenPlanUnderlayService(
        repo._sites,
        repo,
        attachments,
        attachments.as_service(),  # type: ignore[arg-type]
    )


class TestSetAndRead:
    async def test_it_stores_the_underlay_on_the_plan_without_touching_the_revision(self, service, repo) -> None:
        stored = await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay())

        plan = repo._sites.sites[SITE].plan
        assert plan.underlay == stored and plan.plan_revision == 3
        assert service.get_underlay(SITE, tenant_key=TENANT) == stored
        assert repo.applied == [] and repo.audit == []

    async def test_a_viewer_may_not_set_it(self, service) -> None:
        with pytest.raises(ForbiddenError):
            await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.VIEWER, underlay=_underlay())

    async def test_a_site_without_a_plan_is_a_422_plan_required(self, service, repo) -> None:
        repo._sites.sites[SITE].plan = None

        with pytest.raises(PlanError) as excinfo:
            await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay())

        assert excinfo.value.status_code == 422 and excinfo.value.error_code == "plan.required"

    async def test_a_foreign_site_is_a_404_before_the_attachment_is_read(self, service, attachments) -> None:
        with pytest.raises(NotFoundError):
            await service.set_underlay(FOREIGN_SITE, tenant_key=TENANT, role=TenantRole.LEAD, underlay=_underlay())

        assert attachments.deleted == []


class TestTheAttachmentIsTheCallersOwn:
    @pytest.mark.parametrize(
        "setup",
        ["absent", "foreign_tenant", "wrong_category", "outside_namespace"],
    )
    async def test_every_other_attachment_is_one_422_reference_not_found(
        self, service, attachments, repo, setup
    ) -> None:
        if setup == "foreign_tenant":
            attachments.add("att_x", tenant_key=OTHER_TENANT)
        elif setup == "wrong_category":
            attachments.add("att_x", tenant_key=TENANT, category=AttachmentCategory.PLANT)
        elif setup == "outside_namespace":
            attachments.add("att_x", tenant_key=TENANT, storage_key=f"t/{OTHER_TENANT}/garden_plan_underlay/x.png")

        with pytest.raises(PlanValidationError) as excinfo:
            await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay("att_x"))

        assert excinfo.value.status_code == 422 and excinfo.value.codes == ["reference.not_found"]
        assert excinfo.value.details[0]["field"] == "attachment_key"
        assert repo._sites.sites[SITE].plan.underlay is None


class TestOnePerSite:
    async def test_replacing_deletes_the_superseded_attachment_through_the_holder_asking_delete(
        self, service, attachments
    ) -> None:
        await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay("att_1"))

        await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay("att_2"))

        assert attachments.deleted == [("att_1", TENANT)]

    async def test_saving_the_same_picture_again_deletes_nothing(self, service, attachments) -> None:
        await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay("att_1"))

        await service.set_underlay(
            SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay("att_1", opacity=0.8)
        )

        assert attachments.deleted == []

    async def test_removing_clears_the_plan_and_deletes_the_attachment_and_is_idempotent(
        self, service, attachments, repo
    ) -> None:
        await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay())

        assert await service.remove_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER) is True
        assert await service.remove_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER) is False

        assert repo._sites.sites[SITE].plan.underlay is None
        assert attachments.deleted == [("att_1", TENANT)]

    async def test_a_viewer_may_not_remove_it(self, service) -> None:
        with pytest.raises(ForbiddenError):
            await service.remove_underlay(SITE, tenant_key=TENANT, role=TenantRole.VIEWER)


class TestNeverInTheJsonExport:
    async def test_the_backup_has_no_underlay(self, service, repo) -> None:
        await service.set_underlay(SITE, tenant_key=TENANT, role=TenantRole.GROWER, underlay=_underlay())
        export = GardenPlanExportService(repo._sites, repo, GardenPlanService(repo._sites, repo))

        document = export.export_json(SITE, tenant_key=TENANT)

        dumped = document.model_dump_json()
        assert "underlay" not in dumped and "att_1" not in dumped and "distance_m" not in dumped
