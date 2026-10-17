"""REQ-053 WP 1.8 (#2327) — the garden-plan service: check order, roles, geometry rules, quotas, write set.

The repository is a faithful in-memory double: it holds the structure, applies a write set the way
the transaction does (revision check first, then the writes) and records what it was handed. The
tests assert on what the *service decides* — which request reaches the repository at all, and with
what — so every refusal test also asserts ``repo.applied == []``: a refusal that still wrote is the
defect, not the status code.

Falsification of the order (SR-013): ``TestTheCheckOrder`` swaps pairs of defects in one request and
asserts that the *earlier* check in the spec's order answers — a service that ran Pydantic before the
role check answers 422 where the spec says 403.
"""

from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from app.common.enums import GardenObjectType, TenantRole
from app.common.exceptions import (
    ForbiddenError,
    NotFoundError,
    PlanError,
    PlanRevisionConflictError,
    PlanValidationError,
)
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    MAX_BATCH_BODY_BYTES,
    PlanAuditEntry,
    PlantShortInfo,
    SetBoundaryOp,
    TaskCounter,
)
from app.domain.models.site import Site, SitePlan, Slot
from app.domain.services import garden_plan_service
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.garden_plan_fakes import (  # noqa: F401
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

_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


@pytest.fixture
def world():
    site = make_site()
    sites = FakeSites(site, make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    repo = FakePlanRepo(sites)
    service = GardenPlanService(sites, repo)
    return service, repo, site


def batch(service, ops, *, role=TenantRole.GROWER, revision=5, tenant=TENANT, body_bytes=1000, site=SITE):
    return service.apply_batch(
        site,
        tenant_key=tenant,
        user_key=USER,
        role=role,
        expected_revision=revision,
        operations=ops,
        body_bytes=body_bytes,
    )


def create_bed(temp="tmp1", geometry=None, **data):
    return {
        "op": "create_location",
        "temp_key": temp,
        "data": {"name": "Beet 6", "location_type_key": "bed", "geometry": geometry or rect(4, 1), **data},
    }


class TestAGoodBatch:
    def test_creates_a_bed_and_derives_its_values(self, world):
        service, repo, _ = world
        result = batch(service, [create_bed()])
        assert result.plan_revision == 6
        (real,) = result.key_map.values()
        assert result.derived[real].area_m2 == 2.0
        assert result.derived[real].bbox == (4.0, 1.0, 6.0, 2.0)
        assert repo.locations[real].path == "beet_6"

    def test_a_child_names_its_parent_by_temp_key_and_inserts_come_parents_first(self, world):
        service, repo, _ = world
        ops = [
            create_bed("child", rect(1, 1, 0.5, 0.5), parent_location_key="parent", name="Reihe"),
            create_bed("parent", rect(0.5, 0.5, 4, 4), location_type_key="greenhouse", name="Haus"),
        ]
        # The child is listed first, but its parent is declared later: not resolvable at that point.
        with pytest.raises(PlanValidationError) as refused:
            batch(service, ops)
        assert refused.value.codes == ["reference.not_found"]
        assert repo.applied == []

        batch(service, list(reversed(ops)))
        (write,) = repo.applied
        assert [temp for temp, _ in write.location_inserts] == ["parent", "child"]
        child = next(loc for loc in repo.locations.values() if loc.name == "Reihe")
        assert child.parent_location_key in repo.locations
        assert child.path == "haus/reihe"

    def test_update_geometry_recomputes_area_and_bbox_and_marks_the_row_updated(self, world):
        service, repo, _ = world
        repo.locations["loc_b03"] = make_location("loc_b03", geometry=rect(1, 1, 2, 1))
        result = batch(
            service,
            [{"op": "update_geometry", "entity": "location", "key": "loc_b03", "geometry": rect(1, 1.5, 2, 1, 90)}],
        )
        assert result.updated == ["loc_b03"]
        assert result.derived["loc_b03"].bbox == (0.0, 1.5, 1.0, 3.5)  # §20.1 worked example, shifted by 0.5
        assert repo.locations["loc_b03"].geometry.rotation_deg == 90.0

    def test_a_garden_object_with_a_tree_circle_takes_its_crown_from_the_drawing(self, world):
        service, repo, _ = world
        result = batch(
            service,
            [
                {
                    "op": "create_garden_object",
                    "temp_key": "t1",
                    "data": {
                        "object_type": "tree",
                        "geometry": {"kind": "circle", "origin": [5, 5], "radius_m": 1.5},
                        "props": {},
                    },
                }
            ],
        )
        (key,) = result.key_map.values()
        assert repo.objects[key].props.crown_radius_m == 1.5
        assert repo.objects[key].created_by == USER

    def test_a_batch_that_only_sets_flags_changes_those_rows(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1))
        repo.locations["b"] = make_location("b", name="B", geometry=rect(5, 5))
        result = batch(
            service,
            [
                {"op": "set_locked", "entity": "location", "key": "a", "locked": True},
                {"op": "set_z_order", "entity": "location", "key": "a", "z_order": 7},
            ],
        )
        assert result.updated == ["a"]  # b is untouched and is not rewritten
        assert repo.locations["a"].locked is True
        assert repo.locations["a"].z_order == 7

    def test_update_fields_renames_and_moves_the_path(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", name="Old name", geometry=rect(1, 1))
        batch(service, [{"op": "update_fields", "entity": "location", "key": "a", "fields": {"name": "New Name"}}])
        assert repo.locations["a"].name == "New Name"
        assert repo.locations["a"].path == "new_name"

    def test_update_fields_on_an_object_replaces_its_props(self, world):
        service, repo, _ = world
        repo.objects["go"] = GardenObject(
            _key="go",
            site_key=SITE,
            object_type=GardenObjectType.WATER_SOURCE,
            geometry={"kind": "point", "origin": [9.7, 0.4]},
            props={"water_source_kind": "rain_barrel"},
        )
        batch(
            service,
            [
                {
                    "op": "update_fields",
                    "entity": "garden_object",
                    "key": "go",
                    "fields": {"props": {"water_source_kind": "tap", "capacity_liters": 300}},
                }
            ],
        )
        assert repo.objects["go"].props.capacity_liters == 300


class TestTheCheckOrder:
    """SR-013: authentication → tenant anchor and references → role per op → Pydantic → domain → revision."""

    def test_a_foreign_site_is_a_404_before_anything_in_the_body_is_read(self, world):
        service, repo, _ = world
        with pytest.raises(NotFoundError):
            batch(service, [{"op": "nonsense"}] * 600, site="site_foreign")  # 600 ops and garbage: still 404
        assert repo.applied == []

    def test_an_unknown_site_is_the_same_404(self, world):
        service, _, _ = world
        with pytest.raises(NotFoundError) as unknown:
            batch(service, [create_bed()], site="nope")
        with pytest.raises(NotFoundError) as foreign:
            batch(service, [create_bed()], site="site_foreign")
        assert unknown.value.status_code == foreign.value.status_code == 404
        assert unknown.value.details[0]["entity"] == foreign.value.details[0]["entity"]

    def test_the_role_is_measured_before_pydantic(self, world):
        service, repo, _ = world
        repo.objects["go_old"] = _object("go_old")
        ops = [
            {"op": "update_geometry", "entity": "garden_object", "key": "go_old", "geometry": {"kind": "bogus"}},  # 422
            {"op": "delete", "entity": "garden_object", "key": "go_old"},  # above a grower
        ]
        with pytest.raises(PlanError) as refused:
            batch(service, ops, role=TenantRole.GROWER)
        assert refused.value.error_code == "batch.operation_forbidden"
        assert refused.value.status_code == 403
        assert refused.value.details[0]["op_index"] == 1
        # The same request from a lead reaches Pydantic and is refused for the geometry instead —
        # proving the 403 above was the role check and not a side effect of the bad geometry.
        with pytest.raises(PlanValidationError) as invalid:
            batch(service, ops, role=TenantRole.LEAD)
        assert invalid.value.codes[0] == "geometry.invalid"
        assert repo.applied == []

    def test_a_reference_is_resolved_before_the_role_is_measured(self, world):
        service, _, _ = world
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [{"op": "delete", "entity": "location", "key": "ghost"}], role=TenantRole.GROWER)
        assert refused.value.codes == ["reference.not_found"]  # not 403: the key must resolve first (T-03)

    def test_pydantic_comes_before_the_domain_rules(self, world):
        service, repo, _ = world
        ops = [
            create_bed("ok", rect(9.5, 9.5)),  # outside the boundary: a domain finding
            create_bed("bad", {"kind": "rect", "origin": [1, 1], "width_m": -1, "length_m": 1}),  # V-01
        ]
        with pytest.raises(PlanValidationError) as refused:
            batch(service, ops)
        assert refused.value.codes == ["geometry.invalid"]  # the domain finding of op 0 is not even computed
        assert repo.applied == []

    def test_the_revision_is_checked_last(self, world):
        service, repo, _ = world
        with pytest.raises(PlanValidationError):  # stale revision AND invalid geometry: the 422 wins
            batch(service, [create_bed(geometry=rect(9.5, 9.5))], revision=1)
        with pytest.raises(PlanRevisionConflictError):  # a valid batch with the stale revision: 409
            batch(service, [create_bed()], revision=1)
        assert repo.applied == []


class TestRolesPerOperation:
    def test_a_grower_with_a_delete_in_second_position_is_refused_whole_gp_acc_042(self, world):
        service, repo, _ = world
        repo.locations["loc_b03"] = make_location("loc_b03", geometry=rect(1, 1))
        repo.objects["go_old"] = _object("go_old")
        ops = [
            {"op": "update_geometry", "entity": "location", "key": "loc_b03", "geometry": rect(2, 2)},
            {"op": "delete", "entity": "garden_object", "key": "go_old"},
        ]
        with pytest.raises(PlanError) as refused:
            batch(service, ops, role=TenantRole.GROWER)
        assert (refused.value.error_code, refused.value.status_code) == ("batch.operation_forbidden", 403)
        assert refused.value.details[0]["op_index"] == 1
        assert repo.applied == []
        assert repo.locations["loc_b03"].geometry.origin == (1.0, 1.0)  # the first op is not applied either

    def test_a_viewer_may_run_no_operation(self, world):
        service, repo, _ = world
        with pytest.raises(PlanError) as refused:
            batch(service, [create_bed()], role=TenantRole.VIEWER)
        assert refused.value.details[0]["op_index"] == 0
        assert repo.applied == []

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
    @pytest.mark.parametrize(
        "op",
        [
            create_bed("t"),
            {"op": "set_boundary", "boundary": _BOUNDARY},
            {"op": "set_locked", "entity": "location", "key": "a", "locked": True},
            {"op": "set_z_order", "entity": "location", "key": "a", "z_order": 2},
            {"op": "update_fields", "entity": "location", "key": "a", "fields": {"notes": "x"}},
            {"op": "update_geometry", "entity": "location", "key": "a", "geometry": rect(3, 3)},
        ],
    )
    def test_every_non_delete_operation_is_open_to_a_grower_and_a_lead(self, world, role, op):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1))
        batch(service, [op], role=role)
        assert len(repo.applied) == 1

    def test_a_lead_may_delete(self, world):
        service, repo, _ = world
        repo.objects["go_old"] = _object("go_old")
        result = batch(service, [{"op": "delete", "entity": "garden_object", "key": "go_old"}], role=TenantRole.LEAD)
        assert result.deleted == ["go_old"]
        assert "go_old" not in repo.objects


