"""REQ-033 tool-level tests — each tool delegates to its domain service (§2).

Uses a :class:`ToolContext` with injected fake services so no ArangoDB is
required. Verifies the LLM-friendly envelope (summary/data/links) and the
delegation call.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.enums import ReminderType, TenantRole
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.tools.care import ConfirmCareTask, GetDueCareTasks
from app.mcp_server.tools.harvest import GetHarvestReadiness
from app.mcp_server.tools.plants import ArchivePlant, SetPlantLocation
from app.mcp_server.tools.privacy import GetMcpActivity
from app.mcp_server.tools.runs import ListPlantingRuns
from app.mcp_server.tools.sites import CreateSite
from app.mcp_server.tools.species import GetSpeciesInfo, ListSpecies
from app.mcp_server.tools.tasks import ListTasks


def _principal() -> McpPrincipal:
    return McpPrincipal(
        service_account_key="sa-1",
        display_name="bot",
        tenant_key="home",
        tenant_slug="home",
        role=TenantRole.LEAD,
    )


def _ctx(**services) -> ToolContext:
    return ToolContext(_principal(), services=services)


@pytest.mark.asyncio
async def test_list_species_delegates_and_wraps():
    species = [
        SimpleNamespace(key="sp-1", scientific_name="Solanum lycopersicum", common_names=["Tomato"], genus="Solanum")
    ]
    svc = SimpleNamespace(list_species=lambda offset, limit: (species, 1))
    resp = await ListSpecies().run(_ctx(species_service=svc), ListSpecies.Input())
    assert resp.data["total"] == 1
    assert resp.data["items"][0]["species_key"] == "sp-1"
    assert any(link.type == "api" for link in resp.links)


@pytest.mark.asyncio
async def test_get_species_info_includes_companions():
    species = SimpleNamespace(
        key="sp-1", scientific_name="Basil", common_names=["Basil"], genus="Ocimum", growth_habit="herb"
    )
    svc = SimpleNamespace(
        get_species=lambda key: species,
        get_compatible_species=lambda key: [{"species_key": "sp-2"}],
    )
    resp = await GetSpeciesInfo().run(_ctx(species_service=svc), GetSpeciesInfo.Input(species_key="sp-1"))
    assert resp.data["compatible_companions"] == [{"species_key": "sp-2"}]


@pytest.mark.asyncio
async def test_list_planting_runs_passes_tenant_key():
    seen = {}

    def _list_runs(offset, limit, filters, tenant_key):
        seen["tenant_key"] = tenant_key
        seen["filters"] = filters
        return ([SimpleNamespace(key="run-1", name="Run", status="active", species_key="sp-1")], 1)

    svc = SimpleNamespace(list_runs=_list_runs)
    resp = await ListPlantingRuns().run(_ctx(planting_run_service=svc), ListPlantingRuns.Input(status="active"))
    assert seen["tenant_key"] == "home"
    assert seen["filters"] == {"status": "active"}
    assert resp.data["items"][0]["run_key"] == "run-1"


@pytest.mark.asyncio
async def test_list_tasks_delegates():
    svc = SimpleNamespace(
        list_tasks=lambda offset, limit, filters, tenant_key: (
            [
                SimpleNamespace(
                    key="t-1", title="Water", status="pending", priority="high", due_date=None, category="care"
                )
            ],
            1,
        )
    )
    resp = await ListTasks().run(_ctx(task_service=svc), ListTasks.Input(status="pending"))
    assert resp.data["items"][0]["task_key"] == "t-1"


@pytest.mark.asyncio
async def test_get_due_care_tasks_filters_actionable():
    entries = [
        SimpleNamespace(
            plant_key="p1", plant_name="A", species_name="S", reminder_type="watering", urgency="overdue", due_date=None
        ),
        SimpleNamespace(
            plant_key="p2",
            plant_name="B",
            species_name="S",
            reminder_type="watering",
            urgency="upcoming",
            due_date=None,
        ),
    ]
    svc = SimpleNamespace(get_care_dashboard_for_tenant=lambda tenant_key: entries)
    resp = await GetDueCareTasks().run(_ctx(care_reminder_service=svc), GetDueCareTasks.Input())
    assert resp.data["count"] == 1
    assert resp.data["items"][0]["plant_key"] == "p1"


@pytest.mark.asyncio
async def test_confirm_care_task_preview_and_execute():
    calls = {}

    def _confirm(plant_key, reminder_type, notes, tenant_key=""):
        calls["plant_key"] = plant_key
        calls["tenant_key"] = tenant_key
        return SimpleNamespace(key="cc-1")

    plant_svc = SimpleNamespace(get_plant=lambda key, tenant_key: SimpleNamespace(key=key))
    svc = SimpleNamespace(confirm_reminder=_confirm)
    ctx = _ctx(care_reminder_service=svc, plant_instance_service=plant_svc)
    tool = ConfirmCareTask()
    args = ConfirmCareTask.Input(plant_key="p1", reminder_type=ReminderType.WATERING)

    preview = await tool.preview(ctx, args)
    assert "Would confirm" in preview.summary
    assert calls == {}  # preview must not write

    result = await tool.execute(ctx, args)
    assert calls["plant_key"] == "p1"
    assert calls["tenant_key"] == "home"  # SEC-001: tenant threaded for defence-in-depth
    assert result.data["confirmation_key"] == "cc-1"


@pytest.mark.asyncio
async def test_confirm_care_task_rejects_foreign_plant_key():
    # SEC-001: a tenant-A caller must NOT be able to confirm a tenant-B plant.
    # get_plant fails closed (404) on a foreign/missing key, so no care state is
    # ever mutated across the tenant boundary.
    from app.common.exceptions import NotFoundError

    confirmed = {"called": False}

    def _confirm(plant_key, reminder_type, notes, tenant_key=""):
        confirmed["called"] = True
        return SimpleNamespace(key="cc-1")

    def _get_plant(key, tenant_key):
        raise NotFoundError("PlantInstance", key)

    plant_svc = SimpleNamespace(get_plant=_get_plant)
    svc = SimpleNamespace(confirm_reminder=_confirm)
    ctx = _ctx(care_reminder_service=svc, plant_instance_service=plant_svc)
    tool = ConfirmCareTask()
    args = ConfirmCareTask.Input(plant_key="foreign-plant", reminder_type=ReminderType.WATERING)

    with pytest.raises(NotFoundError):
        await tool.preview(ctx, args)
    with pytest.raises(NotFoundError):
        await tool.execute(ctx, args)
    assert confirmed["called"] is False  # no cross-tenant write happened


@pytest.mark.asyncio
async def test_archive_plant_delegates_to_remove_plant():
    calls = {}

    def _remove(key, *, termination_type, tenant_key):
        calls["key"] = key
        calls["tenant_key"] = tenant_key
        return SimpleNamespace(key=key, removed_on="2026-07-12")

    svc = SimpleNamespace(remove_plant=_remove, get_plant=lambda key, tenant_key: SimpleNamespace(key=key))
    tool = ArchivePlant()
    ctx = _ctx(plant_instance_service=svc)
    result = await tool.execute(ctx, ArchivePlant.Input(plant_key="pl-1"))
    assert calls["key"] == "pl-1"
    assert calls["tenant_key"] == "home"  # tenant isolation defence in depth
    assert result.data["removed_on"] == "2026-07-12"


@pytest.mark.asyncio
async def test_set_plant_location_updates_fields():
    plant = SimpleNamespace(key="pl-1", site_key="s0", location_key="l0", slot_key=None)
    updated = {}
    verified = {}

    def _update(key, p):
        updated["location_key"] = p.location_key
        return p

    def _get_location(key, tenant_key):
        verified["location_key"] = key
        verified["tenant_key"] = tenant_key
        return SimpleNamespace(key=key, tenant_key=tenant_key)

    plant_svc = SimpleNamespace(
        get_plant=lambda key, tenant_key: plant,
        update_plant=_update,
    )
    site_svc = SimpleNamespace(get_location=_get_location)
    tool = SetPlantLocation()
    result = await tool.execute(
        _ctx(plant_instance_service=plant_svc, site_service=site_svc),
        SetPlantLocation.Input(plant_key="pl-1", location_key="l9"),
    )
    assert updated["location_key"] == "l9"
    assert result.data["location_key"] == "l9"
    # SEC-002: the destination location was tenant-verified before assignment.
    assert verified == {"location_key": "l9", "tenant_key": "home"}


@pytest.mark.asyncio
async def test_set_plant_location_rejects_foreign_destination():
    # SEC-002: a foreign/missing destination location fails closed (404) and the
    # plant is never persisted onto it.
    from app.common.exceptions import NotFoundError

    plant = SimpleNamespace(key="pl-1", site_key="s0", location_key="l0", slot_key=None)
    updated = {"called": False}

    def _update(key, p):
        updated["called"] = True
        return p

    def _get_location(key, tenant_key):
        raise NotFoundError("Location", key)

    plant_svc = SimpleNamespace(get_plant=lambda key, tenant_key: plant, update_plant=_update)
    site_svc = SimpleNamespace(get_location=_get_location)
    tool = SetPlantLocation()
    ctx = _ctx(plant_instance_service=plant_svc, site_service=site_svc)
    args = SetPlantLocation.Input(plant_key="pl-1", location_key="foreign-loc")

    with pytest.raises(NotFoundError):
        await tool.preview(ctx, args)
    with pytest.raises(NotFoundError):
        await tool.execute(ctx, args)
    assert updated["called"] is False  # no cross-tenant move persisted


@pytest.mark.asyncio
async def test_create_site_sets_tenant_key():
    created = {}

    def _create(site):
        created["tenant_key"] = site.tenant_key
        site.key = "site-1"
        return site

    svc = SimpleNamespace(create_site=_create)
    tool = CreateSite()
    result = await tool.execute(_ctx(site_service=svc), CreateSite.Input(name="Balcony"))
    assert created["tenant_key"] == "home"
    assert result.data["site_key"] == "site-1"


@pytest.mark.asyncio
async def test_get_harvest_readiness_aggregates():
    plants = [
        SimpleNamespace(key="p1", removed_on=None),
        SimpleNamespace(key="p2", removed_on="2026-01-01"),  # archived → skipped
    ]
    harvest = SimpleNamespace(
        assess_readiness=lambda key: {"overall_score": 80, "recommendation": "harvest", "estimated_days": 0}
    )
    plant_svc = SimpleNamespace(list_plants=lambda offset, limit, tenant_key: (plants, 2))
    resp = await GetHarvestReadiness().run(
        _ctx(plant_instance_service=plant_svc, harvest_service=harvest), GetHarvestReadiness.Input()
    )
    assert resp.data["assessed"] == 1
    assert resp.data["ready_count"] == 1


@pytest.mark.asyncio
async def test_get_mcp_activity_reads_own_audit():
    entries = [
        SimpleNamespace(
            tool_name="list_species",
            status="ok",
            output_size_bytes=10,
            duration_ms=2,
            error_class=None,
            created_at=None,
        )
    ]
    repo = SimpleNamespace(list_for_service_account=lambda sa_key, limit: entries)
    resp = await GetMcpActivity().run(_ctx(mcp_audit_repo=repo), GetMcpActivity.Input())
    assert resp.data["count"] == 1
    assert resp.data["items"][0]["tool_name"] == "list_species"
