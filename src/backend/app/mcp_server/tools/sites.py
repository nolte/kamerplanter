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
from app.mcp_server.base import TenantToolInput, ToolBase, WriteToolBase, WriteToolInput, mcp_tool
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


@mcp_tool(name="get_location", permission=McpPermission.READ)
class GetLocation(ToolBase):
    """Return one location's own properties — type, climate, frost exposure."""

    class Input(TenantToolInput):
        location_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Requested by both #949 and #1098, for the same reason from two
        # directions: deciding *which* plants a treatment or a medium applies to
        # needs the location's own properties, and ``list_plants_at_location``
        # returns the plants while never returning the location.
        #
        # The concrete case from #1098: a peat-based indoor mix at EC 1.2 is a
        # reasonable choice for two rooms and a poor one for a balcony, and the
        # only thing that distinguishes them is ``frost_exposed`` on the location
        # record — which MCP could not read.
        location = ctx.site_service.get_location(args.location_key, ctx.tenant_key)
        return self._response(
            summary=f"Location '{location.name}' ({location.type}).",
            data={
                "location_key": location.key,
                "name": location.name,
                "type": location.type,
                "site_key": getattr(location, "site_key", None),
                "frost_exposed": getattr(location, "frost_exposed", None),
                "climate_zone": getattr(location, "climate_zone", None),
                "light_situation": getattr(location, "light_situation", None),
                "area_sqm": getattr(location, "area_sqm", None),
                "notes": getattr(location, "notes", None),
            },
            links=[ctx.ui_link("/sites"), ctx.api_link(f"/locations/{location.key}")],
        )