class TestDomainRules:
    def test_a_bed_outside_the_boundary_is_refused_and_nothing_is_persisted_gp_acc_009(self, world):
        service, repo, site = world
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(geometry=rect(9.5, 9.5))])
        detail = refused.value.details[0]
        assert (detail["code"], detail["op_index"]) == ("geometry.outside_parent", 0)
        assert repo.applied == [] and repo.locations == {}
        assert site.plan.plan_revision == 5

    def test_a_bed_inside_the_boundary_within_one_centimetre_is_tolerated(self, world):
        service, repo, _ = world
        batch(service, [create_bed(geometry=rect(8.005, 8.995))])  # protrudes by 5 mm at the top edge
        assert len(repo.applied) == 1

    def test_a_rotated_bed_is_checked_by_its_transformed_corners(self, world):
        service, _, _ = world
        # 4 x 1 m turned 90° about its origin sticks out to the left: x from 0.5 - 1 = -0.5.
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(geometry=rect(0.5, 1, 4, 1, 90))])
        assert refused.value.codes == ["geometry.outside_parent"]

    def test_a_child_must_lie_inside_its_parent(self, world):
        service, repo, _ = world
        repo.locations["house"] = make_location("house", location_type_key="greenhouse", geometry=rect(1, 1, 4, 4))
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(geometry=rect(4.5, 4.5, 2, 2), parent_location_key="house")])
        assert refused.value.codes == ["geometry.outside_parent"]
        batch(service, [create_bed(geometry=rect(2, 2, 1, 1), parent_location_key="house")])
        assert len(repo.applied) == 1

    def test_moving_a_parent_rechecks_its_children(self, world):
        service, repo, _ = world
        repo.locations["house"] = make_location("house", location_type_key="greenhouse", geometry=rect(1, 1, 4, 4))
        repo.locations["child"] = make_location("child", geometry=rect(2, 2, 1, 1), parent_location_key="house")
        with pytest.raises(PlanValidationError) as refused:
            batch(
                service,
                [{"op": "update_geometry", "entity": "location", "key": "house", "geometry": rect(6, 6, 2, 2)}],
            )
        assert refused.value.details[0]["key"] == "child"
        assert refused.value.details[0]["op_index"] == 0

    def test_two_beds_of_one_parent_may_not_overlap_but_a_bed_may_overlap_an_object(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1, 2, 2))
        repo.objects["path"] = _object("path")
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(geometry=rect(2, 2, 2, 2))])
        assert refused.value.codes == ["bed.overlap"]
        batch(service, [create_bed(geometry=rect(3, 1, 2, 2))])  # touching edges is not overlap
        batch(
            service,
            [
                {
                    "op": "create_garden_object",
                    "temp_key": "p",
                    "data": {
                        "object_type": "path",
                        "geometry": {"kind": "polyline", "points": [[0, 1.5], [9, 1.5]], "width_m": 0.6},
                    },
                }
            ],
            revision=6,
        )

    def test_beds_under_different_parents_do_not_compete(self, world):
        service, repo, _ = world
        repo.locations["h1"] = make_location("h1", location_type_key="greenhouse", geometry=rect(0, 0, 4, 4))
        repo.locations["h2"] = make_location("h2", location_type_key="greenhouse", geometry=rect(5, 5, 4, 4))
        repo.locations["a"] = make_location("a", geometry=rect(1, 1, 2, 2), parent_location_key="h1")
        batch(service, [create_bed(geometry=rect(6, 6, 2, 2), parent_location_key="h2")])
        assert len(repo.applied) == 1

    def test_a_self_intersecting_polygon_is_refused(self, world):
        service, _, _ = world
        bowtie = {"kind": "polygon", "points": [[1, 1], [3, 3], [3, 1], [1, 3]]}
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(geometry=bowtie)])
        assert refused.value.codes == ["geometry.self_intersecting"]

    def test_an_off_site_object_is_exempt_from_containment(self, world):
        service, repo, _ = world
        batch(
            service,
            [
                {
                    "op": "create_garden_object",
                    "temp_key": "n",
                    "data": {
                        "object_type": "building",
                        "off_site": True,
                        "geometry": rect(10.5, 2, 5, 5),
                    },
                }
            ],
        )
        assert len(repo.objects) == 1

    def test_a_site_without_a_boundary_has_no_outer_containment(self, world):
        service, repo, site = world
        site.plan = SitePlan(plan_revision=5)
        batch(service, [create_bed(geometry=rect(500, 500))])
        assert len(repo.applied) == 1

    def test_findings_name_every_operation_not_only_the_first(self, world):
        service, _, _ = world
        with pytest.raises(PlanValidationError) as refused:
            batch(
                service, [create_bed("a", rect(9.5, 9.5)), create_bed("b", rect(1, 1)), create_bed("c", rect(9.5, 0))]
            )
        assert [d["op_index"] for d in refused.value.details] == [0, 2]


