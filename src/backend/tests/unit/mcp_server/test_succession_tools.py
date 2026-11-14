"""MCP succession tools: the writes ``create_succession_plan`` / ``generate_succession_runs`` (#2776,
REQ-033 §2.4) and the reads ``list_succession_plans`` / ``get_succession_plan`` (REQ-033 §2.1).

Driven through the real :class:`ToolDispatcher`, the real ``SuccessionPlanService`` and the real
``PlantingRunService`` over repository doubles, so the refusals asserted here are the services' own. Every
refusal is asserted at the store as well.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.api.v1.succession_plans.schemas import SuccessionPlanCreate, SuccessionPlanResponse
from app.common.enums import McpPermission, SuccessionPlanStatus, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.succession_plan_service import SuccessionPlanService
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry, load_tools
from app.mcp_server.tools.runs import ListPlantingRuns
from app.mcp_server.tools.succession import (
    CreateSuccessionPlan,
    GenerateSuccessionRuns,
    GetSuccessionPlan,
    ListSuccessionPlans,
    _plan_detail,
)
from tests.unit.domain.services.test_planting_run_location_ownership import OWN, FakeSiteRepo
from tests.unit.domain.services.test_succession_plan_service import _FakeSuccessionRepo
from tests.unit.mcp_server.test_create_planting_run import _RunRepo, _species
from tests.unit.mcp_server.test_dispatcher import _FakeAuditRepo, _FakeIdempotencyRepo


class _PlanRepo(_FakeSuccessionRepo):
    """Plans as stored; ``verify_references`` refuses a cultivar the tenant may not bind (#948)."""

    def verify_references(self, plan) -> None:
        if plan.cultivar_key is not None and plan.cultivar_key != "cv_own":
            raise NotFoundError("Cultivar", plan.cultivar_key)

    def create(self, plan):
        self.verify_references(plan)
        return super().create(plan)


def _setup(role: TenantRole = TenantRole.GROWER):
    run_repo = _RunRepo()
    run_service = PlantingRunService(
        run_repo, MagicMock(), engine=PlantingRunEngine(), site_repo=FakeSiteRepo(), species_resolver=_species
    )
    plan_repo = _PlanRepo()
    service = SuccessionPlanService(plan_repo, run_service, site_repo=FakeSiteRepo(), species_resolver=_species)
    registry = ToolRegistry()
    for tool in (
        CreateSuccessionPlan(),
        GenerateSuccessionRuns(),
        ListPlantingRuns(),
        ListSuccessionPlans(),
        GetSuccessionPlan(),
    ):
        registry.register(tool)
    dispatcher = ToolDispatcher(
        registry,
        MCPAuditLogger(_FakeAuditRepo()),
        IdempotencyStore(_FakeIdempotencyRepo()),
        services={"succession_plan_service": service, "planting_run_service": run_service},
    )
    membership = McpTenantMembership(tenant_key=OWN, tenant_slug="own", tenant_name="Own", role=role)
    principal = McpPrincipal(account_key="sa-1", display_name="bot", is_service_account=True, memberships=(membership,))
    return dispatcher, principal, plan_repo, run_repo


_PLAN = {
    "name": "Salat",
    "species_key": "sp_own",
    "interval_days": 14,
    "start_date": "2027-04-01",
    "end_date": "2027-05-13",
    "plants_per_batch": 6,
    "location_key": "loc_own",
}


async def _created_plan(dispatcher, principal) -> str:
    response = await dispatcher.dispatch(principal, "create_succession_plan", _PLAN)
    return response.data["succession_plan_key"]


# ── Contract ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ["create_succession_plan", "generate_succession_runs"])
def test_the_tool_is_a_tenant_scoped_write_with_dry_run_and_idempotency(name: str):
    tool = load_tools().get(name)
    assert tool is not None
    assert tool.permission is McpPermission.WRITE
    assert tool.write and tool.tenant_scoped
    assert {"tenant", "dry_run", "idempotency_key"} <= set(tool.spec().input_schema["properties"])


def test_create_succession_plan_takes_what_the_rest_create_body_takes():
    call_fields = {"tenant", "dry_run", "idempotency_key"}
    assert set(CreateSuccessionPlan.Input.model_fields) - call_fields == set(SuccessionPlanCreate.model_fields)


# ── create_succession_plan ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_plan_dry_run_counts_the_batches_and_writes_nothing():
    dispatcher, principal, plans, _runs = _setup()

    response = await dispatcher.dispatch(principal, "create_succession_plan", {**_PLAN, "dry_run": True})

    assert response.dry_run is True
    assert response.data["total_batches"] == 4  # 1 Apr, 15 Apr, 29 Apr, 13 May
    assert plans._store == {}


@pytest.mark.asyncio
async def test_a_plan_is_created_in_the_bound_tenant():
    dispatcher, principal, plans, _runs = _setup()

    key = await _created_plan(dispatcher, principal)

    stored = plans._store[key]
    assert stored.tenant_key == OWN and stored.status is SuccessionPlanStatus.PLANNED and stored.total_batches == 4


@pytest.mark.asyncio
async def test_the_same_idempotency_key_creates_one_plan():
    dispatcher, principal, plans, _runs = _setup()
    args = {**_PLAN, "idempotency_key": "salat-2027"}

    first = await dispatcher.dispatch(principal, "create_succession_plan", args)
    second = await dispatcher.dispatch(principal, "create_succession_plan", args)

    assert len(plans._store) == 1
    assert second.idempotent_replay is True
    assert second.data["succession_plan_key"] == first.data["succession_plan_key"]


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [{"location_key": "loc_foreign"}, {"species_key": "sp_foreign"}, {"cultivar_key": "cv_foreign"}],
    ids=["location", "species", "cultivar"],
)
async def test_a_key_of_another_tenant_is_refused_and_nothing_is_stored(overrides, dry_run: bool):
    dispatcher, principal, plans, _runs = _setup()

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(principal, "create_succession_plan", {**_PLAN, **overrides, "dry_run": dry_run})

    assert plans._store == {}


