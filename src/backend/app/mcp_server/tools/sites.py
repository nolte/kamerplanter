"""REQ-033 setup tools (§2.3, permission ``mcp.setup``).

Delegates to ``SiteService``. ``mcp.setup`` is the most privileged class (site /
location lifecycle) and is admin-only (§4.4), so a read/write bot can never
create or destroy standort hierarchies (AC-S6).
"""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission, SiteType
from app.domain.models.mcp import McpToolResponse
from app.domain.models.site import Site
from app.mcp_server.base import WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="create_site", permission=McpPermission.SETUP)
class CreateSite(WriteToolBase):
    """Create a standort root (apartment, garden, balcony, greenhouse)."""

    class Input(WriteToolInput):
        name: str = Field(min_length=1, max_length=200)
        type: SiteType = SiteType.INDOOR
        climate_zone: str = ""

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        return self._response(
            summary=f"Would create site '{args.name}' ({args.type}).",
            data={"name": args.name, "type": args.type, "climate_zone": args.climate_zone},
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        site = Site(
            tenant_key=ctx.tenant_key,
            name=args.name,
            type=args.type,
            climate_zone=args.climate_zone,
        )
        created = ctx.site_service.create_site(site)
        return self._response(
            summary=f"Created site '{created.name}'.",
            data={"site_key": created.key, "name": created.name, "type": created.type},
            links=[ctx.ui_link("/sites"), ctx.api_link("/sites")],
        )
