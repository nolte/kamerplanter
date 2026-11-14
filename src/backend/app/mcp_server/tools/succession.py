"""REQ-033 succession tools (§2.4, permission ``mcp.write``). Delegates to ``SuccessionPlanService``.

A succession plan (REQ-013 §2) re-sows one species at a fixed interval; generating it creates one planting run
per batch, so ``list_planting_runs`` finds the result. Both tools run the checks of their REST routes
(``POST /succession-plans``, ``POST /succession-plans/{key}/generate`` / ``generate-next``) through the same
service, and a dry run makes every one of them without writing (#2776).
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import Field, model_validator
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import (
    MAX_BATCH_DURATION_DAYS,
    MAX_PLANTS_PER_BATCH,
    MAX_SUCCESSION_BATCHES,
    MAX_SUCCESSION_INTERVAL_DAYS,
    MAX_SUCCESSION_WINDOW_DAYS,
    SuccessionPlan,
    check_succession_quotas,
)
from app.mcp_server.base import WriteToolBase, WriteToolInput, domain_validation_error, mcp_tool, record_fields
from app.mcp_server.context import ToolContext


@mcp_tool(name="create_succession_plan", permission=McpPermission.WRITE)
class CreateSuccessionPlan(WriteToolBase):
    """Create a succession plan that re-sows one species at a fixed interval between two dates."""

    class Input(WriteToolInput):
        name: str = Field(min_length=1, max_length=200)
        species_key: str = Field(min_length=1, description="Species to sow; list_species resolves it.")
        cultivar_key: str | None = Field(default=None, min_length=1, description="list_cultivars resolves it.")
        interval_days: int = Field(ge=1, le=MAX_SUCCESSION_INTERVAL_DAYS, description="Days between two sowings.")
        start_date: date = Field(description="Day of the first sowing (YYYY-MM-DD).")
        end_date: date = Field(
            description=(
                f"Last day a batch may be sown (YYYY-MM-DD); at most {MAX_SUCCESSION_WINDOW_DAYS} days after "
                f"start_date and at most {MAX_SUCCESSION_BATCHES} batches in all."
            )
        )
        plants_per_batch: int = Field(ge=1, le=MAX_PLANTS_PER_BATCH)
        reminder_days_before: int = Field(default=3, ge=0)
        batch_duration_days: int | None = Field(
            default=None,
            ge=1,
            le=MAX_BATCH_DURATION_DAYS,
            description="Days one batch holds its slots in the bed; omit for an open end.",
        )
        location_key: str | None = Field(
            default=None, min_length=1, description="Bed the batches are sown in; get_location resolves it."
        )
        notes: str | None = None

        @model_validator(mode="after")
        def _date_range(self) -> CreateSuccessionPlan.Input:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be on or after start_date.")
            check_succession_quotas(self.start_date, self.end_date, self.interval_days)
            return self

    @staticmethod
    def _own_input(args: WriteToolInput) -> CreateSuccessionPlan.Input:
        """Narrow the base-typed argument; the dispatcher always builds it from :attr:`Input`."""
        if not isinstance(args, CreateSuccessionPlan.Input):
            raise TypeError(f"create_succession_plan takes CreateSuccessionPlan.Input, not {type(args).__name__}")
        return args

    @staticmethod
    def _draft(ctx: ToolContext, args: CreateSuccessionPlan.Input) -> SuccessionPlan:
        """The plan as ``POST /succession-plans`` builds it; the tenant is the bound one, never an argument."""
        try:
            return SuccessionPlan(**record_fields(args), tenant_key=ctx.tenant_key)
        except PydanticValidationError as exc:
            raise domain_validation_error(exc, "The succession plan is invalid.") from None

    @staticmethod
    def _plan_data(plan: SuccessionPlan) -> dict[str, Any]:
        return {
            "succession_plan_key": plan.key,
            "name": plan.name,
            "species_key": plan.species_key,
            "cultivar_key": plan.cultivar_key,
            "location_key": plan.location_key,
            "interval_days": plan.interval_days,
            "start_date": plan.start_date.isoformat(),
            "end_date": plan.end_date.isoformat(),
            "plants_per_batch": plan.plants_per_batch,
            "total_batches": plan.total_batches,
            "status": plan.status,
        }

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        checked = ctx.succession_plan_service.preview_plan(
            self._draft(ctx, self._own_input(args)), tenant_key=ctx.tenant_key
        )
        return self._response(
            summary=f"Would create succession plan '{checked.name}' with {checked.total_batches} batches.",
            data=self._plan_data(checked),
        )

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        created = ctx.succession_plan_service.create_plan(
            self._draft(ctx, self._own_input(args)), tenant_key=ctx.tenant_key
        )
        return self._response(
            summary=(
                f"Created succession plan '{created.name}' ({created.total_batches} batches); "
                "generate_succession_runs creates its runs."
            ),
            data=self._plan_data(created),
            links=[
                ctx.api_link(f"/succession-plans/{created.key}"),
                ctx.ui_link(f"/durchlaeufe/succession-plans/{created.key}"),
            ],
        )


@mcp_tool(name="generate_succession_runs", permission=McpPermission.WRITE)
class GenerateSuccessionRuns(WriteToolBase):
    """Create the planting runs of a succession plan's batches; a dry run lists the runs it would create."""

    class Input(WriteToolInput):
        succession_plan_key: str = Field(min_length=1, description="create_succession_plan returns it.")
        mode: Literal["all", "next"] = Field(
            default="all",
            description=(
                "'all' creates every batch not generated yet, 'next' only the next one. "
                "Batches generated before are never created twice."
            ),
        )

    @staticmethod
    def _own_input(args: WriteToolInput) -> GenerateSuccessionRuns.Input:
        """Narrow the base-typed argument; the dispatcher always builds it from :attr:`Input`."""
        if not isinstance(args, GenerateSuccessionRuns.Input):
            raise TypeError(f"generate_succession_runs takes GenerateSuccessionRuns.Input, not {type(args).__name__}")
        return args

    @staticmethod
    def _run_item(run: PlantingRun, slot_keys: list[str] | None = None) -> dict[str, Any]:
        item: dict[str, Any] = {
            "run_key": run.key,
            "name": run.name,
            "succession_sequence": run.succession_sequence,
            "succession_total": run.succession_total,
            "planned_start_date": run.planned_start_date.isoformat() if run.planned_start_date else None,
            "planned_until": run.planned_until.isoformat() if run.planned_until else None,
            "location_key": run.location_key,
        }
        if slot_keys is not None:
            item["reserved_slot_count"] = len(slot_keys)
        return item

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        own = self._own_input(args)
        plan, batches = ctx.succession_plan_service.preview_generation(
            own.succession_plan_key, tenant_key=ctx.tenant_key, next_only=own.mode == "next"
        )
        return self._response(
            summary=f"Would create {len(batches)} planting runs for succession plan '{plan.name}'.",
            data={
                "succession_plan_key": plan.key,
                "generated_count": len(batches),
                "runs": [self._run_item(run, slot_keys) for run, slot_keys in batches],
            },
        )

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        own = self._own_input(args)
        service = ctx.succession_plan_service
        if own.mode == "next":
            plan, run = service.generate_next_run(own.succession_plan_key, tenant_key=ctx.tenant_key)
            runs = [run] if run is not None else []
        else:
            plan, runs = service.generate_runs(own.succession_plan_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Created {len(runs)} planting runs for succession plan '{plan.name}'.",
            data={
                "succession_plan_key": plan.key,
                "generated_count": len(runs),
                "completed_batches": plan.completed_batches,
                "total_batches": plan.total_batches,
                "status": plan.status,
                "runs": [self._run_item(run) for run in runs],
            },
            links=[ctx.api_link("/planting-runs"), ctx.ui_link("/planting-runs")],
        )
