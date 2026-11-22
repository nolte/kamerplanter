"""MCP ``create_location`` with a ``geometry``: the garden-plan path (#2776, REQ-033 §2.3 v1.12).

Driven through the real :class:`ToolDispatcher` and the real ``GardenPlanService`` over the faithful
in-memory plan repository of ``tests/support/garden_plan_fakes`` (it applies a write set the way the
transaction does: revision check first, then the writes). Every refusal also asserts ``repo.applied == []``:
a refusal that still wrote is the defect, not the error code.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.domain.services.garden_plan_service import GardenPlanService
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.base import McpToolError
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry
from app.mcp_server.tools.sites import CreateLocation
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.unit.mcp_server.test_dispatcher import _FakeAuditRepo, _FakeIdempotencyRepo


def _setup(role: TenantRole = TenantRole.LEAD):
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    repo = FakePlanRepo(sites)
    registry = ToolRegistry()
    registry.register(CreateLocation())
    dispatcher = ToolDispatcher(
        registry,
        MCPAuditLogger(_FakeAuditRepo()),
        IdempotencyStore(_FakeIdempotencyRepo()),
        services={"garden_plan_service": GardenPlanService(sites, repo)},
    )
    membership = McpTenantMembership(tenant_key=TENANT, tenant_slug="own", tenant_name="Own", role=role)
    principal = McpPrincipal(account_key="sa-1", display_name="bot", is_service_account=True, memberships=(membership,))
    return dispatcher, principal, repo, sites


def _bed(**overrides):
    return {"name": "Beet 6", "site_key": SITE, "location_type_key": "bed", "geometry": rect(4, 1), **overrides}


# ── Input rules ───────────────────────────────────────────────────────────────


def test_the_schema_publishes_the_geometry_shapes():
    schema = CreateLocation().spec().input_schema
    assert "geometry" in schema["properties"]
    assert {"RectGeometry", "CircleGeometry", "PolygonGeometry"} <= set(schema.get("$defs", {}))


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ({"name": "Room", "site_key": SITE}, "area_m2 is required"),
        (_bed(location_type_key=""), "needs a location_type_key"),
        (_bed(area_m2=8.0), "cannot be set together with a geometry"),
        (_bed(frost_exposed=True), "cannot be set together with a geometry"),
    ],
    ids=["no-geometry-no-area", "geometry-without-type", "geometry-with-area", "geometry-with-direct-field"],
)
def test_the_input_refuses_what_neither_path_can_take(args: dict, message: str):
    with pytest.raises(ValueError, match=message):
        CreateLocation.Input(**args)


# ── The plan path ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_bed_is_placed_through_the_plan_batch_and_answers_key_and_area():
    dispatcher, principal, repo, sites = _setup()

    response = await dispatcher.dispatch(principal, "create_location", _bed())

    (write,) = repo.applied
    assert write.expected_revision == write.basis_revision == 5  # the tool resolved the revision itself
    key = response.data["key"]
    assert key in repo.locations and repo.locations[key].site_key == SITE
    assert response.data["area_m2"] == 2.0
    assert response.data["bbox"] == [4.0, 1.0, 6.0, 2.0]
    assert response.data["plan_revision"] == sites.sites[SITE].plan.plan_revision


@pytest.mark.asyncio
async def test_a_dry_run_runs_the_plan_rules_and_writes_nothing():
    dispatcher, principal, repo, _sites = _setup()

    response = await dispatcher.dispatch(principal, "create_location", {**_bed(), "dry_run": True})

    assert response.dry_run is True
    assert response.data["key"] is None and response.data["area_m2"] == 2.0
    assert repo.applied == []


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    ("geometry", "code"),
    [(rect(9, 9, 4, 4), "geometry.outside_parent"), (rect(1, 1), "bed.overlap")],
    ids=["V-03-outside-boundary", "V-05-overlapping-bed"],
)
async def test_a_plan_rule_refusal_is_typed_and_keeps_its_code(geometry, code: str, dry_run: bool):
    dispatcher, principal, repo, _sites = _setup()
    repo.locations["bed_a"] = make_location("bed_a", geometry=rect(1, 1))

    with pytest.raises(McpToolError) as refused:
        await dispatcher.dispatch(principal, "create_location", {**_bed(geometry=geometry), "dry_run": dry_run})

    assert refused.value.error_code == "validation.error"
    assert code in {finding["code"] for finding in refused.value.error_details["findings"]}
    assert repo.applied == []


@pytest.mark.asyncio
async def test_a_revision_conflict_is_a_typed_refusal_and_is_not_retried():
    dispatcher, principal, repo, sites = _setup()
    original = repo.apply_plan_batch
    attempts: list[int] = []

    def concurrent_edit_first(write):
        attempts.append(write.expected_revision)
        site = sites.sites[SITE]
        sites.sites[SITE] = site.model_copy(
            update={"plan": site.plan.model_copy(update={"plan_revision": site.plan.plan_revision + 1})}
        )
        return original(write)

    repo.apply_plan_batch = concurrent_edit_first

    with pytest.raises(McpToolError) as refused:
        await dispatcher.dispatch(principal, "create_location", _bed())

    assert refused.value.error_code == "conflict.plan_revision"
    assert refused.value.status_code == 409
    assert refused.value.error_details == {"current_revision": 6}
    assert attempts == [5]  # one attempt, no silent retry
    assert repo.applied == []


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
async def test_another_tenants_site_is_not_found(dry_run: bool):
    dispatcher, principal, repo, _sites = _setup()

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(principal, "create_location", {**_bed(site_key="site_foreign"), "dry_run": dry_run})

    assert repo.applied == []


@pytest.mark.asyncio
async def test_an_unknown_parent_is_a_reference_finding():
    dispatcher, principal, repo, _sites = _setup()

    with pytest.raises(McpToolError) as refused:
        await dispatcher.dispatch(principal, "create_location", _bed(parent_location_key="nowhere"))

    assert "reference.not_found" in {finding["code"] for finding in refused.value.error_details["findings"]}
    assert repo.applied == []


@pytest.mark.asyncio
async def test_the_same_idempotency_key_places_one_bed():
    dispatcher, principal, repo, _sites = _setup()
    args = {**_bed(), "idempotency_key": "beet-6"}

    first = await dispatcher.dispatch(principal, "create_location", args)
    second = await dispatcher.dispatch(principal, "create_location", args)

    assert len(repo.applied) == 1
    assert second.idempotent_replay is True and second.data["key"] == first.data["key"]


@pytest.mark.asyncio
async def test_a_grower_may_not_call_the_setup_tool():
    dispatcher, principal, repo, _sites = _setup(TenantRole.GROWER)

    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(principal, "create_location", _bed())

    assert repo.applied == []


@pytest.mark.asyncio
async def test_an_invalid_shape_for_a_location_is_a_caller_error():
    """A point encloses no area; the batch refuses it as a finding, never as an internal failure."""
    dispatcher, principal, repo, _sites = _setup()

    with pytest.raises((McpToolError, ValidationError)):
        await dispatcher.dispatch(principal, "create_location", _bed(geometry={"kind": "point", "origin": [1, 1]}))

    assert repo.applied == []
