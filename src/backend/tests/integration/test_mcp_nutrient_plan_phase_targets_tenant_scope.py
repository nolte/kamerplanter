"""#2104 (MT-006) — the nutrient-plan dry run does not read the phase entries of a foreign plan.

``set_nutrient_plan_phase_targets`` resolved its phase through
``nutrient_plan_service.get_phase_entries(plan_key)``, which looked the plan up without a
tenant — so ``dry_run=true`` with another tenant's plan key returned ``preview.before`` (EC
values), the phase names, and the error text of an unknown phase listed the foreign plan's
phases. Measured through the real dispatcher, tool and service on a real ArangoDB.
"""

from __future__ import annotations

import pytest

from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import open_env, put

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def env():
    from app.data_access.arango import collections as col
    from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry

    e = open_env(run_database_name("mcp_plan_targets_scope"))
    for key, tenant in (("plan-a", "tenant-alice"), ("plan-b", "tenant-bob"), ("plan-global", "")):
        put(e.db, col.NUTRIENT_PLANS, NutrientPlan(_key=key, tenant_key=tenant, name=f"Plan {key}"))
        put(
            e.db,
            col.NUTRIENT_PLAN_PHASE_ENTRIES,
            NutrientPlanPhaseEntry(
                _key=f"entry-{key}",
                plan_key=key,
                phase_name="vegetative",
                sequence_order=1,
                week_start=1,
                week_end=4,
                target_ec_ms=1.9 if tenant == "tenant-bob" else 1.1,
            ),
        )
    yield e
    e.close()


def _principal():
    from app.common.enums import TenantRole
    from app.mcp_server.principal import McpPrincipal, McpTenantMembership

    member = McpTenantMembership(
        tenant_key="tenant-alice", tenant_slug="alice", tenant_name="Alice", role=TenantRole.LEAD
    )
    return McpPrincipal(account_key="user-a", display_name="Alice", memberships=(member,))


async def _dry_run(plan_key: str, phase: str = "vegetative"):
    from app.common.dependencies import get_mcp_dispatcher

    return await get_mcp_dispatcher().dispatch(
        _principal(),
        "set_nutrient_plan_phase_targets",
        {"plan_key": plan_key, "phase": phase, "target_ec_ms": 2.0, "dry_run": True},
    )


@pytest.mark.asyncio
async def test_a_foreign_plan_is_not_found_and_leaks_no_entry_data(env) -> None:
    from app.common.exceptions import NotFoundError

    with pytest.raises(NotFoundError) as caught:
        await _dry_run("plan-b")
    assert "1.9" not in str(caught.value) and "vegetative" not in str(caught.value)


@pytest.mark.asyncio
async def test_an_unknown_phase_of_a_foreign_plan_answers_like_an_unknown_plan(env) -> None:
    """The plan is resolved before the phase, so a foreign plan never reaches the phase list.

    Measured before the fix: the unknown-phase error carried the foreign plan's phase names
    in its cause (``It covers: vegetative``) while the response said only "failed inside the
    server" — the names reached the log, not the caller.
    """
    from app.common.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await _dry_run("plan-b", phase="flowering")
    with pytest.raises(NotFoundError):
        await _dry_run("plan-nowhere", phase="flowering")


@pytest.mark.asyncio
async def test_an_own_plan_still_previews_its_current_values(env) -> None:
    response = await _dry_run("plan-a")
    assert response.dry_run is True
    assert response.data["before"] == {"target_ec_ms": 1.1}


@pytest.mark.asyncio
async def test_a_global_plan_is_refused_on_the_dry_run_as_on_the_write(env) -> None:
    """The tool patches a plan the tenant owns; the dry run no longer promises more than execute (#1263)."""
    from app.common.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await _dry_run("plan-global")


def test_the_service_reads_the_entries_of_a_visible_plan_only(env) -> None:
    from app.common.dependencies import get_nutrient_plan_service
    from app.common.exceptions import NotFoundError

    service = get_nutrient_plan_service()
    assert [e.key for e in service.get_phase_entries("plan-a", tenant_key="tenant-alice")] == ["entry-plan-a"]
    assert [e.key for e in service.get_phase_entries("plan-global", tenant_key="tenant-alice")] == ["entry-plan-global"]
    with pytest.raises(NotFoundError):
        service.get_phase_entries("plan-b", tenant_key="tenant-alice")
