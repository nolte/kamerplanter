"""REQ-053 WP 8.18 (#2661) - the photos of a bed: who may link, choose and remove which photo, and what goes with it.

Against the in-memory doubles of ``tests/support/location_photo_fakes.py``; the transactions are measured against
ArangoDB in ``tests/integration/test_location_photo_repository.py`` and the routes in
``tests/api/test_location_photos_api.py``.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.interfaces.location_photo_repository import LocationPhotoState, without_photo
from app.domain.models.site import MAX_PHOTOS_PER_LOCATION, Location
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.location_photo_service import LocationPhotoService, release_location_photos
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.location_photo_fakes import FakeLocationPhotoRepo, FakePhotoAttachments

ME = "u_sabine"
OTHER_MEMBER = "u_tom"
FOREIGN_SITE = "site_foreign"


class World:
    def __init__(self) -> None:
        foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": FOREIGN_SITE})
        self.repo = FakePlanRepo(FakeSites(make_site(), foreign))
        self.repo.locations["bed"] = make_location("bed", "Beet 1")
        self.repo.locations["bed2"] = make_location("bed2", "Beet 2")
        self.repo.locations["foreign_bed"] = make_location("foreign_bed", "Fremdbeet").model_copy(
            update={"site_key": FOREIGN_SITE}
        )
        self.attachments = FakePhotoAttachments(self.repo)
        self.photos = FakeLocationPhotoRepo(self.repo, self.attachments)
        self.service = LocationPhotoService(self.repo._sites, self.photos, self.attachments, lambda: self.attachments)

    def bed(self, key: str = "bed") -> Location:
        return self.repo.locations[key]

    def add(self, attachment_id: str, *, role: TenantRole = TenantRole.GROWER, key: str = "bed", user: str = ME):
        return self.service.add_photo(key, attachment_id, tenant_key=TENANT, user_key=user, role=role)

    async def remove(self, attachment_id: str, *, role: TenantRole = TenantRole.GROWER, user: str = ME):
        return await self.service.remove_photo("bed", attachment_id, tenant_key=TENANT, user_key=user, role=role)


@pytest.fixture
def world() -> World:
    return World()


def _codes(error: PlanValidationError) -> list[str]:
    return list(error.codes)


class TestAdd:
    def test_the_first_photo_becomes_the_cover_and_the_next_one_comes_first(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.attachments.add("p2", tenant_key=TENANT)

        world.add("p1")
        view = world.add("p2")

        assert world.bed().photo_refs == ["p2", "p1"] and world.bed().cover_photo_ref == "p1"
        assert [photo.attachment.key for photo in view.photos] == ["p2", "p1"]
        assert [photo.is_cover for photo in view.photos] == [False, True]

    def test_linking_a_photo_twice_changes_nothing(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")

        world.add("p1")

        assert world.bed().photo_refs == ["p1"]

    @pytest.mark.parametrize(
        ("tenant", "category"),
        [
            (OTHER_TENANT, AttachmentCategory.LOCATION),  # another garden's bed photo
            (TENANT, AttachmentCategory.PLANT),  # the tenant's own, but a plant-gallery photo
            (TENANT, AttachmentCategory.GARDEN_PLAN_UNDERLAY),
        ],
        ids=["foreign_tenant", "plant_category", "underlay_category"],
    )
    def test_an_attachment_that_is_not_the_tenants_bed_photo_is_reference_not_found(
        self, world: World, tenant: str, category: AttachmentCategory
    ) -> None:
        world.attachments.add("p_x", tenant_key=tenant, category=category)

        with pytest.raises(PlanValidationError) as refused:
            world.add("p_x")

        assert _codes(refused.value) == ["reference.not_found"]
        assert refused.value.details[0]["field"] == "attachment_id"
        assert world.bed().photo_refs == []

    def test_a_foreign_attachment_answers_exactly_like_an_absent_one(self, world: World) -> None:
        world.attachments.add("p_foreign", tenant_key=OTHER_TENANT)

        with pytest.raises(PlanValidationError) as foreign:
            world.add("p_foreign")
        with pytest.raises(PlanValidationError) as absent:
            world.add("p_absent")

        assert foreign.value.details == absent.value.details and foreign.value.message == absent.value.message

    def test_an_attachment_outside_its_tenants_namespace_is_refused(self, world: World) -> None:
        row = world.attachments.add("p_odd", tenant_key=TENANT)
        world.attachments.rows["p_odd"] = row.model_copy(update={"storage_key": f"t/{OTHER_TENANT}/location/x.jpg"})

        with pytest.raises(PlanValidationError):
            world.add("p_odd")

    @pytest.mark.parametrize("mime_type", ["application/pdf", "image/heic", "image/gif", ""])
    def test_a_bed_photo_that_is_not_a_strippable_image_is_refused(self, world: World, mime_type: str) -> None:
        """SEC-002: the ``location`` whitelist is operator-configurable, so the link asks the type itself."""
        row = world.attachments.add("p_doc", tenant_key=TENANT)
        world.attachments.rows["p_doc"] = row.model_copy(update={"mime_type": mime_type})

        with pytest.raises(PlanValidationError) as refused:
            world.add("p_doc")

        assert _codes(refused.value) == ["reference.not_found"]
        assert world.bed().photo_refs == []

    @pytest.mark.parametrize("mime_type", ["image/jpeg", "image/png", "image/webp", "IMAGE/PNG"])
    def test_every_strippable_image_type_links(self, world: World, mime_type: str) -> None:
        """The control: the refusal above is the type, not the path the row took."""
        row = world.attachments.add("p_img", tenant_key=TENANT)
        world.attachments.rows["p_img"] = row.model_copy(update={"mime_type": mime_type})

        world.add("p_img")

        assert world.bed().photo_refs == ["p_img"]

    def test_a_viewer_may_not_link_a_photo_a_grower_may(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)

        with pytest.raises(ForbiddenError):
            world.add("p1", role=TenantRole.VIEWER)
        assert world.bed().photo_refs == []

        world.add("p1", role=TenantRole.GROWER)
        assert world.bed().photo_refs == ["p1"]

    def test_another_tenants_bed_is_not_found(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)

        with pytest.raises(NotFoundError) as refused:
            world.add("p1", key="foreign_bed")

        assert refused.value.details[0]["entity"] == "location"
        assert world.bed("foreign_bed").photo_refs == []

    def test_the_bound_is_the_named_limit(self, world: World) -> None:
        for index in range(MAX_PHOTOS_PER_LOCATION):
            world.attachments.add(f"p{index}", tenant_key=TENANT)
            world.add(f"p{index}")
        world.attachments.add("one_more", tenant_key=TENANT)

        with pytest.raises(PlanError) as refused:
            world.add("one_more")

        assert refused.value.error_code == "location.photo_limit_reached" and refused.value.status_code == 422
        assert refused.value.details[0]["limit"] == MAX_PHOTOS_PER_LOCATION == 50
        assert len(world.bed().photo_refs) == MAX_PHOTOS_PER_LOCATION


class TestCover:
    def test_the_cover_must_be_one_of_the_beds_photos(self, world: World) -> None:
        for key in ("p1", "p2"):
            world.attachments.add(key, tenant_key=TENANT)
        world.add("p1")
        world.attachments.add("not_on_this_bed", tenant_key=TENANT)
        world.add("not_on_this_bed", key="bed2")

        view = world.service.set_cover("bed", "p1", tenant_key=TENANT, user_key=ME, role=TenantRole.GROWER)
        assert view.cover_photo_ref == "p1"

        with pytest.raises(PlanError) as refused:
            world.service.set_cover("bed", "not_on_this_bed", tenant_key=TENANT, user_key=ME, role=TenantRole.GROWER)
        assert refused.value.error_code == "location.cover_not_a_photo" and refused.value.status_code == 422
        assert world.bed().cover_photo_ref == "p1"

    def test_none_clears_the_cover(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")

        view = world.service.set_cover("bed", None, tenant_key=TENANT, user_key=ME, role=TenantRole.GROWER)

        assert view.cover_photo_ref is None and world.bed().photo_refs == ["p1"]

    def test_a_viewer_may_not_choose_the_cover(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")

        with pytest.raises(ForbiddenError):
            world.service.set_cover("bed", None, tenant_key=TENANT, user_key=ME, role=TenantRole.VIEWER)


class TestRemove:
    async def test_removing_the_cover_promotes_the_newest_remaining_photo_and_deletes_it(self, world: World) -> None:
        for key in ("p1", "p2", "p3"):
            world.attachments.add(key, tenant_key=TENANT)
            world.add(key)
        assert world.bed().photo_refs == ["p3", "p2", "p1"] and world.bed().cover_photo_ref == "p1"

        view = await world.remove("p1")

        assert world.bed().photo_refs == ["p3", "p2"] and world.bed().cover_photo_ref == "p3"
        assert view.cover_photo_ref == "p3" and [photo.is_cover for photo in view.photos] == [True, False]
        assert world.attachments.deleted == ["p1"]

    async def test_removing_the_last_photo_leaves_no_cover(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")

        view = await world.remove("p1")

        assert world.bed().photo_refs == [] and world.bed().cover_photo_ref is None
        assert view.cover_photo_ref is None and view.photos == ()

    async def test_a_cleared_cover_stays_cleared_when_another_photo_goes(self, world: World) -> None:
        for key in ("p1", "p2", "p3"):
            world.attachments.add(key, tenant_key=TENANT)
            world.add(key)
        world.service.set_cover("bed", None, tenant_key=TENANT, user_key=ME, role=TenantRole.GROWER)

        await world.remove("p2")

        assert world.bed().cover_photo_ref is None

    async def test_removing_another_photo_keeps_the_cover(self, world: World) -> None:
        for key in ("p1", "p2"):
            world.attachments.add(key, tenant_key=TENANT)
            world.add(key)

        await world.remove("p2")

        assert world.bed().cover_photo_ref == "p1"

    async def test_a_photo_another_bed_still_shows_stays(self, world: World) -> None:
        world.attachments.add("shared", tenant_key=TENANT)
        world.add("shared")
        world.add("shared", key="bed2")

        await world.remove("shared")

        assert world.bed().photo_refs == [] and world.bed("bed2").photo_refs == ["shared"]
        assert world.attachments.deleted == [] and "shared" in world.attachments.rows

    async def test_a_grower_may_not_remove_another_members_photo_and_nothing_changes(self, world: World) -> None:
        world.attachments.add("theirs", tenant_key=TENANT, created_by=OTHER_MEMBER)
        world.add("theirs", user=OTHER_MEMBER)

        with pytest.raises(ForbiddenError):
            await world.remove("theirs", role=TenantRole.GROWER)

        assert world.bed().photo_refs == ["theirs"] and world.attachments.deleted == []

    async def test_a_lead_may_remove_another_members_photo(self, world: World) -> None:
        world.attachments.add("theirs", tenant_key=TENANT, created_by=OTHER_MEMBER)
        world.add("theirs", user=OTHER_MEMBER)

        await world.remove("theirs", role=TenantRole.LEAD)

        assert world.bed().photo_refs == [] and world.attachments.deleted == ["theirs"]

    async def test_an_erased_members_photo_is_another_members_photo(self, world: World) -> None:
        world.attachments.add("anon", tenant_key=TENANT, created_by="_anonymized")
        world.add("anon")

        with pytest.raises(ForbiddenError):
            await world.remove("anon", role=TenantRole.GROWER)

    async def test_a_viewer_may_not_remove_even_an_own_photo(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")

        with pytest.raises(ForbiddenError):
            await world.remove("p1", role=TenantRole.VIEWER)

    async def test_a_photo_the_bed_does_not_show_is_not_found(self, world: World) -> None:
        world.attachments.add("elsewhere", tenant_key=TENANT)
        world.add("elsewhere", key="bed2")

        with pytest.raises(NotFoundError) as refused:
            await world.remove("elsewhere")

        assert refused.value.details[0]["entity"] == "location_photo"
        assert world.attachments.deleted == []

    async def test_a_stale_reference_is_cleared_by_any_editor(self, world: World) -> None:
        world.repo.locations["bed"] = world.bed().model_copy(update={"photo_refs": ["gone"]})

        await world.remove("gone", role=TenantRole.GROWER)

        assert world.bed().photo_refs == [] and world.attachments.deleted == []

    async def test_a_failing_discard_is_logged_and_the_removal_still_answers(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")
        world.attachments.fail_with = RuntimeError("storage down")

        view = await world.remove("p1")

        assert view.photos == () and world.bed().photo_refs == []


class TestList:
    def test_every_member_reads_and_can_remove_follows_the_rules(self, world: World) -> None:
        world.attachments.add("mine", tenant_key=TENANT)
        world.attachments.add("theirs", tenant_key=TENANT, created_by=OTHER_MEMBER)
        world.add("mine")
        world.add("theirs", user=OTHER_MEMBER)

        def removable(role: TenantRole) -> dict[str, bool]:
            view = world.service.list_photos("bed", tenant_key=TENANT, user_key=ME, role=role)
            return {photo.attachment.key or "": photo.can_remove for photo in view.photos}

        assert removable(TenantRole.VIEWER) == {"theirs": False, "mine": False}
        assert removable(TenantRole.GROWER) == {"theirs": False, "mine": True}
        assert removable(TenantRole.LEAD) == {"theirs": True, "mine": True}

    def test_a_stale_reference_is_skipped(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.repo.locations["bed"] = world.bed().model_copy(update={"photo_refs": ["gone", "p1"]})

        view = world.service.list_photos("bed", tenant_key=TENANT, user_key=ME, role=TenantRole.VIEWER)

        assert [photo.attachment.key for photo in view.photos] == ["p1"]
        assert world.bed().photo_refs == ["gone", "p1"]  # listing does not rewrite the bed

    def test_the_gallery_is_read_in_one_round_trip_in_the_beds_order(self, world: World) -> None:
        """#2715 item 7: one ``get_many`` for the whole gallery, never one ``get`` per photo."""
        for key in ("p1", "p2", "p3"):
            world.attachments.add(key, tenant_key=TENANT)
        world.attachments.add("foreign", tenant_key=OTHER_TENANT)
        world.repo.locations["bed"] = world.bed().model_copy(update={"photo_refs": ["p3", "foreign", "p1", "p2"]})
        world.attachments.reads.clear()

        view = world.service.list_photos("bed", tenant_key=TENANT, user_key=ME, role=TenantRole.VIEWER)

        assert world.attachments.reads == []
        assert world.attachments.batch_reads == [["p3", "foreign", "p1", "p2"]]
        assert [photo.attachment.key for photo in view.photos] == ["p3", "p1", "p2"]

    def test_another_tenants_bed_is_not_found(self, world: World) -> None:
        with pytest.raises(NotFoundError):
            world.service.list_photos("foreign_bed", tenant_key=TENANT, user_key=ME, role=TenantRole.LEAD)

    def test_a_stale_cover_reads_as_no_cover_and_the_bed_is_not_rewritten(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.repo.locations["bed"] = world.bed().model_copy(
            update={"photo_refs": ["p1", "gone"], "cover_photo_ref": "gone"}
        )

        view = world.service.list_photos("bed", tenant_key=TENANT, user_key=ME, role=TenantRole.VIEWER)

        assert view.cover_photo_ref is None and [photo.is_cover for photo in view.photos] == [False]
        assert world.bed().cover_photo_ref == "gone"  # a read never writes

    def test_a_present_cover_is_reported(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.repo.locations["bed"] = world.bed().model_copy(
            update={"photo_refs": ["gone", "p1"], "cover_photo_ref": "p1"}
        )

        view = world.service.list_photos("bed", tenant_key=TENANT, user_key=ME, role=TenantRole.VIEWER)

        assert view.cover_photo_ref == "p1" and [photo.is_cover for photo in view.photos] == [True]


class TestBedDelete:
    def _resources(self, world: World) -> GardenResourceService:
        plans = GardenPlanService(world.repo._sites, world.repo, photos=lambda: world.service)
        return GardenResourceService(world.repo._sites, world.repo, FakeObjects(world.repo), plans)

    async def test_deleting_the_bed_removes_its_references_and_deletes_its_photos(self, world: World) -> None:
        for key in ("p1", "p2"):
            world.attachments.add(key, tenant_key=TENANT)
            world.add(key)

        await self._resources(world).delete_bed("bed", tenant_key=TENANT, user_key=ME, role=TenantRole.LEAD)

        assert "bed" not in world.repo.locations
        assert sorted(world.attachments.deleted) == ["p1", "p2"]

    async def test_a_photo_another_bed_shows_survives_the_bed_delete(self, world: World) -> None:
        world.attachments.add("shared", tenant_key=TENANT)
        world.add("shared")
        world.add("shared", key="bed2")

        await self._resources(world).delete_bed("bed", tenant_key=TENANT, user_key=ME, role=TenantRole.LEAD)

        assert world.attachments.deleted == [] and world.bed("bed2").photo_refs == ["shared"]

    async def test_the_plan_batch_delete_discards_the_photos_too(self, world: World) -> None:
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")
        plans = GardenPlanService(world.repo._sites, world.repo, photos=lambda: world.service)

        await plans.apply_batch_async(
            SITE,
            tenant_key=TENANT,
            user_key=ME,
            role=TenantRole.LEAD,
            expected_revision=None,
            operations=[{"op": "delete", "entity": "location", "key": "bed"}],
            body_bytes=0,
        )

        assert "bed" not in world.repo.locations and world.attachments.deleted == ["p1"]

    async def test_the_commit_hook_runs_before_the_discard(self, world: World) -> None:
        """#2715 item 8: the route's batch-duration metric stops at the commit, not after the storage deletes."""
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")
        plans = GardenPlanService(world.repo._sites, world.repo, photos=lambda: world.service)
        events: list[str] = []
        original = world.attachments.delete_if_unreferenced

        async def deleting(attachment_id: str, tenant_key: str) -> bool:
            events.append("discard")
            return await original(attachment_id, tenant_key)

        world.attachments.delete_if_unreferenced = deleting  # type: ignore[method-assign]

        result = await plans.apply_batch_async(
            SITE,
            tenant_key=TENANT,
            user_key=ME,
            role=TenantRole.LEAD,
            expected_revision=None,
            operations=[{"op": "delete", "entity": "location", "key": "bed"}],
            body_bytes=0,
            on_commit=lambda committed: events.append(f"commit:{committed.plan_revision}"),
        )

        assert events == [f"commit:{result.plan_revision}", "discard"]

    async def test_a_failing_commit_hook_neither_fails_the_batch_nor_skips_the_release(self, world: World) -> None:
        """#2715 review I: the metric hook runs after the commit; its failure is logged, the photos still go."""
        world.attachments.add("p1", tenant_key=TENANT)
        world.add("p1")
        plans = GardenPlanService(world.repo._sites, world.repo, photos=lambda: world.service)

        def broken(_committed: object) -> None:
            raise RuntimeError("metrics registry gone")

        result = await plans.apply_batch_async(
            SITE,
            tenant_key=TENANT,
            user_key=ME,
            role=TenantRole.LEAD,
            expected_revision=None,
            operations=[{"op": "delete", "entity": "location", "key": "bed"}],
            body_bytes=0,
            on_commit=broken,
        )

        assert result.plan_revision is not None and world.attachments.deleted == ["p1"]

    async def test_discard_released_never_deletes_another_category(self, world: World) -> None:
        world.attachments.add("gallery", tenant_key=TENANT, category=AttachmentCategory.PLANT)
        world.attachments.add("foreign", tenant_key=OTHER_TENANT)

        discarded = await world.service.discard_released(["gallery", "foreign", "gone"], tenant_key=TENANT)

        assert discarded == 0 and world.attachments.deleted == []
        assert {"gallery", "foreign"} <= set(world.attachments.rows)

    async def test_the_photos_of_every_deleted_bed_go_in_one_batch(self, world: World) -> None:
        """#2715 item 6: one ``delete_many_if_unreferenced`` for the whole delete, not one reference scan per photo."""
        for bed in ("bed", "bed2"):
            for index in range(3):
                key = f"{bed}_p{index}"
                world.attachments.add(key, tenant_key=TENANT)
                world.add(key, key=bed)
        plans = GardenPlanService(world.repo._sites, world.repo, photos=lambda: world.service)

        await plans.apply_batch_async(
            SITE,
            tenant_key=TENANT,
            user_key=ME,
            role=TenantRole.LEAD,
            expected_revision=None,
            operations=[
                {"op": "delete", "entity": "location", "key": "bed"},
                {"op": "delete", "entity": "location", "key": "bed2"},
            ],
            body_bytes=0,
        )

        assert len(world.attachments.batch_deletes) == 1 and len(world.attachments.batch_deletes[0]) == 6
        assert len(world.attachments.deleted) == 6

    async def test_a_failing_batch_is_logged_and_counts_nothing(self, world: World) -> None:
        from unittest.mock import patch

        from app.domain.services import location_photo_service

        world.attachments.add("p1", tenant_key=TENANT)
        world.attachments.fail_with = RuntimeError("scan budget exhausted")

        with patch.object(location_photo_service, "logger") as logger:
            discarded = await world.service.discard_released(["p1", "p1"], tenant_key=TENANT)

        assert discarded == 0 and "p1" in world.attachments.rows
        assert logger.warning.call_args.args[0] == "location_photos_discard_failed"
        assert logger.warning.call_args.kwargs["attachment_ids"] == ["p1"]

    async def test_records_deleted_with_objects_left_count_and_report_only_the_objects(self, world: World) -> None:
        """#2715 review SEC-S02: the records are gone - they count; the objects that stayed are the reported error."""
        from unittest.mock import patch

        from app.domain.services import location_photo_service

        for key in ("p1", "p2"):
            world.attachments.add(key, tenant_key=TENANT)
        world.attachments.objects_fail = True

        with patch.object(location_photo_service, "logger") as logger:
            discarded = await world.service.discard_released(["p1", "p2"], tenant_key=TENANT)

        assert discarded == 2 and world.attachments.deleted == ["p1", "p2"]
        assert logger.warning.call_args.args[0] == "location_photo_objects_release_failed"
        fields = logger.warning.call_args.kwargs
        assert fields["deleted"] == 2 and fields["attachment_ids"] == ["p1", "p2"] and fields["objects"] == 2
        assert "location_photos_discard_failed" not in [call.args[0] for call in logger.warning.call_args_list]

    async def test_an_empty_release_asks_nothing(self, world: World) -> None:
        assert await world.service.discard_released([], tenant_key=TENANT) == 0
        assert world.attachments.batch_deletes == []

    async def test_release_without_a_provider_and_with_a_failing_one_never_raises(self, world: World) -> None:
        await release_location_photos(None, ["p1"], tenant_key=TENANT)

        def broken() -> Any:
            raise RuntimeError("no storage configured")

        await release_location_photos(broken, ["p1"], tenant_key=TENANT)

    async def test_a_failed_release_logs_the_attachment_ids_the_sweep_will_collect(self) -> None:
        """GDPR-001: the ids (never a URI) name what ``cleanup_orphaned_location_photos`` picks up later."""
        from unittest.mock import patch

        from app.domain.services import location_photo_service

        def broken() -> Any:
            raise RuntimeError("no storage configured")

        with patch.object(location_photo_service, "logger") as logger:
            await release_location_photos(broken, ["p1", "p2", "p1"], tenant_key=TENANT)

        event, fields = logger.warning.call_args.args[0], logger.warning.call_args.kwargs
        assert event == "location_photos_discard_failed"
        assert fields["attachment_ids"] == ["p1", "p2"] and fields["count"] == 2
        assert not any("/" in str(value) for value in fields["attachment_ids"])


class TestWithoutPhoto:
    """The removal rule both repositories share (``without_photo``), on its own."""

    @pytest.mark.parametrize(
        ("refs", "cover", "removed", "expected"),
        [
            (("p3", "p2", "p1"), "p1", "p1", (("p3", "p2"), "p3")),  # the cover goes: the newest remaining takes over
            (("p3", "p2", "p1"), "p3", "p3", (("p2", "p1"), "p2")),
            (("p1",), "p1", "p1", ((), None)),  # the last photo goes: no cover
            (("p2", "p1"), "p1", "p2", (("p1",), "p1")),  # another photo goes: the cover stays
            (("p2", "p1"), None, "p2", (("p1",), None)),  # a cleared cover stays cleared
        ],
        ids=["cover_oldest", "cover_newest", "last", "other", "cleared"],
    )
    def test_the_cover_after_a_removal(
        self, refs: tuple[str, ...], cover: str | None, removed: str, expected: tuple[tuple[str, ...], str | None]
    ) -> None:
        state = without_photo(LocationPhotoState(refs, cover), removed)

        assert (state.photo_refs, state.cover_photo_ref) == expected


class TestTheModel:
    def test_a_photo_twice_is_refused(self) -> None:
        with pytest.raises(PydanticValidationError):
            make_location("b", photo_refs=["p1", "p1"])

    def test_a_cover_that_is_not_a_photo_is_refused(self) -> None:
        with pytest.raises(PydanticValidationError):
            make_location("b", photo_refs=["p1"], cover_photo_ref="p2")

    def test_more_than_the_bound_is_refused(self) -> None:
        with pytest.raises(PydanticValidationError):
            make_location("b", photo_refs=[f"p{i}" for i in range(MAX_PHOTOS_PER_LOCATION + 1)])

    def test_a_bed_without_photos_reads_as_before(self) -> None:
        location = Location.model_validate({"_key": "b", "name": "B", "area_m2": 0})

        assert location.photo_refs == [] and location.cover_photo_ref is None
