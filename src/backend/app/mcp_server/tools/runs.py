"""REQ-033 planting-run tools (§2.1 read, §2.4 write). Delegates to ``PlantingRunService``."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    DepthKind,
    LayoutStrategy,
    McpPermission,
    PlacementHint,
    PlanRole,
    PlantingRunType,
    RowDirection,
)
from app.domain.models.mcp import McpToolResponse
from app.domain.models.planting_run import (
    MAX_DEPTH_CM,
    MAX_EDGE_MARGIN_CM,
    MAX_ROTATION_OVERRIDE_REASON,
    MAX_SPACING_CM,
    MIN_ROW_SPACING_CM,
    RUN_SOURCES,
    PlantingRun,
    PlantingRunEntry,
    check_row_assignment,
)
from app.mcp_server.base import TenantToolInput, ToolBase, WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="list_planting_runs", permission=McpPermission.READ)
class ListPlantingRuns(ToolBase):
    """List the tenant's planting runs incl. phase and status."""

    class Input(TenantToolInput):
        status: str | None = Field(default=None, description="Optional status filter, e.g. 'active'.")
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=25, ge=1, le=100)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        filters = {"status": args.status} if args.status else None
        runs, total = ctx.planting_run_service.list_runs(
            offset=args.offset,
            limit=args.limit,
            filters=filters,
            tenant_key=ctx.tenant_key,
        )
        data = {
            "total": total,
            "items": [
                {
                    "run_key": r.key,
                    "name": getattr(r, "name", None),
                    "status": getattr(r, "status", None),
                    "species_key": getattr(r, "species_key", None),
                }
                for r in runs
            ],
        }
        return self._response(
            summary=f"{total} planting runs ({len(runs)} returned).",
            data=data,
            links=[ctx.api_link("/planting-runs"), ctx.ui_link("/planting-runs")],
        )


class PlantingRunEntryInput(BaseModel):
    """One entry of a new run — the fields and bounds of the REST ``EntryCreate``."""

    species_key: str = Field(description="Species of the entry; list_species resolves it.")
    cultivar_key: str | None = Field(default=None, description="Optional cultivar; list_cultivars resolves it.")
    quantity: int = Field(ge=1, description="Number of plants this entry plans.")
    id_prefix: str = Field(pattern=r"^[A-Z]{2,5}$", description="2-5 capital letters that prefix the plant IDs.")
    spacing_cm: float | None = Field(default=None, ge=0, le=MAX_SPACING_CM)
    row_spacing_cm: float | None = Field(default=None, ge=MIN_ROW_SPACING_CM, le=MAX_SPACING_CM)
    row_direction: RowDirection | None = None
    edge_margin_along_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    edge_margin_across_cm: float | None = Field(default=None, ge=0, le=MAX_EDGE_MARGIN_CM)
    depth_cm: float | None = Field(default=None, ge=0, le=MAX_DEPTH_CM)
    depth_kind: DepthKind | None = None
    sowing_spacing_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    thinning_to_cm: float | None = Field(default=None, gt=0, le=MAX_SPACING_CM)
    layout_strategy: LayoutStrategy | None = None
    placement_hint: PlacementHint | None = None
    row_assignment: list[int] | None = None
    notes: str | None = None

    @field_validator("row_assignment")
    @classmethod
    def _row_assignment(cls, value: list[int] | None) -> list[int] | None:
        return check_row_assignment(value)


