"""REQ-033 plant write tools (§2.4). Delegates to ``PlantInstanceService``."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from pydantic import Field
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import CycleType, McpPermission, SubstrateType, TerminationType
from app.domain.models.mcp import McpToolResponse
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import MAX_CONTAINER_VOLUME_L
from app.mcp_server.base import WriteToolBase, WriteToolInput, domain_validation_error, mcp_tool, record_fields
from app.mcp_server.context import ToolContext

#: A document key the caller names. ``""`` is malformed input, not a reference: it is refused here with
#: ``validation.error``, as ``POST /plant-instances`` refuses it with 422 (``ReferenceKey`` there).
_Key = Annotated[str, Field(min_length=1)]


@mcp_tool(name="create_plant", permission=McpPermission.WRITE)
class CreatePlant(WriteToolBase):
    """Create one plant instance in the tenant, optionally placed on a site, location and slot."""

    class Input(WriteToolInput):
        instance_id: str = Field(
            min_length=1, description="The plant's human-facing ID, unique within the tenant (e.g. 'TOM-001')."
        )
        species_key: _Key = Field(description="Species of the plant; list_species resolves it.")
        cultivar_key: _Key | None = Field(default=None, description="Optional cultivar; list_cultivars resolves it.")
        site_key: _Key | None = Field(default=None, description="Site the plant stands at.")
        location_key: _Key | None = Field(
            default=None, description="Location (room, tent, bed) under that site; get_location resolves it."
        )
        slot_key: _Key | None = Field(
            default=None, description="Slot inside that location; the location is derived from it when omitted."
        )
        substrate_batch_key: _Key | None = Field(default=None, description="list_substrate_batches resolves it.")
        substrate_key: _Key | None = Field(default=None, description="Growing medium; list_substrates resolves it.")
        plant_name: str | None = None
        planted_on: date = Field(description="Day the plant was sown, planted or taken over (YYYY-MM-DD).")
        current_phase_key: _Key | None = Field(
            default=None,
            description=(
                "Phase the plant is in right now, for a plant taken over mid-lifecycle; "
                "get_species_phase_sequence lists the legal keys. Omit to start at the species' first phase."
            ),
        )
        container_volume_liters: float | None = Field(default=None, ge=0.1, le=MAX_CONTAINER_VOLUME_L)
        substrate_type_override: SubstrateType | None = None
        cultivation_cycle_type: CycleType | None = Field(
            default=None, description="Practised lifespan of this plant; omit for the species default."
        )

    @staticmethod
    def _own_input(args: WriteToolInput) -> CreatePlant.Input:
        """Narrow the base-typed argument; the dispatcher always builds it from :attr:`Input`."""
        if not isinstance(args, CreatePlant.Input):
            raise TypeError(f"create_plant takes CreatePlant.Input, not {type(args).__name__}")
        return args

    @staticmethod
    def _draft(ctx: ToolContext, args: CreatePlant.Input) -> PlantInstance:
        """The plant as ``POST /plant-instances`` builds it; the tenant is the bound one, never an argument."""
        try:
            return PlantInstance(**record_fields(args), tenant_key=ctx.tenant_key)
        except PydanticValidationError as exc:
            raise domain_validation_error(exc, "The plant is invalid.") from None

    @staticmethod
    def _plant_data(plant: PlantInstance) -> dict[str, Any]:
        return {
            "plant_key": plant.key,
            "instance_id": plant.instance_id,
            "species_key": plant.species_key,
            "cultivar_key": plant.cultivar_key,
            "site_key": plant.site_key,
            "location_key": plant.location_key,
            "slot_key": plant.slot_key,
            "planted_on": plant.planted_on.isoformat(),
            "current_phase_key": plant.current_phase_key,
        }

    async def preview(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        # Every check create_plant makes — the tenant of each key, the placement chain, a free slot, crop
        # rotation and companions, the phase — plus the cultivar and instance_id checks the write makes in
        # the repository; nothing is written.
        checked = ctx.plant_service.preview_plant(self._draft(ctx, self._own_input(args)), tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would create plant '{checked.instance_id}'.",
            data=self._plant_data(checked),
        )

    async def execute(self, ctx: ToolContext, args: WriteToolInput) -> McpToolResponse:
        created = ctx.plant_service.create_plant(self._draft(ctx, self._own_input(args)), tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Created plant '{created.instance_id}'.",
            data=self._plant_data(created),
            links=[ctx.api_link(f"/plant-instances/{created.key}"), ctx.ui_link(f"/plants/{created.key}")],
        )


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

    @staticmethod
    def _verify_targets(ctx: ToolContext, args: Input) -> None:
        # SEC-002: the plant is ownership-checked, but the destination foreign
        # keys are caller-supplied — validate each non-null target belongs to the
        # caller's tenant BEFORE assigning it, so a plant can never be moved onto
        # a foreign/dangling site/location/slot. Each getter fails closed with the
        # 404 not-found contract on a foreign/missing target (never a 403), so a
        # foreign key's existence is never disclosed.
        if args.site_key is not None:
            ctx.site_service.get_site(args.site_key, tenant_key=ctx.tenant_key)
        if args.location_key is not None:
            ctx.site_service.get_location(args.location_key, tenant_key=ctx.tenant_key)
        if args.slot_key is not None:
            ctx.site_service.get_slot(args.slot_key, tenant_key=ctx.tenant_key)

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        self._verify_targets(ctx, args)
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
        self._verify_targets(ctx, args)
        if args.site_key is not None:
            plant.site_key = args.site_key
        if args.location_key is not None:
            plant.location_key = args.location_key
        if args.slot_key is not None:
            plant.slot_key = args.slot_key
        updated = ctx.plant_service.update_plant(args.plant_key, plant, tenant_key=ctx.tenant_key)
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
