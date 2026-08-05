"""REQ-033 read tools for plant instances (§2.1).

These close the addressing gap in the palette: every write tool takes a
``plant_key``, but until now only ``get_due_care_tasks`` (plants with pending
care) and ``get_harvest_readiness`` (keys without names) ever produced one. A
plant with no open task was unreachable, so the write tools could not act on it.

All four delegate to the same services the REST API uses and are tenant-scoped,
so they inherit isolation rather than re-implementing it.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission, ReminderType
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, mcp_tool
from app.mcp_server.context import ToolContext

#: Upper bound on a single page. The palette favours compact, LLM-readable
#: answers over completeness — a bigger page is a worse answer, not a better one.
_MAX_LIMIT = 200

#: How many records are read before filtering. Filtering has to happen across the
#: whole set, not within one page: a name filter applied to page 1 reports "no
#: match" for a plant sitting on page 3, which is a wrong answer rather than an
#: incomplete one — and this is the tool a model uses to resolve a name into the
#: plant_key every write tool demands. Beyond this bound the set is genuinely
#: unscanned, which the response says out loud via ``truncated``.
_SCAN_LIMIT = 1000


def _summarise(plant: Any) -> dict[str, Any]:
    """The compact projection every list tool returns per plant."""

    return {
        "plant_key": plant.key,
        "instance_id": plant.instance_id,
        "plant_name": plant.plant_name,
        "species_key": plant.species_key,
        "cultivar_key": plant.cultivar_key,
        "site_key": plant.site_key,
        "location_key": plant.location_key,
        "slot_key": plant.slot_key,
        # The medium this plant actually stands in. Raw keys only: resolving them
        # here would be an N+1 across a page, and ``get_plant`` resolves the type
        # on the detail view instead. Without these, ``list_substrates`` is a
        # catalogue an agent cannot connect to a plant — the substrate properties
        # a feeding judgement needs (ph_base, ec_base_ms, buffer_capacity,
        # cec_meq_per_100g) would have no way in.
        "substrate_key": plant.substrate_key,
        "substrate_batch_key": plant.substrate_batch_key,
        "substrate_type_override": plant.substrate_type_override,
        "planted_on": plant.planted_on,
        "removed_on": plant.removed_on,
        "current_phase_key": plant.current_phase_key,
    }


def _matches(plant: Any, needle: str) -> bool:
    """Case-insensitive substring match over the plant's human-facing names."""

    haystack = " ".join(
        str(value) for value in (plant.plant_name, plant.instance_id, plant.species_key) if value
    ).lower()
    return needle in haystack


@mcp_tool(name="list_plants", permission=McpPermission.READ)
class ListPlants(ToolBase):
    """List the tenant's plants, optionally filtered by name and archived state."""

    class Input(TenantToolInput):
        query: str | None = Field(
            default=None,
            description="Case-insensitive substring filter over plant name, instance id and species key.",
        )
        include_archived: bool = Field(
            default=False,
            description="Include plants that have already been removed/archived.",
        )
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # The repository has no name filter, so read the tenant's set and narrow it
        # here. Reading _SCAN_LIMIT rather than args.limit is load-bearing: paging
        # first and filtering second would search only the current page and report
        # "no match" for a plant further down — a wrong answer, not a short one.
        # Filtering after the tenant-scoped read keeps isolation intact; a plant of
        # another tenant is never in the set to begin with.
        plants, total = ctx.plant_service.list_plants(
            offset=0,
            limit=_SCAN_LIMIT,
            tenant_key=ctx.tenant_key,
        )
        selected = [p for p in plants if args.include_archived or not p.removed_on]
        if args.query:
            needle = args.query.strip().lower()
            selected = [p for p in selected if _matches(p, needle)]

        page = selected[args.offset : args.offset + args.limit]
        # True only when the tenant holds more records than we read — then the
        # filter genuinely did not see everything and the caller must know.
        truncated = total > _SCAN_LIMIT

        data = {
            "count": len(page),
            "matched": len(selected),
            "total_in_tenant": total,
            "offset": args.offset,
            "truncated": truncated,
            "items": [_summarise(p) for p in page],
        }
        if args.query:
            summary = f"{len(selected)} plants match '{args.query}'"
            summary += f" ({len(page)} returned)." if len(page) != len(selected) else "."
        else:
            summary = f"{len(page)} plants returned (of {total} in this tenant)."
        if truncated:
            summary += f" Only the first {_SCAN_LIMIT} records were searched — narrow the query."
        return self._response(summary=summary, data=data, links=[ctx.api_link("/plants"), ctx.ui_link("/plants")])


