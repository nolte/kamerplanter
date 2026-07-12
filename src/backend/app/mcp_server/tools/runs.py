"""REQ-033 planting-run read tools (§2.1). Delegates to ``PlantingRunService``."""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="list_planting_runs", permission=McpPermission.READ)
class ListPlantingRuns(ToolBase):
    """List the tenant's planting runs incl. phase and status."""

    class Input(ToolInput):
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