class TestLockedObjects:
    def test_a_locked_bed_cannot_be_moved_or_deleted_but_its_notes_can_change(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1), locked=True)
        for op, role in (
            ({"op": "update_geometry", "entity": "location", "key": "a", "geometry": rect(2, 2)}, TenantRole.GROWER),
            ({"op": "delete", "entity": "location", "key": "a"}, TenantRole.LEAD),
        ):
            with pytest.raises(PlanValidationError) as refused:
                batch(service, [op], role=role)
            assert refused.value.codes == ["object.locked"]
        batch(service, [{"op": "update_fields", "entity": "location", "key": "a", "fields": {"notes": "n"}}])
        assert repo.locations["a"].notes == "n"

    def test_unlocking_and_moving_in_one_batch_is_still_refused_the_lock_is_read_in_order(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1), locked=True)
        ops = [
            {"op": "update_geometry", "entity": "location", "key": "a", "geometry": rect(2, 2)},
            {"op": "set_locked", "entity": "location", "key": "a", "locked": False},
        ]
        with pytest.raises(PlanValidationError):
            batch(service, ops)
        batch(service, list(reversed(ops)))
        assert repo.locations["a"].geometry.origin == (2.0, 2.0)


class TestTheBoundary:
    def test_the_first_save_creates_the_plan_with_revision_one_gp_acc_001(self):
        site = Site(_key=SITE, tenant_key=TENANT, name="Garten", type="outdoor")
        sites = FakeSites(site)
        repo = FakePlanRepo(sites)
        service = GardenPlanService(sites, repo)
        result = service.set_boundary(
            SITE,
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
            operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY, north_angle_deg=0),
            expected_revision=None,
        )
        assert result.plan_revision == 1
        (write,) = repo.applied
        assert write.total_area_m2 == 100.0
        assert write.audit == [{"op": "set_boundary", "entity": "site", "key": SITE, "summary": "rect"}]

    def test_a_viewer_cannot_set_it(self, world):
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            service.set_boundary(
                SITE,
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.VIEWER,
                operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY),
                expected_revision=None,
            )
        assert repo.applied == []

    def test_a_stale_expected_revision_is_a_conflict(self, world):
        service, repo, _ = world
        with pytest.raises(PlanRevisionConflictError) as conflict:
            service.set_boundary(
                SITE,
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.GROWER,
                operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY),
                expected_revision=2,
            )
        assert conflict.value.current_revision == 5
        assert repo.applied == []

    def test_shrinking_below_a_top_level_object_is_refused_with_its_key_v19(self, world):
        service, repo, _ = world
        repo.locations["far"] = make_location("far", geometry=rect(7, 7, 2, 2))
        repo.locations["near"] = make_location("near", name="Near", geometry=rect(1, 1, 2, 2))
        smaller = {"op": "set_boundary", "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}}
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [smaller])
        detail = refused.value.details[0]
        assert detail["code"] == "boundary.shrinks_below_objects"
        assert detail["keys"] == ["location:far"]  # near is inside and not listed
        assert repo.applied == []

    def test_an_off_site_object_and_a_child_do_not_block_a_smaller_boundary(self, world):
        service, repo, _ = world
        repo.locations["house"] = make_location("house", location_type_key="greenhouse", geometry=rect(1, 1, 3, 3))
        repo.locations["child"] = make_location("child", geometry=rect(2, 2, 1, 1), parent_location_key="house")
        repo.objects["nb"] = GardenObject(
            _key="nb",
            site_key=SITE,
            object_type=GardenObjectType.BUILDING,
            geometry=rect(20, 20, 3, 3),
            props={},
            off_site=True,
        )
        smaller = {"op": "set_boundary", "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}}
        batch(service, [smaller])
        assert len(repo.applied) == 1

    def test_moving_the_blocker_in_the_same_batch_lets_the_boundary_shrink(self, world):
        service, repo, _ = world
        repo.locations["far"] = make_location("far", geometry=rect(7, 7, 2, 2))
        ops = [
            {"op": "update_geometry", "entity": "location", "key": "far", "geometry": rect(1, 1, 2, 2)},
            {"op": "set_boundary", "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}},
        ]
        batch(service, ops)
        assert len(repo.applied) == 1

    def test_a_circle_is_not_a_boundary(self, world):
        service, _, _ = world
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [{"op": "set_boundary", "boundary": {"kind": "circle", "origin": [5, 5], "radius_m": 3}}])
        assert refused.value.codes == ["geometry.invalid"]


class TestComplexityBudgetAndQuotas:
    def test_501_operations_are_refused_gp_acc_013(self, world):
        service, repo, _ = world
        with pytest.raises(PlanError) as refused:
            batch(service, [{"op": "set_z_order", "entity": "location", "key": "a", "z_order": 1}] * 501)
        assert (refused.value.error_code, refused.value.status_code) == ("batch.too_many_operations", 422)
        assert refused.value.details[0]["limit"] == 500
        assert repo.applied == []

    def test_500_operations_are_still_fine(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1))
        batch(service, [{"op": "set_z_order", "entity": "location", "key": "a", "z_order": n} for n in range(500)])
        assert repo.locations["a"].z_order == 499

    def test_a_body_over_two_megabytes_is_too_complex(self, world):
        service, repo, _ = world
        with pytest.raises(PlanError) as refused:
            batch(service, [create_bed()], body_bytes=MAX_BATCH_BODY_BYTES + 1)
        assert refused.value.error_code == "batch.too_complex"
        assert repo.applied == []

    def test_more_than_20000_points_are_too_complex(self, world):
        service, repo, _ = world
        ring = [[1 + (i % 2) * 0.001, 1 + i * 0.0001] for i in range(200)]
        ops = [
            {
                "op": "create_garden_object",
                "temp_key": f"p{n}",
                "data": {"object_type": "path", "geometry": {"kind": "polyline", "points": ring, "width_m": 0.5}},
            }
            for n in range(101)
        ]
        with pytest.raises(PlanError) as refused:
            batch(service, ops)
        assert refused.value.error_code == "batch.too_complex"
        assert refused.value.details[0]["limit"] == 20_000
        assert repo.applied == []

    def test_the_time_budget_is_enforced_before_the_transaction(self, world, monkeypatch):
        service, repo, _ = world
        ticks = iter([0.0, 11.0])  # the request starts at 0; the first deadline check reads 11 s
        monkeypatch.setattr(garden_plan_service, "_now", lambda: next(ticks, 11.0))
        with pytest.raises(PlanError) as refused:
            batch(service, [create_bed()])
        assert refused.value.error_code == "batch.too_complex"
        assert repo.applied == []

    def test_the_transaction_gets_what_is_left_of_the_budget(self, world, monkeypatch):
        service, repo, _ = world
        ticks = iter([0.0, 0.0, 0.0, 4.0])  # started, two deadline checks, then the budget left for the transaction
        monkeypatch.setattr(garden_plan_service, "_now", lambda: next(ticks, 4.0))
        batch(service, [create_bed()])
        assert repo.applied[0].time_budget_seconds == pytest.approx(6.0)

    def test_the_501st_location_or_object_is_a_quota_error_with_limit_and_current(self, world):
        service, repo, _ = world
        for n in range(500):
            repo.objects[f"o{n}"] = _object(f"o{n}")
        with pytest.raises(PlanError) as refused:
            batch(service, [create_bed()])
        assert (refused.value.error_code, refused.value.status_code) == ("plan.quota_exceeded", 422)
        assert refused.value.details[0]["limit"] == 500
        assert refused.value.details[0]["current"] == 501
        assert repo.applied == []

    def test_an_already_oversized_plan_may_still_shrink(self, world):
        service, repo, _ = world
        for n in range(520):
            repo.objects[f"o{n}"] = _object(f"o{n}")
        batch(service, [{"op": "delete", "entity": "garden_object", "key": "o0"}], role=TenantRole.LEAD)
        assert len(repo.applied) == 1


