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
from app.common.dependencies import (
    get_bed_rotation_service,
    get_garden_resource_service,
    get_rotation_matrix_service,
    get_tenant_service,
)
from app.common.enums import NutrientDemand, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.user import User
from app.domain.services import rotation_matrix_service
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.care_event_service import CareEventService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.rotation_matrix_service import RotationMatrixService
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
    return SimpleNamespace(
        service=service,
        history=history,
        care_repo=care_repo,
        plan=plan,
        sites=sites,
        validator=validator,
        species=species,
        graph=graph,
    )


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
    app.dependency_overrides[get_rotation_matrix_service] = lambda: RotationMatrixService(
        world.sites, world.plan, world.validator
    )
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


class TestReplantOfAFailedPlant:
    """REQ-053 §11.3 "ausgefallen" (W-015, #2888): ``replant_of_plant_key`` on the wire - a hint, never an error."""

    _URL = f"{_BASE}/locations/bed/validate-planting"

    def _died(self, world, cause: str | None, *, tenant: str = TENANT) -> str:
        return world.history.add_plant(
            "bed",
            "cabbage",
            date(2026, 4, 1),
            removed_on=date(2026, 5, 1),
            termination_type="died",
            termination_cause=cause,
            tenant=tenant,
        )

    def test_the_replaced_plant_is_no_previous_crop_and_a_disease_leaves_a_warning(self, client, world) -> None:
        replaced = self._died(world, "disease")

        before = client().post(self._URL, json={"species_key": "cabbage"}).json()
        after = client().post(self._URL, json={"species_key": "cabbage", "replant_of_plant_key": replaced})

        assert [f["code"] for f in before["rotation"]] == ["rotation.pause_not_elapsed"]
        assert before["severity"] == "CRITICAL"
        assert after.status_code == 200
        body = after.json()
        assert body["severity"] == "WARNING"
        finding = body["rotation"][0]
        assert (finding["code"], finding["severity"], finding["termination_cause"], finding["family_name"]) == (
            "rotation.replant_after_biotic_failure",
            "WARNING",
            "disease",
            "Brassicaaceae",
        )
        assert "rotation.pause_not_elapsed" not in [f["code"] for f in body["rotation"]]

    def test_an_unrecorded_cause_is_an_info(self, client, world) -> None:
        replaced = self._died(world, None)

        body = client().post(self._URL, json={"species_key": "cabbage", "replant_of_plant_key": replaced}).json()

        assert body["severity"] == "INFO"
        assert "rotation.replant_cause_unknown" in [f["code"] for f in body["rotation"]]

    def test_another_tenants_plant_and_an_unknown_key_answer_alike_and_change_nothing(self, client, world) -> None:
        self._died(world, "frost")
        foreign = self._died(world, "disease", tenant=OTHER_TENANT)

        named_foreign = client().post(self._URL, json={"species_key": "cabbage", "replant_of_plant_key": foreign})
        named_unknown = client().post(self._URL, json={"species_key": "cabbage", "replant_of_plant_key": "nope"})

        assert named_foreign.status_code == named_unknown.status_code == 200
        assert named_foreign.json() == named_unknown.json()
        assert [f["code"] for f in named_foreign.json()["rotation"]] == ["rotation.pause_not_elapsed"]

    def test_an_empty_key_is_a_422(self, client) -> None:
        response = client().post(self._URL, json={"species_key": "cabbage", "replant_of_plant_key": ""})
        assert response.status_code == 422


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


