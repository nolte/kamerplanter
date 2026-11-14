"""REQ-033 setup tools (§2.3, permission ``mcp.setup``).

Delegates to ``SiteService``. ``mcp.setup`` is the most privileged class (site /
location lifecycle) and is admin-only (§4.4), so a read/write bot can never
create or destroy standort hierarchies (AC-S6).
"""

from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import IrrigationSystem, LightType, McpPermission, Orientation, SiteType
from app.domain.models.mcp import McpToolResponse
from app.domain.models.site import Location, Site
from app.mcp_server.base import (
    TenantToolInput,
    ToolBase,
    WriteToolBase,
    WriteToolInput,
    domain_validation_error,
    mcp_tool,
    record_fields,
)
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
    """Return one location's own properties — type, area, light, frost exposure."""

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
        location = ctx.site_service.get_location(args.location_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Location '{location.name}' ({location.location_type_key or 'untyped'}).",
            data={
                "location_key": location.key,
                "name": location.name,
                "location_type_key": location.location_type_key,
                "site_key": location.site_key,
                "parent_location_key": location.parent_location_key,
                "depth": location.depth,
                "path": location.path,
                "area_m2": location.area_m2,
                "orientation": location.orientation,
                "light_type": location.light_type,
                "irrigation_system": location.irrigation_system,
                "frost_exposed": location.frost_exposed,
            },
            links=[ctx.ui_link("/sites"), ctx.api_link(f"/locations/{location.key}")],
        )


@mcp_tool(name="create_location", permission=McpPermission.SETUP)
class CreateLocation(WriteToolBase):
    """Create a location (room, tent, shelf, bed) in a site, nested under a parent location if given."""

    class Input(WriteToolInput):
        name: str = Field(min_length=1, max_length=200)
        site_key: str = Field(min_length=1, description="Site the location belongs to; create_site returns it.")
        parent_location_key: str | None = Field(
            default=None,
            min_length=1,
            description="Parent location to nest under; get_location resolves it. Its site wins over site_key.",
        )
        location_type_key: str = Field(default="", description="Location type, e.g. a room, a tent or a bed type.")
        area_m2: float = Field(ge=0, description="Floor area in square metres.")
        orientation: Orientation | None = None
        light_type: LightType = LightType.NATURAL
        irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
        lights_on: str | None = Field(default=None, description="Start of the light period, HH:MM.")
        lights_off: str | None = Field(default=None, description="End of the light period, HH:MM.")
        use_dynamic_sunrise: bool = False
        tank_key: str | None = Field(default=None, min_length=1, description="Tank that waters this location.")
        frost_exposed: bool | None = Field(
            default=None, description="Override of the frost exposure; omit to inherit it from the site type."
        )

    @staticmethod
    def _own_input(args: WriteToolInput) -> CreateLocation.Input:
        """Narrow the base-typed argument; the dispatcher always builds it from :attr:`Input`."""
        if not isinstance(args, CreateLocation.Input):
            raise TypeError(f"create_location takes CreateLocation.Input, not {type(args).__name__}")
        return args

    @staticmethod
    def _draft(args: CreateLocation.Input) -> Location:
        """The location as ``POST /locations`` builds it. A location carries no tenant: its site is the anchor."""
        try:
            return Location(**record_fields(args))
        except PydanticValidationError as exc:
            raise domain_validation_error(exc, "The location is invalid.") from None

    @staticmethod
    def _location_data(location: Location) -> dict[str, Any]:
        return {
            "key": location.key,
            "location_key": location.key,
            "name": location.name,
            "site_key": location.site_key,
            "parent_location_key": location.parent_location_key,
            "location_type_key": location.location_type_key,
            "depth": location.depth,
            "path": location.path,
            "area_m2": location.area_m2,
        }

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        # The parent, the site and the tank are resolved under the bound tenant exactly as on create; a
        # foreign or unknown key answers not_found and nothing is written.
        checked = ctx.site_service.preview_location(self._draft(self._own_input(args)), tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would create location '{checked.name}'.",
            data=self._location_data(checked),
        )

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        created = ctx.site_service.create_location(self._draft(self._own_input(args)), tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Created location '{created.name}'.",
            data=self._location_data(created),
            links=[ctx.ui_link("/sites"), ctx.api_link(f"/locations/{created.key}")],
        )