class TestMalformedOperations:
    @pytest.mark.parametrize(
        "raw",
        [
            "not a mapping",
            {},
            {"op": "slot_move", "key": "x"},  # slot operations are not part of the batch (GP-API-003)
            {"op": "delete", "entity": "slot", "key": "x"},
            {"op": "update_fields", "entity": "location", "key": "a", "fields": {"tenant_key": "ten_other"}},
            {"op": "update_fields", "entity": "location", "key": "a", "fields": {"geometry": rect(1, 1)}},
            {"op": "create_location", "temp_key": "bad key!", "data": {}},
        ],
    )
    def test_each_is_a_422_naming_its_index_and_nothing_is_written(self, world, raw):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1))
        with pytest.raises((PlanValidationError, PlanError)) as refused:
            batch(service, [create_bed("ok", rect(5, 5)), raw], role=TenantRole.LEAD)
        assert refused.value.status_code == 422
        assert repo.applied == []

    def test_a_duplicate_temp_key_is_refused(self, world):
        service, repo, _ = world
        with pytest.raises(PlanValidationError):
            batch(service, [create_bed("t", rect(1, 1)), create_bed("t", rect(5, 5))])
        assert repo.applied == []

    def test_a_temp_key_that_is_a_stored_key_is_refused(self, world):
        service, repo, _ = world
        repo.locations["12345"] = make_location("12345", geometry=rect(1, 1))
        with pytest.raises(PlanValidationError):
            batch(service, [create_bed("12345", rect(5, 5))])

    def test_an_unknown_location_type_is_a_reference_error(self, world):
        service, _, _ = world
        op = create_bed()
        op["data"]["location_type_key"] = "no_such_type"
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [op])
        assert refused.value.details[0]["field"] == "data.location_type_key"
        assert refused.value.codes == ["reference.not_found"]

    def test_a_parent_of_another_site_is_not_resolvable(self, world):
        # The structure the service loads is the path site's: a key that exists elsewhere is just unknown.
        service, _, _ = world
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(parent_location_key="loc_of_another_site")])
        assert refused.value.codes == ["reference.not_found"]


