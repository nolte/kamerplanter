"""REQ-033 §2.2 — the two nutrient-plan writes from #1244.

#1244 measured what the "no plan editor" scope line from #931 §6 costs: a
correctly configured plant on a species-appropriate GLOBAL template whose every
phase carries `target_ec_ms: null`. For that plant the nutrient assessment's
tier 2 (plan target vs. actual supply) is structurally unreachable — a perfect
runoff-EC reading has nothing to compare against — and correcting the template
by hand edits master data shared across tenants.

`clone_nutrient_plan` + `set_nutrient_plan_phase_targets` are the smallest pair
that removes that cost. These tests pin the properties that make them stay short
of a plan editor, and the two resolution hazards that would otherwise be silent:
an ambiguous phase name, and an empty patch.

Ownership is deliberately NOT re-asserted here — it lives in
`update_phase_entry` (#1263) and has its own tests. What is asserted is that
these tools route through it rather than around it.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.nutrition import CloneNutrientPlan, SetNutrientPlanPhaseTargets


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


class _Plan:
    def __init__(self, key, name, tenant=""):
        self.key = key
        self.name = name
        self.tenant_key = tenant
        self.cloned_from_key = None


class _Entry:
    def __init__(self, key, phase, *, ec=None, ref=None, ws=1, we=4):
        self.key = key
        self.phase_name = phase
        self.week_start = ws
        self.week_end = we
        self.target_ec_ms = ec
        self.reference_ec_ms = ref


class _Service:
    """Records what the tools ask of it; nothing more permissive than the real one."""

    def __init__(self, plans, entries):
        self._plans = plans
        self._entries = entries
        self.cloned: list[tuple] = []
        self.updated: list[tuple] = []

    def get_plan(self, key, tenant_key="", *, for_write=False):
        if key not in self._plans:
            raise KeyError(key)
        return self._plans[key]

    def get_phase_entries(self, plan_key):
        return self._entries.get(plan_key, [])

    def clone_plan(self, source_key, new_name, author="", tenant_key=""):
        self.cloned.append((source_key, new_name, author, tenant_key))
        clone = _Plan("plan-copy", new_name, tenant_key)
        clone.cloned_from_key = source_key
        return clone

    def update_phase_entry(self, key, data, *, plan_key, tenant_key):
        self.updated.append((key, dict(data), plan_key, tenant_key))
        entry = next(e for es in self._entries.values() for e in es if e.key == key)
        for field, value in data.items():
            setattr(entry, field, value)
        return entry


GLOBAL_PLAN = _Plan("plan-global", "Yucca — Gardol", tenant="")
OWN_PLAN = _Plan("plan-own", "Yucca — meine Fassung", tenant="home")


def _service(entries=None):
    return _Service(
        {"plan-global": GLOBAL_PLAN, "plan-own": OWN_PLAN},
        entries if entries is not None else {"plan-own": [_Entry("e-veg", "vegetative")]},
    )


@pytest.mark.asyncio
class TestClone:
    async def test_a_global_template_can_be_copied_into_the_tenant(self):
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        result = await CloneNutrientPlan().execute(ctx, CloneNutrientPlan.Input(plan_key="plan-global"))

        (source, name, author, tenant) = svc.cloned[0]
        assert (source, tenant) == ("plan-global", "home")
        assert author.startswith("mcp:")
        assert result.data["cloned_from_key"] == "plan-global"

    async def test_the_copy_is_named_from_the_source_when_no_name_is_given(self):
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        await CloneNutrientPlan().execute(ctx, CloneNutrientPlan.Input(plan_key="plan-global"))

        assert svc.cloned[0][1] == "Yucca — Gardol (Kopie)"

    async def test_the_source_is_resolved_through_the_read_path(self):
        """`for_write=True` refuses global templates — cloning one is the point."""
        svc = _service()
        calls: list[dict] = []
        original = svc.get_plan

        def _spy(key, tenant_key="", *, for_write=False):
            calls.append({"for_write": for_write})
            return original(key, tenant_key, for_write=for_write)

        svc.get_plan = _spy  # type: ignore[method-assign]
        ctx = _ctx(nutrient_plan_service=svc)

        await CloneNutrientPlan().execute(ctx, CloneNutrientPlan.Input(plan_key="plan-global"))

        assert calls and all(c["for_write"] is False for c in calls)

    async def test_a_dry_run_writes_nothing(self):
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        result = await CloneNutrientPlan().preview(ctx, CloneNutrientPlan.Input(plan_key="plan-global"))

        assert svc.cloned == []
        assert result.data["source_is_global"] is True


@pytest.mark.asyncio
class TestSetTargets:
    async def test_a_phase_name_resolves_to_its_entry(self):
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        await SetNutrientPlanPhaseTargets().execute(
            ctx,
            SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="vegetative", target_ec_ms=1.4),
        )

        assert svc.updated == [("e-veg", {"target_ec_ms": 1.4}, "plan-own", "home")]

    async def test_an_entry_key_resolves_directly(self):
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        await SetNutrientPlanPhaseTargets().execute(
            ctx,
            SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="e-veg", target_ec_ms=1.4),
        )

        assert svc.updated[0][0] == "e-veg"

    async def test_it_routes_through_the_guarded_service_method(self):
        """Plan and tenant reach `update_phase_entry`, which is what refuses a
        foreign or global entry (#1263). A tool that passed neither would be
        rejected by the keyword-only signature — this pins that it passes the
        RIGHT ones."""
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        await SetNutrientPlanPhaseTargets().execute(
            ctx,
            SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="vegetative", target_ec_ms=1.4),
        )

        (_, _, plan_key, tenant_key) = svc.updated[0]
        assert (plan_key, tenant_key) == ("plan-own", "home")

    async def test_an_ambiguous_phase_name_is_refused_with_the_candidates(self):
        """Two entries may share a phase name with different week windows.
        Picking the first would patch one of two and the caller could not tell
        which."""
        svc = _service({"plan-own": [_Entry("e-a", "vegetative", ws=1, we=4), _Entry("e-b", "vegetative", ws=5, we=9)]})
        ctx = _ctx(nutrient_plan_service=svc)

        with pytest.raises(ValueError, match="occurs 2x"):
            await SetNutrientPlanPhaseTargets().execute(
                ctx,
                SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="vegetative", target_ec_ms=1.4),
            )

        assert svc.updated == []

    async def test_an_unknown_phase_names_the_ones_that_exist(self):
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        with pytest.raises(ValueError, match="vegetative"):
            await SetNutrientPlanPhaseTargets().execute(
                ctx,
                SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="flowering", target_ec_ms=1.4),
            )

    async def test_an_empty_patch_is_refused_rather_than_written(self):
        """Omitting a field means 'leave unchanged', so an all-omitted call has
        no meaning. Treating it as a no-op success would let a caller believe it
        had set something."""
        svc = _service()
        ctx = _ctx(nutrient_plan_service=svc)

        with pytest.raises(ValueError, match="Nothing to set"):
            await SetNutrientPlanPhaseTargets().execute(
                ctx, SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="vegetative")
            )

        assert svc.updated == []

    async def test_omitting_a_field_leaves_it_alone(self):
        """The tool can never clear a value — there is no way to spell 'set to null'."""
        svc = _service({"plan-own": [_Entry("e-veg", "vegetative", ec=None, ref=0.4)]})
        ctx = _ctx(nutrient_plan_service=svc)

        await SetNutrientPlanPhaseTargets().execute(
            ctx,
            SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="vegetative", target_ec_ms=1.4),
        )

        assert svc.updated[0][1] == {"target_ec_ms": 1.4}

    async def test_a_dry_run_shows_before_and_after_and_writes_nothing(self):
        svc = _service({"plan-own": [_Entry("e-veg", "vegetative", ec=None)]})
        ctx = _ctx(nutrient_plan_service=svc)

        result = await SetNutrientPlanPhaseTargets().preview(
            ctx,
            SetNutrientPlanPhaseTargets.Input(plan_key="plan-own", phase="vegetative", target_ec_ms=1.4),
        )

        assert svc.updated == []
        assert result.data["before"] == {"target_ec_ms": None}
        assert result.data["after"] == {"target_ec_ms": 1.4}


def test_both_tools_are_registered_as_writes():
    """A mutating tool under `mcp.read` is a silent privilege downgrade (SEC-006).

    The decorator asserts it at import time; this states the expected end state
    so a later permission change is a test failure rather than a quiet one.
    """
    from app.common.enums import McpPermission

    for tool in (CloneNutrientPlan, SetNutrientPlanPhaseTargets):
        assert tool.write is True
        assert tool.permission is McpPermission.WRITE
