"""REQ-053 WP 1.8 (#2327) — the garden-plan routes through the deployed app.

``app.main`` with the real ``GardenPlanService``, the real tenant gate (``get_current_tenant`` resolving a
membership from a double) and an in-memory repository: the path a client takes, minus the database. What
the unit tier cannot show is how a refusal *reads on the wire* — the envelope, the status, the dotted code,
``details[0].op_index`` — and that the gates and the rate limit sit on the routes at all.

**The role matrix is exercised twice on purpose:** once through the route gate (a viewer never reaches the
service) and once through the per-operation check (a grower reaches it and is refused for one operation).
A route that opted out of the gate would still pass the second.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from app.common.auth import get_current_user
from app.common.dependencies import get_garden_plan_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
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

_BASE = "/api/v1/t/own"
_PLAN = f"{_BASE}/sites/{SITE}/plan"


class _Tenants:
    """Memberships of one caller: ``own`` is TENANT, ``other`` is OTHER_TENANT; the role is the test's."""

    role = TenantRole.GROWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def repo() -> FakePlanRepo:
    sites = FakeSites(make_site())
    repository = FakePlanRepo(sites)
    repository.locations["bed"] = make_location("bed", geometry=rect(1, 1, 2, 1))
    return repository


@pytest.fixture
def client(repo: FakePlanRepo) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = GardenPlanService(repo._sites, repo)

    def build(role: TenantRole = TenantRole.GROWER, *, raise_server_exceptions: bool = True) -> TestClient:
        _Tenants.role = role
        return TestClient(app, raise_server_exceptions=raise_server_exceptions)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_garden_plan_service] = lambda: service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _create(temp: str = "t1", geometry: dict | None = None) -> dict:
    return {
        "op": "create_location",
        "temp_key": temp,
        "data": {"name": "Beet 6", "location_type_key": "bed", "geometry": geometry or rect(4, 4)},
    }


class TestReadingThePlan:
    def test_the_whole_plan_comes_in_one_response(self, client, repo) -> None:
        repo.plants = []
        response = client(TenantRole.VIEWER).get(_PLAN)

        assert response.status_code == 200
        body = response.json()
        assert body["schema_version"] == "1"
        assert body["site_key"] == SITE and body["plan_revision"] == 5
        assert body["plan"]["boundary"]["kind"] == "rect"
        assert [loc["key"] for loc in body["locations"]] == ["bed"]
        assert body["locations"][0]["area_m2"] == 2.0 and body["locations"][0]["bbox"] == [1.0, 1.0, 3.0, 2.0]

    def test_the_plan_names_its_editor_by_display_name_never_by_key(self, client) -> None:
        body = client(TenantRole.VIEWER).get(_PLAN).json()
        assert body["plan"]["plan_updated_by_name"] == "Sabine"
        assert '"plan_updated_by"' not in json.dumps(body)

    def test_the_task_badges_of_beds_and_garden_objects_are_on_the_plan(self, client, repo) -> None:
        from app.common.enums import GardenObjectType
        from app.domain.models.garden_object import GardenObject
        from app.domain.models.garden_plan import TaskCounter

        repo.objects["go_1"] = GardenObject(
            _key="go_1",
            site_key=SITE,
            object_type=GardenObjectType.COMPOST,
            geometry=rect(8, 8, 1, 1),
            props={"object_type": "compost"},
        )
        repo.task_counters = {"bed": TaskCounter(open_task_count=2, overdue_task_count=1)}
        repo.object_task_counters = {"go_1": TaskCounter(open_task_count=3, overdue_task_count=2)}

        body = client(TenantRole.VIEWER).get(_PLAN).json()

        assert (body["locations"][0]["open_task_count"], body["locations"][0]["overdue_task_count"]) == (2, 1)
        assert (body["garden_objects"][0]["open_task_count"], body["garden_objects"][0]["overdue_task_count"]) == (3, 2)
        assert body["garden_objects"][0]["object_type"] == "compost"  # the object itself is unchanged

    def test_an_unknown_include_is_a_422(self, client) -> None:
        response = client().get(_PLAN, params={"include": "plants,fish"})
        assert response.status_code == 422 and response.json()["details"][0]["field"] == "include"

    def test_include_narrows_the_response(self, client, repo) -> None:
        from app.domain.models.garden_plan import PlantShortInfo

        repo.plants = [PlantShortInfo(key="p", instance_id="T-1", species_key="sp", location_key="bed")]
        full = client().get(_PLAN).json()
        slim = client().get(_PLAN, params={"include": "zones"}).json()
        assert [p["key"] for p in full["plants"]] == ["p"]
        assert slim["plants"] == []

    def test_a_foreign_tenants_site_is_a_404_for_the_read_gp_acc_014(self, client) -> None:
        response = client().get(f"/api/v1/t/other/sites/{SITE}/plan")
        assert response.status_code == 404
        assert response.json()["error_code"] == "ENTITY_NOT_FOUND"


