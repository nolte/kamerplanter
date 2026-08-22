"""REQ-033 — `validate_nutrient_plan_coverage`, item 3 of #1244.

The defect it makes visible is real and measured in
`app/domain/engines/nutrient_plan_engine.py:28`:

    # Fallback without phase name constraint (week range only)
    for entry in sorted_entries:
        if entry.week_start <= current_week <= entry.week_end:
            return entry

When no phase entry's NAME matches the plant's phase, the engine silently
returns whatever entry the calendar week lands in, and the return value carries
no indication of which branch matched. So a plant fed from the wrong phase looks
exactly like one fed from the right one. This tool is the reportable version of
that.

Read-only: it adds no write surface. Its whole contribution is turning a silent
mismatch into a named one.
"""

from __future__ import annotations

import pytest

from app.common.enums import McpPermission, TenantRole
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.nutrition import ValidateNutrientPlanCoverage


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


class _Plant:
    def __init__(self, species_key="sp-yucca"):
        self.key = "plant-1"
        self.plant_name = "Yucca"
        self.instance_id = "YUCCA-0617-DIJ"
        self.species_key = species_key


class _Plan:
    def __init__(self, tenant=""):
        self.key = "plan-1"
        self.name = "Yucca — Gardol"
        self.tenant_key = tenant


class _Entry:
    def __init__(self, phase, ec=None):
        self.key = f"e-{phase}"
        self.phase_name = phase
        self.week_start = 1
        self.week_end = 9
        self.target_ec_ms = ec


class _Sequence:
    key = "seq-1"


def _services(*, entries, sequence_phases, current_phase, plan=None):
    class _PlantService:
        def get_plant(self, key, tenant_key=""):
            return _Plant()

    class _PlanService:
        def get_plant_plan(self, plant_key, *, tenant_key):
            # Parameter NAME matters: `test_mcp_service_doubles_match_their_service`
            # compares it against the real signature, because a double that
            # accepts a call the service rejects makes the test certify nothing.
            return plan if plan is not None else _Plan()

        def get_phase_entries(self, plan_key):
            return entries

    class _PhaseService:
        def get_current_phase(self, key):
            return {"phase": current_phase} if current_phase else {}

    class _SequenceService:
        def get_sequence_by_species(self, species_key):
            return _Sequence() if sequence_phases is not None else None

        def get_full_sequence(self, key):
            return {"entries": [{"phase_definition": {"name": n}} for n in (sequence_phases or [])]}

    # The KEYS are the ones `ToolContext._service` looks up, not the property
    # names: `ctx.plant_service` resolves "plant_instance_service". Getting one
    # wrong does not fail loudly — `_service` falls through to the real factory
    # in `dependencies`, which opens a live ArangoDB connection. The unit-tier
    # db guard caught exactly that here.
    return {
        "plant_instance_service": _PlantService(),
        "nutrient_plan_service": _PlanService(),
        "phase_service": _PhaseService(),
        "phase_sequence_service": _SequenceService(),
    }


@pytest.mark.asyncio
class TestCoverage:
    async def test_the_measured_case_is_reported(self):
        """#1244's plant: phase `active_growth`, plan names only `vegetative`,
        every phase without a target EC."""
        ctx = _ctx(
            **_services(
                entries=[_Entry("vegetative"), _Entry("flowering")],
                sequence_phases=["active_growth", "dormancy"],
                current_phase="active_growth",
            )
        )

        result = await ValidateNutrientPlanCoverage().run(ctx, ValidateNutrientPlanCoverage.Input(plant_key="plant-1"))

        assert result.data["current_phase_covered_by_name"] is False
        assert result.data["phases_not_covered_by_name"] == ["active_growth", "dormancy"]
        assert result.data["phases_without_target_ec"] == ["flowering", "vegetative"]

    async def test_the_summary_names_the_consequence_not_just_the_fact(self):
        """A report saying 'not covered' leaves the reader to work out why it
        matters. The silent week-range fallback is the reason."""
        ctx = _ctx(
            **_services(
                entries=[_Entry("vegetative", ec=1.4)],
                sequence_phases=["active_growth"],
                current_phase="active_growth",
            )
        )

        result = await ValidateNutrientPlanCoverage().run(ctx, ValidateNutrientPlanCoverage.Input(plant_key="plant-1"))

        assert "calendar-week match" in result.summary
        assert "silent" in result.summary

    async def test_a_fully_covered_plan_says_so(self):
        ctx = _ctx(
            **_services(
                entries=[_Entry("vegetative", ec=1.4)],
                sequence_phases=["vegetative"],
                current_phase="vegetative",
            )
        )

        result = await ValidateNutrientPlanCoverage().run(ctx, ValidateNutrientPlanCoverage.Input(plant_key="plant-1"))

        assert result.data["phases_not_covered_by_name"] == []
        assert result.data["phases_without_target_ec"] == []
        assert result.data["current_phase_covered_by_name"] is True

    async def test_a_species_without_a_sequence_reports_nothing_rather_than_full_coverage(self):
        """The distinction that matters: 'nothing to compare' is not 'all good'."""
        ctx = _ctx(
            **_services(entries=[_Entry("vegetative", ec=1.4)], sequence_phases=None, current_phase="vegetative")
        )

        result = await ValidateNutrientPlanCoverage().run(ctx, ValidateNutrientPlanCoverage.Input(plant_key="plant-1"))

        assert result.data["sequence_phases"] == []
        assert result.data["phases_not_covered_by_name"] == []

    async def test_a_plant_without_a_plan_is_not_an_error(self):
        ctx = _ctx(**_services(entries=[], sequence_phases=["vegetative"], current_phase="vegetative", plan=None))
        ctx._services["nutrient_plan_service"].get_plant_plan = lambda plant_key, *, tenant_key: None  # type: ignore[attr-defined]  # noqa: E501

        result = await ValidateNutrientPlanCoverage().run(ctx, ValidateNutrientPlanCoverage.Input(plant_key="plant-1"))

        assert result.data["plan"] is None
        assert "nothing to check" in result.summary

    async def test_a_global_template_is_flagged_as_such(self):
        """Correcting one is the wrong operation — clone it first (#1244 item 1)."""
        ctx = _ctx(
            **_services(
                entries=[_Entry("vegetative")],
                sequence_phases=["vegetative"],
                current_phase="vegetative",
                plan=_Plan(tenant=""),
            )
        )

        result = await ValidateNutrientPlanCoverage().run(ctx, ValidateNutrientPlanCoverage.Input(plant_key="plant-1"))

        assert result.data["plan_is_global_template"] is True


def test_it_is_registered_read_only():
    """It adds no write surface — that is the point of item 3."""
    assert ValidateNutrientPlanCoverage.write is False
    assert ValidateNutrientPlanCoverage.permission is McpPermission.READ
