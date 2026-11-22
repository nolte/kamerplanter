"""MCP ``create_planting_run`` (#2775, REQ-033 §2.4, AC-17, AC-18, AC-19).

Driven through the real :class:`ToolDispatcher` and the real ``PlantingRunService`` and
``PlantingRunEngine`` over repository doubles, so the refusals asserted here are the
service's own — a stubbed service could only show that the tool calls it. Every refusal is
asserted at the store as well: a ``pytest.raises`` alone would pass for a refusal that came
after a write.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import model_validator

from app.api.v1.planting_runs.schemas import EntryCreate, PlantingRunCreate
from app.common.enums import McpPermission, PlantingRunStatus, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.planting_run import PlantingRun
from app.domain.services.planting_run_service import PlantingRunService
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.base import McpToolError
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry, load_tools
from app.mcp_server.tools import runs as runs_module
from app.mcp_server.tools.runs import CreatePlantingRun, ListPlantingRuns, PlantingRunEntryInput
from tests.unit.domain.services.test_planting_run_location_ownership import OWN, FakeRunRepo, FakeSiteRepo
from tests.unit.mcp_server.test_dispatcher import _FakeAuditRepo, _FakeIdempotencyRepo

_READABLE_SPECIES = {"sp_global", "sp_own"}
_OWN_CULTIVARS = {"cv_own"}


def _species(key: str, *, tenant_key: str) -> None:
    if key not in _READABLE_SPECIES:
        raise NotFoundError("Species", key)


class _RunRepo(FakeRunRepo):
    """Runs and entries as stored; lists the tenant's runs the way ``list_planting_runs`` reads them."""

    def verify_entry_references(self, entry) -> None:
        if entry.cultivar_key is not None and entry.cultivar_key not in _OWN_CULTIVARS:
            raise NotFoundError("Cultivar", entry.cultivar_key)

    def get_all(self, offset, limit, filters=None, *, tenant_key=""):
        runs = [run for run in self.store.values() if run.tenant_key == tenant_key]
        return runs[offset : offset + limit], len(runs)


def _setup(role: TenantRole = TenantRole.GROWER):
    repo = _RunRepo()
    service = PlantingRunService(
        repo, MagicMock(), engine=PlantingRunEngine(), site_repo=FakeSiteRepo(), species_resolver=_species
    )
    registry = ToolRegistry()
    registry.register(CreatePlantingRun())
    registry.register(ListPlantingRuns())
    dispatcher = ToolDispatcher(
        registry,
        MCPAuditLogger(_FakeAuditRepo()),
        IdempotencyStore(_FakeIdempotencyRepo()),
        services={"planting_run_service": service},
    )
    membership = McpTenantMembership(tenant_key=OWN, tenant_slug="own", tenant_name="Own", role=role)
    principal = McpPrincipal(account_key="sa-1", display_name="bot", is_service_account=True, memberships=(membership,))
    return dispatcher, principal, repo


def _args(**overrides):
    args = {
        "name": "Tomaten Beet A",
        "run_type": "monoculture",
        "location_key": "loc_own",
        "planned_start_date": "2027-04-01",
        "entries": [{"species_key": "sp_own", "quantity": 6, "id_prefix": "TOM"}],
    }
    args.update(overrides)
    return args


# ── Contract ──────────────────────────────────────────────────────────────────


def test_the_tool_is_registered_as_a_tenant_scoped_write():
    tool = load_tools().get("create_planting_run")
    assert tool is not None
    assert tool.permission is McpPermission.WRITE
    assert tool.write and tool.tenant_scoped
    properties = tool.spec().input_schema["properties"]
    assert {"dry_run", "idempotency_key", "tenant", "name", "run_type", "entries"} <= set(properties)


def test_the_input_mirrors_the_rest_create_body():
    """The tool takes what ``POST /planting-runs`` takes — no field more, none less."""
    call_fields = {"tenant", "dry_run", "idempotency_key"}
    assert set(CreatePlantingRun.Input.model_fields) - call_fields == set(PlantingRunCreate.model_fields)
    assert set(PlantingRunEntryInput.model_fields) == set(EntryCreate.model_fields)


# ── AC-17 / AC-18 / AC-19 ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_a_monoculture_run_is_created_in_the_bound_tenant_and_listed():
    dispatcher, principal, repo = _setup()

    response = await dispatcher.dispatch(
        principal, "create_planting_run", _args(planned_from="2027-04-01", planned_until="2027-09-30")
    )

    (stored,) = repo.store.values()
    assert stored.tenant_key == OWN
    assert stored.status is PlantingRunStatus.PLANNED
    assert stored.planned_quantity == 6
    assert [(e.species_key, e.quantity, e.run_key) for e in repo.entries] == [("sp_own", 6, stored.key)]
    assert response.data["run_key"] == stored.key
    assert response.data["planned_until"] == "2027-09-30"

    listed = await dispatcher.dispatch(principal, "list_planting_runs", {})
    assert [item["run_key"] for item in listed.data["items"]] == [stored.key]