class TestDeletes:
    def test_deleting_a_location_cascades_to_its_children_and_objects_and_is_audited(self, world):
        service, repo, _ = world
        repo.locations["house"] = make_location(
            "house", name="Haus", location_type_key="greenhouse", geometry=rect(1, 1, 4, 4)
        )
        repo.locations["child"] = make_location(
            "child", name="Reihe", geometry=rect(2, 2, 1, 1), parent_location_key="house"
        )
        repo.objects["inside"] = _object("inside", parent_location_key="house")
        repo.locations["other"] = make_location("other", name="Other", geometry=rect(7, 7, 1, 1))
        result = batch(service, [{"op": "delete", "entity": "location", "key": "house"}], role=TenantRole.LEAD)
        assert sorted(result.deleted) == ["child", "house", "inside"]
        assert set(repo.locations) == {"other"} and repo.objects == {}
        (write,) = repo.applied
        assert {(a["op"], a["key"]) for a in write.audit} == {
            ("delete", "house"),
            ("delete_cascade", "child"),
            ("delete_cascade", "inside"),
        }
        assert next(a for a in write.audit if a["key"] == "house")["summary"] == "Haus"

    def test_a_location_with_active_plants_is_refused_with_the_count_v09(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1))
        repo.active_plants = 3
        with pytest.raises(PlanError) as refused:
            batch(service, [{"op": "delete", "entity": "location", "key": "a"}], role=TenantRole.LEAD)
        assert (refused.value.error_code, refused.value.status_code) == ("location.has_active_plants", 409)
        assert refused.value.details[0]["active_plant_count"] == 3
        assert repo.applied == [] and "a" in repo.locations

    def test_a_location_created_and_deleted_in_one_batch_leaves_no_trace(self, world):
        service, repo, _ = world
        result = batch(
            service,
            [create_bed("t"), {"op": "delete", "entity": "location", "key": "t"}],
            role=TenantRole.LEAD,
        )
        assert result.deleted == [] and result.key_map == {}
        (write,) = repo.applied
        assert write.location_inserts == [] and write.audit == []

    def test_deleting_the_same_key_twice_is_a_reference_error_the_second_time(self, world):
        service, repo, _ = world
        repo.objects["o"] = _object("o")
        ops = [{"op": "delete", "entity": "garden_object", "key": "o"}] * 2
        with pytest.raises(PlanValidationError) as refused:
            batch(service, ops, role=TenantRole.LEAD)
        assert refused.value.details[0]["op_index"] == 1


