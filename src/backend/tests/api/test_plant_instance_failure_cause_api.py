"""API test: the cause class at the termination endpoint and the dialog options (REQ-003 E5/E6, #2888 F-19).

The routes run against the real ``PlantInstanceService`` (only the repositories are doubles), so the request
schema's 422 and the stored record come from the same rule the service applies — the UI is not the gate.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_bed_soil_hazard_service, get_plant_instance_service
from app.common.enums import FailureCauseClass, SoilHazard, TenantRole, TerminationCause
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_instance_service import PlantInstanceService
from tests.support.bed_soil_hazard_fakes import soil_hazard_service
from tests.support.garden_plan_fakes import FakePlanRepo, FakeSites

TENANT_KEY = "t-test-1"
BASE = "/api/v1/t/test-slug/plant-instances"


class _Families:
    def get_by_key(self, key: str) -> BotanicalFamily | None:
        return BotanicalFamily(_key=key, name="Solanaceae") if key == "solanaceae" else None


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug="test-slug", user_key="user-1", role=TenantRole.GROWER)


@pytest.fixture
def world():
    plant = PlantInstance(
        _key="plant-1",
        tenant_key=TENANT_KEY,
        instance_id="P-1",
        species_key="sp-tomato",
        planted_on=date(2026, 4, 1),
        # No phase key: the response's phase label is resolved through the phase catalogue, not under test here.
        current_phase_started_at=datetime(2026, 5, 1, tzinfo=UTC),
    )
    plant_repo = MagicMock()

    def get_or_raise(key: str) -> PlantInstance:
        if key == "plant-1":
            return plant
        if key == "plant-foreign":
            return PlantInstance(
                _key="plant-foreign",
                tenant_key="t-other",
                instance_id="X-1",
                species_key="sp-tomato",
                planted_on=date(2026, 4, 1),
            )
        if key == "plant-foreign-ended":
            return PlantInstance(
                _key="plant-foreign-ended",
                tenant_key="t-other",
                instance_id="X-2",
                species_key="sp-tomato",
                planted_on=date(2026, 4, 1),
                removed_on=date(2026, 6, 1),
                termination_type="died",
                termination_cause="frost",
                failure_cause_class="abiotic",
            )
        raise NotFoundError("PlantInstance", key)

    plant_repo.get_or_raise.side_effect = get_or_raise
    plant_repo.get_by_key.return_value = plant
    plant_repo.update.side_effect = lambda _key, p: p
    phase_repo = MagicMock()
    phase_repo.get_phase_history.return_value = [
        PhaseHistory(
            _key="h-1",
            plant_instance_key="plant-1",
            phase_key="ph-veg",
            phase_name="vegetative",
            entered_at=datetime(2026, 5, 1, tzinfo=UTC),
        )
    ]
    species_repo = MagicMock()
    species_repo.get_by_key.return_value = Species(
        _key="sp-tomato", scientific_name="Solanum lycopersicum", family_key="solanaceae"
    )
    service = PlantInstanceService(
        plant_repo,
        MagicMock(),
        MagicMock(),
        MagicMock(),
        phase_repo=phase_repo,
        task_repo=MagicMock(),
        species_repo=species_repo,
        family_repo=_Families(),
    )
    app = FastAPI()
    app.include_router(plant_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    # #2888 F-20: the remove answer carries the soil-hazard follow-up; the plants here stand in no bed.
    hazards = soil_hazard_service(FakePlanRepo(FakeSites()))
    app.dependency_overrides[get_bed_soil_hazard_service] = lambda: hazards
    app.dependency_overrides[get_current_tenant] = _ctx
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    return TestClient(app), plant_repo


class TestRemove:
    def test_disease_without_a_class_answers_422_and_writes_nothing(self, world) -> None:
        client, plant_repo = world

        resp = client.post(f"{BASE}/plant-1/remove", json={"termination_type": "died", "termination_cause": "disease"})

        assert resp.status_code == 422
        assert "needs a failure_cause_class" in resp.text
        plant_repo.update.assert_not_called()

    def test_an_abiotic_cause_is_stored_with_its_prefill(self, world) -> None:
        client, plant_repo = world

        resp = client.post(f"{BASE}/plant-1/remove", json={"termination_type": "died", "termination_cause": "frost"})

        assert resp.status_code == 200
        assert resp.json()["failure_cause_class"] == "abiotic"
        assert plant_repo.update.call_args.args[1].failure_cause_class is FailureCauseClass.ABIOTIC

    def test_a_soil_borne_loss_with_a_confirmed_pathogen_round_trips(self, world) -> None:
        client, plant_repo = world
        body = {
            "termination_type": "died",
            "termination_cause": "heat",
            "failure_cause_class": "disease_soil",
            "failure_pathogen": "verticillium",
            "failure_pathogen_confirmed": True,
            "failure_pathogen_source": "lab_test",
        }

        resp = client.post(f"{BASE}/plant-1/remove", json=body)

        assert resp.status_code == 200
        out = resp.json()
        assert {k: out[k] for k in body if k.startswith("failure_")} == {
            k: v for k, v in body.items() if k.startswith("failure_")
        }
        assert plant_repo.update.call_args.args[1].failure_pathogen is SoilHazard.VERTICILLIUM

    def test_a_pathogen_outside_the_hazard_list_answers_422(self, world) -> None:
        client, plant_repo = world

        resp = client.post(
            f"{BASE}/plant-1/remove",
            json={
                "termination_type": "died",
                "termination_cause": "disease",
                "failure_cause_class": "disease_soil",
                "failure_pathogen": "fusarium",
            },
        )

        assert resp.status_code == 422
        plant_repo.update.assert_not_called()

    def test_an_empty_body_is_a_plain_removal_without_a_class(self, world) -> None:
        client, _ = world

        resp = client.post(f"{BASE}/plant-1/remove", json={})

        assert resp.status_code == 200
        out = resp.json()
        assert (out["termination_type"], out["failure_cause_class"], out["failure_pathogen"]) == (None, None, None)


class TestTerminationOptions:
    def test_the_options_carry_the_table_resolved_for_the_plant(self, world) -> None:
        client, _ = world

        resp = client.get(f"{BASE}/plant-1/termination-options")

        assert resp.status_code == 200
        body = resp.json()
        assert body["suggested_cause"] is None
        assert body["wilt_prone_family"] is True
        assert [r["termination_cause"] for r in body["rules"]] == [c.value for c in TerminationCause]
        by_cause = {r["termination_cause"]: r for r in body["rules"]}
        assert by_cause["disease"] == {
            "termination_cause": "disease",
            "prefill": None,
            "choices": ["disease_foliar", "disease_soil"],
            "asks_wilt_follow_up": False,
        }
        assert by_cause["unknown"]["asks_wilt_follow_up"] is True  # a tomato is Solanaceae
        assert by_cause["bolting"]["prefill"] == "abiotic"
        assert body["wilt_follow_up_class"] == "disease_soil"
        # #2888 F-20 (review D4): juglone is no pathogen of a loss - entered at the bed by hand only.
        assert body["pathogens"] == [h.value for h in SoilHazard if h is not SoilHazard.JUGLONE]
        assert body["pathogen_classes"] == ["pest_soil", "disease_soil"]

    def test_the_options_path_is_not_captured_by_the_key_route(self, world) -> None:
        client, _ = world
        assert "rules" in client.get(f"{BASE}/plant-1/termination-options").json()


class TestNotTheCallersPlant:
    @pytest.mark.parametrize("key", ["plant-foreign", "plant-missing"])
    def test_a_foreign_and_an_unknown_plant_answer_the_same_404(self, world, key) -> None:
        client, _ = world

        resp = client.get(f"{BASE}/{key}/termination-options")

        assert resp.status_code == 404
        assert "t-other" not in resp.text

    def test_a_foreign_ended_plant_answers_404_not_the_terminal_state_422(self, world) -> None:
        """Ownership is checked before the terminal state: a 422 would tell another tenant the plant has ended."""
        client, plant_repo = world

        foreign = client.post(f"{BASE}/plant-foreign-ended/remove", json={})
        unknown = client.post(f"{BASE}/plant-missing/remove", json={})

        assert (foreign.status_code, unknown.status_code) == (404, 404)
        assert foreign.json()["error_code"] == unknown.json()["error_code"]
        plant_repo.update.assert_not_called()


class TestAnEndedPlant:
    def test_a_second_remove_answers_422_and_keeps_the_first_record(self, world) -> None:
        client, plant_repo = world
        first = {
            "termination_type": "died",
            "termination_cause": "disease",
            "failure_cause_class": "disease_soil",
            "failure_pathogen": "clubroot",
            "failure_pathogen_confirmed": True,
            "failure_pathogen_source": "lab_test",
        }
        assert client.post(f"{BASE}/plant-1/remove", json=first).status_code == 200
        plant_repo.update.reset_mock()

        resp = client.post(f"{BASE}/plant-1/remove", json={})

        assert resp.status_code == 422
        assert resp.json()["error_code"] == "INVALID_STATUS_TRANSITION"
        plant_repo.update.assert_not_called()