@mcp_tool(name="get_plant", permission=McpPermission.READ)
class GetPlant(ToolBase):
    """Return one plant's master data: species, phase, location and lifecycle dates."""

    class Input(TenantToolInput):
        plant_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Tenant-scoped read: a foreign key raises not_found, never a distinguishable
        # permission error, so the tool cannot be used to probe other tenants.
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        data = _summarise(plant)

        # Resolving the species name is worth one extra lookup on a detail view —
        # it is what lets a model connect "my tomato" to a key. The list tools
        # deliberately skip it to avoid an N+1 across a whole page.
        try:
            species = ctx.species_service.get_species(plant.species_key)
            data["species_name"] = getattr(species, "scientific_name", None)
            data["species_common_names"] = getattr(species, "common_names", None)
        except Exception:  # noqa: BLE001 — a missing catalogue entry must not fail the read
            data["species_name"] = None

        # The effective medium, resolved once on the detail view for the same
        # reason as the species name. The cascade is the one PlantInstance
        # declares and WateringService applies: an explicit override wins, else
        # the referenced Substrate's own type. Rebuilding that order in a recipe
        # would be a second opinion on the same data.
        data["substrate_type"] = plant.substrate_type_override
        if plant.substrate_key:
            try:
                substrate = ctx.substrate_service.get_substrate(plant.substrate_key)
                data["substrate_type"] = data["substrate_type"] or getattr(substrate, "type", None)
                data["substrate_name"] = getattr(substrate, "name", None)
            except Exception:  # noqa: BLE001 — a missing catalogue entry must not fail the read
                data["substrate_name"] = None
        else:
            data["substrate_name"] = None

        name = plant.plant_name or plant.instance_id
        return self._response(
            summary=f"Plant '{name}' ({data.get('species_name') or plant.species_key}).",
            data=data,
            links=[ctx.api_link(f"/plants/{plant.key}"), ctx.ui_link(f"/plants/{plant.key}")],
        )


@mcp_tool(name="list_plants_at_location", permission=McpPermission.READ)
class ListPlantsAtLocation(ToolBase):
    """List the plants standing at a given site, location/bed or slot."""

    class Input(TenantToolInput):
        site_key: str | None = None
        location_key: str | None = None
        slot_key: str | None = None
        include_archived: bool = Field(default=False)
        limit: int = Field(default=_MAX_LIMIT, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        wanted = {
            "site_key": args.site_key,
            "location_key": args.location_key,
            "slot_key": args.slot_key,
        }
        given = {field: value for field, value in wanted.items() if value}
        if not given:
            from app.common.exceptions import ValidationError

            raise ValidationError("Pass at least one of site_key, location_key or slot_key.")

        # Same reason as in list_plants: filter across the tenant's set, not within
        # one page, or a bed's plants go missing depending on insertion order.
        plants, total = ctx.plant_service.list_plants(offset=0, limit=_SCAN_LIMIT, tenant_key=ctx.tenant_key)
        selected = [
            p
            for p in plants
            if (args.include_archived or not p.removed_on)
            and all(getattr(p, field, None) == value for field, value in given.items())
        ]
        page = selected[: args.limit]
        truncated = total > _SCAN_LIMIT
        where = ", ".join(f"{field}={value}" for field, value in given.items())
        summary = f"{len(selected)} plants at {where}."
        if truncated:
            summary += f" Only the first {_SCAN_LIMIT} records were searched."
        return self._response(
            summary=summary,
            data={
                "count": len(page),
                "matched": len(selected),
                "truncated": truncated,
                "filter": given,
                "items": [_summarise(p) for p in page],
            },
            links=[ctx.api_link("/plants"), ctx.ui_link("/plants")],
        )


@mcp_tool(name="get_plant_care_log", permission=McpPermission.READ)
class GetPlantCareLog(ToolBase):
    """Return a plant's confirmed care history — watering, fertilising and the rest."""

    class Input(TenantToolInput):
        plant_key: str
        reminder_type: ReminderType | None = Field(
            default=None,
            description="Restrict to one kind of care, e.g. 'watering' for the watering log.",
        )
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # get_confirmation_history takes no tenant, so establish ownership first —
        # the same fetch-then-use guard confirm_care_task applies (SEC-001).
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)

        entries = ctx.care_service.get_confirmation_history(
            plant.key,
            args.reminder_type,
            limit=args.limit,
        )
        items = [
            {
                "confirmed_at": e.confirmed_at,
                "reminder_type": e.reminder_type,
                "action": e.action,
                "notes": e.notes,
                "interval_at_time_days": e.interval_at_time,
            }
            for e in entries
        ]
        name = plant.plant_name or plant.instance_id
        kind = f" ({args.reminder_type})" if args.reminder_type else ""
        latest = items[0]["confirmed_at"] if items else None
        return self._response(
            summary=f"{len(items)} care entries{kind} for '{name}'."
            + (f" Most recent: {latest}." if latest else " No care recorded yet."),
            data={"plant_key": plant.key, "count": len(items), "items": items},
            links=[ctx.api_link(f"/plants/{plant.key}"), ctx.ui_link(f"/plants/{plant.key}#care")],
        )