class TestRotationMatrix:
    """GP-FR-135, GP-API-063 / WP 8.12 (#2655): ``GET /sites/{key}/rotation-matrix`` - a cell is a ``/rotation`` row."""

    URL = f"{_BASE}/sites/site_1/rotation-matrix"

    @staticmethod
    def _fill(client, world) -> None:
        world.history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))
        world.history.add_plant("bed", "bean", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        recorded = client().post(
            f"{_BASE}/locations/bed/history/backfill",
            json={"year": 2023, "season": "spring", "family_key": "brassica", "plan_role": "main_crop"},
        )
        assert recorded.status_code == 201, recorded.text

    def test_a_cell_is_the_rotation_row_of_the_same_bed_and_year(self, client, world) -> None:
        self._fill(client, world)

        matrix = client(TenantRole.VIEWER).get(self.URL).json()
        (row,) = matrix["beds"]
        timeline = client().get(f"{_BASE}/locations/{row['location_key']}/rotation", params={"years": matrix["years"]})
        rotation = {year["year"]: year["plantings"] for year in timeline.json()["timeline"]}
        cells = {cell["year"]: cell["plantings"] for cell in row["cells"]}

        # bean (family pause 6) widens the default look-back to six years
        assert list(cells) == matrix["columns"] == [2021, 2022, 2023, 2024, 2025, 2026]
        assert cells == rotation  # the same expression: every year, every field, in the same order
        # not vacuous: three years carry a crop, and the season and the backfill key made it into the cell
        assert [year for year, plantings in cells.items() if plantings] == [2023, 2024, 2025]
        assert (cells[2023][0]["season"], cells[2023][0]["source"]) == ("spring", "backfill")
        assert cells[2023][0]["care_event_key"] is not None
        assert (cells[2024][0]["family_key"], cells[2024][0]["nutrient_demand"]) == ("solanum", "medium_feeder")

    def test_an_exempt_bed_and_a_bed_switched_off_are_listed_and_marked(self, client, world) -> None:
        world.plan.locations["perennial"] = make_location("perennial", "Hedge", rotation_exempt=True)
        world.plan.locations["off"] = make_location("off", "Off", rotation_enabled=False)
        world.history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        world.history.add_plant("off", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        rows = {row["location_key"]: row for row in client().get(self.URL).json()["beds"]}

        assert (rows["perennial"]["rotation_applicable"], rows["perennial"]["not_applicable_reason"]) == (
            False,
            "rotation.not_applicable.rotation_exempt",
        )
        assert (rows["off"]["rotation_applicable"], rows["off"]["not_applicable_reason"]) == (
            False,
            "rotation.not_applicable.disabled",
        )
        # the control: an ordinary bed of the same site is not marked, and a marked bed still shows what stood there
        assert (rows["bed"]["rotation_applicable"], rows["bed"]["not_applicable_reason"]) == (True, None)
        assert rows["off"]["cells"][-2]["plantings"][0]["family_key"] == "solanum"

    def test_a_planter_is_no_bed_and_stays_out_of_the_matrix(self, client) -> None:
        assert [row["location_key"] for row in client().get(self.URL).json()["beds"]] == ["bed"]

    def test_every_role_may_read(self, client) -> None:
        for role in TenantRole:
            assert client(role).get(self.URL).status_code == 200, role

    def test_a_foreign_site_an_unknown_site_and_the_other_tenants_url_are_404(self, client) -> None:
        foreign = client().get(f"{_BASE}/sites/site_foreign/rotation-matrix")
        unknown = client().get(f"{_BASE}/sites/site_nope/rotation-matrix")
        assert (foreign.status_code, unknown.status_code) == (404, 404)
        # the same body but for the key the caller named: a foreign site is no more visible than an absent one
        assert foreign.text.replace("site_foreign", "K") == unknown.text.replace("site_nope", "K").replace(
            unknown.json().get("error_id", ""), foreign.json().get("error_id", "")
        )
        assert client().get("/api/v1/t/other/sites/site_1/rotation-matrix").status_code == 404

    def test_years_is_bounded_and_defines_the_columns(self, client) -> None:
        assert client().get(self.URL, params={"years": 11}).status_code == 422
        assert client().get(self.URL, params={"years": 0}).status_code == 422
        ten = client().get(self.URL, params={"years": 10}).json()
        assert (ten["years"], len(ten["columns"]), ten["columns"][-1]) == (10, 10, 2026)

    def test_the_default_look_back_follows_the_longest_pause_of_the_beds_shown(self, client, world) -> None:
        assert client().get(self.URL).json()["years"] == 5
        world.history.add_plant("bed", "bean", date(2022, 5, 1), removed_on=date(2022, 8, 1))  # fabace: pause 6
        assert client().get(self.URL).json()["years"] == 6

    def test_the_list_is_paged_in_name_order_and_says_how_many_exist(self, client, world) -> None:
        for key, name in (("b1", "Charlie"), ("b2", "Alpha"), ("b3", "Bravo")):
            world.plan.locations[key] = make_location(key, name)

        pages = [client().get(self.URL, params={"limit": 2, "offset": offset}).json() for offset in (0, 2, 4)]

        # name order across the pages, disjoint and complete: Alpha, Bed, Bravo, Charlie
        assert [[row["name"] for row in page["beds"]] for page in pages] == [["Alpha", "Bed"], ["Bravo", "Charlie"], []]
        assert [(page["total"], page["truncated"], page["offset"]) for page in pages] == [
            (4, False, 0),
            (4, False, 2),
            (4, False, 4),
        ]
        assert client().get(self.URL, params={"limit": 201}).status_code == 422

    def test_a_site_beyond_the_ceiling_is_cut_and_says_so(self, client, world, monkeypatch) -> None:
        monkeypatch.setattr(rotation_matrix_service, "MAX_ROTATION_MATRIX_BEDS", 2)
        for key, name in (("b1", "Charlie"), ("b2", "Alpha"), ("b3", "Bravo")):
            world.plan.locations[key] = make_location(key, name)

        body = client().get(self.URL, params={"limit": 50}).json()

        assert (body["total"], body["truncated"], len(body["beds"])) == (2, True, 2)
        # the control: with the ceiling back at 500 the same site is whole
        monkeypatch.undo()
        whole = client().get(self.URL, params={"limit": 50}).json()
        assert (whole["total"], whole["truncated"]) == (4, False)


class TestSuccessionRecommendation:
    """GP-FR-133, GP-API-064 / WP 8.14 (#2657): ``GET /locations/{key}/succession-recommendation`` - the next step."""

    URL = f"{_BASE}/locations/bed/succession-recommendation"

    @pytest.fixture
    def cycle(self, world):
        """A catalogue with one species per feeder level, edges from Solanaceae, and a heavy feeder in 2025."""
        world.species.by_key.update(
            {
                "tomato": make_species("tomato", "solanum", nutrient_demand=NutrientDemand.HEAVY_FEEDER),
                "cabbage": make_species("cabbage", "brassica", nutrient_demand=NutrientDemand.MEDIUM_FEEDER),
                "kale": make_species("kale", "brassica"),  # no stored level: must never appear
                "bean": make_species("bean", "fabace", nutrient_demand=NutrientDemand.LIGHT_FEEDER),
                "clover": make_species("clover", "fabace", green_manure_suitable=True),
                "secret_cabbage": make_species(
                    "secret_cabbage", "brassica", tenant=OTHER_TENANT, nutrient_demand=NutrientDemand.MEDIUM_FEEDER
                ),
            }
        )
        world.graph.successors["solanum"] = [("fabace", 0.6, "nitrogen_fixation"), ("brassica", 0.8, "pest_break")]
        world.history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        return world

    def get(self, client, role=TenantRole.VIEWER) -> dict:
        response = client(role).get(self.URL)
        assert response.status_code == 200, response.text
        return response.json()

    def test_after_a_heavy_feeder_comes_a_medium_feeder_and_only_species_that_state_it(self, client, cycle) -> None:
        body = self.get(client)

        assert (body["status"], body["target"]) == ("ok", "medium_feeder")
        assert body["previous"] == {
            "year": 2025,
            "step": "main_crop",
            "nutrient_demand": "heavy_feeder",
            "family_keys": ["solanum"],
        }
        (family,) = body["families"]  # fabace has only a light feeder and a green manure: not this step
        assert (family["family_key"], family["benefit_score"], family["benefit_reason"]) == (
            "brassica",
            0.8,
            "pest_break",
        )
        # the species with a stored level is listed, the one without is not, a foreign tenant's never is
        assert [species["species_key"] for species in family["species"]] == ["cabbage"]
        assert family["species"][0]["nutrient_demand"] == "medium_feeder"
        assert body["fallow_option"] is False

    def test_after_a_medium_feeder_comes_a_light_feeder(self, client, cycle) -> None:
        cycle.species.by_key["tomato"] = make_species("tomato", "solanum", nutrient_demand=NutrientDemand.MEDIUM_FEEDER)

        body = self.get(client)

        assert body["target"] == "light_feeder"
        assert [(f["family_key"], [s["species_key"] for s in f["species"]]) for f in body["families"]] == [
            ("fabace", ["bean"])
        ]

    def test_after_a_light_feeder_comes_green_manure_or_a_fallow_year(self, client, cycle) -> None:
        cycle.species.by_key["tomato"] = make_species("tomato", "solanum", nutrient_demand=NutrientDemand.LIGHT_FEEDER)

        body = self.get(client)

        assert body["target"] == "restoring"
        assert body["fallow_option"] is True
        assert [(f["family_key"], [s["species_key"] for s in f["species"]]) for f in body["families"]] == [
            ("fabace", ["clover"])
        ]

    def test_after_a_green_manure_the_cycle_starts_again_with_a_heavy_feeder(self, client, world) -> None:
        world.species.by_key["clover"] = make_species("clover", "fabace", green_manure_suitable=True)
        world.species.by_key["tomato"] = make_species("tomato", "solanum", nutrient_demand=NutrientDemand.HEAVY_FEEDER)
        world.graph.successors["fabace"] = [("solanum", 0.7, "soil_structure")]
        world.history.add_plant(
            "bed", "clover", date(2025, 8, 1), removed_on=date(2025, 11, 1), plan_role="green_manure"
        )

        body = self.get(client)

        assert (body["target"], body["previous"]["step"]) == ("heavy_feeder", "restoring")
        assert [s["species_key"] for f in body["families"] for s in f["species"]] == ["tomato"]

    def test_a_previous_crop_without_a_stated_level_gives_no_recommendation_instead_of_a_default(
        self, client, world
    ) -> None:
        world.species.by_key["ghost"] = make_species("ghost", "ghostfam")  # family not in the catalogue
        world.history.add_plant("bed", "ghost", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        body = self.get(client)

        assert (body["status"], body["target"], body["families"]) == ("demand_unknown", None, [])

    def test_a_bed_without_history_and_a_family_without_edges_say_why_the_list_is_empty(self, client, world) -> None:
        assert self.get(client)["status"] == "no_history"
        world.species.by_key["tomato"] = make_species("tomato", "solanum", nutrient_demand=NutrientDemand.HEAVY_FEEDER)
        world.history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        assert self.get(client)["status"] == "no_successor_data"

    def test_a_family_that_still_keeps_its_pause_in_this_bed_is_held_back_not_offered(self, client, cycle) -> None:
        cycle.history.add_plant("bed", "cabbage", date(2024, 5, 1), removed_on=date(2024, 9, 1))  # brassica: pause 4

        body = self.get(client)

        assert body["families"] == []
        assert body["status"] == "no_matching_species"
        assert body["held_back"] == [
            {"family_key": "brassica", "family_name": "Brassicaaceae", "last_year": 2024, "pause_years": 4}
        ]

    def test_a_species_pause_override_holds_back_what_the_family_pause_would_allow(self, client, cycle) -> None:
        # brassica keeps 4 years; cabbage stood in 2023 (3 years ago): the family alone would be free again ...
        cycle.history.add_plant("bed", "cabbage", date(2022, 5, 1), removed_on=date(2022, 9, 1))
        assert [f["family_key"] for f in self.get(client)["families"]] == ["brassica"]
        # ... but a species that states a longer pause of its own is left out, as the planting hint would warn
        cycle.species.by_key["cabbage"] = make_species(
            "cabbage", "brassica", nutrient_demand=NutrientDemand.MEDIUM_FEEDER, rotation_pause_years=6
        )
        body = self.get(client)
        assert body["families"] == []
        assert body["held_back"] == [
            {"family_key": "brassica", "family_name": "Brassicaaceae", "last_year": 2022, "pause_years": 6}
        ]

    def test_after_a_light_feeder_a_fallow_year_is_offered_even_without_any_edge_data(self, client, world) -> None:
        world.species.by_key["bean"] = make_species("bean", "fabace", nutrient_demand=NutrientDemand.LIGHT_FEEDER)
        world.history.add_plant("bed", "bean", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        body = self.get(client)

        assert (body["status"], body["target"], body["fallow_option"]) == ("no_successor_data", "restoring", True)

    def test_after_a_green_manure_the_successors_of_the_last_crop_are_the_candidates(self, client, world) -> None:
        world.species.by_key["tomato"] = make_species("tomato", "solanum", nutrient_demand=NutrientDemand.HEAVY_FEEDER)
        world.species.by_key["clover"] = make_species("clover", "fabace", green_manure_suitable=True)
        world.species.by_key["pumpkin"] = make_species(
            "pumpkin", "cucurbit", nutrient_demand=NutrientDemand.HEAVY_FEEDER
        )
        # edges exist for the crop family only, none for the cover family
        world.graph.successors["solanum"] = [("cucurbit", 0.7, "soil_structure")]
        world.history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))
        world.history.add_plant(
            "bed", "clover", date(2025, 8, 1), removed_on=date(2025, 11, 1), plan_role="green_manure"
        )

        body = self.get(client)

        assert (body["target"], body["previous"]["step"]) == ("heavy_feeder", "restoring")
        assert [s["species_key"] for f in body["families"] for s in f["species"]] == ["pumpkin"]

    def test_the_species_common_name_follows_the_language_map_not_the_list_order(self, client, cycle) -> None:
        """#2902: species.yaml lists the English name first; the planner shows the canonical German one."""
        cycle.species.by_key["cabbage"] = make_species(
            "cabbage",
            "brassica",
            nutrient_demand=NutrientDemand.MEDIUM_FEEDER,
            common_names=["Cabbage", "Weißkohl"],
            common_names_i18n={"en": ["Cabbage"], "de": ["Weißkohl"]},
        )
        assert self.get(client)["families"][0]["species"][0]["common_name"] == "Weißkohl"

        # a species without a language map (tenant-created, CSV import) keeps its first listed name ...
        cycle.species.by_key["cabbage"] = make_species(
            "cabbage", "brassica", nutrient_demand=NutrientDemand.MEDIUM_FEEDER, common_names=["Mein Kohl", "Kohl"]
        )
        assert self.get(client)["families"][0]["species"][0]["common_name"] == "Mein Kohl"

        # ... and one whose map has no German name shows none (the scientific name has its own field)
        cycle.species.by_key["cabbage"] = make_species(
            "cabbage",
            "brassica",
            nutrient_demand=NutrientDemand.MEDIUM_FEEDER,
            common_names=["Cabbage"],
            common_names_i18n={"en": ["Cabbage"]},
        )
        species = self.get(client)["families"][0]["species"][0]
        assert species["common_name"] is None
        assert species["scientific_name"]

    def test_a_species_the_tenant_may_read_through_a_grant_is_listed(self, client, cycle) -> None:
        assert "secret_cabbage" not in [s["species_key"] for f in self.get(client)["families"] for s in f["species"]]
        cycle.species.grants.add(("secret_cabbage", TENANT))
        listed = [s["species_key"] for f in self.get(client)["families"] for s in f["species"]]
        assert listed == ["cabbage", "secret_cabbage"]

    def test_a_bed_the_rotation_check_is_off_for_gets_no_recommendation(self, client, world) -> None:
        world.plan.locations["bed"] = make_location("bed", rotation_exempt=True)
        body = self.get(client)
        assert (body["rotation_applicable"], body["status"], body["families"]) == (False, "not_applicable", [])

    def test_every_role_may_read_and_a_foreign_bed_is_a_404(self, client, cycle) -> None:
        for role in TenantRole:
            assert client(role).get(self.URL).status_code == 200, role
        assert client().get(f"{_BASE}/locations/alien/succession-recommendation").status_code == 404
        assert client().get("/api/v1/t/other/locations/bed/succession-recommendation").status_code == 404
