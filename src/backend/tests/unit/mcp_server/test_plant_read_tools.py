"""REQ-033 §2.1 — plant read tools.

These tools exist to close the addressing gap: every write tool takes a
``plant_key``, and before them only plants with a pending care task ever exposed
one. The tests below pin the two properties that matter — the tenant-scoped
delegation, and the filtering that makes a plant findable by name.

Fake services throughout, so no ArangoDB is involved.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.common.enums import ReminderType, TenantRole
from app.common.exceptions import ValidationError
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.plant_reads import (
    GetPlant,
    GetPlantCareLog,
    ListPlants,
    ListPlantsAtLocation,
)


class _Plant:
    def __init__(self, key, name=None, *, species="sp-tomato", location=None, slot=None, site=None, removed=None):
        self.key = key
        self.instance_id = f"INST-{key}"
        self.plant_name = name
        self.species_key = species
        self.cultivar_key = None
        self.site_key = site
        self.location_key = location
        self.slot_key = slot
        self.planted_on = date(2026, 4, 1)
        self.removed_on = removed
        self.current_phase_key = "vegetative"


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


class _PlantService:
    """Records the tenant it was asked for, so isolation is assertable."""

    def __init__(self, plants):
        self._plants = plants
        self.seen_tenant = None

    def list_plants(self, offset=0, limit=50, tenant_key=""):
        self.seen_tenant = tenant_key
        page = self._plants[offset : offset + limit]
        return page, len(self._plants)

    def get_plant(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        for p in self._plants:
            if p.key == key:
                return p
        from app.common.exceptions import NotFoundError

        raise NotFoundError("PlantInstance", key)


@pytest.mark.asyncio
async def test_list_plants_is_tenant_scoped():
    svc = _PlantService([_Plant("p1", "Tomate"), _Plant("p2", "Basilikum")])
    tool = ListPlants()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input())
    assert svc.seen_tenant == "home"
    assert resp.data["count"] == 2
    assert {i["plant_key"] for i in resp.data["items"]} == {"p1", "p2"}


@pytest.mark.asyncio
async def test_list_plants_filters_by_name_so_a_plant_becomes_addressable():
    # The point of the query filter: turn "my tomato" into a plant_key the write
    # tools can consume.
    svc = _PlantService([_Plant("p1", "Tomate Nord"), _Plant("p2", "Basilikum")])
    tool = ListPlants()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input(query="tomate"))
    assert [i["plant_key"] for i in resp.data["items"]] == ["p1"]


@pytest.mark.asyncio
async def test_list_plants_hides_archived_unless_asked():
    svc = _PlantService([_Plant("p1", "Alt", removed=date(2026, 5, 1)), _Plant("p2", "Neu")])
    tool = ListPlants()

    default = await tool.run(_ctx(plant_instance_service=svc), tool.Input())
    assert [i["plant_key"] for i in default.data["items"]] == ["p2"]

    with_archived = await tool.run(_ctx(plant_instance_service=svc), tool.Input(include_archived=True))
    assert {i["plant_key"] for i in with_archived.data["items"]} == {"p1", "p2"}


@pytest.mark.asyncio
async def test_get_plant_returns_master_data_and_resolves_the_species_name():
    svc = _PlantService([_Plant("p1", "Tomate")])
    species = type("S", (), {"scientific_name": "Solanum lycopersicum", "common_names": ["Tomate"]})()
    ctx = _ctx(plant_instance_service=svc, species_service=type("X", (), {"get_species": lambda self, k: species})())
    tool = GetPlant()

    resp = await tool.run(ctx, tool.Input(plant_key="p1"))
    assert svc.seen_tenant == "home"
    assert resp.data["species_name"] == "Solanum lycopersicum"
    assert resp.data["plant_key"] == "p1"


@pytest.mark.asyncio
async def test_get_plant_survives_a_missing_catalogue_entry():
    # A dangling species reference must not turn a plant read into an error.
    svc = _PlantService([_Plant("p1", "Tomate")])

    class _Broken:
        def get_species(self, key):
            raise RuntimeError("catalogue unavailable")

    resp = await GetPlant().run(
        _ctx(plant_instance_service=svc, species_service=_Broken()),
        GetPlant.Input(plant_key="p1"),
    )
    assert resp.data["species_name"] is None
    assert resp.data["plant_key"] == "p1"


@pytest.mark.asyncio
async def test_list_plants_at_location_filters_on_the_given_level():
    svc = _PlantService(
        [
            _Plant("p1", "Beet-2-A", location="loc-beet-2"),
            _Plant("p2", "Beet-3-A", location="loc-beet-3"),
        ]
    )
    tool = ListPlantsAtLocation()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input(location_key="loc-beet-2"))
    assert [i["plant_key"] for i in resp.data["items"]] == ["p1"]


@pytest.mark.asyncio
async def test_list_plants_at_location_requires_a_filter():
    # Without one it would silently degrade into "list everything", which is what
    # list_plants is for — refuse instead of answering a different question.
    svc = _PlantService([_Plant("p1", "X")])
    with pytest.raises(ValidationError):
        await ListPlantsAtLocation().run(_ctx(plant_instance_service=svc), ListPlantsAtLocation.Input())


@pytest.mark.asyncio
async def test_care_log_checks_plant_ownership_before_reading_history():
    # get_confirmation_history takes no tenant, so the ownership check has to
    # happen on the plant first — otherwise a foreign key would leak its history.
    svc = _PlantService([_Plant("p1", "Tomate")])
    calls = {}

    class _Care:
        def get_confirmation_history(self, plant_key, reminder_type=None, limit=50):
            calls["args"] = (plant_key, reminder_type, limit)
            return [
                type(
                    "C",
                    (),
                    {
                        "confirmed_at": datetime(2026, 8, 1, 9, 0),
                        "reminder_type": ReminderType.WATERING,
                        "action": "done",
                        "notes": None,
                        "interval_at_time": 5,
                    },
                )()
            ]

    tool = GetPlantCareLog()
    resp = await tool.run(
        _ctx(plant_instance_service=svc, care_reminder_service=_Care()),
        tool.Input(plant_key="p1", reminder_type=ReminderType.WATERING),
    )

    assert svc.seen_tenant == "home"  # ownership verified against the acting tenant
    assert calls["args"] == ("p1", ReminderType.WATERING, 50)
    assert resp.data["count"] == 1


@pytest.mark.asyncio
async def test_care_log_says_so_when_nothing_was_recorded():
    svc = _PlantService([_Plant("p1", "Tomate")])

    class _Empty:
        def get_confirmation_history(self, plant_key, reminder_type=None, limit=50):
            return []

    resp = await GetPlantCareLog().run(
        _ctx(plant_instance_service=svc, care_reminder_service=_Empty()),
        GetPlantCareLog.Input(plant_key="p1"),
    )
    assert resp.data["count"] == 0
    assert "No care recorded yet" in resp.summary
