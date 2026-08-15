"""REQ-033 fertiliser-calculator tools (§2.1, REQ-004/REQ-004-A).

``calculate_mixing_protocol`` runs the canonical EC-budget pipeline: it turns a
target volume, target EC/pH and a set of fertilisers into per-product doses,
ordered by the mixing sequence that keeps the solution from precipitating.

``list_fertilizers`` exists because of it. The calculator takes ``fertilizer_keys``,
and a key nobody can look up is an argument nobody can fill — the same
addressability rule recorded in REQ-033 §4.1. The two ship together.

Both are read tools: the calculator computes and returns, it persists nothing.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission, PhaseName, SubstrateType
from app.domain.engines.phase_role_map import ec_phase
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, mcp_tool
from app.mcp_server.context import ToolContext

_MAX_LIMIT = 100


@mcp_tool(name="list_fertilizers", permission=McpPermission.READ)
class ListFertilizers(ToolBase):
    """List the fertilisers available here — own products plus global entries."""

    class Input(TenantToolInput):
        query: str | None = Field(default=None, description="Case-insensitive filter over product name and brand.")
        organic_only: bool = Field(default=False, description="Restrict to organic products.")
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        ferts, total = ctx.fertilizer_service.list_fertilizers(
            offset=0,
            limit=_MAX_LIMIT,
            tenant_key=ctx.tenant_key,
        )
        selected = list(ferts)
        if args.organic_only:
            selected = [f for f in selected if f.is_organic]
        if args.query:
            needle = args.query.strip().lower()
            selected = [f for f in selected if needle in f"{f.product_name} {f.brand}".lower()]

        page = selected[: args.limit]
        items = [
            {
                "fertilizer_key": f.key,
                "product_name": f.product_name,
                "brand": f.brand,
                "fertilizer_type": f.fertilizer_type,
                "is_organic": f.is_organic,
                "npk_ratio": list(f.npk_ratio) if f.npk_ratio else None,
                "ec_contribution_per_ml": f.ec_contribution_per_ml,
                # A product whose EC contribution is only estimated makes every
                # dose derived from it an estimate too — surface it, don't bury it.
                "ec_contribution_uncertain": f.ec_contribution_uncertain,
                "max_dose_ml_per_liter": f.max_dose_ml_per_liter,
            }
            for f in page
        ]
        return self._response(
            summary=f"{len(page)} fertilisers available (of {total}).",
            data={"count": len(page), "total": total, "items": items},
            links=[ctx.api_link("/fertilizers"), ctx.ui_link("/fertilizers")],
        )


@mcp_tool(name="calculate_mixing_protocol", permission=McpPermission.READ)
class CalculateMixingProtocol(ToolBase):
    """Compute per-fertiliser doses for a target volume and EC, in mixing order."""

    class Input(TenantToolInput):
        fertilizer_keys: list[str] = Field(
            min_length=1,
            description="Keys of the fertilisers to mix — discover them with list_fertilizers.",
        )
        target_volume_liters: float = Field(gt=0, le=10000)
        target_ec_ms: float = Field(gt=0, le=10, description="Target EC of the finished solution in mS/cm.")
        base_water_ec: float = Field(
            default=0.0,
            ge=0,
            le=5,
            description="EC of the water before anything is added. Subtracted from the target (EC-net).",
        )
        target_ph: float = Field(default=6.0, ge=0, le=14)
        base_water_ph: float = Field(default=7.2, ge=0, le=14)
        alkalinity_ppm: float = Field(
            default=0,
            ge=0,
            le=500,
            description="Carbonate hardness of the base water; drives the pH reserve.",
        )
        substrate_type: SubstrateType = SubstrateType.COCO
        substrate_key: str | None = Field(
            default=None,
            description=(
                "Key of the actual medium. When given, its recorded properties are used and "
                "`substrate_type` is ignored. Omit to fall back to the coarse type."
            ),
        )
        phase: str = Field(
            default="vegetative",
            description=(
                "Growth phase driving the EC target. Accepts a phase-definition key from the "
                "v0027 catalogue (e.g. 'active_growth', 'establishment', 'bract_coloring') OR a "
                "coarse nutrient phase ('seedling', 'vegetative', 'flowering', 'ripening', "
                "'flushing', 'dormancy'). A plant on a fine-typed sequence has no coarse phase, so "
                "pass its current_phase_key directly — it is resolved to the matching feeding band."
            ),
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        from app.domain.engines.ec_budget_engine import (
            EcBudgetCalculator,
            EcBudgetFertilizerInput,
            EcBudgetInput,
        )

        # Resolve each fertiliser through the tenant-scoped service: a product of
        # another tenant raises not_found rather than silently entering the mix.
        inputs: list[EcBudgetFertilizerInput] = []
        uncertain: list[str] = []
        for key in args.fertilizer_keys:
            fert = ctx.fertilizer_service.get_fertilizer(key, tenant_key=ctx.tenant_key)
            if fert.ec_contribution_uncertain:
                uncertain.append(fert.product_name)
            inputs.append(
                EcBudgetFertilizerInput(
                    key=key,
                    product_name=fert.product_name,
                    ec_contribution_per_ml=fert.ec_contribution_per_ml,
                    ec_contribution_uncertain=fert.ec_contribution_uncertain,
                    max_dose_ml_per_liter=fert.max_dose_ml_per_liter,
                    fertilizer_type=fert.fertilizer_type,
                )
            )

        # Resolve the (possibly fine-typed) phase key to the coarse EC vocabulary
        # the budget engine keys its EC_MAX table on. Before this, the tool only
        # accepted the pre-#576 PhaseName enum, so a plant on a v0027 fine-typed
        # sequence (e.g. 'active_growth') had no valid phase to pass and the feed
        # calc silently fell to a wrong band (#1099 defect 4).
        resolved_phase = PhaseName(ec_phase(args.phase))

        # P4 of #1098: prefer the *recorded* medium over the coarse enum.
        #
        # The engine takes a `SubstrateType`, and two media of the same type can
        # differ in exactly the properties that decide a safe dose — the mix
        # created in the #1098 session had CEC 6.1 against Light-Mix's 12, `low`
        # buffer capacity against `medium`, and 0.6 mS already in the medium. A
        # dose computed for "soil" is a dose computed for twice the buffering the
        # plant actually sits in.
        #
        # Resolving the key here does two things the enum could not: it takes the
        # medium's *own* type rather than one the caller guessed, and it surfaces
        # the properties in the response so the number can be checked against the
        # medium it was computed for. Scoped, so a foreign mix is `not_found`.
        substrate_type = args.substrate_type
        resolved_substrate: dict[str, object] | None = None
        if args.substrate_key is not None:
            medium = ctx.substrate_service.get_substrate(args.substrate_key, tenant_key=ctx.tenant_key)
            substrate_type = medium.type
            resolved_substrate = {
                "substrate_key": medium.key,
                "name_de": medium.name_de,
                "type": medium.type,
                "cec_meq_per_100cm3": medium.cec_meq_per_100cm3,
                "buffer_capacity": medium.buffer_capacity,
                "ec_base_ms": medium.ec_base_ms,
                "ph_base": medium.ph_base,
            }

        result = EcBudgetCalculator().calculate(
            EcBudgetInput(
                base_water_ec=args.base_water_ec,
                target_ec=args.target_ec_ms,
                alkalinity_ppm=args.alkalinity_ppm,
                substrate=substrate_type,
                phase=resolved_phase,
                volume_liters=args.target_volume_liters,
                fertilizers=inputs,
                recipe_ml_per_liter={},
            )
        )

        dosages = [
            {
                "fertilizer_key": row.get("key"),
                "product_name": row.get("product_name", ""),
                "ml_per_liter": row.get("ml_per_liter", 0.0),
                "total_ml": row.get("total_ml", 0.0),
                "ec_contribution": row.get("ec_contribution", 0.0),
            }
            for row in result.dosage_table
        ]

        data: dict[str, Any] = {
            "valid": result.valid,
            "target_volume_liters": args.target_volume_liters,
            "target_ec_ms": args.target_ec_ms,
            "base_water_ec": args.base_water_ec,
            # The phase as given and the coarse EC band it resolved to — so a
            # fine-typed phase key is visibly mapped, not silently reinterpreted.
            "phase": args.phase,
            "resolved_ec_phase": resolved_phase.value,
            # EC-net is the budget the fertilisers actually have to fill.
            "ec_net": result.ec_net,
            "ec_ph_reserve": result.ec_ph_reserve,
            "calculated_ec": result.ec_final,
            # Order matters: the sequence prevents precipitation (REQ-004).
            "dosages": dosages,
            "instructions": result.dosage_instructions,
            "warnings": list(result.warnings),
        }
        if uncertain:
            data["estimated_ec_products"] = uncertain
        if resolved_substrate is not None:
            # Reported back so the dose can be checked against the medium it was
            # computed for. Without this, a caller passing `substrate_key` gets a
            # number and no way to tell which properties produced it — which is
            # the state `substrate_type` alone left every caller in.
            data["substrate"] = resolved_substrate

        summary = (
            f"{len(dosages)} fertilisers for {args.target_volume_liters} L at "
            f"EC {result.ec_final:.2f} mS/cm (net {result.ec_net:.2f})."
        )
        # Both caveats can hold at once, and both matter independently: an invalid
        # mix that is *also* built on estimated figures is worse than either alone.
        # Chaining these with elif would silently drop the second one.
        if not result.valid:
            summary += " The mix does NOT satisfy the constraints — see warnings."
        if uncertain:
            summary += f" Doses are estimates: EC contribution is uncertain for {', '.join(uncertain)}."
        if resolved_substrate is None:
            # Said out loud, because the difference is invisible in the numbers.
            # A dose computed from the coarse type is computed for a *category* of
            # medium, and two media in one category can differ by a factor of two
            # in the buffering that decides whether the dose is safe (#1098 §7).
            summary += " Computed from the substrate TYPE — pass substrate_key to use the medium's own properties."
        return self._response(
            summary=summary,
            data=data,
            links=[ctx.api_link("/nutrient-calculations/mixing-protocol")],
        )
