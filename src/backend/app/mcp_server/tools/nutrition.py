"""REQ-033 read tools for nutrient plans (§2.1, REQ-004).

A nutrient plan carries the per-phase feeding targets — NPK ratio, EC, secondary
nutrients and the week window each phase covers. These tools expose them so an
LLM can answer "what should I be feeding this plant right now" from the user's
real plan instead of from general horticultural lore.

Nutrient plans are a **hybrid catalogue**: a tenant sees its own plans plus the
globally seeded templates (which carry an empty ``tenant_key``). The service's
``verify_tenant_read_access`` implements that split; these read tools inherit it
rather than reimplementing the rule.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, mcp_tool
from app.mcp_server.context import ToolContext

_MAX_LIMIT = 100

#: How many records are read before filtering. Filtering within a single page
#: turns "not on this page" into "does not exist" — see plant_reads._SCAN_LIMIT.
_SCAN_LIMIT = 500


def _plan_summary(plan: Any) -> dict[str, Any]:
    return {
        "plan_key": plan.key,
        "name": plan.name,
        "description": plan.description,
        "is_template": plan.is_template,
        # An empty tenant_key is what marks a globally seeded plan.
        "is_global_template": not getattr(plan, "tenant_key", ""),
        "recommended_substrate_type": getattr(plan, "recommended_substrate_type", None),
        "version": plan.version,
        "tags": plan.tags,
    }


def _entry_summary(entry: Any) -> dict[str, Any]:
    """One phase row, trimmed to what actually drives a feeding decision."""

    data = {
        "phase_name": entry.phase_name,
        "sequence_order": entry.sequence_order,
        "week_start": entry.week_start,
        "week_end": entry.week_end,
        "is_recurring": entry.is_recurring,
        "npk_ratio": list(entry.npk_ratio) if entry.npk_ratio else None,
        "target_ec_ms": getattr(entry, "target_ec_ms", None),
    }
    # Secondary nutrients are frequently unset; drop them rather than padding the
    # answer with a dozen nulls the model has to read past.
    for field in ("calcium_ppm", "magnesium_ppm", "sulfur_ppm", "iron_ppm"):
        value = getattr(entry, field, None)
        if value is not None:
            data[field] = value
    return data


@mcp_tool(name="list_nutrient_plans", permission=McpPermission.READ)
class ListNutrientPlans(ToolBase):
    """List the nutrient plans available here — the tenant's own plus global templates."""

    class Input(TenantToolInput):
        query: str | None = Field(default=None, description="Case-insensitive substring filter over name and tags.")
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Read before filtering, not one page of it — see the note on _SCAN_LIMIT.
        plans, total = ctx.nutrient_plan_service.list_plans(
            offset=0,
            limit=_SCAN_LIMIT,
            tenant_key=ctx.tenant_key,
        )
        selected = list(plans)
        if args.query:
            needle = args.query.strip().lower()
            selected = [p for p in selected if needle in f"{p.name} {' '.join(p.tags or [])}".lower()]

        page = selected[args.offset : args.offset + args.limit]
        truncated = total > _SCAN_LIMIT
        summary = f"{len(selected)} nutrient plans available (of {total})."
        if truncated:
            summary += f" Only the first {_SCAN_LIMIT} were searched."
        return self._response(
            summary=summary,
            data={
                "count": len(page),
                "matched": len(selected),
                "total": total,
                "truncated": truncated,
                "items": [_plan_summary(p) for p in page],
            },
            links=[ctx.api_link("/nutrient-plans"), ctx.ui_link("/nutrient-plans")],
        )


@mcp_tool(name="get_nutrient_plan", permission=McpPermission.READ)
class GetNutrientPlan(ToolBase):
    """Return one nutrient plan with its per-phase feeding targets (NPK, EC, week window)."""

    class Input(TenantToolInput):
        plan_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Read access spans own + global plans; a foreign tenant's plan raises.
        plan = ctx.nutrient_plan_service.get_plan(args.plan_key, tenant_key=ctx.tenant_key)
        entries = ctx.nutrient_plan_service.get_phase_entries(plan.key)
        ordered = sorted(entries, key=lambda e: (e.sequence_order, e.week_start))

        data = _plan_summary(plan)
        data["phases"] = [_entry_summary(e) for e in ordered]
        return self._response(
            summary=f"Nutrient plan '{plan.name}' with {len(ordered)} phase entries.",
            data=data,
            links=[ctx.api_link(f"/nutrient-plans/{plan.key}"), ctx.ui_link(f"/nutrient-plans/{plan.key}")],
        )


@mcp_tool(name="get_plant_nutrient_plan", permission=McpPermission.READ)
class GetPlantNutrientPlan(ToolBase):
    """Return the nutrient plan assigned to one plant, with its phase targets."""

    class Input(TenantToolInput):
        plant_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # Ownership is established on the plant (SEC-001, the same fetch-then-use
        # guard the care log applies) *and* carried into the plan lookup, which is
        # tenant-scoped since #927 — the second half of that pair no longer
        # depends on this call site remembering the first.
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        plan = ctx.nutrient_plan_service.get_plant_plan(plant.key, tenant_key=ctx.tenant_key)

        name = plant.plant_name or plant.instance_id
        if plan is None:
            return self._response(
                summary=f"No nutrient plan is assigned to '{name}'.",
                data={"plant_key": plant.key, "plan": None},
                links=[ctx.ui_link(f"/plants/{plant.key}")],
            )

        entries = ctx.nutrient_plan_service.get_phase_entries(plan.key)
        ordered = sorted(entries, key=lambda e: (e.sequence_order, e.week_start))
        data = _plan_summary(plan)
        data["plant_key"] = plant.key
        data["phases"] = [_entry_summary(e) for e in ordered]
        return self._response(
            summary=f"'{name}' follows nutrient plan '{plan.name}' ({len(ordered)} phases).",
            data=data,
            links=[ctx.api_link(f"/nutrient-plans/{plan.key}"), ctx.ui_link(f"/plants/{plant.key}")],
        )
