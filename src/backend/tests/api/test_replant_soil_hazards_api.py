"""REQ-053 §11.3a Nr. 6-7 / GP-API-025 (#2888 F-21) — the soil hazards of a bed in the planting check, on the wire.

``app.main`` with the real ``BedRotationService`` and the real validator over the shipped knowledge table. Pinned:

* acceptance-6 — ``POST /locations/{key}/validate-planting`` answers exactly what the validator decides: the planting
  dialog and the rotation check read one source, there is no second way to compute a soil-hazard finding.
* acceptance-1 — the hazard reaches the wire also on a bed whose rotation check is off; never a 4xx.
* acceptance-5 — ``soil_profile.substrate_replaced_on`` written through ``PATCH /locations/{key}`` lifts it; a day
  after today is a 422 before anything is written.
* REQ-053 §11.3a Nr. 5 v1.60 (#2888 O3/O5) — a juglone recorded at the garden reaches the planting check of a bed in
  it; a bed left at ``manual`` under a hydroponic room is not checked, not even for what it holds itself.

Dates are relative to today (UTC) instead of a frozen clock: the app's routes are built lazily, under a frozen clock
FastAPI cannot build a ``date`` parameter (a local tooling limit of the other API tests of this area).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import asdict
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.datetimes import today_utc
from app.common.dependencies import get_bed_rotation_service, get_garden_resource_service, get_tenant_service
from app.common.enums import IrrigationSystem, PathogenConfirmationSource, SoilHazard, TenantRole
from app.common.exceptions import NotFoundError
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.engines.soil_hazard_planting_engine import add_years
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species
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
from tests.support.rotation_fakes import FakeFamilies, FakeRotationGraph, FakeRotationHistory, FakeSpecies

_BASE = "/api/v1/t/own"


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


def _clubroot(confirmed_at: date) -> list[BedSoilHazard]:
    return [
        BedSoilHazard(
            hazard=SoilHazard.CLUBROOT,
            confirmed_at=confirmed_at,
            source=PathogenConfirmationSource.LAB_TEST,
        )
    ]


@pytest.fixture
def world() -> SimpleNamespace:
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    # Today is read once per test: a run across midnight UTC must not compare two different days.
    today = today_utc()
    confirmed = today - timedelta(days=365)
    plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot(confirmed))
    plan.locations["perennial"] = make_location("perennial", rotation_exempt=True, soil_hazards=_clubroot(confirmed))
    juglone = BedSoilHazard(
        hazard=SoilHazard.JUGLONE, confirmed_at=confirmed, source=PathogenConfirmationSource.CLEAR_SYMPTOMS
    )
    plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=[juglone])
    plan.locations["under_walnut"] = make_location("under_walnut", parent_location_key="garden")
    plan.locations["room"] = make_location(
        "room", location_type_key="greenhouse", irrigation_system=IrrigationSystem.HYDRO
    )
    plan.locations["in_room"] = make_location("in_room", parent_location_key="room", soil_hazards=_clubroot(confirmed))
    species = FakeSpecies(
        Species(_key="cabbage", scientific_name="Brassica oleracea", genus="Brassica", family_key="fam_brassica"),
        Species(_key="tomato", scientific_name="Solanum lycopersicum", genus="Solanum", family_key="fam_solanum"),
    )
    families = FakeFamilies(
        BotanicalFamily(_key="fam_brassica", name="Brassicaceae", rotation_pause_years=4),
        BotanicalFamily(_key="fam_solanum", name="Solanaceae", rotation_pause_years=4),
    )
    care_repo = FakeCareEventRepo()
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    history = FakeRotationHistory(care_repo)
    graph = FakeRotationGraph()
    validator = CropRotationValidator(
        None,
        species,
        graph,
        site_repo=sites,
        family_repo=families,
        history_repo=history,
        soil_hazards=YamlSoilHazardKnowledgeSource(),
    )
    service = BedRotationService(sites, plan, graph, species, families, care, validator)
    return SimpleNamespace(
        service=service, validator=validator, plan=plan, sites=sites, history=history, today=today, confirmed=confirmed
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
    app.dependency_overrides[get_garden_resource_service] = lambda: GardenResourceService(
        world.sites, world.plan, FakeObjects(world.plan), GardenPlanService(world.sites, world.plan)
    )
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _hints(client: Callable[..., TestClient], bed: str, species: str = "cabbage") -> dict:
    response = client().post(f"{_BASE}/locations/{bed}/validate-planting", json={"species_key": species})
    assert response.status_code == 200, response.text
    return response.json()


def _wire(finding) -> dict:
    """A validator finding as the wire carries it (dates as ISO strings)."""
    return {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in asdict(finding).items()}


class TestOneSourceForTheDialogAndTheCheck:
    """acceptance-6."""

    @pytest.mark.parametrize("bed", ["bed", "perennial"])
    def test_the_answer_is_the_validators_finding_for_finding(self, client, world, bed) -> None:
        expected = world.validator.validate_planting_in_location(bed, "cabbage", tenant_key=TENANT)

        body = _hints(client, bed)

        assert body["severity"] == expected.severity == "WARNING"
        assert body["rotation_applicable"] is expected.applicable
        assert body["rotation"] == [_wire(finding) for finding in expected.findings]

    def test_the_soil_hazard_finding_carries_its_end_and_host(self, client, world) -> None:
        (finding,) = [f for f in _hints(client, "bed")["rotation"] if f["code"].startswith("soil_hazard.")]

        confirmed = world.confirmed
        assert finding == {
            **finding,
            "severity": "WARNING",
            "code": "soil_hazard.pause",
            "hazard": "clubroot",
            "hazard_confirmed_at": confirmed.isoformat(),
            "hazard_stage": "pause",
            "hazard_until": add_years(confirmed, 7).isoformat(),
            "host_level": "family",
            "host_name": "Brassicaceae",
        }

    def test_a_bed_with_the_rotation_off_still_answers_the_hazard(self, client) -> None:
        body = _hints(client, "perennial")

        assert (body["rotation_applicable"], body["not_applicable_reason"]) == (
            False,
            "rotation.not_applicable.rotation_exempt",
        )
        assert [f["code"] for f in body["rotation"]] == ["soil_hazard.pause"]

    def test_a_species_that_is_no_host_gets_no_soil_finding(self, client) -> None:
        body = _hints(client, "bed", "tomato")

        assert not [f for f in body["rotation"] if f["code"].startswith("soil_hazard.")]


class TestFreshSubstrateOnTheWire:
    """acceptance-5: the field is written through the location PATCH and lifts the warning."""

    def test_setting_changing_and_clearing_the_day_each_write_a_plan_log_row(self, client, world) -> None:
        """D-S3 (2026-11-28): who, when, which location, old and new day - only for a real change."""
        first = (world.today - timedelta(days=30)).isoformat()
        second = (world.today - timedelta(days=10)).isoformat()

        def patch(day):  # type: ignore[no-untyped-def]
            body = {"soil_profile": {"substrate_replaced_on": day}}
            response = client().patch(f"{_BASE}/locations/bed", json=body)
            assert response.status_code == 200, response.text

        patch(first)
        patch(first)
        patch(second)
        patch(None)

        assert [(r.op, r.entity, r.key, r.user_key, r.summary) for r in world.plan.audit_rows] == [
            ("update", "substrate_replaced_on", "bed", "u_sabine", f"none -> {first}"),
            ("update", "substrate_replaced_on", "bed", "u_sabine", f"{first} -> {second}"),
            ("update", "substrate_replaced_on", "bed", "u_sabine", f"{second} -> none"),
        ]

    def test_clearing_the_whole_profile_logs_the_day_that_went(self, client, world) -> None:
        day = (world.today - timedelta(days=30)).isoformat()
        client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"substrate_replaced_on": day}})

        response = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": None})

        assert response.status_code == 200, response.text
        assert [r.summary for r in world.plan.audit_rows] == [f"none -> {day}", f"{day} -> none"]

    def test_another_soil_field_and_a_refused_day_write_no_row(self, client, world) -> None:
        assert client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"drainage": "poor"}}).status_code == 200
        future = (world.today + timedelta(days=2)).isoformat()
        refused = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"substrate_replaced_on": future}})

        assert refused.status_code == 422
        assert world.plan.audit_rows == []

    def test_a_renewal_after_the_confirmation_lifts_the_warning(self, client, world) -> None:
        renewed = (world.today - timedelta(days=30)).isoformat()

        patched = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"substrate_replaced_on": renewed}})

        assert patched.status_code == 200, patched.text
        assert patched.json()["soil_profile"]["substrate_replaced_on"] == renewed
        body = _hints(client, "bed")
        assert not [f for f in body["rotation"] if f["code"].startswith("soil_hazard.")]

    def test_a_renewal_after_today_is_a_422_and_changes_nothing(self, client, world) -> None:
        # Two days ahead: still after today when the request lands just past midnight UTC.
        tomorrow = (world.today + timedelta(days=2)).isoformat()

        response = client().patch(f"{_BASE}/locations/bed", json={"soil_profile": {"substrate_replaced_on": tomorrow}})

        assert response.status_code == 422, response.text
        assert world.plan.locations["bed"].soil_profile is None
        assert [f["code"] for f in _hints(client, "bed")["rotation"]][0] == "soil_hazard.pause"


class TestTheParentChainOnTheWire:
    """REQ-053 §11.3a Nr. 5 v1.60: the soil under a bed carries the hazards above it; hydroponics is inherited."""

    def test_the_gardens_juglone_reaches_the_planting_check_of_a_bed_in_it(self, client, world) -> None:
        expected = world.validator.validate_planting_in_location("under_walnut", "tomato", tenant_key=TENANT)

        body = _hints(client, "under_walnut", "tomato")

        juglone = [f for f in body["rotation"] if f.get("hazard") == "juglone"]
        assert len(juglone) == 1 and juglone[0]["code"].startswith("soil_hazard.")
        assert juglone[0]["host_name"] == "Solanum lycopersicum"
        assert body["rotation"] == [_wire(finding) for finding in expected.findings]

    def test_a_bed_outside_the_garden_hears_nothing_of_it(self, client) -> None:
        body = _hints(client, "bed", "tomato")

        assert not [f for f in body["rotation"] if f.get("hazard") == "juglone"]

    def test_a_soil_bed_under_a_hydroponic_room_keeps_its_own_hazard(self, client) -> None:
        """Review S1 (REQ-053 v1.61): flipped - the bed's own confirmed clubroot still warns there."""
        body = _hints(client, "in_room", "cabbage")

        assert [f["code"] for f in body["rotation"] if f["code"].startswith("soil_hazard.")] == ["soil_hazard.pause"]

    def test_the_inherited_finding_names_its_location_on_the_wire(self, client, world) -> None:
        """Review S3: key and name of the location above the bed; ``null`` for the bed's own hazard."""
        (inherited,) = [f for f in _hints(client, "under_walnut", "tomato")["rotation"] if f.get("hazard") == "juglone"]
        (own,) = [f for f in _hints(client, "bed")["rotation"] if f["code"].startswith("soil_hazard.")]

        assert (inherited["hazard_location_key"], inherited["hazard_location_name"]) == (
            "garden",
            world.plan.locations["garden"].name,
        )
        assert (own["hazard_location_key"], own["hazard_location_name"]) == (None, None)
