"""REQ-053 WP 3.2 — slot reservation, planting states, bed clearing and quick planting through the deployed app.

``app.main`` with the real services, the real tenant gate and the in-memory doubles of
``tests/support/planting_reservation_fakes.py``. The unit tier shows what the services decide; this tier shows how
a decision reads on the wire: the status, the dotted code, the 409 body of V-08, that a body cannot carry what the
server owns — and, per route, that **another tenant's resource answers 404** (GP-NFR-050: the cross-tenant
negative test of every route) with a body that names nothing about it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import (
    get_planting_reservation_service,
    get_planting_run_service,
    get_tenant_service,
)
from app.common.enums import PlantingRunStatus, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.slot_reservation_engine import ActivePlant, Reservation
from app.domain.models.planting_reservation import PlantingRow
from app.domain.models.planting_run import PlantingRunEntry
from app.domain.models.site import Slot
from app.domain.models.user import User
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT
from tests.support.planting_reservation_fakes import build_world

_OWN = "/api/v1/t/own"
_OTHER = "/api/v1/t/other"
D = date


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
    world = build_world()
    world.plan.slots = [
        Slot(_key="s1", slot_id="BED3_001", location_key="bed"),
        Slot(_key="s2", slot_id="BED3_002", location_key="bed"),
        Slot(_key="s_other", slot_id="NOGEO_001", location_key="bed_nogeo"),
    ]
    return world


@pytest.fixture
def client(world) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_planting_run_service] = lambda: world.service
    app.dependency_overrides[get_planting_reservation_service] = lambda: world.reservations
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def run_body(**overrides) -> dict:
    return {
        "name": "Tomatoes 2026",
        "run_type": "monoculture",
        "location_key": "bed",
        "planned_start_date": "2026-05-15",
        "planned_until": "2026-09-30",
        "entries": [
            {
                "species_key": "sp_tomato",
                "quantity": 6,
                "id_prefix": "TOM",
                "spacing_cm": 60,
                "row_spacing_cm": 80,
                "layout_strategy": "rows",
            }
        ],
        **overrides,
    }


def created_run(client, **overrides) -> dict:
    response = client().post(f"{_OWN}/planting-runs", json=run_body(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def plan_run_with_entry(world, run_key: str = "run_b") -> str:
    """A stored planned run on ``bed`` with one entry, for the routes that act on an existing run."""
    from app.common.enums import PlantingRunType
    from app.domain.models.planting_run import PlantingRun, PlantingRunEntry

    run = PlantingRun(
        _key=run_key,
        tenant_key=TENANT,
        name="Lettuce",
        run_type=PlantingRunType.MONOCULTURE,
        status=PlantingRunStatus.PLANNED,
        location_key="bed",
        planned_start_date=D(2026, 10, 5),
    )
    world.runs.runs[run_key] = run
    world.runs.entries["e_b"] = PlantingRunEntry(
        _key="e_b", run_key=run_key, tenant_key=TENANT, species_key="sp_tomato", quantity=2, id_prefix="LET"
    )
    return "e_b"


class TestCreateRun:
    def test_a_bed_with_geometry_gets_its_slots_and_the_response_carries_the_window(self, client, world) -> None:
        body = created_run(client)

        assert body["planned_from"] == "2026-05-15" and body["planned_until"] == "2026-09-30"
        assert body["plan_role"] == "main_crop"
        assert len(world.repo.reservations) == 6
        assert [r.sequence for r in world.repo.reservations] == [1, 2, 3, 4, 5, 6]

    def test_the_new_run_fields_are_stored(self, client, world) -> None:
        body = created_run(
            client,
            source="plan_editor",
            reserved_area_m2=3.8,
            rotation_override_reason="no other bed free",
            entries=None,
        )

        assert (body["source"], body["reserved_area_m2"], body["rotation_override_reason"]) == (
            "plan_editor",
            3.8,
            "no other bed free",
        )

    @pytest.mark.parametrize(
        "overrides",
        [
            {"plan_role": "fallow"},
            {"source": "carrier_pigeon"},
            {"planned_from": "2026-06-01", "planned_until": "2026-05-01"},
            {"reserved_area_m2": 0},
        ],
        ids=["fallow", "source outside the allowlist", "window reversed", "zero area"],
    )
    def test_a_malformed_reservation_field_is_422(self, client, world, overrides) -> None:
        response = client().post(f"{_OWN}/planting-runs", json=run_body(**overrides))

        assert response.status_code == 422
        assert world.runs.runs == {}

    def test_a_bed_of_another_tenant_is_404(self, client, world) -> None:
        response = client().post(f"{_OWN}/planting-runs", json=run_body(location_key="loc_foreign"))

        assert response.status_code == 404
        assert world.runs.runs == {} and world.repo.reservations == []


class TestPlanSlots:
    def test_a_follow_up_crop_after_the_window_is_200(self, client, world) -> None:
        entry = plan_run_with_entry(world)
        world.repo.reservations.append(
            Reservation("s1", "run_a", "e_a", "sp", 1, D(2026, 5, 15), D(2026, 9, 30), "planned")
        )

        response = client().post(
            f"{_OWN}/planting-runs/run_b/plan-slots", json={"entry_key": entry, "slot_keys": ["s1", "s2"]}
        )

        assert response.status_code == 200, response.text
        assert response.json()["slots"] == [
            {"slot_key": "s1", "sequence": 1},
            {"slot_key": "s2", "sequence": 2},
        ]
        assert response.json()["planned_from"] == "2026-10-05"

    def test_an_overlap_is_409_with_the_published_body(self, client, world) -> None:
        """GP-ACC-021 / GP-ACC-039."""
        entry = plan_run_with_entry(world)
        world.runs.runs["run_b"].planned_start_date = D(2026, 8, 1)
        world.repo.reservations.append(
            Reservation("s1", "run_a", "e_a", "sp", 1, D(2026, 5, 15), D(2026, 9, 30), "planned")
        )

        response = client().post(
            f"{_OWN}/planting-runs/run_b/plan-slots", json={"entry_key": entry, "slot_keys": ["s1"]}
        )

        assert response.status_code == 409
        detail = response.json()["details"][0]
        assert detail["code"] == "slot.already_planned"
        assert (detail["conflicting_run_key"], detail["overlap_from"], detail["overlap_until"]) == (
            "run_a",
            "2026-08-01",
            "2026-09-30",
        )

    def test_an_active_plant_is_409(self, client, world) -> None:
        entry = plan_run_with_entry(world)
        world.repo.plants.append(ActivePlant("s1", "pi_1", "run_a", D(2026, 12, 31)))

        response = client().post(
            f"{_OWN}/planting-runs/run_b/plan-slots", json={"entry_key": entry, "slot_keys": ["s1"]}
        )

        assert response.status_code == 409

    def test_a_slot_of_another_bed_is_422_and_reads_like_a_missing_one(self, client, world) -> None:
        entry = plan_run_with_entry(world)
        bodies = []
        for key in ("s_other", "ghost"):
            response = client().post(
                f"{_OWN}/planting-runs/run_b/plan-slots", json={"entry_key": entry, "slot_keys": [key]}
            )
            assert response.status_code == 422
            bodies.append(response.json()["details"])

        assert bodies[0] == bodies[1]

    @pytest.mark.parametrize("entry_key", ["e_a", "ghost"])
    def test_an_entry_that_is_not_the_runs_is_422_reference_not_found(self, client, world, entry_key) -> None:
        plan_run_with_entry(world)
        world.runs.entries["e_a"] = PlantingRunEntry(
            _key="e_a", run_key="run_a", tenant_key=TENANT, species_key="sp_tomato", quantity=1, id_prefix="TOM"
        )

        response = client().post(
            f"{_OWN}/planting-runs/run_b/plan-slots", json={"entry_key": entry_key, "slot_keys": ["s1"]}
        )

        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "reference.not_found"

    def test_the_body_is_checked(self, client, world) -> None:
        plan_run_with_entry(world)
        response = client().post(f"{_OWN}/planting-runs/run_b/plan-slots", json={"slot_keys": ["s1"]})
        assert response.status_code == 422

    def test_a_viewer_gets_403(self, client, world) -> None:
        entry = plan_run_with_entry(world)
        response = client(TenantRole.VIEWER).post(
            f"{_OWN}/planting-runs/run_b/plan-slots", json={"entry_key": entry, "slot_keys": ["s1"]}
        )
        assert response.status_code == 403
        assert world.repo.reservation_writes == []

    def test_another_tenants_run_is_404(self, client, world) -> None:
        entry = plan_run_with_entry(world)

        response = client().post(
            f"{_OTHER}/planting-runs/run_b/plan-slots", json={"entry_key": entry, "slot_keys": ["s1"]}
        )

        assert response.status_code == 404
        assert world.repo.reservation_writes == []


class TestReleasePlanSlot:
    def test_a_grower_releases_a_planned_runs_slot(self, client, world) -> None:
        plan_run_with_entry(world)
        world.repo.reservations.append(Reservation("s1", "run_b", "e_b", "sp", 1, D(2026, 10, 5), None, "planned"))

        response = client().delete(f"{_OWN}/planting-runs/run_b/plan-slots/s1")

        assert response.status_code == 204
        assert world.repo.reservations == []

    def test_a_started_runs_slot_needs_the_lead(self, client, world) -> None:
        plan_run_with_entry(world)
        world.runs.runs["run_b"].status = PlantingRunStatus.ACTIVE
        world.repo.reservations.append(Reservation("s1", "run_b", "e_b", "sp", 1, D(2026, 10, 5), None, "active"))

        assert client().delete(f"{_OWN}/planting-runs/run_b/plan-slots/s1").status_code == 403
        assert client(TenantRole.LEAD).delete(f"{_OWN}/planting-runs/run_b/plan-slots/s1").status_code == 204

    def test_a_reservation_that_does_not_exist_is_404(self, client, world) -> None:
        plan_run_with_entry(world)
        assert client().delete(f"{_OWN}/planting-runs/run_b/plan-slots/s1").status_code == 404

    def test_another_tenants_run_is_404_and_nothing_is_released(self, client, world) -> None:
        plan_run_with_entry(world)
        world.repo.reservations.append(Reservation("s1", "run_b", "e_b", "sp", 1, D(2026, 10, 5), None, "planned"))

        response = client(TenantRole.LEAD).delete(f"{_OTHER}/planting-runs/run_b/plan-slots/s1")

        assert response.status_code == 404
        assert len(world.repo.reservations) == 1


class TestCreatePlants:
    def test_the_body_is_optional_and_the_plants_stand_on_the_planned_slots(self, client, world) -> None:
        run = created_run(client, entries=[{"species_key": "sp_tomato", "quantity": 2, "id_prefix": "TOM"}])
        entry = next(iter(world.runs.entries.values()))
        world.repo.reservations = [
            Reservation("s2", run["key"], entry.key, "sp_tomato", 1, D(2026, 5, 15), None),
            Reservation("s1", run["key"], entry.key, "sp_tomato", 2, D(2026, 5, 15), None),
        ]

        response = client().post(f"{_OWN}/planting-runs/{run['key']}/create-plants")

        assert response.status_code == 201, response.text
        assert response.json()["assigned_slots"] == ["s2", "s1"]

    def test_assign_to_slots_false_and_planted_on_travel_in_the_body(self, client, world) -> None:
        run = created_run(client, entries=[{"species_key": "sp_tomato", "quantity": 1, "id_prefix": "TOM"}])

        response = client().post(
            f"{_OWN}/planting-runs/{run['key']}/create-plants",
            json={"assign_to_slots": False, "planted_on": "2026-05-20"},
        )

        assert response.status_code == 201
        assert response.json()["assigned_slots"] == []
        assert world.plants.created[0].planted_on == D(2026, 5, 20)

    def test_another_tenants_run_is_404(self, client, world) -> None:
        run = created_run(client, entries=[{"species_key": "sp_tomato", "quantity": 1, "id_prefix": "TOM"}])
        assert client().post(f"{_OTHER}/planting-runs/{run['key']}/create-plants").status_code == 404
        assert world.plants.created == []


class TestPlantings:
    def rows(self, world) -> None:
        world.repo.rows = [
            PlantingRow(
                state="planned", slot_key="s1", slot_id="BED3_001", species_key="sp", planned_from=D(2026, 10, 5)
            ),
            PlantingRow(state="active", slot_key="s2", slot_id="BED3_002", species_key="sp", planted_on=D(2026, 5, 1)),
        ]

    def test_it_lists_by_state(self, client, world) -> None:
        self.rows(world)

        everything = client().get(f"{_OWN}/locations/bed/plantings")
        planned = client().get(f"{_OWN}/locations/bed/plantings", params={"state": "planned"})

        assert [r["state"] for r in everything.json()] == ["planned", "active"]
        assert [r["slot_id"] for r in planned.json()] == ["BED3_001"]
        assert planned.json()[0]["planned_from"] == "2026-10-05"

    def test_a_viewer_may_read(self, client, world) -> None:
        self.rows(world)
        assert client(TenantRole.VIEWER).get(f"{_OWN}/locations/bed/plantings").status_code == 200

    def test_an_unknown_state_is_422(self, client, world) -> None:
        response = client().get(f"{_OWN}/locations/bed/plantings", params={"state": "sown"})
        assert response.status_code == 422
        assert response.json()["details"][0]["code"] == "plantings.unknown_state"

    def test_the_window_is_bounded(self, client, world) -> None:
        self.rows(world)
        assert len(client().get(f"{_OWN}/locations/bed/plantings", params={"limit": 1}).json()) == 1
        assert client().get(f"{_OWN}/locations/bed/plantings", params={"limit": 100000}).status_code == 422

    def test_another_tenants_bed_is_404(self, client, world) -> None:
        self.rows(world)
        assert client().get(f"{_OTHER}/locations/bed/plantings").status_code == 404
        assert client().get(f"{_OWN}/locations/loc_foreign/plantings").status_code == 404


class TestClear:
    def test_it_clears_and_reports_the_counts(self, client, world) -> None:
        from app.domain.models.planting_reservation import ClearBedOutcome

        world.repo.clear_outcome = ClearBedOutcome(
            plants_removed=12, runs_completed=2, slots_archived=12, slots_released=0, care_event_key="ce_9"
        )

        response = client().post(f"{_OWN}/locations/bed/clear", json={"termination_type": "senesced"})

        assert response.status_code == 200, response.text
        assert response.json() == {
            "plants_removed": 12,
            "runs_completed": 2,
            "slots_archived": 12,
            "slots_released": 0,
            "care_event_key": "ce_9",
        }
        assert world.repo.clear_writes[0].event.category == "clearing"

    @pytest.mark.parametrize(
        "body",
        [{}, {"termination_type": "evaporated"}, {"termination_type": "died", "harvested_batch": {}}],
        ids=["missing", "unknown", "unknown field"],
    )
    def test_a_bad_body_is_422(self, client, world, body) -> None:
        assert client().post(f"{_OWN}/locations/bed/clear", json=body).status_code == 422
        assert world.repo.clear_writes == []

    def test_a_viewer_gets_403(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(f"{_OWN}/locations/bed/clear", json={"termination_type": "died"})
        assert response.status_code == 403
        assert world.repo.clear_writes == []

    def test_another_tenants_bed_is_404_and_nothing_is_written(self, client, world) -> None:
        assert client().post(f"{_OTHER}/locations/bed/clear", json={"termination_type": "died"}).status_code == 404
        assert (
            client().post(f"{_OWN}/locations/loc_foreign/clear", json={"termination_type": "died"}).status_code == 404
        )
        assert world.repo.clear_writes == []


class TestQuickPlanting:
    def test_it_creates_run_slots_and_plants_in_one_write(self, client, world) -> None:
        response = client().post(
            f"{_OWN}/locations/bed/quick-planting",
            json={"species_key": "sp_tomato", "quantity": 4, "layout_strategy": "grid", "spacing_cm": 50},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert len(body["plant_keys"]) == 4 and len(body["slot_keys"]) == 4 and body["warnings"] == []
        assert world.repo.quick_writes[0].run.source == "field_mode"

    def test_a_species_the_tenant_may_not_read_is_422_reference_not_found(self, client, world) -> None:
        response = client().post(
            f"{_OWN}/locations/bed/quick-planting", json={"species_key": "sp_foreign", "quantity": 2}
        )

        assert response.status_code == 422
        detail = response.json()["details"][0]
        assert (detail["code"], detail["field"]) == ("reference.not_found", "species_key")
        assert world.repo.quick_writes == []

    def test_without_a_layout_it_still_plants(self, client, world) -> None:
        response = client().post(
            f"{_OWN}/locations/bed/quick-planting", json={"species_key": "sp_tomato", "quantity": 3}
        )
        assert response.status_code == 201
        assert response.json()["slot_keys"] == []

    @pytest.mark.parametrize(
        "body",
        [
            {"species_key": "sp_tomato", "quantity": 501},
            {"species_key": "sp_tomato", "quantity": 0},
            {"species_key": "sp_tomato", "quantity": 2, "layout_strategy": "zone", "spacing_cm": 30},
            {"species_key": "sp_tomato", "quantity": 2, "source": "plan_editor"},
            {"species_key": "sp_tomato", "quantity": 2, "tenant_key": "ten_other"},
            {"quantity": 2},
        ],
        ids=["above 500", "zero", "zone layout", "client-set source", "client-set tenant", "no species"],
    )
    def test_a_bad_body_is_422(self, client, world, body) -> None:
        assert client().post(f"{_OWN}/locations/bed/quick-planting", json=body).status_code == 422
        assert world.repo.quick_writes == []

    def test_a_viewer_gets_403(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(
            f"{_OWN}/locations/bed/quick-planting", json={"species_key": "sp_tomato", "quantity": 1}
        )
        assert response.status_code == 403

    def test_another_tenants_bed_is_404_and_nothing_is_written(self, client, world) -> None:
        body = {"species_key": "sp_tomato", "quantity": 1}
        assert client().post(f"{_OTHER}/locations/bed/quick-planting", json=body).status_code == 404
        assert client().post(f"{_OWN}/locations/loc_foreign/quick-planting", json=body).status_code == 404
        assert world.repo.quick_writes == []
