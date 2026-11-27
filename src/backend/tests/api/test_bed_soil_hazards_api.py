"""The soil hazards of a bed through the deployed app (AP-API-012, REQ-054 §5.2, REQ-053 §11.3a Nr. 5, #2888 F-20).

``app.main`` with the real tenant gate (``require_permission`` reads the membership role), the real
``BedSoilHazardService``, ``PlantInstanceService``, ``SiteService`` and ``GardenResourceService``, the real ownership
walk (``resolve_owned_location`` through the site) and the shipped knowledge table. Only persistence is a double
(``tests/support``): the plant store is one dict both services read, so the offer after a loss and its acceptance run
over the plant the remove call stored. The cross-tenant matrix against ArangoDB is
``tests/integration/test_garden_plan_tenant_isolation.py``; the transaction ``test_bed_soil_hazard_repository.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import (
    get_bed_soil_hazard_service,
    get_garden_resource_service,
    get_plant_instance_service,
    get_site_service,
    get_tenant_service,
)
from app.common.enums import IrrigationSystem, PathogenConfirmationSource, SoilHazard, TenantRole
from app.common.exceptions import NotFoundError, StoredDocumentInvalidError
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.models.user import User
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.plant_instance_service import PlantInstanceService
from app.domain.services.site_service import SiteService
from tests.support.bed_soil_hazard_fakes import FakeBedSoilHazardRepo, soil_hazard_service
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)

_BASE = "/api/v1/t/own"
_FOREIGN = "/api/v1/t/other"
ME = "u_sabine"

#: The F-19 body of a confirmed clubroot loss (REQ-003 E5 v2.24).
CONFIRMED_LOSS: dict[str, Any] = {
    "termination_type": "died",
    "termination_cause": "disease",
    "failure_cause_class": "disease_soil",
    "failure_pathogen": "clubroot",
    "failure_pathogen_confirmed": True,
    "failure_pathogen_source": "lab_test",
}
#: The same loss as a suspicion: named, not confirmed, no source.
SUSPECTED_LOSS: dict[str, Any] = {
    **CONFIRMED_LOSS,
    "failure_pathogen_confirmed": False,
    "failure_pathogen_source": None,
}
CLUBROOT_2025 = BedSoilHazard(
    hazard=SoilHazard.CLUBROOT, confirmed_at=date(2025, 6, 1), source=PathogenConfirmationSource.CLEAR_SYMPTOMS
)


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


class _Sites(FakeSites):
    """The fake site reads plus the one ``SiteService.get_location`` makes."""

    def get_location_or_raise(self, key: str):  # type: ignore[no-untyped-def]
        location = self.get_location_by_key(key)
        if location is None:
            raise NotFoundError("Location", key)
        return location


class _PlantStore:
    """One store for both services: the remove call writes the plant the offer is then accepted for."""

    def __init__(self, *plants: PlantInstance) -> None:
        self.rows = {plant.key: plant for plant in plants}

    def get_by_key(self, key: str) -> PlantInstance | None:
        return self.rows.get(key)

    def get_or_raise(self, key: str) -> PlantInstance:
        plant = self.rows.get(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant

    def update(self, key: str, plant: PlantInstance) -> PlantInstance:
        self.rows[key] = plant
        return plant


def _standing(key: str, location_key: str, tenant: str = TENANT) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant,
        instance_id=key.upper(),
        species_key="sp_kohl",
        site_key="site_1",
        location_key=location_key,
        planted_on=date(2026, 4, 1),
        current_phase_started_at=datetime(2026, 5, 1, tzinfo=UTC),
    )


class World:
    def __init__(self) -> None:
        self.repo = FakePlanRepo(_Sites(make_site()))
        self.repo.bed_types.update({"planter": True, "tent": False, "shelf": False})
        self.repo.locations["bed"] = make_location("bed", "Kohlbeet")
        self.repo.locations["bed2"] = make_location("bed2", "Nachbarbeet")
        self.repo.locations["hydro"] = make_location("hydro", "NFT-Rinne", irrigation_system=IrrigationSystem.NFT)
        for type_key in ("planter", "tent", "shelf"):
            self.repo.locations[type_key] = make_location(type_key, type_key, location_type_key=type_key)
        self.repo.locations["greenhouse"] = make_location("greenhouse", "Haus", location_type_key="greenhouse")
        self.plants = _PlantStore(
            _standing("kohl", "bed"),
            _standing("kohl_bed2", "bed2"),
            _standing("kohl_hydro", "hydro"),
            _standing("kohl_foreign", "bed", tenant=OTHER_TENANT),
        )
        self.hazard_repo = FakeBedSoilHazardRepo(self.repo)
        # The plant store the plant service writes, so an accepted offer reads the loss the remove call stored.
        self.hazards = soil_hazard_service(self.repo, hazards=self.hazard_repo, plant_store=self.plants)
        self.sites = SiteService(self.repo._sites)  # type: ignore[arg-type]
        self.resources = GardenResourceService(
            self.repo._sites, self.repo, FakeObjects(self.repo), GardenPlanService(self.repo._sites, self.repo)
        )
        phase_repo = MagicMock()
        phase_repo.get_phase_history.return_value = [
            PhaseHistory(
                _key="h-1",
                plant_instance_key="kohl",
                phase_key="ph-veg",
                phase_name="vegetative",
                entered_at=datetime(2026, 5, 1, tzinfo=UTC),
            )
        ]
        species_repo = MagicMock()
        species_repo.get_by_key.return_value = Species(
            _key="sp_kohl", scientific_name="Brassica oleracea", family_key="brassicaceae"
        )
        families = MagicMock()
        families.get_by_key.return_value = BotanicalFamily(_key="brassicaceae", name="Brassicaceae")
        self.plant_service = PlantInstanceService(
            self.plants,  # type: ignore[arg-type]
            MagicMock(),
            MagicMock(),
            MagicMock(),
            phase_repo=phase_repo,
            task_repo=MagicMock(),
            species_repo=species_repo,
            family_repo=families,
        )

    def entries(self, key: str = "bed") -> list[BedSoilHazard]:
        return list(self.repo.locations[key].soil_hazards)

    def seed(self, key: str, *entries: BedSoilHazard) -> None:
        self.repo.locations[key] = self.repo.locations[key].model_copy(update={"soil_hazards": list(entries)})


@pytest.fixture
def world() -> World:
    return World()


@pytest.fixture
def client(world: World) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(_key=ME, email="s@example.org", display_name="Sabine")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_bed_soil_hazard_service] = lambda: world.hazards
    app.dependency_overrides[get_site_service] = lambda: world.sites
    app.dependency_overrides[get_garden_resource_service] = lambda: world.resources
    app.dependency_overrides[get_plant_instance_service] = lambda: world.plant_service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _codes(response) -> list[str]:
    return [item.get("code") for item in response.json().get("details", [])]


def _manual(hazard: str = "verticillium", confirmed_at: str = "2026-07-01", source: str = "lab_test") -> dict:
    return {"hazard": hazard, "confirmed_at": confirmed_at, "source": source}


class TestABedShowsItsSoilHazards:
    """acceptance-1: pathogen, endangered plants (from the table, at read time), confirmation date and source."""

    def test_the_location_carries_its_hazards_with_hosts_resolved_at_read_time(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        response = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed")

        assert response.status_code == 200
        assert response.json()["soil_hazards"] == [
            {
                "hazard": "clubroot",
                "confirmed_at": "2025-06-01",
                "source": "clear_symptoms",
                "pathogens": ["Plasmodiophora brassicae"],
                "soft": False,
                "hosts": [{"level": "family", "name": "Brassicaceae", "evidence_status": "evidenced"}],
                "non_hosts": [],
            }
        ]

    def test_the_bed_summary_carries_them_too(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        response = client(TenantRole.VIEWER).get(f"{_BASE}/locations/bed/summary")

        assert response.status_code == 200
        (entry,) = response.json()["soil_hazards"]
        assert entry["hazard"] == "clubroot" and entry["hosts"][0]["name"] == "Brassicaceae"

    def test_a_bed_without_hazards_reads_an_empty_list(self, client) -> None:
        assert client().get(f"{_BASE}/locations/bed").json()["soil_hazards"] == []

    def test_the_stored_entry_holds_the_key_not_a_host_snapshot(self, client, world) -> None:
        client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual("clubroot"))

        (stored,) = world.hazard_repo.writes[0][1]
        assert set(stored.model_dump()) == {"hazard", "confirmed_at", "source"}


class TestGrowersAddOnlyTheLeadRemoves:
    """acceptance-2 (API half): POST as grower 201, DELETE as grower 403 / lead 204; vessels refused."""

    def test_a_grower_records_a_hazard(self, client, world) -> None:
        response = client(TenantRole.GROWER).post(f"{_BASE}/locations/bed/soil-hazards", json=_manual())

        assert response.status_code == 201
        assert response.json()["location_key"] == "bed" and response.json()["changed"] is True
        assert [e["hazard"] for e in response.json()["soil_hazards"]] == ["verticillium"]
        assert [e.hazard for e in world.entries()] == [SoilHazard.VERTICILLIUM]

    def test_a_viewer_is_refused_at_the_gate(self, client, world) -> None:
        response = client(TenantRole.VIEWER).post(f"{_BASE}/locations/bed/soil-hazards", json=_manual())

        assert response.status_code == 403 and world.entries() == []

    def test_a_grower_cannot_remove_one(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        response = client(TenantRole.GROWER).delete(f"{_BASE}/locations/bed/soil-hazards/clubroot")

        assert response.status_code == 403 and world.entries() == [CLUBROOT_2025]

    def test_the_lead_removes_one(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed/soil-hazards/clubroot")

        assert response.status_code == 204 and world.entries() == []

    def test_removing_a_hazard_the_bed_does_not_hold_is_404(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed/soil-hazards/white_rot")

        assert response.status_code == 404 and world.entries() == [CLUBROOT_2025]

    def test_an_unknown_hazard_key_is_422(self, client) -> None:
        response = client(TenantRole.LEAD).delete(f"{_BASE}/locations/bed/soil-hazards/fusarium")
        assert response.status_code == 422

    @pytest.mark.parametrize("vessel", ["planter", "tent", "shelf"])
    def test_a_vessel_is_refused(self, client, world, vessel: str) -> None:
        response = client(TenantRole.LEAD).post(f"{_BASE}/locations/{vessel}/soil-hazards", json=_manual())

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.container"]
        assert world.entries(vessel) == []

    def test_a_location_that_is_no_bed_is_refused(self, client, world) -> None:
        response = client().post(f"{_BASE}/locations/greenhouse/soil-hazards", json=_manual())

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.not_a_bed"]

    def test_a_later_confirmation_replaces_an_earlier_one_never_the_reverse(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        earlier = client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual("clubroot", "2024-01-01"))
        # Nothing written: 200 and ``changed: false``, never the 201 of a recorded entry (review D3).
        assert earlier.status_code == 200 and earlier.json()["changed"] is False
        assert world.entries() == [CLUBROOT_2025] and world.hazard_repo.writes == []

        later = client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual("clubroot", "2026-07-01"))
        assert later.status_code == 201 and later.json()["changed"] is True
        assert [(e.hazard, e.confirmed_at) for e in world.entries()] == [(SoilHazard.CLUBROOT, date(2026, 7, 1))]

    def test_the_same_date_again_writes_nothing_and_says_so(self, client, world) -> None:
        world.seed("bed", CLUBROOT_2025)

        again = client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual("clubroot", "2025-06-01"))

        assert again.status_code == 200 and again.json()["changed"] is False
        assert world.hazard_repo.writes == []

    def test_a_confirmation_before_1900_is_422(self, client, world) -> None:
        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual(confirmed_at="1899-12-31"))

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.confirmed_too_early"]
        assert world.entries() == []

    def test_a_container_group_is_refused_with_the_vessel_words(self, client, world) -> None:
        """Review D8: ``container`` (pot/container group) is no bed type but a vessel - the vessel answer."""
        world.repo.locations["pots"] = make_location("pots", "Topfgruppe", location_type_key="container")

        response = client().post(f"{_BASE}/locations/pots/soil-hazards", json=_manual())

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.container"]

    def test_a_confirmation_in_the_future_is_422(self, client, world) -> None:
        tomorrow = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()

        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual(confirmed_at=tomorrow))

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.confirmed_in_future"]
        assert world.entries() == []

    @pytest.mark.parametrize(
        "body",
        [
            {},
            {"hazard": "clubroot", "confirmed_at": "2026-07-01"},
            {**_manual(), "plant_key": "kohl"},
            {"plant_key": ""},
            {**_manual(), "recorded_by": ME},
            _manual(hazard="fusarium"),
            _manual(source="neighbour"),
        ],
        ids=["empty", "no_source", "both_forms", "empty_plant_key", "extra_field", "unknown_hazard", "free_source"],
    )
    def test_a_malformed_body_is_422_and_writes_nothing(self, client, world, body: dict) -> None:
        assert client().post(f"{_BASE}/locations/bed/soil-hazards", json=body).status_code == 422
        assert world.entries() == []


class TestTheOfferAfterALoss:
    """acceptance-3: a confirmed, listed soil-borne loss is offered; the acceptance writes; a suspicion never does."""

    def test_a_confirmed_loss_is_offered_and_nothing_is_written_yet(self, client, world) -> None:
        response = client().post(f"{_BASE}/plant-instances/kohl/remove", json=CONFIRMED_LOSS)

        assert response.status_code == 200
        assert response.json()["soil_hazard_follow_up"] == {
            "kind": "offer",
            "location_key": "bed",
            "hazard": "clubroot",
            "confirmed_at": datetime.now(UTC).date().isoformat(),
            "source": "lab_test",
        }
        assert world.entries() == [] and world.hazard_repo.writes == []

    def test_accepting_the_offer_records_the_pathogen_of_the_loss(self, client, world) -> None:
        client().post(f"{_BASE}/plant-instances/kohl/remove", json=CONFIRMED_LOSS)

        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "kohl"})

        assert response.status_code == 201
        assert world.entries() == [
            BedSoilHazard(
                hazard=SoilHazard.CLUBROOT,
                confirmed_at=datetime.now(UTC).date(),
                source=PathogenConfirmationSource.LAB_TEST,
            )
        ]

    def test_an_unconfirmed_loss_is_never_offered(self, client, world) -> None:
        response = client().post(f"{_BASE}/plant-instances/kohl/remove", json=SUSPECTED_LOSS)

        assert response.status_code == 200 and response.json()["soil_hazard_follow_up"] is None

    def test_an_unconfirmed_loss_never_becomes_an_entry_whatever_the_client_sends(self, client, world) -> None:
        client().post(f"{_BASE}/plant-instances/kohl/remove", json=SUSPECTED_LOSS)

        response = client(TenantRole.LEAD).post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "kohl"})

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.loss_not_confirmed"]
        assert world.entries() == [] and world.hazard_repo.writes == []

    def test_a_standing_plant_is_no_loss_to_take_over(self, client, world) -> None:
        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "kohl"})

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.loss_not_confirmed"]
        assert world.entries() == []

    def test_a_new_loss_naming_juglone_is_refused(self, client, world) -> None:
        removed = client().post(
            f"{_BASE}/plant-instances/kohl/remove", json={**CONFIRMED_LOSS, "failure_pathogen": "juglone"}
        )

        assert removed.status_code == 422 and "no pathogen of a loss" in removed.text
        assert world.plants.rows["kohl"].removed_on is None and world.entries() == []

    def test_a_juglone_loss_stored_before_the_rule_is_neither_offered_nor_taken_over(self, client, world) -> None:
        # Possible data: F-19 accepted juglone until #2888 F-20 (review D4); such a loss keeps loading.
        legacy = world.plants.rows["kohl"].model_copy(
            update={
                "removed_on": date(2026, 7, 1),
                "termination_type": "died",
                "termination_cause": "disease",
                "failure_cause_class": "disease_soil",
                "failure_pathogen": "juglone",
                "failure_pathogen_confirmed": True,
                "failure_pathogen_source": "clear_symptoms",
            }
        )
        world.plants.rows["kohl"] = legacy
        assert world.hazards.follow_up_for_loss(legacy, tenant_key=TENANT) is None

        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "kohl"})

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.loss_not_confirmed"]
        assert world.entries() == []

    def test_juglone_is_recorded_by_hand(self, client, world) -> None:
        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json=_manual("juglone", "2019-03-01"))

        assert response.status_code == 201 and [e.hazard for e in world.entries()] == [SoilHazard.JUGLONE]

    def test_the_loss_of_another_bed_is_not_taken_over_here(self, client, world) -> None:
        client().post(f"{_BASE}/plant-instances/kohl_bed2/remove", json=CONFIRMED_LOSS)

        response = client().post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "kohl_bed2"})

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.plant_not_in_bed"]
        assert world.entries() == [] and world.entries("bed2") == []

    def test_a_bed_that_holds_the_hazard_already_is_not_offered_it_again(self, client, world) -> None:
        today = datetime.now(UTC).date()
        world.seed("bed", CLUBROOT_2025.model_copy(update={"confirmed_at": today}))

        response = client().post(f"{_BASE}/plant-instances/kohl/remove", json=CONFIRMED_LOSS)

        assert response.json()["soil_hazard_follow_up"] is None


class TestHydroponics:
    """acceptance-4: a soil-borne loss at a hydroponic location is the clean-system hint, never a soil hazard."""

    def test_a_confirmed_loss_in_the_nft_channel_is_the_clean_system_hint(self, client, world) -> None:
        response = client().post(f"{_BASE}/plant-instances/kohl_hydro/remove", json=CONFIRMED_LOSS)

        assert response.status_code == 200
        assert response.json()["soil_hazard_follow_up"] == {
            "kind": "clean_system",
            "location_key": "hydro",
            "hazard": None,
            "confirmed_at": None,
            "source": None,
        }
        assert world.entries("hydro") == []

    def test_the_loss_there_cannot_be_taken_over_either(self, client, world) -> None:
        client().post(f"{_BASE}/plant-instances/kohl_hydro/remove", json=CONFIRMED_LOSS)

        response = client().post(f"{_BASE}/locations/hydro/soil-hazards", json={"plant_key": "kohl_hydro"})

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.hydroponic"]
        assert world.entries("hydro") == []

    def test_a_hazard_by_hand_is_refused_there(self, client, world) -> None:
        response = client().post(f"{_BASE}/locations/hydro/soil-hazards", json=_manual())

        assert response.status_code == 422 and _codes(response) == ["soil_hazard.hydroponic"]


class TestAnotherTenantsHazards:
    """acceptance-5: neither readable nor changeable - the same 404 as for an unknown bed (no existence oracle)."""

    @pytest.mark.parametrize(
        ("method", "path", "body"),
        [
            ("GET", "/locations/{bed}", None),
            ("GET", "/locations/{bed}/summary", None),
            ("POST", "/locations/{bed}/soil-hazards", _manual()),
            ("POST", "/locations/{bed}/soil-hazards", {"plant_key": "kohl"}),
            ("DELETE", "/locations/{bed}/soil-hazards/clubroot", None),
        ],
        ids=["read", "summary", "record", "take_over", "remove"],
    )
    def test_a_foreign_bed_answers_like_an_unknown_one(self, client, world, method, path, body) -> None:
        world.seed("bed", CLUBROOT_2025)
        lead = client(TenantRole.LEAD)

        foreign = lead.request(method, _FOREIGN + path.format(bed="bed"), json=body)
        unknown = lead.request(method, _FOREIGN + path.format(bed="gone"), json=body)

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["message"].replace("bed", "gone") == unknown.json()["message"]
        # The request path is echoed back (the caller sent it); nothing of the bed beyond it is.
        echoed = {k: v for k, v in foreign.json().items() if k != "path"}
        assert "clubroot" not in str(echoed) and "Kohlbeet" not in foreign.text
        assert world.entries() == [CLUBROOT_2025] and world.hazard_repo.writes == []

    def test_another_tenants_loss_is_not_taken_over_into_an_own_bed(self, client, world) -> None:
        # The foreign plant stands (by its location key) in this bed - only its tenant tells it apart.
        world.plants.rows["kohl_foreign"] = world.plants.rows["kohl_foreign"].model_copy(
            update={
                "removed_on": date(2026, 7, 1),
                "termination_type": "died",
                "termination_cause": "disease",
                "failure_cause_class": "disease_soil",
                "failure_pathogen": "clubroot",
                "failure_pathogen_confirmed": True,
                "failure_pathogen_source": "lab_test",
            }
        )

        foreign = client().post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "kohl_foreign"})
        unknown = client().post(f"{_BASE}/locations/bed/soil-hazards", json={"plant_key": "gone"})

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["message"].replace("kohl_foreign", "gone") == unknown.json()["message"]
        assert world.entries() == []


class TestTheFollowUpNeverFailsTheRemoval:
    """Review D2: the loss is stored before the follow-up is computed; a failing read there must not fail the call."""

    def test_a_location_read_that_raises_answers_the_removal_without_a_follow_up(self, client, world) -> None:
        def broken(key: str):  # type: ignore[no-untyped-def]
            raise StoredDocumentInvalidError("Location", key, ["soil_hazards"])

        world.repo._sites.get_location_by_key = broken  # type: ignore[method-assign]

        response = client().post(f"{_BASE}/plant-instances/kohl/remove", json=CONFIRMED_LOSS)

        assert response.status_code == 200
        assert response.json()["removed_on"] is not None and response.json()["soil_hazard_follow_up"] is None
        assert world.plants.rows["kohl"].termination_type == "died"