class TestTheBoundary:
    def test_the_first_save_creates_the_plan_gp_acc_001(self, client, repo) -> None:
        repo._sites.sites[SITE].plan = None
        boundary = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}
        response = client().put(f"{_PLAN}/boundary", json={"boundary": boundary, "north_angle_deg": 0})

        assert response.status_code == 200
        assert response.json()["plan_revision"] == 1 and response.json()["total_area_m2"] == 100.0
        assert client().get(_PLAN).json()["plan"]["boundary"] == boundary

    def test_a_boundary_point_past_1000_m_is_a_422_and_1000_m_is_accepted_gp_acc_056(self, client, repo) -> None:
        repo._sites.sites[SITE].plan = None
        too_far = {"kind": "polygon", "points": [[0, 0], [1000.5, 0], [1000.5, 10], [0, 10]]}
        refused = client().put(f"{_PLAN}/boundary", json={"boundary": too_far, "north_angle_deg": 0})
        assert refused.status_code == 422, refused.text
        body = refused.json()
        assert body["error_code"] == "VALIDATION_ERROR"
        offending = [detail for detail in body["details"] if detail["code"] == "geometry.invalid"]
        assert offending, body
        assert offending[0]["point_index"] == 1  # the first vertex past 1 000 m, not the first vertex
        assert offending[0]["field"] == "body.boundary.polygon.points"
        assert repo._sites.sites[SITE].plan is None

        at_limit = {"kind": "polygon", "points": [[0, 0], [1000.0, 0], [1000.0, 10], [0, 10]]}
        accepted = client().put(f"{_PLAN}/boundary", json={"boundary": at_limit, "north_angle_deg": 0})
        assert accepted.status_code == 200, accepted.text

    def test_a_viewer_is_refused_at_the_gate(self, client, repo) -> None:
        response = client(TenantRole.VIEWER).put(
            f"{_PLAN}/boundary", json={"boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}}
        )
        assert response.status_code == 403 and repo.applied == []

    def test_shrinking_below_an_object_is_a_422_with_the_keys_v19(self, client, repo) -> None:
        repo.locations["far"] = make_location("far", name="Far", geometry=rect(7, 7, 2, 2))
        response = client().put(
            f"{_PLAN}/boundary",
            json={"boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}},
        )
        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert detail["code"] == "boundary.shrinks_below_objects" and detail["keys"] == ["location:far"]

    def test_a_stale_expected_revision_is_a_409(self, client) -> None:
        response = client().put(
            f"{_PLAN}/boundary",
            json={
                "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10},
                "expected_revision": 1,
            },
        )
        assert response.status_code == 409 and response.json()["error_code"] == "plan.revision_conflict"


class TestTheBatchOnTheWire:
    def test_a_batch_answers_with_the_new_revision_and_the_key_map(self, client, repo) -> None:
        response = client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [_create()]})

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["plan_revision"] == 6
        (real,) = body["key_map"].values()
        assert body["derived"][real] == {"area_m2": 2.0, "bbox": [4.0, 4.0, 6.0, 5.0]}

    def test_a_validation_failure_names_the_operation_and_persists_nothing_gp_acc_009(self, client, repo) -> None:
        response = client().post(
            f"{_PLAN}/batch",
            json={"expected_revision": 5, "operations": [_create("a", rect(9.5, 9.5))]},
        )

        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert (detail["code"], detail["op_index"]) == ("geometry.outside_parent", 0)
        assert repo.applied == [] and repo._sites.sites[SITE].plan.plan_revision == 5

    def test_a_revision_conflict_carries_the_current_revision_and_a_display_name_gp_acc_010(self, client) -> None:
        first = client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [_create("a")]})
        second = client().post(
            f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [_create("b", rect(1, 5))]}
        )

        assert first.status_code == 200 and first.json()["plan_revision"] == 6
        assert second.status_code == 409
        body = second.json()
        assert body["error_code"] == "plan.revision_conflict"
        detail = body["details"][0]
        assert (detail["current_revision"], detail["changed_by"]) == (6, "Sabine")
        assert "u_sabine" not in json.dumps(body)

    def test_501_operations_are_a_422_gp_acc_013(self, client) -> None:
        ops = [{"op": "set_z_order", "entity": "location", "key": "bed", "z_order": 1}] * 501
        response = client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": ops})
        assert response.status_code == 422 and response.json()["error_code"] == "batch.too_many_operations"

    def test_props_nested_5000_deep_are_a_422_never_a_500(self, client, repo) -> None:
        """#2542 S-1: the point count walked a raw operation recursively; deep ``props`` ended in a RecursionError."""
        nested: dict = {}
        for _ in range(5000):
            nested = {"inner": nested}
        operation = {
            "op": "create_garden_object",
            "temp_key": "p1",
            "data": {"object_type": "path", "geometry": rect(4, 4), "props": nested},
        }

        response = client(raise_server_exceptions=False).post(
            f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [operation]}
        )

        assert response.status_code == 422, response.text
        body = response.json()
        # Measured: the unknown ``inner`` key of the props is the finding; the walk itself no longer fails.
        assert body["error_code"] == "VALIDATION_ERROR"
        assert [(d["field"], d["code"], d["op_index"]) for d in body["details"]] == [
            ("props.path.inner", "validation.invalid", 0)
        ]
        assert repo.applied == []

    def test_an_empty_operation_list_is_a_422(self, client) -> None:
        assert client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": []}).status_code == 422

    def test_a_negative_revision_is_a_422(self, client) -> None:
        assert (
            client().post(f"{_PLAN}/batch", json={"expected_revision": -1, "operations": [_create()]}).status_code
            == 422
        )

    def test_a_body_over_the_global_json_ceiling_is_refused_before_the_route_gp_acc_060(self, client) -> None:
        # The edge ceiling for a non-multipart body is 1 MiB (app/common/body_limit.py) — stricter than the
        # spec's 2 MB, so the service's own 2 MB check is the second line, not the first.
        filler = {"op": "update_fields", "entity": "location", "key": "bed", "fields": {"notes": "x" * 3000}}
        response = client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [filler] * 400})
        assert response.status_code == 413

    def test_the_eleventh_batch_in_a_minute_is_rate_limited(self, client) -> None:
        c = client()
        for revision in range(5, 15):
            assert (
                c.post(
                    f"{_PLAN}/batch",
                    json={
                        "expected_revision": revision,
                        "operations": [_create(f"t{revision}", rect(0.5 + (revision - 5) * 0.9, 8, 0.5, 0.5))],
                    },
                ).status_code
                == 200
            )
        limited = c.post(f"{_PLAN}/batch", json={"expected_revision": 15, "operations": [_create("late")]})
        assert limited.status_code == 429
        assert "retry-after" in {name.lower() for name in limited.headers}


