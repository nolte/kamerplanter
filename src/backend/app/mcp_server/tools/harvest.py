"""REQ-033 harvest readiness read tool (§2.1, §5).

Aggregates per-plant readiness signals across the tenant's active plants so the
LLM gets one answer without a second round-trip (AC-5 pattern). Delegates to
``PlantInstanceService`` (plant listing) + ``HarvestService`` (readiness).
"""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="get_harvest_readiness", permission=McpPermission.READ)
class GetHarvestReadiness(ToolBase):
    """Harvest-readiness overview across the tenant's active plants."""

    class Input(TenantToolInput):
        limit: int = Field(default=50, ge=1, le=200)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plants, _total = ctx.plant_service.list_plants(offset=0, limit=args.limit, tenant_key=ctx.tenant_key)
        items = []
        ready_count = 0
        for plant in plants:
            if getattr(plant, "removed_on", None):
                continue
            readiness = ctx.harvest_service.assess_readiness(plant.key, tenant_key=ctx.tenant_key)
            recommendation = readiness.get("recommendation", "immature")
            if recommendation in ("harvest", "ready", "harvest_now"):
                ready_count += 1
            items.append(
                {
                    "plant_key": plant.key,
                    "overall_score": readiness.get("overall_score", 0),
                    "recommendation": recommendation,
                    "estimated_days": readiness.get("estimated_days"),
                }
            )
        return self._response(
            summary=f"{ready_count} of {len(items)} active plants signal harvest readiness.",
            data={"ready_count": ready_count, "assessed": len(items), "items": items},
            links=[ctx.api_link("/harvest/readiness"), ctx.ui_link("/harvest")],
        )
