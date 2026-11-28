"""The production wiring of the bed-level planting check reaches the soil hazards (#2888 F-21 review S2).

``_bed_rotation_validator()`` is built exactly as the app builds it - only the database handle is a stub, nothing is
read from it here. Pinned: the knowledge source is the process-wide table (not ``None``), and a host on a bed with a
confirmed soil hazard gets a finding through that very instance. Without ``soil_hazards=`` in the factory the check
would be implemented but inert: every unit test injects its own source.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from app.common import dependencies
from app.common.datetimes import today_utc
from app.common.enums import PathogenConfirmationSource, SoilHazard
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species
from tests.support.garden_plan_fakes import TENANT, FakePlanRepo, FakeSites, make_location, make_site
from tests.support.rotation_fakes import FakeFamilies, FakeRotationGraph, FakeRotationHistory, FakeSpecies


@pytest.fixture
def production_validator(monkeypatch):
    monkeypatch.setattr(dependencies, "get_db", lambda: MagicMock())
    return dependencies._bed_rotation_validator()


def test_the_factory_hands_the_process_wide_knowledge_table_to_the_validator(production_validator) -> None:
    assert production_validator._soil_hazards is dependencies.get_soil_hazard_knowledge_source()


def test_a_host_on_a_bed_with_a_confirmed_hazard_gets_a_finding_through_the_wired_source(production_validator) -> None:
    # Only the stores behind the factory's repositories are replaced; the knowledge source stays the wired one.
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location(
        "bed",
        soil_hazards=[
            BedSoilHazard(
                hazard=SoilHazard.CLUBROOT,
                confirmed_at=today_utc() - timedelta(days=365),
                source=PathogenConfirmationSource.LAB_TEST,
            )
        ],
    )
    production_validator._sites = sites
    production_validator._species_repo = FakeSpecies(
        Species(_key="cabbage", scientific_name="Brassica oleracea", genus="Brassica", family_key="fam_brassica")
    )
    production_validator._families = FakeFamilies(
        BotanicalFamily(_key="fam_brassica", name="Brassicaceae", rotation_pause_years=4)
    )
    production_validator._history = FakeRotationHistory()
    production_validator._graph_repo = FakeRotationGraph()

    result = production_validator.validate_planting_in_location("bed", "cabbage", tenant_key=TENANT)

    assert [(f.code, f.hazard) for f in result.findings if f.code.startswith("soil_hazard.")] == [
        ("soil_hazard.pause", "clubroot")
    ]


def test_the_wired_validator_reads_the_hazard_of_the_area_above_the_bed(production_validator) -> None:
    """REQ-053 §11.3a Nr. 5 v1.60 (#2888 O3): the production instance walks the parent chain, not only the bed."""
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    plan.locations["garden"] = make_location(
        "garden",
        location_type_key="garden",
        soil_hazards=[
            BedSoilHazard(
                hazard=SoilHazard.JUGLONE,
                confirmed_at=today_utc() - timedelta(days=365),
                source=PathogenConfirmationSource.CLEAR_SYMPTOMS,
            )
        ],
    )
    plan.locations["bed"] = make_location("bed", parent_location_key="garden")
    production_validator._sites = sites
    production_validator._species_repo = FakeSpecies(
        Species(_key="tomato", scientific_name="Solanum lycopersicum", genus="Solanum", family_key="fam_solanum")
    )
    production_validator._families = FakeFamilies(
        BotanicalFamily(_key="fam_solanum", name="Solanaceae", rotation_pause_years=4)
    )
    production_validator._history = FakeRotationHistory()
    production_validator._graph_repo = FakeRotationGraph()

    result = production_validator.validate_planting_in_location("bed", "tomato", tenant_key=TENANT)

    assert [f.hazard for f in result.findings if f.code.startswith("soil_hazard.")] == ["juglone"]


def test_the_wired_soil_hazard_service_writes_the_removal_with_its_audit_row(monkeypatch) -> None:
    """#2888 O6: the factory's repository is the Arango one whose removal writes ``garden_plan_audit`` (an abstract
    ``remove_soil_hazard`` would not even construct); the route hands it the caller's account
    (``tests/api/test_bed_soil_hazards_api.py::TestTheRemovalIsInThePlanChangeLog``)."""
    from app.data_access.arango.bed_soil_hazard_repository import ArangoBedSoilHazardRepository

    monkeypatch.setattr(dependencies, "get_db", lambda: MagicMock())
    service = dependencies.get_bed_soil_hazard_service()

    assert isinstance(service._hazards, ArangoBedSoilHazardRepository)