class TestRolesOnTheWire:
    def test_a_viewer_is_refused_at_the_gate_with_nothing_applied(self, client, repo) -> None:
        response = client(TenantRole.VIEWER).post(
            f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [_create()]}
        )
        assert response.status_code == 403 and repo.applied == []

    def test_a_grower_with_a_delete_is_refused_whole_gp_acc_042(self, client, repo) -> None:
        repo.locations["loc_b03"] = make_location("loc_b03", name="B03", geometry=rect(5, 5))
        ops = [
            {"op": "update_geometry", "entity": "location", "key": "loc_b03", "geometry": rect(6, 6)},
            {"op": "delete", "entity": "location", "key": "bed"},
        ]
        response = client(TenantRole.GROWER).post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": ops})

        assert response.status_code == 403
        body = response.json()
        assert (body["error_code"], body["details"][0]["op_index"]) == ("batch.operation_forbidden", 1)
        assert repo.applied == [] and repo.locations["loc_b03"].geometry.origin == (5.0, 5.0)

    def test_a_lead_may_delete_and_the_audit_lists_it(self, client, repo) -> None:
        response = client(TenantRole.LEAD).post(
            f"{_PLAN}/batch",
            json={"expected_revision": 5, "operations": [{"op": "delete", "entity": "location", "key": "bed"}]},
        )
        assert response.status_code == 200 and response.json()["deleted"] == ["bed"]
        assert [a["op"] for a in repo.applied[0].audit] == ["delete"]


