"""REQ-019 substrate tools (#1098). Delegates to ``SubstrateService``.

Before this, the whole substrate layer was represented by exactly one MCP tool:
``list_substrates``, a catalogue listing. Nothing about substrates was writable,
no single substrate was readable, the mixer was unreachable and the entire batch
layer was invisible — while ``PlantCreate.substrate_batch_key`` shows the data
model expects batches to be in play.

**Two scoping rules apply here, and conflating them is the mistake to avoid**
(they are the rules #1195 established for the REST surface, mirrored):

* the **catalogue** is hybrid — seeded base media plus a tenant's own mixes — so
  its tools take :class:`CatalogueToolInput`, where an omitted ``tenant`` means
  the shared catalogue and a member's slug widens the read;
* **batches** are strictly owned — there is no global batch — so their tools take
  :class:`TenantToolInput`, which *requires* an acting tenant. "No tenant" is not
  a meaningful answer for a batch, and letting it default would return the rows
  the ``v0043`` backfill could not attribute.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.domain.models.substrate import MixComponent
from app.mcp_server.base import (
    CatalogueToolInput,
    TenantToolInput,
    ToolBase,
    WriteToolBase,
    WriteToolInput,
    mcp_tool,
)
from app.mcp_server.context import ToolContext


def _substrate_summary(s: Any) -> dict[str, Any]:
    """The property set an agent needs to reason about a medium.

    Deliberately the full physical picture rather than a name and a type: the
    numbers that decide a safe fertigation dose — CEC, buffer capacity, the EC
    already in the medium — are exactly the ones that differ between two media of
    the same ``type``, and an agent that cannot see them will compute a dose for
    the wrong substrate (the #1098 §7 finding).
    """
    return {
        "substrate_key": s.key,
        "name_de": s.name_de,
        "name_en": s.name_en,
        "type": s.type,
        "brand": s.brand,
        "is_mix": s.is_mix,
        "mix_components": [{"substrate_key": c.substrate_key, "fraction": c.fraction} for c in s.mix_components],
        "ph_base": s.ph_base,
        "ec_base_ms": s.ec_base_ms,
        "water_retention": s.water_retention,
        "air_porosity_percent": s.air_porosity_percent,
        "buffer_capacity": s.buffer_capacity,
        "cec_meq_per_100cm3": s.cec_meq_per_100cm3,
        "water_holding_capacity_percent": s.water_holding_capacity_percent,
        "easily_available_water_percent": s.easily_available_water_percent,
        "bulk_density_g_per_l": s.bulk_density_g_per_l,
        "irrigation_strategy": s.irrigation_strategy,
        "reusable": s.reusable,
        "max_reuse_cycles": s.max_reuse_cycles,
        "composition": s.composition,
    }


def _batch_summary(b: Any) -> dict[str, Any]:
    return {
        "batch_key": b.key,
        "batch_id": b.batch_id,
        "substrate_key": b.substrate_key,
        "volume_liters": b.volume_liters,
        "mixed_on": b.mixed_on,
        "last_amended": b.last_amended,
        "cycles_used": b.cycles_used,
        "ph_current": b.ph_current,
        "ec_current_ms": b.ec_current_ms,
    }


# ── the catalogue: hybrid ────────────────────────────────────────────────────


@mcp_tool(name="get_substrate", permission=McpPermission.READ)
class GetSubstrate(ToolBase):
    """Return one substrate: type, pH/EC base, porosity, CEC, buffer capacity, reuse limits."""

    class Input(CatalogueToolInput):
        substrate_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Without this tool an agent had to list the whole catalogue — 28 entries
        # of ~18 numeric properties — to inspect one medium.
        tenant_key = ctx.catalogue_tenant_key(args.tenant)
        substrate = ctx.substrate_service.get_substrate(args.substrate_key, tenant_key=tenant_key)
        return self._response(
            summary=f"Substrate '{substrate.name_de or substrate.name_en}' ({substrate.type}).",
            data=_substrate_summary(substrate),
            links=[{"type": "api", "url": f"/api/v1/substrates/{substrate.key}"}],
        )


@mcp_tool(name="preview_substrate_mix", permission=McpPermission.READ)
class PreviewSubstrateMix(ToolBase):
    """Compute what a weighted substrate mix would behave like, without creating it."""

    class Input(CatalogueToolInput):
        components: list[dict[str, Any]] = Field(
            description="Weighted parts: [{'substrate_key': str, 'fraction': 0..1}]. Fractions must sum to 1.0.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # A pure calculation on a read surface, the same category as
        # ``calculate_mixing_protocol``. Without it an agent asked "what would a
        # 50/50 mix behave like?" has to average the component properties itself —
        # and the correct weighting differs per property (volume for porosity and
        # bulk density, *mass* for CEC, buffer-weighted for pH). Getting that wrong
        # produces plausible numbers that are wrong in the direction that decides a
        # fertigation dose.
        tenant_key = ctx.catalogue_tenant_key(args.tenant)
        components = [MixComponent(**c) for c in args.components]
        props = ctx.substrate_service.preview_mix(components, tenant_key=tenant_key)
        return self._response(
            summary=f"Preview of a {len(components)}-component mix (nothing was created).",
            data={"components": [c.model_dump() for c in components], **props},
            links=[{"type": "api", "url": "/api/v1/substrates/preview-mix"}],
        )


@mcp_tool(name="create_substrate_mix", permission=McpPermission.WRITE)
class CreateSubstrateMix(WriteToolBase):
    """Create and persist a substrate mix, owned by the acting tenant."""

    class Input(WriteToolInput):
        name_de: str
        name_en: str
        components: list[dict[str, Any]] = Field(
            description="Weighted parts: [{'substrate_key': str, 'fraction': 0..1}]. Fractions must sum to 1.0.",
        )

    @staticmethod
    def _components(args: Input) -> list[MixComponent]:
        return [MixComponent(**c) for c in args.components]

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        components = self._components(args)
        # The dry run is the *same* calculation the write performs, resolved in the
        # same scope — so a preview that succeeds cannot be followed by a create
        # that refuses a component it was never allowed to see.
        props = ctx.substrate_service.preview_mix(components, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Would create mix '{args.name_de}' from {len(components)} components.",
            data={"name_de": args.name_de, "name_en": args.name_en, **props},
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        created = ctx.substrate_service.create_mix(
            self._components(args),
            name_de=args.name_de,
            name_en=args.name_en,
            tenant_key=ctx.tenant_key,
            caller_role=ctx.role,
        )
        return self._response(
            summary=f"Created mix '{created.name_de}' in this tenant's catalogue.",
            data=_substrate_summary(created),
            links=[{"type": "api", "url": f"/api/v1/substrates/{created.key}"}],
        )


# ── batches: strictly owned, so the tenant is required ───────────────────────


@mcp_tool(name="list_substrate_batches", permission=McpPermission.READ)
class ListSubstrateBatches(ToolBase):
    """List this tenant's mixed batches of one substrate, with their pH/EC and reuse count."""

    class Input(TenantToolInput):
        substrate_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        batches = ctx.substrate_service.list_batches(args.substrate_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"{len(batches)} batches of substrate '{args.substrate_key}'.",
            data={
                "substrate_key": args.substrate_key,
                "count": len(batches),
                "items": [_batch_summary(b) for b in batches],
            },
            links=[{"type": "api", "url": f"/api/v1/substrates/{args.substrate_key}/batches"}],
        )


@mcp_tool(name="get_substrate_batch", permission=McpPermission.READ)
class GetSubstrateBatch(ToolBase):
    """Return one substrate batch — the target of ``plant.substrate_batch_key``."""

    class Input(TenantToolInput):
        batch_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # This is what makes ``PlantCreate.substrate_batch_key`` resolvable by an
        # agent: the model has always expected a plant to be traceable to a
        # specific batch, and nothing over MCP could follow the reference.
        batch = ctx.substrate_service.get_batch(args.batch_key, tenant_key=ctx.tenant_key)
        return self._response(
            summary=f"Batch '{batch.batch_id}' of substrate '{batch.substrate_key}', {batch.cycles_used} cycles used.",
            data=_batch_summary(batch),
            links=[{"type": "api", "url": f"/api/v1/substrates/batches/{batch.key}"}],
        )


@mcp_tool(name="check_batch_reusability", permission=McpPermission.READ)
class CheckBatchReusability(ToolBase):
    """Assess whether a batch may be reused, and which treatments it would need first."""

    class Input(TenantToolInput):
        batch_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Agent-shaped work, and the reason the batch layer is worth exposing at
        # all: ``reusable`` and ``max_reuse_cycles`` are catalogue facts, but
        # whether *this* batch may be reused is a decision from its own history.
        can_reuse, issues, steps, prep_hours, ready_on = ctx.substrate_service.check_reusability(
            args.batch_key, tenant_key=ctx.tenant_key
        )
        return self._response(
            summary=("Batch can be reused." if can_reuse else f"Batch cannot be reused: {len(issues)} issue(s)."),
            data={
                "batch_key": args.batch_key,
                "can_reuse": can_reuse,
                "issues": issues,
                "preparation_steps": steps,
                "preparation_hours": prep_hours,
                "ready_on": ready_on,
            },
            links=[{"type": "api", "url": f"/api/v1/substrates/batches/{args.batch_key}/check-reusability"}],
        )


# ── the setter that keeps callers off the full-replacement PUT ───────────────


@mcp_tool(name="set_plant_substrate", permission=McpPermission.WRITE)
class SetPlantSubstrate(WriteToolBase):
    """Set a plant's substrate and/or its batch, leaving every other field alone."""

    class Input(WriteToolInput):
        plant_key: str
        substrate_key: str | None = Field(default=None, description="Substrate to assign; omit to leave unchanged.")
        substrate_batch_key: str | None = Field(default=None, description="Batch to assign; omit to leave unchanged.")

    @staticmethod
    def _verify_targets(ctx: ToolContext, args: Input) -> None:
        """Resolve both targets **in the caller's tenant** before assigning either.

        The exact shape ``set_plant_location`` uses, and the reason this tool
        could not be written before #1195: a substrate and a batch carried no
        owner, so there was nothing to verify against. Copying the template then
        would have produced the template without its guard.

        A foreign target answers the same 404 an absent one does, so this cannot
        be walked to discover which media other tenants hold.
        """
        if args.substrate_key is not None:
            ctx.substrate_service.get_substrate(args.substrate_key, tenant_key=ctx.tenant_key)
        if args.substrate_batch_key is not None:
            ctx.substrate_service.get_batch(args.substrate_batch_key, tenant_key=ctx.tenant_key)

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        self._verify_targets(ctx, args)
        return self._response(
            summary=f"Would set the substrate of plant '{plant.key}'.",
            data={
                "plant_key": plant.key,
                "from": {
                    "substrate_key": plant.substrate_key,
                    "substrate_batch_key": plant.substrate_batch_key,
                },
                "to": {
                    "substrate_key": args.substrate_key if args.substrate_key is not None else plant.substrate_key,
                    "substrate_batch_key": (
                        args.substrate_batch_key if args.substrate_batch_key is not None else plant.substrate_batch_key
                    ),
                },
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Loads the full stored model and changes only the named fields, exactly
        # as ``set_plant_location`` does. That is what keeps this off
        # ``PUT /plant-instances/{key}``, whose ``PlantCreate`` body is a full
        # replacement: composing that call from the schema name erases the plant's
        # location, slot, cultivar, name, container volume and — with some irony —
        # the very batch reference this tool exists to set (#1098).
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        self._verify_targets(ctx, args)
        if args.substrate_key is not None:
            plant.substrate_key = args.substrate_key
        if args.substrate_batch_key is not None:
            plant.substrate_batch_key = args.substrate_batch_key
        updated = ctx.plant_service.update_plant(args.plant_key, plant)
        return self._response(
            summary=f"Set the substrate of plant '{updated.key}'.",
            data={
                "plant_key": updated.key,
                "substrate_key": updated.substrate_key,
                "substrate_batch_key": updated.substrate_batch_key,
                # Reported back because it is the field a naive PUT would have
                # destroyed, and an agent verifying its own work should see it
                # survive rather than have to ask again.
                "current_phase_key": updated.current_phase_key,
                "location_key": updated.location_key,
            },
            links=[ctx.ui_link("/plants")],
        )