@pytest.mark.asyncio
async def test_an_inverted_date_range_is_a_caller_error():
    dispatcher, principal, plans, _runs = _setup()

    with pytest.raises(ValidationError):
        await dispatcher.dispatch(principal, "create_succession_plan", {**_PLAN, "end_date": "2027-03-01"})

    assert plans._store == {}


@pytest.mark.asyncio
async def test_a_viewer_may_not_create_a_plan():
    dispatcher, principal, plans, _runs = _setup(TenantRole.VIEWER)

    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(principal, "create_succession_plan", _PLAN)

    assert plans._store == {}


# ── generate_succession_runs ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_generate_dry_run_lists_the_runs_and_writes_nothing():
    dispatcher, principal, plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)

    response = await dispatcher.dispatch(
        principal, "generate_succession_runs", {"succession_plan_key": key, "dry_run": True}
    )

    assert response.dry_run is True and response.data["generated_count"] == 4
    assert [item["planned_start_date"] for item in response.data["runs"]] == [
        "2027-04-01",
        "2027-04-15",
        "2027-04-29",
        "2027-05-13",
    ]
    assert all(item["run_key"] is None for item in response.data["runs"])
    assert runs.store == {} and runs.entries == []
    assert plans._store[key].completed_batches == 0


@pytest.mark.asyncio
async def test_generated_runs_are_listed_by_list_planting_runs():
    dispatcher, principal, plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)

    response = await dispatcher.dispatch(principal, "generate_succession_runs", {"succession_plan_key": key})

    assert response.data["generated_count"] == 4 and len(runs.store) == 4
    assert {run.succession_plan_key for run in runs.store.values()} == {key}
    assert all(run.tenant_key == OWN and run.location_key == "loc_own" for run in runs.store.values())
    listed = await dispatcher.dispatch(principal, "list_planting_runs", {})
    assert sorted(item["run_key"] for item in listed.data["items"]) == sorted(runs.store)
    assert plans._store[key].completed_batches == 4


