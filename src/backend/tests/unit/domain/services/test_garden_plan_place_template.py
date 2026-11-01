"""REQ-053 WP 7.9 (#2475) - ``place-template`` and the template reference in the JSON file.

``place_template`` runs through the same path as a batch ``create_location``; what is pinned here is what it adds:
the template is resolved under the tenant (a foreign key answers like an absent one), the bed receives a copy and
a provenance key, nothing of ``recurring_task_templates`` is applied, and every refusal leaves the repository
untouched. The import half: ``template_key`` travels in the file and is resolved against the system templates and
the target tenant's own - otherwise dropped and reported.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import GrowingMediumKind, SoilDrainage, TenantRole
from app.common.exceptions import (
    ForbiddenError,
    NotFoundError,
    PlanError,
    PlanRevisionConflictError,
    PlanValidationError,
)
from app.domain.models.bed_template import BedTemplate, SoilProfileDefaults
from app.domain.models.site import SitePlan
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_import_service import GardenPlanImportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.bed_template_fakes import FakeTemplates
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

_RECT_2X1 = {"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}


def _template(key: str, tenant: str | None, **overrides: Any) -> BedTemplate:
    return BedTemplate(
        **{
            "_key": key,
            "tenant_key": tenant,
            "name": "Raised bed 2 x 1",
            "location_type_key": "raised_bed",
            "default_geometry": _RECT_2X1,
            **overrides,
        }
    )


class World:
    def __init__(self) -> None:
        site = make_site()
        site.plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0},
            plan_revision=5,
        )
        self.sites = FakeSites(site, make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
        self.repo = FakePlanRepo(self.sites)
        self.templates = FakeTemplates()
        self.templates.add(
            _template(
                "sys_raised",
                None,
                height_m=0.8,
                soil_profile_defaults=SoilProfileDefaults(
                    growing_medium_kind=GrowingMediumKind.RAISED_BED_MIX, drainage=SoilDrainage.GOOD
                ),
                recurring_task_templates=["tt_refill"],
            )
        )
        self.templates.add(_template("own", TENANT, name="Own bed", location_type_key="bed"))
        self.templates.add(_template("theirs", OTHER_TENANT, name="Their bed"))
        self.plans = GardenPlanService(self.sites, self.repo, template_repo=self.templates)

    def place(self, template: str = "sys_raised", **overrides: Any):
        arguments: dict[str, Any] = {
            "tenant_key": TENANT,
            "user_key": USER,
            "role": TenantRole.GROWER,
            "template_key": template,
            "origin": (4.0, 1.0),
            "rotation_deg": 0.0,
            "expected_revision": 5,
        } | overrides
        return self.plans.place_template(SITE, **arguments)


@pytest.fixture
def world() -> World:
    return World()


class TestPlacing:
    def test_a_bed_is_created_through_the_batch_path_with_a_copy_of_the_template(self, world: World) -> None:
        result = world.place()

        assert result.plan_revision == 6
        (real,) = result.key_map.values()
        bed = world.repo.locations[real]
        assert (bed.name, bed.location_type_key, bed.height_m) == ("Raised bed 2 x 1", "raised_bed", 0.8)
        assert bed.template_key == "sys_raised"
        assert bed.soil_profile is not None
        assert (bed.soil_profile.growing_medium_kind, bed.soil_profile.drainage) == (
            GrowingMediumKind.RAISED_BED_MIX,
            SoilDrainage.GOOD,
        )
        assert result.derived[real].area_m2 == 2.0
        assert result.derived[real].bbox == (4.0, 1.0, 6.0, 2.0)
        (write,) = world.repo.applied
        assert (write.expected_revision, write.tenant_key, write.editor_key) == (5, TENANT, USER)

    def test_the_rotation_is_applied_about_the_anchor(self, world: World) -> None:
        result = world.place(rotation_deg=90.0)

        (real,) = result.key_map.values()
        geometry = world.repo.locations[real].geometry
        assert geometry is not None and geometry.rotation_deg == 90.0
        assert result.derived[real].bbox == (3.0, 1.0, 4.0, 3.0)

    def test_the_recurring_task_templates_are_stored_but_not_applied(self, world: World) -> None:
        world.place()

        (write,) = world.repo.applied
        assert write.care_events == []
        assert "tt_refill" not in repr([loc for _, loc in write.location_inserts])

    def test_a_tenants_own_template_can_be_placed(self, world: World) -> None:
        result = world.place("own")

        (real,) = result.key_map.values()
        assert world.repo.locations[real].template_key == "own"

    def test_later_edits_to_the_template_do_not_follow_the_bed(self, world: World) -> None:
        (real,) = world.place().key_map.values()

        world.templates.templates["sys_raised"] = _template("sys_raised", None, name="Renamed", height_m=0.3)

        assert (world.repo.locations[real].name, world.repo.locations[real].height_m) == ("Raised bed 2 x 1", 0.8)


class TestRefusals:
    def test_a_foreign_template_answers_422_reference_not_found_like_an_absent_one(self, world: World) -> None:
        for key in ("theirs", "nope"):
            with pytest.raises(PlanValidationError) as refused:
                world.place(key)
            assert refused.value.codes == ["reference.not_found"]
            assert refused.value.details[0]["field"] == "template_key"
        assert world.repo.applied == []

    def test_a_service_without_a_template_catalogue_places_nothing(self) -> None:
        site = make_site()
        sites = FakeSites(site)
        service = GardenPlanService(sites, FakePlanRepo(sites))

        with pytest.raises(PlanValidationError):
            service.place_template(
                SITE,
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.GROWER,
                template_key="sys_raised",
                origin=(1.0, 1.0),
                rotation_deg=0.0,
                expected_revision=5,
            )

    def test_a_viewer_places_nothing_and_a_foreign_site_is_a_404_first(self, world: World) -> None:
        with pytest.raises(ForbiddenError):
            world.place(role=TenantRole.VIEWER)
        with pytest.raises(NotFoundError):
            world.plans.place_template(
                "site_foreign",
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.VIEWER,  # the anchor answers before the role (SR-013)
                template_key="theirs",
                origin=(1.0, 1.0),
                rotation_deg=0.0,
                expected_revision=5,
            )
        assert world.repo.applied == []

    def test_a_stale_revision_is_409_and_writes_nothing(self, world: World) -> None:
        world.repo.applied.clear()

        with pytest.raises(PlanRevisionConflictError) as conflict:
            world.place(expected_revision=4)

        assert conflict.value.status_code == 409 and conflict.value.error_code == "plan.revision_conflict"
        assert world.repo.locations == {}

    def test_a_bed_that_leaves_the_boundary_is_422_outside_parent(self, world: World) -> None:
        with pytest.raises(PlanValidationError) as refused:
            world.place(origin=(9.5, 9.5))

        assert "geometry.outside_parent" in refused.value.codes
        assert world.repo.applied == []

    def test_an_origin_outside_the_plan_frame_is_422_geometry_invalid(self, world: World) -> None:
        with pytest.raises(PlanValidationError) as refused:
            world.place(origin=(2000.0, 1.0))

        assert refused.value.codes == ["geometry.invalid"]
        assert world.repo.applied == []

    def test_a_bed_on_top_of_another_is_refused(self, world: World) -> None:
        world.repo.locations["b1"] = make_location("b1", "Beet 1", geometry=rect(4, 1, 2, 1))

        with pytest.raises(PlanValidationError) as refused:
            world.place()

        assert any(code.startswith("bed.overlap") or code.endswith("overlap") for code in refused.value.codes)
        assert world.repo.applied == []

    def test_a_template_whose_location_type_is_gone_is_refused_as_an_absent_reference(self, world: World) -> None:
        world.repo.bed_types.pop("raised_bed")

        with pytest.raises(PlanValidationError) as refused:
            world.place()

        assert refused.value.codes == ["reference.not_found"]

    def test_a_template_whose_location_type_stopped_being_a_bed_type_is_refused_up_front(self, world: World) -> None:
        # #2529: the batch path would create the location as a non-bed (outside the overlap rule); refused first.
        world.repo.bed_types["raised_bed"] = False

        with pytest.raises(PlanError) as refused:
            world.place()

        assert (refused.value.error_code, refused.value.status_code) == ("bed_template.not_a_bed_type", 422)
        assert world.repo.applied == [] and world.repo.locations == {}


class TestTheBatchRouteIgnoresTheTemplateFields:
    def test_a_client_cannot_smuggle_a_template_key_or_a_soil_profile_through_create_location(
        self, world: World
    ) -> None:
        operation = {
            "op": "create_location",
            "temp_key": "t1",
            "data": {"name": "B", "location_type_key": "bed", "geometry": rect(1, 1), "template_key": "theirs"},
        }

        with pytest.raises(PlanValidationError):
            world.plans.apply_batch(
                SITE,
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.GROWER,
                expected_revision=5,
                operations=[operation],
                body_bytes=100,
            )
        assert world.repo.applied == []


class TestExportAndImport:
    @staticmethod
    def _rig(world: World) -> tuple[GardenPlanExportService, GardenPlanImportService]:
        export = GardenPlanExportService(world.sites, world.repo, world.plans)
        return export, GardenPlanImportService(world.sites, world.repo, world.plans, export)

    @staticmethod
    def _import(importer: GardenPlanImportService, document: dict[str, Any], *, tenant: str = TENANT, site: str = SITE):
        return importer.import_plan(
            site,
            tenant_key=tenant,
            user_key=USER,
            document=document,
            role=TenantRole.LEAD,
            mode="merge",
            dry_run=False,
            force=False,
            confirm_site_name=None,
        )

    def test_the_export_carries_the_template_key_and_nothing_of_the_template(self, world: World) -> None:
        export, _ = self._rig(world)
        world.place()

        document = export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")

        (bed,) = document["locations"]
        assert bed["template_key"] == "sys_raised"
        assert "Raised bed" not in repr({k: v for k, v in document.items() if k != "locations"})
        assert "recurring_task_templates" not in repr(document)

    def test_a_system_and_an_own_template_resolve_on_import(self, world: World) -> None:
        export, importer = self._rig(world)
        world.place()
        world.place("own", origin=(7.0, 1.0), expected_revision=6)
        document = export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")
        world.repo.locations.clear()

        report = self._import(importer, document)

        assert report.applied and report.dropped_references == []
        assert sorted(loc.template_key or "" for loc in world.repo.locations.values()) == ["own", "sys_raised"]

    def test_a_template_key_the_target_cannot_see_is_dropped_and_reported(self, world: World) -> None:
        export, importer = self._rig(world)
        world.place()
        document = export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")
        document["locations"][0]["template_key"] = "theirs"  # another tenant's template, or one that never existed
        world.repo.locations.clear()

        report = self._import(importer, document)

        assert report.applied
        assert [(d.entity, d.field, d.reason) for d in report.dropped_references] == [
            ("location", "template_key", "not_found")
        ]
        (bed,) = world.repo.locations.values()
        assert bed.template_key is None

    def test_a_file_from_another_installation_without_the_catalogue_keeps_the_bed_and_drops_the_key(
        self, world: World
    ) -> None:
        export, importer = self._rig(world)
        world.place()
        document = export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")
        world.templates.templates.clear()
        world.repo.locations.clear()

        report = self._import(importer, document)

        assert report.applied and report.would_create.locations == 1
        assert report.dropped_references_total == 1

    def test_a_file_older_than_wp_7_9_has_no_template_key_and_imports_unchanged(self, world: World) -> None:
        export, importer = self._rig(world)
        world.place()
        document = export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")
        for location in document["locations"]:
            location.pop("template_key")
        world.repo.locations.clear()

        report = self._import(importer, document)

        assert report.applied and report.dropped_references == []