class TestRevisionConflict:
    def test_the_conflict_names_the_editor_by_display_name_and_the_current_revision(self, world):
        service, repo, _ = world
        repo.editor_name = "Sabine"
        with pytest.raises(PlanRevisionConflictError) as conflict:
            batch(service, [create_bed()], revision=4)
        assert conflict.value.status_code == 409
        detail = conflict.value.details[0]
        assert (detail["code"], detail["current_revision"], detail["changed_by"]) == (
            "plan.revision_conflict",
            5,
            "Sabine",
        )
        assert USER not in str(detail)

    def test_two_writers_with_the_same_revision_the_first_wins_gp_acc_010(self, world):
        service, repo, site = world
        first = batch(service, [create_bed("a", rect(1, 1))], revision=5)
        assert first.plan_revision == 6
        with pytest.raises(PlanRevisionConflictError) as conflict:
            batch(service, [create_bed("b", rect(5, 5))], revision=5)
        assert conflict.value.current_revision == 6
        assert len(repo.locations) == 1  # the second writer's bed is not persisted


class TestThePlanReadModel:
    def test_a_foreign_site_is_a_404(self, world):
        service, _, _ = world
        with pytest.raises(NotFoundError):
            service.get_plan("site_foreign", tenant_key=TENANT)

    def test_slots_come_back_in_plan_coordinates_gp_acc_005(self, world):
        service, repo, _ = world
        repo.locations["bed"] = make_location("bed", geometry=rect(1, 1.5, 2, 1, 90))
        repo.slots = [
            Slot(_key="s0", slot_id="BED_P0", location_key="bed", geometry={"kind": "point", "origin": [0, 0]}),
            Slot(_key="s1", slot_id="BED_P1", location_key="bed", geometry={"kind": "point", "origin": [1.0, 0.5]}),
            Slot(_key="s2", slot_id="BED_P2", location_key="bed"),  # no geometry: unplaced
        ]
        view = service.get_plan(SITE, tenant_key=TENANT)
        by_key = {slot.key: slot for slot in view.slots}
        assert by_key["s0"].plan_geometry == {"kind": "point", "origin": [1.0, 1.5]}  # origin + R(90°)·(0,0)
        assert by_key["s1"].plan_geometry["origin"] == pytest.approx([0.5, 2.5])  # R(90°)·(1.0, 0.5) = (-0.5, 1.0)
        assert by_key["s2"].plan_geometry is None

    def test_the_slot_of_a_bed_without_geometry_is_unplaced(self, world):
        service, repo, _ = world
        repo.locations["bed"] = make_location("bed")
        repo.slots = [
            Slot(_key="s0", slot_id="BED_P0", location_key="bed", geometry={"kind": "point", "origin": [0, 0]})
        ]
        assert service.get_plan(SITE, tenant_key=TENANT).slots[0].plan_geometry is None

    def test_row_and_zone_slots_are_transformed_point_by_point(self, world):
        service, repo, _ = world
        repo.locations["bed"] = make_location("bed", geometry=rect(1, 1, 2, 1))
        repo.slots = [
            Slot(
                _key="row",
                slot_id="BED_R1",
                location_key="bed",
                slot_role="row",
                geometry={"kind": "polyline", "points": [[0, 0.5], [2, 0.5]], "width_m": 0.1},
            ),
            Slot(
                _key="zone",
                slot_id="BED_Z1",
                location_key="bed",
                slot_role="zone",
                geometry={"kind": "polygon", "points": [[0, 0], [1, 0], [1, 1]]},
            ),
        ]
        by_key = {slot.key: slot for slot in service.get_plan(SITE, tenant_key=TENANT).slots}
        assert by_key["row"].plan_geometry == {"kind": "polyline", "points": [[1.0, 1.5], [3.0, 1.5]], "width_m": 0.1}
        assert by_key["zone"].plan_geometry == {"kind": "polygon", "points": [[1.0, 1.0], [2.0, 1.0], [2.0, 2.0]]}

    def test_include_narrows_what_is_returned(self, world):
        service, repo, _ = world
        repo.locations["bed"] = make_location("bed", geometry=rect(1, 1))
        repo.plants = [PlantShortInfo(key="p", instance_id="T-1", species_key="sp", location_key="bed")]
        repo.task_counters = {"bed": TaskCounter(open_task_count=2)}
        everything = service.get_plan(SITE, tenant_key=TENANT)
        assert [p.key for p in everything.plants] == ["p"]
        assert everything.task_counters["bed"].open_task_count == 2
        assert everything.season_states == {"bed": "planted"}
        nothing = service.get_plan(SITE, tenant_key=TENANT, include=frozenset())
        assert nothing.plants == [] and nothing.task_counters == {} and nothing.season_states == {}

    def test_a_bed_without_a_plant_is_empty(self, world):
        service, repo, _ = world
        repo.locations["bed"] = make_location("bed", geometry=rect(1, 1))
        assert service.get_plan(SITE, tenant_key=TENANT).season_states == {"bed": "empty"}

    def test_a_site_without_a_plan_reads_as_revision_zero(self):
        site = Site(_key=SITE, tenant_key=TENANT, name="Garten", type="outdoor")
        sites = FakeSites(site)
        view = GardenPlanService(sites, FakePlanRepo(sites)).get_plan(SITE, tenant_key=TENANT)
        assert view.plan is None and view.plan_revision == 0