@mcp_tool(name="create_planting_run", permission=McpPermission.WRITE)
class CreatePlantingRun(WriteToolBase):
    """Create a planned planting run (monoculture or clone), optionally with its entry."""

    class Input(WriteToolInput):
        name: str = Field(min_length=1, max_length=200)
        run_type: PlantingRunType = Field(
            description=(
                "'monoculture' or 'clone'. Either has exactly one entry; a mixed culture is not one run with "
                "several entries and is refused."
            )
        )
        location_key: str | None = Field(default=None, description="Bed or location; get_location resolves it.")
        substrate_batch_key: str | None = Field(default=None, description="list_substrate_batches resolves it.")
        planned_start_date: date | None = None
        source_plant_key: str | None = Field(default=None, description="Mother plant; required for a clone run.")
        notes: str | None = None
        entries: list[PlantingRunEntryInput] | None = None
        # ── Garden plan (REQ-053 §16.3, §20.6, GP-FR-065/132) ──
        plan_role: PlanRole = PlanRole.MAIN_CROP
        rotation_override_reason: str | None = Field(default=None, max_length=MAX_ROTATION_OVERRIDE_REASON)
        reserved_area_m2: float | None = Field(default=None, gt=0)
        planned_from: date | None = Field(
            default=None, description="Start of the reservation window; defaults to planned_start_date."
        )
        planned_until: date | None = Field(default=None, description="End of the reservation window (inclusive).")
        source: str | None = Field(default=None, max_length=50, description="Origin, e.g. 'manual' or 'plan_editor'.")

        @field_validator("plan_role")
        @classmethod
        def _plan_role(cls, value: PlanRole) -> PlanRole:
            if value is PlanRole.FALLOW:
                raise ValueError("A fallow period has no planting run.")
            return value

        @field_validator("source")
        @classmethod
        def _source(cls, value: str | None) -> str | None:
            if value is not None and value not in RUN_SOURCES:
                raise ValueError(f"source must be one of: {', '.join(sorted(RUN_SOURCES))}")
            return value

        @model_validator(mode="after")
        def _window(self) -> CreatePlantingRun.Input:
            start = self.planned_from or self.planned_start_date
            if start and self.planned_until and self.planned_until < start:
                raise ValueError("planned_until must not lie before the start of the window.")
            # The domain model refuses this on construction; checked here it is a validation error the
            # caller can fix, not a failure inside the tool.
            if self.run_type is PlantingRunType.CLONE and not self.source_plant_key:
                raise ValueError("Clone runs require a source_plant_key.")
            return self

    #: Input fields that steer the call rather than describe the run.
    _CALL_FIELDS = frozenset({"tenant", "dry_run", "idempotency_key", "entries"})

    @classmethod
    def _drafts(cls, ctx: ToolContext, args: Input) -> tuple[PlantingRun, list[PlantingRunEntry] | None]:
        """The run and entries as ``POST /planting-runs`` builds them; the tenant is the bound one, not an argument."""
        run = PlantingRun(**args.model_dump(exclude=set(cls._CALL_FIELDS)), tenant_key=ctx.tenant_key)
        entries = [PlantingRunEntry(**entry.model_dump()) for entry in args.entries] if args.entries else None
        return run, entries

    @staticmethod
    def _run_data(run: PlantingRun, entries: list[PlantingRunEntry]) -> dict[str, Any]:
        return {
            "run_key": run.key,
            "name": run.name,
            "run_type": run.run_type,
            "status": run.status,
            "location_key": run.location_key,
            "planned_start_date": run.planned_start_date.isoformat() if run.planned_start_date else None,
            "planned_quantity": run.planned_quantity,
            "plan_role": run.plan_role,
            "planned_from": run.planned_from.isoformat() if run.planned_from else None,
            "planned_until": run.planned_until.isoformat() if run.planned_until else None,
            "reserved_area_m2": run.reserved_area_m2,
            "entries": [
                {
                    "species_key": entry.species_key,
                    "cultivar_key": entry.cultivar_key,
                    "quantity": entry.quantity,
                    "id_prefix": entry.id_prefix,
                }
                for entry in entries
            ],
        }

    @staticmethod
    def _own_input(args: WriteToolInput) -> CreatePlantingRun.Input:
        """Narrow the base-typed argument; the dispatcher always builds it from :attr:`Input`.

        Typed against the base so the override keeps the base signature instead of adding a mypy
        ``override`` finding (#2169 ratchet).
        """
        if not isinstance(args, CreatePlantingRun.Input):
            raise TypeError(f"create_planting_run takes CreatePlantingRun.Input, not {type(args).__name__}")
        return args

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        # The service runs every check create_run runs (the tenant of each key, the run type, the layout)
        # and writes nothing, so a dry run refuses exactly what the real call would refuse.
        run, entries = self._drafts(ctx, self._own_input(args))
        checked, checked_entries, layout_slots = ctx.planting_run_service.preview_run(
            run, entries, tenant_key=ctx.tenant_key
        )
        data = self._run_data(checked, checked_entries)
        data["layout_slots"] = layout_slots
        return self._response(
            summary=(
                f"Would create planting run '{checked.name}' ({checked.run_type}) with "
                f"{checked.planned_quantity} planned plants."
            ),
            data=data,
        )

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        run, entries = self._drafts(ctx, self._own_input(args))
        created = ctx.planting_run_service.create_run(run, entries, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Created planting run '{created.name}' ({created.planned_quantity} planned plants).",
            data=self._run_data(created, entries or []),
            links=[ctx.api_link(f"/planting-runs/{created.key}"), ctx.ui_link("/planting-runs")],
        )
