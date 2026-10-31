"""REQ-053 WP 3.4 (#2394) — rotation hints, the rotation timeline and the history backfill on the wire.

``app.main`` with the real ``BedRotationService``, the real care-event service over the in-memory repository, the
real tenant gate and a recording history. The unit tier shows what the service decides; this tier shows the status
codes, the gate per role, the published codes and that a refusal reaches the wire before anything is written.

Pinned: GP-ACC-028 (the timeline carries family, ``nutrient_demand`` and ``plan_role`` per year), GP-API-025 (hints,
never an error), GP-API-042 (server-stamped backfill, V-11 exception), cross-tenant answers equal to absent ones.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time

from app.common.auth import get_current_user
from app.common.dependencies import get_bed_rotation_service, get_garden_resource_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.user import User
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.care_event_service import CareEventService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.rotation_fakes import (
    FakeFamilies,
    FakeRotationGraph,
    FakeRotationHistory,
    FakeSpecies,
    make_family,
    make_species,
)

_BASE = "/api/v1/t/own"
TODAY = date(2026, 6, 1)


@pytest.fixture(autouse=True)
def _frozen_today():
    with freeze_time("2026-06-01"):
        yield


class _Tenants:
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
def world() -> SimpleNamespace:
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed")
    plan.locations["pot"] = make_location("pot", location_type_key="planter")
    plan.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    species = FakeSpecies(
        make_species("tomato", "solanum"),
        make_species("bean", "fabace"),
        make_species("cabbage", "brassica"),
        make_species("secret", "solanum", tenant=OTHER_TENANT),
    )
    families = FakeFamilies(
        make_family("solanum", pause=4), make_family("fabace", pause=6), make_family("brassica", pause=4)
    )
    care_repo = FakeCareEventRepo()
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    history = FakeRotationHistory(care_repo)
    graph = FakeRotationGraph()
    validator = CropRotationValidator(None, species, graph, site_repo=sites, family_repo=families, history_repo=history)
    service = BedRotationService(sites, plan, graph, species, families, care, validator)
    return SimpleNamespace(service=service, history=history, care_repo=care_repo, plan=plan, sites=sites)


@pytest.fixture
def client(world: SimpleNamespace) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_bed_rotation_service] = lambda: world.service
    app.dependency_overrides[get_garden_resource_service] = lambda: GardenResourceService(
        world.sites, world.plan, FakeObjects(world.plan), GardenPlanService(world.sites, world.plan)
    )
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


class TestValidatePlanting:
    def test_a_violation_is_a_200_with_a_strength_and_a_reason(self, client, world) -> None:
        world.history.add_plant("bed", "cabbage", date(2025, 4, 1), removed_on=date(2025, 9, 1))

        response = client().post(f"{_BASE}/locations/bed/validate-planting", json={"species_key": "cabbage"})

        assert response.status_code == 200
        body = response.json()
        assert body["severity"] == "CRITICAL"
        assert body["rotation_applicable"] is True
        (finding,) = body["rotation"]
        assert (finding["code"], finding["family_key"], finding["years_since"], finding["pause_years"]) == (
            "rotation.pause_not_elapsed",
            "brassica",
            1,
            4,
        )
        assert "1 year(s) ago" in finding["message"]
        assert finding["family_name"] == "Brassicaaceae"

    def test_every_role_may_ask(self, client) -> None:
        for role in (TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD):
            response = client(role).post(f"{_BASE}/locations/bed/validate-planting", json={"species_key": "tomato"})
            assert response.status_code == 200, role

    def test_a_planter_is_reported_as_not_applicable(self, client) -> None:
        body = client().post(f"{_BASE}/locations/pot/validate-planting", json={"species_key": "tomato"}).json()
        assert (body["rotation_applicable"], body["not_applicable_reason"], body["rotation"]) == (
            False,
            "rotation.not_applicable.container",
            [],
        )

    def test_a_foreign_bed_and_an_unknown_bed_answer_alike(self, client) -> None:
        foreign = client().post(f"{_BASE}/locations/alien/validate-planting", json={"species_key": "tomato"})
        unknown = client().post(f"{_BASE}/locations/nope/validate-planting", json={"species_key": "tomato"})
        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["message"].replace("alien", "?") == unknown.json()["message"].replace("nope", "?")

    def test_the_other_tenants_url_cannot_reach_the_bed(self, client) -> None:
        response = client().post("/api/v1/t/other/locations/bed/validate-planting", json={"species_key": "tomato"})
        assert response.status_code == 404

    def test_a_foreign_species_is_a_422_like_an_unknown_one(self, client) -> None:
        foreign = client().post(f"{_BASE}/locations/bed/validate-planting", json={"species_key": "secret"})
        unknown = client().post(f"{_BASE}/locations/bed/validate-planting", json={"species_key": "nope"})
        assert foreign.status_code == unknown.status_code == 422
        assert foreign.json()["details"] == unknown.json()["details"]
        assert foreign.json()["details"][0]["code"] == "reference.not_found"

    def test_the_window_is_bounded_and_unknown_fields_are_refused(self, client) -> None:
        url = f"{_BASE}/locations/bed/validate-planting"
        assert client().post(url, json={"species_key": "tomato", "rotation_window_years": 9}).status_code == 422
        assert client().post(url, json={"species_key": "tomato", "rotation_window_years": 8}).status_code == 200
        assert client().post(url, json={"species_key": "tomato", "tenant_key": OTHER_TENANT}).status_code == 422

    def test_a_foreign_slot_is_a_422_like_an_unknown_one(self, client, world) -> None:
        url = f"{_BASE}/locations/bed/validate-planting"
        foreign = client().post(url, json={"species_key": "tomato", "slot_key": "z1"})
        unknown = client().post(url, json={"species_key": "tomato", "slot_key": "nope"})
        assert foreign.status_code == unknown.status_code == 422
        assert foreign.json()["details"] == unknown.json()["details"]


class TestPerBedSwitchGpAcc055:
    """GP-ACC-055 / GP-FR-137: the rotation check is off for planter/tent/shelf until one bed is switched on."""

    CONTAINERS = ("planter", "tent", "shelf")

    @pytest.fixture
    def containers(self, world) -> None:
        for kind in self.CONTAINERS:
            world.plan.locations[kind] = make_location(kind, location_type_key=kind)
            world.history.add_plant(kind, "tomato", date(2025, 4, 1), removed_on=date(2025, 9, 1))

    @staticmethod
    def hints(client, kind: str) -> dict:
        response = client().post(f"{_BASE}/locations/{kind}/validate-planting", json={"species_key": "tomato"})
        assert response.status_code == 200, response.text
        return response.json()

    def test_switching_one_container_on_gives_only_that_one_the_hint(self, client, world, containers) -> None:
        assert [self.hints(client, kind)["rotation"] for kind in self.CONTAINERS] == [[], [], []]

        patched = client().patch(f"{_BASE}/locations/shelf", json={"rotation_enabled": True})

        assert patched.status_code == 200, patched.text
        assert patched.json()["rotation_enabled"] is True
        shelf = self.hints(client, "shelf")
        assert shelf["rotation_applicable"] is True
        assert [f["code"] for f in shelf["rotation"]] == ["rotation.pause_not_elapsed"]
        for kind in ("planter", "tent"):
            body = self.hints(client, kind)
            assert (body["rotation_applicable"], body["not_applicable_reason"], body["rotation"]) == (
                False,
                "rotation.not_applicable.container",
                [],
            )

    def test_null_returns_the_bed_to_its_type_default(self, client, world, containers) -> None:
        client().patch(f"{_BASE}/locations/tent", json={"rotation_enabled": True})

        cleared = client().patch(f"{_BASE}/locations/tent", json={"rotation_enabled": None})

        assert cleared.status_code == 200, cleared.text
        assert cleared.json()["rotation_enabled"] is None
        assert self.hints(client, "tent")["rotation_applicable"] is False

    def test_an_open_bed_can_be_switched_off(self, client, world) -> None:
        world.history.add_plant("bed", "tomato", date(2025, 4, 1), removed_on=date(2025, 9, 1))

        client().patch(f"{_BASE}/locations/bed", json={"rotation_enabled": False})

        body = self.hints(client, "bed")
        assert (body["rotation_applicable"], body["not_applicable_reason"]) == (
            False,
            "rotation.not_applicable.disabled",
        )

    @pytest.mark.parametrize(
        ("stored", "sent"),
        [
            ({}, {"rotation_exempt": True, "rotation_enabled": True}),
            ({"rotation_exempt": True}, {"rotation_enabled": True}),
            ({"rotation_enabled": True}, {"rotation_exempt": True}),
        ],
        ids=["both in one body", "switch on an exempt bed", "exempt a switched-on bed"],
    )
    def test_exempt_and_switched_on_together_is_422_and_writes_nothing(self, client, world, stored, sent) -> None:
        world.plan.locations["tent"] = make_location("tent", location_type_key="tent", **stored)
        before = world.plan.locations["tent"]

        response = client().patch(f"{_BASE}/locations/tent", json=sent)

        assert response.status_code == 422, response.text
        assert response.json()["error_code"] == "patch.rotation_exempt_and_enabled"
        assert world.plan.locations["tent"] == before

    def test_exempting_a_switched_on_bed_works_when_the_switch_is_cleared_in_the_same_body(self, client, world) -> None:
        world.plan.locations["tent"] = make_location("tent", location_type_key="tent", rotation_enabled=True)

        response = client().patch(f"{_BASE}/locations/tent", json={"rotation_exempt": True, "rotation_enabled": None})

        assert response.status_code == 200, response.text
        assert (response.json()["rotation_exempt"], response.json()["rotation_enabled"]) == (True, None)

    @pytest.mark.parametrize(
        "sent", [{"name": "Renamed"}, {"rotation_exempt": False}], ids=["rotation untouched", "exempt cleared"]
    )
    def test_a_stored_conflicting_pair_does_not_block_a_patch_that_does_not_switch_on(
        self, client, world, sent
    ) -> None:
        """SCR-002: a row written before the guard (or by an import) may hold both; only a PATCH that touches the
        rotation flags is judged by the pair it leaves behind."""
        world.plan.locations["tent"] = make_location(
            "tent", location_type_key="tent", rotation_exempt=True, rotation_enabled=True
        )

        response = client().patch(f"{_BASE}/locations/tent", json=sent)

        assert response.status_code == 200, response.text

    def test_rotation_exempt_cannot_be_null(self, client, world) -> None:
        response = client().patch(f"{_BASE}/locations/bed", json={"rotation_exempt": None})

        assert response.status_code == 422
        assert response.json()["error_code"] == "VALIDATION_ERROR", response.text
        # The null guard is a body-level validator shared by every non-clearable field: it reports ``body`` and
        # names the field in the reason.
        details = response.json()["details"]
        assert [(d["field"], d["code"]) for d in details] == [("body", "value_error")], response.text
        assert "rotation_exempt cannot be null" in details[0]["reason"]
        assert world.plan.locations["bed"].rotation_exempt is False

    def test_a_viewer_cannot_switch(self, client, world, containers) -> None:
        response = client(TenantRole.VIEWER).patch(f"{_BASE}/locations/tent", json={"rotation_enabled": True})

        assert response.status_code == 403
        assert world.plan.locations["tent"].rotation_enabled is None


class TestRotationTimeline:
    def test_carries_family_demand_and_role_per_year_gp_acc_028(self, client, world) -> None:
        world.history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))
        world.history.add_plant("bed", "bean", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        response = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed/rotation", params={"years": 5})

        assert response.status_code == 200
        timeline = {row["year"]: row["plantings"] for row in response.json()["timeline"]}
        assert list(timeline) == [2026, 2025, 2024, 2023, 2022]  # newest first, every year listed
        assert timeline[2024][0]["family_key"] == "solanum"
        assert timeline[2024][0]["nutrient_demand"] == "medium_feeder"
        assert timeline[2024][0]["plan_role"] == "main_crop"
        assert timeline[2025][0]["family_key"] == "fabace"
        assert timeline[2023] == []

    def test_more_than_ten_years_is_a_422(self, client) -> None:
        assert client().get(f"{_BASE}/locations/bed/rotation", params={"years": 11}).status_code == 422
        assert client().get(f"{_BASE}/locations/bed/rotation", params={"years": 10}).status_code == 200

    def test_a_foreign_bed_is_a_404(self, client) -> None:
        assert client().get(f"{_BASE}/locations/alien/rotation").status_code == 404
        assert client().get("/api/v1/t/other/locations/bed/rotation").status_code == 404


class TestBackfill:
    def test_a_grower_records_a_year_and_the_timeline_shows_it(self, client, world) -> None:
        response = client().post(
            f"{_BASE}/locations/bed/history/backfill",
            json={"year": 2024, "season": "spring", "family_key": "solanum", "plan_role": "main_crop"},
        )

        assert response.status_code == 201
        body = response.json()
        assert (body["year"], body["family_key"], body["plan_role"]) == (2024, "solanum", "main_crop")
        assert body["performed_at"].startswith("2024-04-15T12:00:00")
        (event,) = world.care_repo.inserted
        assert (event.category, event.trigger) == ("planting", "backfill")
        timeline = client().get(f"{_BASE}/locations/bed/rotation", params={"years": 5}).json()["timeline"]
        assert {row["year"]: row["plantings"] for row in timeline}[2024][0]["care_event_key"] == body["care_event_key"]

    def test_the_client_cannot_send_the_trigger_or_the_category(self, client, world) -> None:
        url = f"{_BASE}/locations/bed/history/backfill"
        for extra in ({"trigger": "backfill"}, {"category": "planting"}, {"performed_at": "2020-01-01T00:00:00Z"}):
            response = client().post(url, json={"year": 2024, "family_key": "solanum", **extra})
            assert response.status_code == 422, extra
        assert world.care_repo.inserted == []

    def test_a_viewer_is_refused_before_the_service(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(
            f"{_BASE}/locations/bed/history/backfill", json={"year": 2024, "family_key": "solanum"}
        )
        assert response.status_code == 403
        assert world.care_repo.inserted == []

    def test_a_year_outside_the_range_carries_the_published_code(self, client, world) -> None:
        response = client().post(
            f"{_BASE}/locations/bed/history/backfill", json={"year": 1999, "family_key": "solanum"}
        )
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "backfill.year_out_of_range"
        assert world.care_repo.inserted == []

    def test_a_foreign_bed_is_a_404_and_writes_nothing(self, client, world) -> None:
        assert (
            client()
            .post(f"{_BASE}/locations/alien/history/backfill", json={"year": 2024, "family_key": "solanum"})
            .status_code
            == 404
        )
        assert (
            client()
            .post("/api/v1/t/other/locations/bed/history/backfill", json={"year": 2024, "family_key": "solanum"})
            .status_code
            == 404
        )
        assert world.care_repo.inserted == []

    def test_cancelling_takes_the_year_out_of_the_history(self, client, world) -> None:
        key = (
            client()
            .post(f"{_BASE}/locations/bed/history/backfill", json={"year": 2024, "family_key": "solanum"})
            .json()["care_event_key"]
        )

        assert client().delete(f"{_BASE}/locations/bed/history/backfill/{key}").status_code == 204

        assert world.care_repo.events[key].void_reason == "backfill_error"
        timeline = client().get(f"{_BASE}/locations/bed/rotation", params={"years": 5}).json()["timeline"]
        assert all(row["plantings"] == [] for row in timeline)

    def test_cancelling_an_event_of_another_bed_tenant_or_kind_is_a_404(self, client, world) -> None:
        key = (
            client()
            .post(f"{_BASE}/locations/bed/history/backfill", json={"year": 2024, "family_key": "solanum"})
            .json()["care_event_key"]
        )

        assert client().delete(f"{_BASE}/locations/pot/history/backfill/{key}").status_code == 404
        assert (
            client(TenantRole.LEAD).delete(f"/api/v1/t/other/locations/bed/history/backfill/{key}").status_code == 404
        )
        assert client().delete(f"{_BASE}/locations/bed/history/backfill/nope").status_code == 404
        assert world.care_repo.events[key].voided_at is None

    def test_a_viewer_cannot_cancel(self, client, world) -> None:
        key = (
            client()
            .post(f"{_BASE}/locations/bed/history/backfill", json={"year": 2024, "family_key": "solanum"})
            .json()["care_event_key"]
        )
        assert client(TenantRole.VIEWER).delete(f"{_BASE}/locations/bed/history/backfill/{key}").status_code == 403
        assert world.care_repo.events[key].voided_at is None