@pytest.mark.asyncio
async def test_a_second_generation_creates_nothing_and_its_dry_run_says_so():
    dispatcher, principal, _plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)
    await dispatcher.dispatch(principal, "generate_succession_runs", {"succession_plan_key": key})

    preview = await dispatcher.dispatch(
        principal, "generate_succession_runs", {"succession_plan_key": key, "dry_run": True}
    )
    again = await dispatcher.dispatch(principal, "generate_succession_runs", {"succession_plan_key": key})

    assert preview.data["generated_count"] == 0 and again.data["generated_count"] == 0
    assert len(runs.store) == 4


@pytest.mark.asyncio
async def test_next_mode_creates_one_batch_at_a_time():
    dispatcher, principal, _plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)
    args = {"succession_plan_key": key, "mode": "next"}

    preview = await dispatcher.dispatch(principal, "generate_succession_runs", {**args, "dry_run": True})
    first = await dispatcher.dispatch(principal, "generate_succession_runs", args)
    second = await dispatcher.dispatch(principal, "generate_succession_runs", args)

    assert [item["succession_sequence"] for item in preview.data["runs"]] == [1]
    assert [item["succession_sequence"] for item in first.data["runs"]] == [1]
    assert [item["succession_sequence"] for item in second.data["runs"]] == [2]
    assert len(runs.store) == 2


@pytest.mark.asyncio
async def test_the_same_idempotency_key_generates_once():
    dispatcher, principal, _plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)
    args = {"succession_plan_key": key, "mode": "next", "idempotency_key": "batch-1"}

    await dispatcher.dispatch(principal, "generate_succession_runs", args)
    replay = await dispatcher.dispatch(principal, "generate_succession_runs", args)

    assert replay.idempotent_replay is True
    assert len(runs.store) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
async def test_another_tenants_plan_is_not_found_and_nothing_is_generated(dry_run: bool):
    dispatcher, principal, plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)
    plans._store[key] = plans._store[key].model_copy(update={"tenant_key": "tenant_foreign"})

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(
            principal, "generate_succession_runs", {"succession_plan_key": key, "dry_run": dry_run}
        )

    assert runs.store == {}


# ── Operational quotas (#2776 SEC-001) ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [True, False])
async def test_a_plan_over_the_batch_quota_is_refused_at_the_input_quickly(dry_run: bool):
    """Ten years sown daily (~3650 batches): refused before the tool runs, in well under a second."""
    import time

    dispatcher, principal, plans, runs = _setup()
    started = time.perf_counter()

    with pytest.raises(ValidationError, match="succession.quota_exceeded"):
        await dispatcher.dispatch(
            principal,
            "create_succession_plan",
            {**_PLAN, "interval_days": 1, "end_date": "2037-04-01", "dry_run": dry_run},
        )

    assert time.perf_counter() - started < 1.0
    assert plans._store == {} and runs.store == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [True, False])
async def test_a_stored_plan_over_the_quota_generates_nothing(dry_run: bool):
    """A row stored before the quota is not re-validated on read; generation refuses it before building runs."""
    from app.common.exceptions import PlanError

    dispatcher, principal, plans, runs = _setup()
    key = await _created_plan(dispatcher, principal)
    plans._store[key] = plans._store[key].model_copy(update={"interval_days": 1, "end_date": date(2029, 4, 1)})

    with pytest.raises(PlanError) as refused:
        await dispatcher.dispatch(
            principal, "generate_succession_runs", {"succession_plan_key": key, "dry_run": dry_run}
        )

    assert refused.value.error_code == "succession.quota_exceeded"
    assert runs.store == {}


# ── list_succession_plans / get_succession_plan (REQ-033 §2.1) ────────────────


@pytest.mark.parametrize("name", ["list_succession_plans", "get_succession_plan"])
def test_the_read_tool_is_a_tenant_scoped_read_without_write_arguments(name: str):
    tool = load_tools().get(name)
    assert tool is not None
    assert tool.permission is McpPermission.READ
    assert not tool.write and tool.tenant_scoped
    assert not {"dry_run", "idempotency_key"} & set(tool.spec().input_schema["properties"])