class TestNoUserTextInLogs:
    """GP-NFR-060 (SR-025): events carry keys, counts and codes — never a name, label or note."""

    SECRET = "Zaunkönig-Geheimbeet"

    def test_a_successful_batch_logs_no_user_text(self, world):
        service, _, _ = world
        op = create_bed(name=self.SECRET, notes=self.SECRET, description=self.SECRET)
        with capture_logs() as logs:
            batch(service, [op])
        assert [entry["event"] for entry in logs] == ["garden_plan.batch_applied"]
        assert self.SECRET not in repr(logs)
        assert set(logs[0]) >= {"site_key", "revision", "op_count", "duration_ms"}

    def test_a_refused_batch_logs_codes_not_payloads(self, world):
        service, _, _ = world
        with capture_logs() as logs, pytest.raises(PlanValidationError):
            batch(service, [create_bed(geometry=rect(9.5, 9.5), name=self.SECRET)])
        assert [entry["event"] for entry in logs] == ["garden_plan.validation_failed"]
        assert logs[0]["codes"] == ["geometry.outside_parent"]
        assert self.SECRET not in repr(logs)

    def test_a_conflict_is_logged_without_the_editor_name(self, world):
        service, repo, _ = world
        with capture_logs() as logs, pytest.raises(PlanRevisionConflictError):
            batch(service, [create_bed()], revision=1)
        assert [entry["event"] for entry in logs] == ["garden_plan.revision_conflict"]
        assert (repo.editor_name or "") not in repr(logs)


class TestTheAuditList:
    def test_it_is_scoped_to_the_site_anchor(self, world):
        service, repo, _ = world
        repo.audit = [
            PlanAuditEntry(revision=6, op="delete", entity="garden_object", key="go", at="2026-10-17T09:00:00+00:00")
        ]
        assert len(service.list_audit(SITE, tenant_key=TENANT)) == 1
        with pytest.raises(NotFoundError):
            service.list_audit("site_foreign", tenant_key=TENANT)


def _object(key: str, **kwargs) -> GardenObject:
    return GardenObject(
        _key=key,
        site_key=SITE,
        object_type=GardenObjectType.PATH,
        geometry={"kind": "polyline", "points": [[0, 3], [9, 3]], "width_m": 0.6},
        props={},
        **kwargs,
    )