class TestTenantIsolation:
    """GP-ACC-014: tenant B asking for tenant A's site learns nothing — read, write and audit alike."""

    def test_every_route_answers_404_and_no_batch_is_logged(self, client, repo) -> None:
        other = client(TenantRole.LEAD)
        with capture_logs() as logs:
            responses = [
                other.get(f"/api/v1/t/other/sites/{SITE}/plan"),
                other.put(
                    f"/api/v1/t/other/sites/{SITE}/plan/boundary",
                    json={"boundary": {"kind": "rect", "origin": [0, 0], "width_m": 5, "length_m": 5}},
                ),
                other.post(
                    f"/api/v1/t/other/sites/{SITE}/plan/batch",
                    json={"expected_revision": 5, "operations": [_create()]},
                ),
                other.get(f"/api/v1/t/other/sites/{SITE}/plan/audit"),
            ]
        assert [r.status_code for r in responses] == [404, 404, 404, 404]
        assert repo.applied == []
        assert not [entry for entry in logs if entry["event"] == "garden_plan.batch_applied"]

    def test_a_foreign_site_with_garbage_and_oversize_is_still_a_plain_404(self, client) -> None:
        response = client(TenantRole.LEAD).post(
            f"/api/v1/t/other/sites/{SITE}/plan/batch",
            json={"expected_revision": 5, "operations": [{"op": "?"}] * 600},
        )
        assert response.status_code == 404


class TestTheAuditRoute:
    def test_any_member_reads_the_change_log(self, client, repo) -> None:
        from app.domain.models.garden_plan import PlanAuditEntry

        repo.audit = [
            PlanAuditEntry(
                revision=6,
                op="delete",
                entity="garden_object",
                key="go",
                at="2026-10-17T09:00:00Z",
                changed_by_name="Sabine",
            )
        ]
        response = client(TenantRole.VIEWER).get(f"{_PLAN}/audit")
        assert response.status_code == 200
        assert response.json()[0]["changed_by_name"] == "Sabine"
        assert "user_key" not in response.text