def test_get_succession_plan_returns_what_the_rest_detail_route_returns():
    """The REST ``SuccessionPlanResponse`` fields, ``key`` named as the write tools name it."""
    expected = (set(SuccessionPlanResponse.model_fields) - {"key"}) | {"succession_plan_key"}
    stored = _PlanRepo().create(
        SuccessionPlan(
            name="Salat",
            species_key="sp_own",
            interval_days=14,
            start_date=date(2027, 4, 1),
            end_date=date(2027, 5, 13),
            plants_per_batch=6,
            tenant_key=OWN,
        )
    )
    assert set(_plan_detail(stored)) == expected


@pytest.mark.asyncio
async def test_a_viewer_lists_and_reads_the_tenants_plans():
    dispatcher, principal, _plans, _runs = _setup()
    key = await _created_plan(dispatcher, principal)
    _dispatcher, viewer, _p, _r = _setup(TenantRole.VIEWER)  # same tenant, read-only role

    listed = await dispatcher.dispatch(viewer, "list_succession_plans", {})
    got = await dispatcher.dispatch(viewer, "get_succession_plan", {"succession_plan_key": key})

    assert listed.data["total"] == 1
    assert [item["succession_plan_key"] for item in listed.data["items"]] == [key]
    assert listed.data["items"][0]["total_batches"] == 4
    assert got.data["succession_plan_key"] == key
    assert got.data["start_date"] == "2027-04-01" and got.data["completed_batches"] == 0
    assert got.data["status"] == SuccessionPlanStatus.PLANNED


@pytest.mark.asyncio
async def test_list_succession_plans_pages_and_reports_the_total():
    dispatcher, principal, plans, _runs = _setup()
    keys = [await _created_plan(dispatcher, principal) for _ in range(3)]

    first = await dispatcher.dispatch(principal, "list_succession_plans", {"offset": 0, "limit": 2})
    second = await dispatcher.dispatch(principal, "list_succession_plans", {"offset": 2, "limit": 2})

    assert first.data["total"] == 3 and second.data["total"] == 3
    paged = [item["succession_plan_key"] for item in first.data["items"] + second.data["items"]]
    assert paged == keys and len(first.data["items"]) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("args", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_list_succession_plans_refuses_a_page_outside_its_caps(args: dict):
    dispatcher, principal, _plans, _runs = _setup()

    with pytest.raises(ValidationError):
        await dispatcher.dispatch(principal, "list_succession_plans", args)


@pytest.mark.asyncio
async def test_another_tenants_plan_is_neither_listed_nor_readable():
    dispatcher, principal, plans, _runs = _setup()
    own = await _created_plan(dispatcher, principal)
    foreign = await _created_plan(dispatcher, principal)
    plans._store[foreign] = plans._store[foreign].model_copy(update={"tenant_key": "tenant_foreign"})

    listed = await dispatcher.dispatch(principal, "list_succession_plans", {})

    assert listed.data["total"] == 1
    assert [item["succession_plan_key"] for item in listed.data["items"]] == [own]
    with pytest.raises(NotFoundError) as foreign_read:
        await dispatcher.dispatch(principal, "get_succession_plan", {"succession_plan_key": foreign})
    with pytest.raises(NotFoundError) as unknown_read:
        await dispatcher.dispatch(principal, "get_succession_plan", {"succession_plan_key": "sp_missing"})
    # Same error class and code for a foreign and an unknown key: nothing tells the two apart.
    assert foreign_read.value.error_code == unknown_read.value.error_code


@pytest.mark.asyncio
async def test_an_empty_plan_key_is_a_caller_error_not_a_lookup():
    dispatcher, principal, _plans, _runs = _setup()

    with pytest.raises(ValidationError):
        await dispatcher.dispatch(principal, "get_succession_plan", {"succession_plan_key": ""})