@pytest.mark.asyncio
async def test_a_dry_run_validates_and_writes_nothing():
    dispatcher, principal, repo = _setup()

    response = await dispatcher.dispatch(principal, "create_planting_run", _args(dry_run=True))

    assert response.dry_run is True
    assert response.data["planned_quantity"] == 6
    assert response.data["planned_from"] == "2027-04-01"
    assert repo.store == {} and repo.entries == []


@pytest.mark.asyncio
async def test_the_same_idempotency_key_creates_one_run():
    dispatcher, principal, repo = _setup()
    args = _args(idempotency_key="plan-2027-bed-a")

    first = await dispatcher.dispatch(principal, "create_planting_run", args)
    second = await dispatcher.dispatch(principal, "create_planting_run", args)

    assert len(repo.store) == 1
    assert second.idempotent_replay is True
    assert second.data["run_key"] == first.data["run_key"]


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
async def test_a_run_with_several_entries_is_refused_as_a_caller_error(dry_run: bool):
    """A mixed culture is separate runs (REQ-013 v2.0) — one run with two entries is a 422, not a 500."""
    dispatcher, principal, repo = _setup()
    entries = [
        {"species_key": "sp_own", "quantity": 6, "id_prefix": "TOM"},
        {"species_key": "sp_global", "quantity": 4, "id_prefix": "BAS"},
    ]

    with pytest.raises(ValidationError, match="exactly one entry"):
        await dispatcher.dispatch(principal, "create_planting_run", _args(entries=entries, dry_run=dry_run))

    assert repo.store == {} and repo.entries == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [{"run_type": "mixed_culture"}, {"run_type": "clone"}],
    ids=["mixed-culture-type", "clone-without-mother-plant"],
)
async def test_an_invalid_run_type_is_refused_at_the_input(overrides):
    """Typed ``validation.error`` before the tool runs — not the internal failure a domain-model refusal was."""
    dispatcher, principal, repo = _setup()

    with pytest.raises(ValidationError):
        await dispatcher.dispatch(principal, "create_planting_run", _args(**overrides))

    assert repo.store == {}


# ── Tenant of every key (#1868, #1872) ────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize(
    "overrides",
    [
        {"location_key": "loc_foreign"},
        {"entries": [{"species_key": "sp_foreign", "quantity": 1, "id_prefix": "AB"}]},
        {"entries": [{"species_key": "sp_own", "cultivar_key": "cv_foreign", "quantity": 1, "id_prefix": "AB"}]},
    ],
    ids=["location", "species", "cultivar"],
)
async def test_a_key_of_another_tenant_is_refused_and_nothing_is_stored(overrides, dry_run: bool):
    dispatcher, principal, repo = _setup()

    with pytest.raises(NotFoundError):
        await dispatcher.dispatch(principal, "create_planting_run", _args(dry_run=dry_run, **overrides))

    assert repo.store == {} and repo.entries == []


@pytest.mark.asyncio
async def test_a_viewer_cannot_create_a_run():
    dispatcher, principal, repo = _setup(TenantRole.VIEWER)

    with pytest.raises(ForbiddenError):
        await dispatcher.dispatch(principal, "create_planting_run", _args())

    assert repo.store == {}


@pytest.mark.asyncio
async def test_a_run_without_entries_is_a_planned_reservation():
    """``POST /planting-runs`` allows it (entries come later via ``/entries``); the tool does too."""
    dispatcher, principal, repo = _setup()

    response = await dispatcher.dispatch(
        principal, "create_planting_run", _args(entries=None, reserved_area_m2=1.5, plan_role="green_manure")
    )

    (stored,) = repo.store.values()
    assert (stored.planned_quantity, stored.reserved_area_m2, repo.entries) == (0, 1.5, [])
    assert response.data["entries"] == []


class _StricterRun(PlantingRun):
    """A domain rule the input does not mirror — what a future drift between the two would look like."""

    @model_validator(mode="after")
    def _refuse(self) -> _StricterRun:
        raise ValueError("a rule only the domain model knows")


@pytest.mark.asyncio
@pytest.mark.parametrize("dry_run", [False, True])
async def test_a_domain_model_refusal_is_a_validation_error_not_an_internal_failure(monkeypatch, dry_run: bool):
    monkeypatch.setattr(runs_module, "PlantingRun", _StricterRun)
    dispatcher, principal, repo = _setup()

    with pytest.raises(ValidationError) as caught:
        await dispatcher.dispatch(principal, "create_planting_run", _args(dry_run=dry_run))

    assert not isinstance(caught.value, McpToolError)
    assert caught.value.error_code == "VALIDATION_ERROR"
    assert repo.store == {}
