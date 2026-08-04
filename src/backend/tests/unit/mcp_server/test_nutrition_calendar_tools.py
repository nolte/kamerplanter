"""REQ-033 §2.1 — nutrient-plan and sowing-calendar read tools.

Pins the two properties that are easy to break silently: the tenant/ownership
guards on services that carry no tenant of their own, and the size discipline on
the sowing calendar (which otherwise returns the entire species catalogue).
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, ValidationError
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.calendar import GetSowingCalendar
from app.mcp_server.tools.nutrition import GetNutrientPlan, GetPlantNutrientPlan, ListNutrientPlans


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


class _Plan:
    def __init__(self, key, name, *, tenant="home", tags=None):
        self.key = key
        self.name = name
        self.tenant_key = tenant
        self.description = ""
        self.is_template = False
        self.recommended_substrate_type = None
        self.version = "1.0"
        self.tags = tags or []


class _Entry:
    def __init__(self, phase, order, *, ec=1.2, npk=(3.0, 1.0, 2.0)):
        self.phase_name = phase
        self.sequence_order = order
        self.week_start = order
        self.week_end = order + 1
        self.is_recurring = False
        self.npk_ratio = npk
        self.target_ec_ms = ec
        self.calcium_ppm = None
        self.magnesium_ppm = 50.0
        self.sulfur_ppm = None
        self.iron_ppm = None


class _NutrientService:
    def __init__(self, plans, entries=None, plant_plan=None):
        self._plans = plans
        self._entries = entries or []
        self._plant_plan = plant_plan
        self.seen_tenant = None

    def list_plans(self, offset=0, limit=50, tenant_key=""):
        self.seen_tenant = tenant_key
        return self._plans, len(self._plans)

    def get_plan(self, key, tenant_key="", *, for_write=False):
        self.seen_tenant = tenant_key
        for p in self._plans:
            if p.key == key:
                return p
        raise NotFoundError("NutrientPlan", key)

    def get_phase_entries(self, plan_key):
        return self._entries

    def get_plant_plan(self, plant_key):
        return self._plant_plan


class _PlantService:
    def __init__(self, plants):
        self._plants = plants
        self.seen_tenant = None

    def get_plant(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        for p in self._plants:
            if p.key == key:
                return p
        raise NotFoundError("PlantInstance", key)


class _Plant:
    def __init__(self, key, name):
        self.key = key
        self.plant_name = name
        self.instance_id = f"INST-{key}"


# ── Nutrient plans ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_nutrient_plans_is_tenant_scoped_and_marks_global_templates():
    svc = _NutrientService([_Plan("np1", "Tomate Bio"), _Plan("np2", "Standard", tenant="")])
    resp = await ListNutrientPlans().run(_ctx(nutrient_plan_service=svc), ListNutrientPlans.Input())

    assert svc.seen_tenant == "home"
    by_key = {i["plan_key"]: i for i in resp.data["items"]}
    # An empty tenant_key is the global marker — the hybrid catalogue must stay
    # distinguishable, otherwise a model cannot tell a template from own data.
    assert by_key["np1"]["is_global_template"] is False
    assert by_key["np2"]["is_global_template"] is True


@pytest.mark.asyncio
async def test_get_nutrient_plan_returns_phases_in_sequence_order():
    entries = [_Entry("flowering", 2), _Entry("vegetative", 1)]
    svc = _NutrientService([_Plan("np1", "Tomate Bio")], entries=entries)
    resp = await GetNutrientPlan().run(_ctx(nutrient_plan_service=svc), GetNutrientPlan.Input(plan_key="np1"))

    assert [p["phase_name"] for p in resp.data["phases"]] == ["vegetative", "flowering"]
    first = resp.data["phases"][0]
    assert first["npk_ratio"] == [3.0, 1.0, 2.0]
    assert first["target_ec_ms"] == 1.2
    # Unset secondary nutrients are omitted rather than returned as nulls.
    assert "magnesium_ppm" in first
    assert "calcium_ppm" not in first


@pytest.mark.asyncio
async def test_get_plant_nutrient_plan_checks_plant_ownership_first():
    # get_plant_plan carries no tenant, so ownership has to be established on the
    # plant — otherwise a foreign plant_key would leak its plan.
    plants = _PlantService([_Plant("p1", "Tomate")])
    svc = _NutrientService([], entries=[_Entry("vegetative", 1)], plant_plan=_Plan("np1", "Tomate Bio"))

    resp = await GetPlantNutrientPlan().run(
        _ctx(plant_instance_service=plants, nutrient_plan_service=svc),
        GetPlantNutrientPlan.Input(plant_key="p1"),
    )
    assert plants.seen_tenant == "home"
    assert resp.data["plan_key"] == "np1"
    assert len(resp.data["phases"]) == 1


@pytest.mark.asyncio
async def test_get_plant_nutrient_plan_says_so_when_none_is_assigned():
    plants = _PlantService([_Plant("p1", "Tomate")])
    svc = _NutrientService([], plant_plan=None)
    resp = await GetPlantNutrientPlan().run(
        _ctx(plant_instance_service=plants, nutrient_plan_service=svc),
        GetPlantNutrientPlan.Input(plant_key="p1"),
    )
    assert resp.data["plan"] is None
    assert "No nutrient plan" in resp.summary


# ── Sowing calendar ───────────────────────────────────────────────────────────
class _Bar:
    def __init__(self, phase):
        self.phase = phase
        self.start_date = date(2026, 3, 1)
        self.end_date = date(2026, 4, 1)
        self.label = phase


class _CalEntry:
    def __init__(self, key, sci, common=""):
        self.species_key = key
        self.species_name = sci
        self.common_name = common
        self.bars = [_Bar("indoor_sowing")]


class _Frost:
    last_frost_date = date(2026, 5, 15)
    first_frost_date = date(2026, 10, 15)
    eisheilige_date = date(2026, 5, 15)


class _CalendarService:
    def __init__(self, entries):
        self._entries = entries
        self.seen = None

    def get_sowing_calendar(self, site_key, year):
        self.seen = (site_key, year)
        return self._entries, _Frost()


class _SiteService:
    def __init__(self, allowed_key="site-1"):
        self._allowed = allowed_key
        self.seen_tenant = None

    def get_site(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        if key != self._allowed:
            raise NotFoundError("Site", key)
        return type("S", (), {"key": key})()


@pytest.mark.asyncio
async def test_sowing_calendar_filters_by_species_name():
    cal = _CalendarService([_CalEntry("sp1", "Solanum lycopersicum", "Tomate"), _CalEntry("sp2", "Ocimum basilicum")])
    resp = await GetSowingCalendar().run(_ctx(calendar_service=cal), GetSowingCalendar.Input(query="tomate", year=2026))
    assert [i["species_key"] for i in resp.data["items"]] == ["sp1"]
    assert resp.data["frost"]["last_frost_date"] == date(2026, 5, 15)


@pytest.mark.asyncio
async def test_sowing_calendar_refuses_an_unfiltered_catalogue_dump():
    # Silently truncating would read like a complete calendar and mislead.
    cal = _CalendarService([_CalEntry(f"sp{i}", f"Species {i}") for i in range(40)])
    with pytest.raises(ValidationError):
        await GetSowingCalendar().run(_ctx(calendar_service=cal), GetSowingCalendar.Input(year=2026))


@pytest.mark.asyncio
async def test_sowing_calendar_verifies_site_ownership_before_reading_runs():
    # A site_key pulls in that site's planting runs, so a foreign key must never
    # reach the engine.
    cal = _CalendarService([_CalEntry("sp1", "Solanum lycopersicum")])
    sites = _SiteService(allowed_key="site-1")
    ctx = _ctx(calendar_service=cal, site_service=sites)

    ok = await GetSowingCalendar().run(ctx, GetSowingCalendar.Input(site_key="site-1", year=2026))
    assert sites.seen_tenant == "home"
    assert cal.seen == ("site-1", 2026)
    assert ok.data["count"] == 1

    with pytest.raises(NotFoundError):
        await GetSowingCalendar().run(ctx, GetSowingCalendar.Input(site_key="site-of-someone-else", year=2026))


@pytest.mark.asyncio
async def test_sowing_calendar_defaults_to_the_current_year():
    from app.common.datetimes import today_utc

    cal = _CalendarService([_CalEntry("sp1", "Solanum lycopersicum")])
    await GetSowingCalendar().run(_ctx(calendar_service=cal), GetSowingCalendar.Input())
    assert cal.seen == (None, today_utc().year)