class TestSiteConditionsOnThePlan:
    """#2538 (D-1/D-2/D-3): the plan carries the lean site conditions and the batch edits the sun profile."""

    @staticmethod
    def _seed(repo: FakePlanRepo) -> None:
        from app.domain.models.site import SiteConditions, SoilProfile

        repo.locations["bed"] = make_location(
            "bed",
            geometry=rect(1, 1, 2, 1),
            site_conditions=SiteConditions(
                sun_profile={"sun_window": "morning", "direct_sun_hours_summer": 5.5},
                microclimate={"frost_risk": "high", "cold_air_pocket": True},
                wind_exposure="exposed",
            ),
            soil_profile=SoilProfile(drainage="poor", soil_texture="clay", ph=6.4),
        )

    def test_the_plan_carries_the_sun_profile_the_frost_risk_and_the_drainage(self, client, repo) -> None:
        self._seed(repo)

        (bed,) = client(TenantRole.VIEWER).get(_PLAN).json()["locations"]

        assert bed["site_conditions"] == {
            "sun_profile": {"sun_window": "morning", "direct_sun_hours_summer": 5.5},
            "microclimate": {"frost_risk": "high"},
        }
        assert bed["soil_profile"] == {"drainage": "poor"}  # lean: no texture, no pH, no wind, no cold-air pocket

    def test_unknown_values_are_left_out_down_to_the_whole_object(self, client, repo) -> None:
        from app.domain.models.site import SiteConditions, SoilProfile

        repo.locations["bed"] = make_location(
            "bed", geometry=rect(1, 1, 2, 1), site_conditions=SiteConditions(), soil_profile=SoilProfile()
        )
        repo.locations["half"] = make_location(
            "half",
            geometry=rect(5, 5, 1, 1),
            site_conditions=SiteConditions(sun_profile={"foliage_shade_in_summer": True}),
        )

        body = client(TenantRole.VIEWER).get(_PLAN).json()
        located = {loc["key"]: loc for loc in body["locations"]}

        assert "site_conditions" not in located["bed"] and "soil_profile" not in located["bed"]
        assert located["half"]["site_conditions"] == {"sun_profile": {"foliage_shade_in_summer": True}}

    def test_update_fields_merges_the_sun_profile_bumps_the_revision_and_the_plan_shows_it(self, client, repo) -> None:
        self._seed(repo)
        op = {
            "op": "update_fields",
            "entity": "location",
            "key": "bed",
            "fields": {"site_conditions": {"sun_profile": {"foliage_shade_in_summer": True}}},
        }

        response = client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [op]})

        assert response.status_code == 200, response.text
        assert response.json()["plan_revision"] == 6 and response.json()["updated"] == ["bed"]
        stored = repo.locations["bed"].site_conditions
        assert stored is not None and stored.sun_profile.source == "manual"
        assert (stored.microclimate.cold_air_pocket, stored.wind_exposure) == (True, "exposed")  # not sent, kept
        plan = client().get(_PLAN).json()
        assert plan["plan_revision"] == 6
        assert plan["locations"][0]["site_conditions"]["sun_profile"] == {
            "sun_window": "morning",
            "direct_sun_hours_summer": 5.5,
            "foliage_shade_in_summer": True,
        }

    @pytest.mark.parametrize(
        ("site_conditions", "pointer"),
        [
            ({"microclimate": {"frost_risk": "low"}}, "fields.site_conditions.microclimate"),
            ({"wind_exposure": "sheltered"}, "fields.site_conditions.wind_exposure"),
            ({"sun_profile": {"source": "computed"}}, "fields.site_conditions.sun_profile.source"),
            (
                {"sun_profile": {"direct_sun_hours_summer": 25}},
                "fields.site_conditions.sun_profile.direct_sun_hours_summer",
            ),
            (None, "fields.site_conditions"),
        ],
    )
    def test_anything_but_the_sun_profile_is_a_422_with_the_pointer(
        self, client, repo, site_conditions, pointer
    ) -> None:
        self._seed(repo)
        op = {"op": "update_fields", "entity": "location", "key": "bed", "fields": {"site_conditions": site_conditions}}

        response = client().post(f"{_PLAN}/batch", json={"expected_revision": 5, "operations": [op]})

        assert response.status_code == 422, response.text
        detail = response.json()["details"][0]
        assert (detail["field"], detail["code"], detail["op_index"]) == (pointer, "validation.invalid", 0)
        assert repo.applied == [] and repo.locations["bed"].site_conditions.microclimate.frost_risk == "high"


class TestTheContract:
    def test_the_four_operations_are_published_with_their_error_responses(self) -> None:
        from app.main import app

        paths = app.openapi()["paths"]
        base = "/api/v1/t/{tenant_slug}/sites/{key}/plan"
        assert set(paths[base]) == {"get"} and set(paths[f"{base}/boundary"]) == {"put"}
        assert set(paths[f"{base}/batch"]) == {"post"} and set(paths[f"{base}/audit"]) == {"get"}
        assert {"403", "409", "422"} <= set(paths[f"{base}/batch"]["post"]["responses"])
