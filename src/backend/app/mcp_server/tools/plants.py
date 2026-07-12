"""REQ-033 plant write tools (§2.4). Delegates to ``PlantInstanceService``."""

from __future__ import annotations

from app.common.enums import McpPermission, TerminationType
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="archive_plant", permission=McpPermission.WRITE)
class ArchivePlant(WriteToolBase):
    """Archive a plant (disposed / given away / died) — never a hard delete."""

    class Input(WriteToolInput):
        plant_key: str
        termination_type: TerminationType | None = None

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would archive plant '{plant.key}'.",
            data={"plant_key": plant.key, "termination_type": args.termination_type},
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.remove_plant(
            args.plant_key,
            termination_type=args.termination_type,
            tenant_key=ctx.tenant_key,
        )
        return self._response(
            summary=f"Archived plant '{plant.key}'. History is retained.",
            data={
                "plant_key": plant.key,
                "removed_on": getattr(plant, "removed_on", None),
                "termination_type": args.termination_type,
            },
            links=[ctx.ui_link("/plants")],
        )


@mcp_tool(name="set_plant_location", permission=McpPermission.WRITE)
class SetPlantLocation(WriteToolBase):
    """Move a plant to another site / location / slot."""

    class Input(WriteToolInput):
        plant_key: str
        site_key: str | None = None
        location_key: str | None = None
        slot_key: str | None = None

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would move plant '{plant.key}' to the requested location.",
            data={
                "plant_key": plant.key,
                "from": {
                    "site_key": plant.site_key,
                    "location_key": plant.location_key,
                    "slot_key": plant.slot_key,
                },
                "to": {
                    "site_key": args.site_key,
                    "location_key": args.location_key,
                    "slot_key": args.slot_key,
                },
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        if args.site_key is not None:
            plant.site_key = args.site_key
        if args.location_key is not None:
            plant.location_key = args.location_key
        if args.slot_key is not None:
            plant.slot_key = args.slot_key
        updated = ctx.plant_service.update_plant(args.plant_key, plant)
        return self._response(
            summary=f"Moved plant '{updated.key}'.",
            data={
                "plant_key": updated.key,
                "site_key": updated.site_key,
                "location_key": updated.location_key,
                "slot_key": updated.slot_key,
            },
            links=[ctx.ui_link("/plants")],
        )
