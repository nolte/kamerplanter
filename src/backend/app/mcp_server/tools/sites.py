"""REQ-033 setup tools (§2.3, permission ``mcp.setup``).

Delegates to ``SiteService``. ``mcp.setup`` is the most privileged class (site /
location lifecycle) and is admin-only (§4.4), so a read/write bot can never
create or destroy standort hierarchies (AC-S6).
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field, model_validator
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import IrrigationSystem, LightType, McpPermission, Orientation, SiteType, SunExposure
from app.common.exceptions import PlanError, PlanRevisionConflictError, PlanValidationError
from app.domain.models.garden_plan import PlanBatchResult
from app.domain.models.geometry import MAX_DIMENSION_M, MIN_DIMENSION_M, Geometry
from app.domain.models.mcp import McpToolResponse
from app.domain.models.site import Location, Site
from app.mcp_server.base import (
    McpToolError,
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


#: Input fields the garden-plan batch does not carry: a location with a geometry is created without them.
_DIRECT_ONLY_FIELDS: tuple[str, ...] = (
    "area_m2",
    "orientation",
    "light_type",
    "irrigation_system",
    "lights_on",
    "lights_off",
    "use_dynamic_sunrise",
    "tank_key",
    "frost_exposed",
)
#: Input fields one ``create_location`` operation of the plan batch takes (``CreateLocationData``).
_PLAN_FIELDS: tuple[str, ...] = (
    "name",
    "location_type_key",
    "parent_location_key",
    "geometry",
    "height_m",
    "description",
    "sun_exposure",
)
#: The request-local key of the one location a ``create_location`` batch creates.
_TEMP_KEY = "new_location"


def _plan_refusal(exc: PlanError | PlanValidationError) -> McpToolError:
    """A garden-plan refusal as a typed MCP error that keeps the plan's own codes (REQ-033 §2.3, #2776).

    A revision conflict is ``conflict.plan_revision`` and is **not** retried here: the plan changed between
    the tool's read and its write, and whether the new location still fits is the caller's decision. Rule
    findings (V-03 ``geometry.outside_parent``, V-05 ``bed.overlap`` …) keep their codes in
    ``details.findings``; any other plan refusal keeps its dotted code.
    """
    if isinstance(exc, PlanRevisionConflictError):
        return McpToolError(
            "conflict.plan_revision",
            "The site's garden plan changed while the location was being created; nothing was written. "
            "Read the plan again and decide whether to repeat the call.",
            details={"current_revision": exc.current_revision},
        )
    raised: list[dict[str, Any]] = exc.details
    if isinstance(exc, PlanValidationError):
        findings = [{key: detail[key] for key in detail if key != "reason"} for detail in raised]
        return McpToolError("validation.error", exc.message, details={"findings": findings})
    first: dict[str, Any] = raised[0] if raised else {}
    return McpToolError(
        exc.error_code,
        exc.message,
        details={key: value for key, value in first.items() if key not in ("reason", "code")},
        status_code=exc.status_code,
    )


@mcp_tool(name="create_location", permission=McpPermission.SETUP)
class CreateLocation(WriteToolBase):
    """Create a location (room, tent, shelf, bed) in a site; with a geometry it is placed on the garden plan."""

    class Input(WriteToolInput):
        name: str = Field(min_length=1, max_length=200)
        site_key: str = Field(min_length=1, description="Site the location belongs to; create_site returns it.")
        parent_location_key: str | None = Field(
            default=None,
            min_length=1,
            description="Parent location to nest under; get_location resolves it. Its site wins over site_key.",
        )
        location_type_key: str = Field(
            default="",
            description="Location type, e.g. a room, a tent or a bed type. Required together with a geometry.",
        )
        area_m2: float | None = Field(
            default=None,
            ge=0,
            description="Floor area in square metres. Required without a geometry; with one it is derived.",
        )
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
        # ── Garden plan (REQ-053; REQ-033 §2.3, #2776) ──
        geometry: Geometry | None = Field(
            default=None,
            description=(
                "Frame of the location on the site's garden plan, in metres in plan coordinates: a rect "
                "(origin, width_m, length_m, rotation_deg), a circle or a polygon. With a geometry the location "
                "is created through the garden plan: it must lie inside the site boundary or its parent "
                "(geometry.outside_parent) and a bed may not overlap another bed (bed.overlap); area_m2 is "
                "derived. Omit for a location that is not drawn on the plan."
            ),
        )
        height_m: float | None = Field(
            default=None, ge=MIN_DIMENSION_M, le=MAX_DIMENSION_M, description="Height of a raised bed, metres."
        )
        description: str | None = Field(default=None, max_length=1000)
        sun_exposure: SunExposure = SunExposure.UNKNOWN

        @model_validator(mode="after")
        def _geometry_or_area(self) -> CreateLocation.Input:
            if self.geometry is None:
                if self.area_m2 is None:
                    raise ValueError("area_m2 is required for a location without a geometry.")
                return self
            if not self.location_type_key:
                raise ValueError("A location with a geometry needs a location_type_key.")
            stray = [name for name in _DIRECT_ONLY_FIELDS if name in self.model_fields_set]
            if stray:
                raise ValueError(
                    f"{', '.join(stray)} cannot be set together with a geometry: the garden plan derives the area "
                    "and does not take the other fields when it creates a location."
                )
            return self

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
    def _plan_batch(args: CreateLocation.Input) -> tuple[list[dict[str, Any]], int]:
        """The one ``create_location`` operation of ``POST /sites/{key}/plan/batch``, and its size in bytes."""
        fields = record_fields(args, mode="json")
        data = {name: fields[name] for name in _PLAN_FIELDS if fields[name] is not None}
        operations: list[dict[str, Any]] = [{"op": "create_location", "temp_key": _TEMP_KEY, "data": data}]
        return operations, len(json.dumps(operations).encode())

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

    @staticmethod
    def _planned_data(args: CreateLocation.Input, key: str | None, result: PlanBatchResult) -> dict[str, Any]:
        derived = result.derived.get(key or _TEMP_KEY)
        return {
            "key": key,
            "location_key": key,
            "name": args.name,
            "site_key": args.site_key,
            "parent_location_key": args.parent_location_key,
            "location_type_key": args.location_type_key,
            "area_m2": derived.area_m2 if derived is not None else None,
            "bbox": list(derived.bbox) if derived is not None and derived.bbox is not None else None,
            "plan_revision": result.plan_revision,
        }

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        own = self._own_input(args)
        if own.geometry is not None:
            # Every check of the plan batch before its transaction (tenant anchor, references, role, the plan
            # rules); only the revision check is left to the real call.
            operations, body_bytes = self._plan_batch(own)
            try:
                result = ctx.garden_plan_service.preview_batch(
                    own.site_key,
                    tenant_key=ctx.tenant_key,
                    user_key=ctx.principal.account_key,
                    role=ctx.role,
                    operations=operations,
                    body_bytes=body_bytes,
                )
            except (PlanError, PlanValidationError) as exc:
                raise _plan_refusal(exc) from None
            return self._response(
                summary=f"Would place location '{own.name}' on the garden plan.",
                data=self._planned_data(own, None, result),
            )
        # The parent, the site and the tank are resolved under the bound tenant exactly as on create; a
        # foreign or unknown key answers not_found and nothing is written.
        checked = ctx.site_service.preview_location(self._draft(own), tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would create location '{checked.name}'.",
            data=self._location_data(checked),
        )

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        own = self._own_input(args)
        if own.geometry is not None:
            operations, body_bytes = self._plan_batch(own)
            try:
                # ``expected_revision=None``: the batch expects the revision its own validation read, so the
                # tool never asks the caller for one; a write that loses the race is refused, never retried.
                result = await ctx.garden_plan_service.apply_batch_async(
                    own.site_key,
                    tenant_key=ctx.tenant_key,
                    user_key=ctx.principal.account_key,
                    role=ctx.role,
                    expected_revision=None,
                    operations=operations,
                    body_bytes=body_bytes,
                )
            except (PlanError, PlanValidationError) as exc:
                raise _plan_refusal(exc) from None
            key = result.key_map[_TEMP_KEY]
            return self._response(
                summary=f"Placed location '{own.name}' on the garden plan.",
                data=self._planned_data(own, key, result),
                links=[ctx.ui_link("/sites"), ctx.api_link(f"/locations/{key}")],
            )
        created = ctx.site_service.create_location(self._draft(own), tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Created location '{created.name}'.",
            data=self._location_data(created),
            links=[ctx.ui_link("/sites"), ctx.api_link(f"/locations/{created.key}")],
        )
