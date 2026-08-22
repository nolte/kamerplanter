"""REQ-033 tools for nutrient plans (§2.1 read, §2.2 write, REQ-004).

A nutrient plan carries the per-phase feeding targets — NPK ratio, EC, secondary
nutrients and the week window each phase covers. These tools expose them so an
LLM can answer "what should I be feeding this plant right now" from the user's
real plan instead of from general horticultural lore.

Nutrient plans are a **hybrid catalogue**: a tenant sees its own plans plus the
globally seeded templates (which carry an empty ``tenant_key``). The service's
``verify_tenant_read_access`` implements that split; these tools inherit it
rather than reimplementing the rule.

**Binding, then the two writes that binding turned out to need.** AC-25 speaks
of "the plan assigned to a plant" as an existing state, while the palette offered
only the reading side — so the assignment came from somewhere the MCP surface
could not reach, and every plan recommendation an agent made ended as a manual
instruction it could never verify was followed. :class:`AssignNutrientPlan`
closed that last step.

**A plan editor remains out of scope**, and for the reason #931 §6 gave: phase
windows, product doses and mixing order are editing work with a UI built for it,
and a tool that could author a plan would let a model invent feeding targets
rather than pick one a human vetted. What #1244 measured is that the line, drawn
there, had a cost that scope note did not anticipate — a correctly configured
plant on a species-appropriate global template whose every phase carries
``target_ec_ms: null``. For that plant the nutrient assessment's tier 2 (plan
target versus actual supply) is not merely unanswered but **structurally
unreachable**: a perfect runoff-EC reading has nothing to be compared against,
so "measure your runoff EC" is advice that provably cannot change the outcome.
And correcting the template by hand is not the fix, because it is shared across
tenants — the correct operation is *derive a tenant-owned copy, then correct the
copy*, which was also unreachable.

:class:`CloneNutrientPlan` and :class:`SetNutrientPlanPhaseTargets` are the
smallest pair that removes that cost, and they are shaped to stay short of an
editor: one derives a copy the tenant owns, the other patches **one field group
on one phase**. Neither creates a plan from nothing, neither touches fertiliser
products, and neither can reach a global template — cloning reads the source and
writes a new tenant-owned row, and the target patch refuses anything the
tenant does not own (#1263).
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, WriteToolBase, WriteToolInput, mcp_tool
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


@mcp_tool(name="assign_nutrient_plan", permission=McpPermission.WRITE)
class AssignNutrientPlan(WriteToolBase):
    """Bind an existing nutrient plan to a plant — the plan itself is never edited."""

    class Input(WriteToolInput):
        plant_key: str = Field(description="Key of the plant to put on the plan. Resolve it with list_plants.")
        plan_key: str = Field(
            description="Key of an existing plan, own or a global template. Resolve it with list_nutrient_plans.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, plan, current = self._resolve(ctx, args)
        replaces = getattr(current, "name", None) if current is not None else None
        return self._response(
            summary=(
                f"Would assign nutrient plan '{plan.name}' to plant '{plant.key}'"
                + (f", replacing '{replaces}'." if replaces else ", which currently follows no plan.")
            ),
            data={
                "plant_key": plant.key,
                "plan_key": plan.key,
                "plan_name": plan.name,
                # An assignment replaces silently in the repository (the existing
                # FOLLOWS_PLAN edge is deleted first). Naming what would be lost is
                # the whole reason a dry run exists for this tool.
                "replaces_plan_key": getattr(current, "key", None) if current is not None else None,
                "replaces_plan_name": replaces,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, plan, current = self._resolve(ctx, args)
        ctx.nutrient_plan_service.assign_to_plant(
            plant.key,
            plan.key,
            f"mcp:{ctx.principal.account_key}",
            tenant_key=ctx.tenant_key,
        )

        name = plant.plant_name or plant.instance_id
        replaced = getattr(current, "key", None) if current is not None else None
        return self._response(
            summary=f"'{name}' now follows nutrient plan '{plan.name}'."
            + (" The previous assignment was replaced." if replaced else ""),
            data={
                "plant_key": plant.key,
                "plan_key": plan.key,
                "plan_name": plan.name,
                "replaced_plan_key": replaced,
            },
            links=[
                # get_plant_nutrient_plan is the read tool that surfaces this
                # write again (REQ-033 §4.1 addressability rule); the deep links
                # point at the same data over REST and in the UI.
                ctx.api_link(f"/plant-instances/{plant.key}/nutrient-plan"),
                ctx.ui_link(f"/plants/{plant.key}"),
            ],
        )

    @staticmethod
    def _resolve(ctx: ToolContext, args: Input) -> tuple[Any, Any, Any]:
        """Ownership-check both sides and read the assignment being replaced.

        Runs on the dry-run path too, so a preview cannot approve an assignment
        the write would refuse.

        ``get_plan`` spans the hybrid catalogue — the tenant's own plans plus the
        global templates — and raises the project's cross-tenant 404 for anything
        else, so a foreign tenant's private plan cannot be bound to this tenant's
        plant. Resolving both keys here first is the SEC-001 fetch-then-use guard,
        and it stays load-bearing even though ``assign_to_plant`` now takes a
        tenant of its own (#950): that argument scopes the *write*, while these
        lookups are what refuse a foreign key before the write is ever reached.

        This paragraph used to end "``assign_to_plant`` itself takes no tenant".
        That was true until #950 made the argument required and keyword-only, and
        the sentence then survived as the reason nobody noticed the MCP call site
        had not been updated — the tool answered 500 on every non-dry-run call
        (#1145).
        """

        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        plan = ctx.nutrient_plan_service.get_plan(args.plan_key, tenant_key=ctx.tenant_key)
        current = ctx.nutrient_plan_service.get_plant_plan(plant.key, tenant_key=ctx.tenant_key)
        return plant, plan, current


@mcp_tool(name="clone_nutrient_plan", permission=McpPermission.WRITE)
class CloneNutrientPlan(WriteToolBase):
    """Derive a tenant-owned copy of a plan so it can be corrected without touching the original."""

    class Input(WriteToolInput):
        plan_key: str = Field(
            description=("Key of the plan to copy — own or a global template. Resolve it with list_nutrient_plans."),
        )
        name: str = Field(
            default="",
            max_length=200,
            description="Name for the copy. Defaults to the source name with a 'Kopie' suffix.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        source = self._source(ctx, args)
        return self._response(
            summary=(
                f"Would copy nutrient plan '{source.name}' into this tenant as "
                f"'{self._new_name(source, args)}'. The source is not modified."
            ),
            data={
                "source_plan_key": source.key,
                "source_name": source.name,
                "source_is_global": not getattr(source, "tenant_key", ""),
                "new_name": self._new_name(source, args),
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        source = self._source(ctx, args)
        clone = ctx.nutrient_plan_service.clone_plan(
            source.key,
            self._new_name(source, args),
            f"mcp:{ctx.principal.account_key}",
            tenant_key=ctx.tenant_key,
        )
        return self._response(
            summary=(
                f"Copied '{source.name}' to '{clone.name}'. The copy belongs to this tenant; "
                "assign it with assign_nutrient_plan to put a plant on it."
            ),
            data={
                "plan_key": clone.key,
                "name": clone.name,
                "source_plan_key": source.key,
                "cloned_from_key": getattr(clone, "cloned_from_key", None),
            },
            links=[ctx.api_link(f"/nutrient-plans/{clone.key}"), ctx.ui_link(f"/duengung/plaene/{clone.key}")],
        )

    @staticmethod
    def _source(ctx: ToolContext, args: Input) -> Any:
        """Resolve the source through the READ path, on both preview and execute.

        Read, not write: cloning a global template is the whole point, and
        ``for_write=True`` refuses exactly those. The copy is tenant-owned by
        construction — ``clone_plan`` stamps ``tenant_key`` from the cloning
        tenant rather than inheriting the source's, so a copy of a global plan is
        private instead of globally visible.
        """
        return ctx.nutrient_plan_service.get_plan(args.plan_key, tenant_key=ctx.tenant_key)

    @staticmethod
    def _new_name(source: Any, args: Input) -> str:
        return args.name.strip() or f"{source.name} (Kopie)"


@mcp_tool(name="set_nutrient_plan_phase_targets", permission=McpPermission.WRITE)
class SetNutrientPlanPhaseTargets(WriteToolBase):
    """Patch the EC targets of ONE phase in a plan the tenant owns."""

    class Input(WriteToolInput):
        plan_key: str = Field(description="Key of a plan this tenant owns. Clone a template first if needed.")
        phase: str = Field(
            description=(
                "Which phase to patch: either the phase entry's key, or its phase name "
                "(e.g. 'vegetative'). Resolve both with get_nutrient_plan."
            ),
        )
        target_ec_ms: float | None = Field(
            default=None,
            ge=0,
            le=10,
            description="Target EC in mS/cm for this phase. Omit to leave unchanged.",
        )
        reference_ec_ms: float | None = Field(
            default=None,
            ge=0,
            le=10,
            description="Reference EC in mS/cm the dosage normalises against. Omit to leave unchanged.",
        )

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entry, patch = self._resolve(ctx, args)
        before = {field: getattr(entry, field, None) for field in patch}
        return self._response(
            summary=(
                f"Would set {self._describe(patch)} on phase '{entry.phase_name}' "
                f"(weeks {entry.week_start}-{entry.week_end}) of this plan."
            ),
            data={
                "plan_key": args.plan_key,
                "phase_entry_key": entry.key,
                "phase_name": str(entry.phase_name),
                "before": before,
                "after": patch,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entry, patch = self._resolve(ctx, args)
        updated = ctx.nutrient_plan_service.update_phase_entry(
            entry.key,
            patch,
            plan_key=args.plan_key,
            tenant_key=ctx.tenant_key,
        )
        return self._response(
            summary=f"Phase '{updated.phase_name}' now carries {self._describe(patch)}.",
            data={
                "plan_key": args.plan_key,
                "phase_entry_key": updated.key,
                "phase_name": str(updated.phase_name),
                "target_ec_ms": updated.target_ec_ms,
                "reference_ec_ms": updated.reference_ec_ms,
            },
            links=[ctx.api_link(f"/nutrient-plans/{args.plan_key}"), ctx.ui_link(f"/duengung/plaene/{args.plan_key}")],
        )

    @staticmethod
    def _describe(patch: dict[str, Any]) -> str:
        return ", ".join(f"{k}={v}" for k, v in patch.items())

    @classmethod
    def _resolve(cls, ctx: ToolContext, args: Input) -> tuple[Any, dict[str, Any]]:
        """Resolve the phase and build the patch, on the dry-run path too.

        A preview that skipped these checks could approve a write the execute
        refuses — the failure `assign_nutrient_plan` documents for the same
        reason.

        Ownership is NOT re-implemented here: ``update_phase_entry`` anchors on
        the entry's own plan and refuses a foreign or global one (#1263). What
        this method adds is resolving a human-usable ``phase`` and refusing an
        empty patch.
        """
        patch = {
            field: value
            for field, value in (
                ("target_ec_ms", args.target_ec_ms),
                ("reference_ec_ms", args.reference_ec_ms),
            )
            if value is not None
        }
        if not patch:
            raise ValueError(
                "Nothing to set — pass target_ec_ms and/or reference_ec_ms. "
                "This tool never clears a value: omitting a field means 'leave unchanged', "
                "so there is no way to spell 'set it back to null' by accident."
            )

        entries = ctx.nutrient_plan_service.get_phase_entries(args.plan_key)
        wanted = args.phase.strip()
        by_key = [e for e in entries if e.key == wanted]
        if by_key:
            return by_key[0], patch

        by_name = [e for e in entries if str(getattr(e.phase_name, "value", e.phase_name)) == wanted]
        if not by_name:
            names = sorted({str(getattr(e.phase_name, "value", e.phase_name)) for e in entries})
            raise ValueError(f"No phase '{wanted}' in this plan. It covers: {', '.join(names) or '(no phases)'}.")
        if len(by_name) > 1:
            # A plan may carry the same phase name twice with different week
            # windows. Picking the first would silently patch one of two, and the
            # caller could not tell which — so name the keys and let them choose.
            keys = ", ".join(f"{e.key} (weeks {e.week_start}-{e.week_end})" for e in by_name)
            raise ValueError(
                f"Phase '{wanted}' occurs {len(by_name)}x in this plan. Pass one of these keys instead: {keys}."
            )
        return by_name[0], patch


__all__ = [
    "AssignNutrientPlan",
    "CloneNutrientPlan",
    "GetNutrientPlan",
    "GetPlantNutrientPlan",
    "ListNutrientPlans",
    "SetNutrientPlanPhaseTargets",
]