class TestOnlyWhatTheBatchChangedIsWritten:
    """Review F-01 — a whole-model write-back would overwrite what another path changed after the read."""

    def test_a_z_order_change_carries_the_z_order_and_nothing_else(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location(
            "a", geometry=rect(1, 1), bed_status="planned", soil_profile={"soil_texture": "loam"}, pitch_m=0.25
        )
        batch(service, [{"op": "set_z_order", "entity": "location", "key": "a", "z_order": 7}])
        (write,) = repo.applied
        assert write.location_updates == [("a", {"z_order": 7})]

    def test_a_move_carries_geometry_bbox_and_area_but_not_status_soil_or_zone(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location(
            "a", geometry=rect(1, 1), irrigation_zone_key="zone_1", bed_status="retired"
        )
        batch(service, [{"op": "update_geometry", "entity": "location", "key": "a", "geometry": rect(3, 3)}])
        (write,) = repo.applied
        ((_, fields),) = write.location_updates
        assert set(fields) == {"geometry", "bbox"}  # the area did not change: same width and length
        assert "bed_status" not in fields and "irrigation_zone_key" not in fields

    def test_clearing_a_note_is_a_none_so_the_repository_removes_it(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1), notes="alt")
        batch(service, [{"op": "update_fields", "entity": "location", "key": "a", "fields": {"notes": None}}])
        assert repo.applied[0].location_updates == [("a", {"notes": None})]

    def test_an_unchanged_entity_is_not_written_at_all(self, world):
        service, repo, _ = world
        repo.locations["a"] = make_location("a", geometry=rect(1, 1))
        batch(service, [{"op": "set_z_order", "entity": "location", "key": "a", "z_order": 0}])
        assert repo.applied[0].location_updates == []


class TestSlotsStayInsideAReshapedBed:
    """Review F-03 — V-04 on the bed's shape, not on its position."""

    def _bed_with_slots(self, repo):
        repo.locations["bed"] = make_location("bed", geometry=rect(1, 1, 4, 2))
        repo.slots = [
            Slot(_key="near", slot_id="BED_P1", location_key="bed", geometry={"kind": "point", "origin": [0.5, 0.5]}),
            Slot(_key="far", slot_id="BED_P2", location_key="bed", geometry={"kind": "point", "origin": [3.5, 1.5]}),
        ]

    def test_shrinking_the_bed_below_a_slot_is_refused_with_the_slot_key(self, world):
        service, repo, _ = world
        self._bed_with_slots(repo)
        with pytest.raises(PlanValidationError) as refused:
            batch(
                service, [{"op": "update_geometry", "entity": "location", "key": "bed", "geometry": rect(1, 1, 2, 2)}]
            )
        detail = refused.value.details[0]
        assert (detail["code"], detail["key"], detail["op_index"]) == ("slot.outside_bed", "far", 0)
        assert repo.applied == []

    def test_moving_and_turning_the_bed_is_not_a_reshape(self, world):
        service, repo, _ = world
        self._bed_with_slots(repo)
        batch(
            service, [{"op": "update_geometry", "entity": "location", "key": "bed", "geometry": rect(2, 3, 4, 2, 90)}]
        )
        assert len(repo.applied) == 1

    def test_growing_the_bed_keeps_every_slot(self, world):
        service, repo, _ = world
        self._bed_with_slots(repo)
        batch(service, [{"op": "update_geometry", "entity": "location", "key": "bed", "geometry": rect(1, 1, 6, 3)}])
        assert len(repo.applied) == 1

    def test_an_archived_slot_does_not_hold_the_bed(self, world):
        service, repo, _ = world
        self._bed_with_slots(repo)
        repo.slots[1] = repo.slots[1].model_copy(update={"archived_at": "2026-01-01T00:00:00+00:00"})
        batch(service, [{"op": "update_geometry", "entity": "location", "key": "bed", "geometry": rect(1, 1, 2, 2)}])
        assert len(repo.applied) == 1


class TestOffSiteIsAPlacementToCheck:
    def test_switching_off_site_off_for_an_object_outside_the_boundary_is_refused(self, world):
        service, repo, _ = world
        repo.objects["nb"] = GardenObject(
            _key="nb",
            site_key=SITE,
            object_type=GardenObjectType.BUILDING,
            geometry=rect(20, 20, 3, 3),
            props={},
            off_site=True,
        )
        with pytest.raises(PlanValidationError) as refused:
            batch(
                service,
                [{"op": "update_fields", "entity": "garden_object", "key": "nb", "fields": {"off_site": False}}],
            )
        assert refused.value.codes == ["geometry.outside_parent"]
        assert repo.applied == []


class TestAnUnplacedParentEnclosesNothing:
    """Review F-05 — below a location without geometry the garden boundary still applies."""

    def test_a_bed_below_an_unplaced_area_cannot_lie_outside_the_boundary(self, world):
        service, repo, _ = world
        repo.locations["area"] = make_location("area", name="Nutzgarten", location_type_key="greenhouse")
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [create_bed(geometry=rect(30, 30), parent_location_key="area")])
        assert refused.value.codes == ["geometry.outside_parent"]
        batch(service, [create_bed(geometry=rect(2, 2), parent_location_key="area")])
        assert len(repo.applied) == 1

    def test_a_shrinking_boundary_sees_the_bed_below_an_unplaced_area(self, world):
        service, repo, _ = world
        repo.locations["area"] = make_location("area", name="Nutzgarten", location_type_key="greenhouse")
        repo.locations["bed"] = make_location("bed", geometry=rect(7, 7, 2, 2), parent_location_key="area")
        smaller = {"op": "set_boundary", "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}}
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [smaller])
        assert refused.value.details[0]["keys"] == ["location:bed"]

    def test_a_bed_inside_a_placed_parent_is_bounded_by_the_parent_not_the_boundary(self, world):
        service, repo, _ = world
        repo.locations["house"] = make_location("house", location_type_key="greenhouse", geometry=rect(1, 1, 3, 3))
        repo.locations["bed"] = make_location("bed", geometry=rect(2, 2, 1, 1), parent_location_key="house")
        smaller = {"op": "set_boundary", "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}}
        batch(service, [smaller])
        assert len(repo.applied) == 1


class TestALockInsideTheSubtreeHoldsTheDelete:
    def test_a_locked_child_is_not_deleted_with_its_unlocked_parent(self, world):
        service, repo, _ = world
        repo.locations["area"] = make_location("area", location_type_key="greenhouse", geometry=rect(1, 1, 5, 5))
        repo.locations["kept"] = make_location("kept", geometry=rect(2, 2), parent_location_key="area", locked=True)
        with pytest.raises(PlanValidationError) as refused:
            batch(service, [{"op": "delete", "entity": "location", "key": "area"}], role=TenantRole.LEAD)
        assert refused.value.details[0]["code"] == "object.locked" and refused.value.details[0]["key"] == "kept"
        assert set(repo.locations) == {"area", "kept"} and repo.applied == []

    def test_a_locked_object_inside_blocks_it_too(self, world):
        service, repo, _ = world
        repo.locations["area"] = make_location("area", location_type_key="greenhouse", geometry=rect(1, 1, 5, 5))
        repo.objects["go"] = _object("go", parent_location_key="area", locked=True)
        with pytest.raises(PlanValidationError):
            batch(service, [{"op": "delete", "entity": "location", "key": "area"}], role=TenantRole.LEAD)


class TestTheBoundaryKeepsTheNorthAngleItWasNotGiven:
    def test_an_omitted_angle_is_not_written(self, world):
        service, repo, _ = world
        service.set_boundary(
            SITE,
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
            operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY),
            expected_revision=None,
        )
        assert repo.applied[0].north_angle_deg is None
        service.set_boundary(
            SITE,
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
            operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY, north_angle_deg=15.0),
            expected_revision=None,
        )
        assert repo.applied[1].north_angle_deg == 15.0
