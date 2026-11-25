"""#3015 — the list reads that replace a per-run, per-site or whole-tenant fan-out in the frontend, on the wire.

The plant list carries each row's runs (``planting_runs``) resolved once per page; the plant and tank lists take a
``location_key`` filter; ``GET /locations/options`` answers every site's locations in one paged read. The services
are doubles: the AQL and its tenant predicate are measured in
``tests/integration/test_list_projections_tenant_scope.py``.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.locations.tenant_router import router as location_router
from app.api.v1.plant_instances.tenant_router import router as plant_router
from app.api.v1.tanks.tenant_router import router as tank_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_garden_resource_service, get_plant_instance_service, get_tank_service
from app.common.enums import TenantRole
from app.domain.models.garden_plan import LocationOption
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext

TENANT_KEY = "t-own"
PREFIX = "/api/v1/t/own"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT_KEY, tenant_slug="own", user_key="u-1", role=TenantRole.VIEWER)


def _plant(key: str) -> PlantInstance:
    return PlantInstance(
        _key=key,
        instance_id=key.upper(),
        species_key="basil",
        planted_on=date(2026, 3, 1),
        tenant_key=TENANT_KEY,
        location_key="loc-1",
    )


def _client(**overrides) -> TestClient:
    app = FastAPI()
    for router in (plant_router, tank_router, location_router):
        app.include_router(router, prefix=PREFIX)
    app.dependency_overrides[get_current_tenant] = _ctx
    providers = {
        "plants": get_plant_instance_service,
        "tanks": get_tank_service,
        "resources": get_garden_resource_service,
    }
    for dependency, double in overrides.items():
        # A parameterless provider: FastAPI reads an override's signature, so a defaulted argument would become a
        # query parameter.
        app.dependency_overrides[providers[dependency]] = _provide(double)
    return TestClient(app)


def _provide(double: MagicMock):
    def provider() -> MagicMock:
        return double

    return provider


def _plant_service(*plants: PlantInstance, run_refs: dict | None = None) -> MagicMock:
    service = MagicMock()
    service.list_plants_window.return_value = list(plants)
    service.resolve_phase_name.return_value = ""
    service.resolve_species.return_value = None
    service.resolve_cultivar.return_value = None
    service.run_refs_for_plants.return_value = run_refs or {}
    return service


class TestPlantListCarriesItsRuns:
    def test_each_row_names_its_runs_from_one_read_per_page(self) -> None:
        service = _plant_service(
            _plant("p-1"),
            _plant("p-2"),
            _plant("p-3"),
            run_refs={
                "p-1": [{"key": "run-new", "name": "Spring", "status": "active"}],
                "p-3": [
                    {"key": "run-b", "name": "B", "status": "active"},
                    {"key": "run-a", "name": "A", "status": "completed"},
                ],
            },
        )

        response = _client(plants=service).get(f"{PREFIX}/plant-instances")

        assert response.status_code == 200, response.text
        runs = {row["key"]: row["planting_runs"] for row in response.json()}
        assert runs == {
            "p-1": [{"key": "run-new", "name": "Spring", "status": "active"}],
            # A plant without a run says so with an empty list on the list route, not with null.
            "p-2": [],
            "p-3": [
                {"key": "run-b", "name": "B", "status": "active"},
                {"key": "run-a", "name": "A", "status": "completed"},
            ],
        }
        # One resolution for the page, whatever the number of runs - the property the frontend relies on.
        service.run_refs_for_plants.assert_called_once_with(["p-1", "p-2", "p-3"], tenant_key=TENANT_KEY)

    def test_the_single_plant_route_leaves_the_runs_unresolved(self) -> None:
        service = _plant_service()
        service.get_plant.return_value = _plant("p-1")

        body = _client(plants=service).get(f"{PREFIX}/plant-instances/p-1").json()

        assert body["planting_runs"] is None
        service.run_refs_for_plants.assert_not_called()


class TestLocationFilters:
    def test_the_plant_list_passes_the_location_to_the_service(self) -> None:
        service = _plant_service(_plant("p-1"))

        response = _client(plants=service).get(f"{PREFIX}/plant-instances", params={"location_key": "loc-1"})

        assert response.status_code == 200, response.text
        assert service.list_plants_window.call_args.kwargs["location_key"] == "loc-1"
        assert service.list_plants_window.call_args.kwargs["tenant_key"] == TENANT_KEY

    def test_the_plant_list_without_a_location_reads_the_whole_tenant(self) -> None:
        service = _plant_service()

        _client(plants=service).get(f"{PREFIX}/plant-instances")

        assert service.list_plants_window.call_args.kwargs["location_key"] is None

    def test_the_tank_list_filters_by_location(self) -> None:
        service = MagicMock()
        service.list_tanks_window.return_value = []

        response = _client(tanks=service).get(
            f"{PREFIX}/tanks", params={"location_key": "loc-1", "offset": 0, "limit": 200}
        )

        assert response.status_code == 200, response.text
        service.list_tanks_window.assert_called_once_with(0, 200, {"location_key": "loc-1"}, tenant_key=TENANT_KEY)

    @pytest.mark.parametrize("path", ["plant-instances", "tanks"])
    def test_an_empty_location_key_is_422_rather_than_every_row(self, path) -> None:
        response = _client(plants=_plant_service(), tanks=MagicMock()).get(
            f"{PREFIX}/{path}", params={"location_key": ""}
        )

        assert response.status_code == 422


class TestLocationOptions:
    def test_the_locations_of_every_site_come_from_one_paged_read(self) -> None:
        resources = MagicMock()
        resources.list_location_options.return_value = [
            LocationOption(key="bed-a", name="Asparagus", site_key="site-2", parent_location_key=None, area_m2=4.5),
            LocationOption(key="bed-c", name="Carrots", site_key="site-1", parent_location_key="area-1", area_m2=None),
        ]

        response = _client(resources=resources).get(
            f"{PREFIX}/locations/options", params={"offset": 200, "limit": 200, "is_bed": "true"}
        )

        assert response.status_code == 200, response.text
        assert response.json() == [
            {"key": "bed-a", "name": "Asparagus", "site_key": "site-2", "parent_location_key": None, "area_m2": 4.5},
            {"key": "bed-c", "name": "Carrots", "site_key": "site-1", "parent_location_key": "area-1", "area_m2": None},
        ]
        resources.list_location_options.assert_called_once_with(
            tenant_key=TENANT_KEY, offset=200, limit=200, is_bed=True, top_level_only=False
        )

    def test_without_filters_every_location_is_asked_for(self) -> None:
        resources = MagicMock()
        resources.list_location_options.return_value = []

        _client(resources=resources).get(f"{PREFIX}/locations/options", params={"top_level_only": "true"})

        resources.list_location_options.assert_called_once_with(
            tenant_key=TENANT_KEY, offset=0, limit=50, is_bed=None, top_level_only=True
        )

    def test_the_page_size_is_bounded(self) -> None:
        response = _client(resources=MagicMock()).get(f"{PREFIX}/locations/options", params={"limit": 201})

        assert response.status_code == 422
