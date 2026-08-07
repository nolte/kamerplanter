"""REQ-033 §2.2 — record a fertigation event (``record_feeding_event``).

**Why this tool is the most expensive absence in the palette.** The nutrient
process an external agent runs (``kamerplanter-goose``) reasons over a five-tier
evidence ladder whose tier 2 is *plan target versus actual supply*. Before this
tool the actual side did not exist in any machine-readable form:

* ``get_plant_care_log`` answers ``reminder_type: "watering"`` with
  ``action: "confirmed"`` — a boolean. It records *that* a feeding happened and
  never how much of what.
* ``add_plant_diary_entry``'s ``measurements`` is an open object whose units and
  provenance are unknowable, so a consuming spec has to discard ambiguous values.

With neither, tier 2 collapses to tier 3 and the process is required to refuse a
dosage recommendation. That is not a missing nicety: **undersupply and oversupply
have opposite corrections**, and a boolean cannot tell them apart. This tool
persists the four quantities that can: amount, EC, pH and the tank/solution
reference.

**Addressability (REQ-033 §4.1 palette rule).** The reference this tool takes —
``plant_key`` — is resolved by ``list_plants`` / ``get_plant``; the fertiliser
keys come from ``list_fertilizers``. Its *result* is surfaced by
:class:`~app.mcp_server.tools.diagnostics.GetPlantDiagnostics`, which returns the
tenant's feeding history for a plant together with the EC/pH trend derived from
it. A write no read tool can find again is a defect, so the two shipped together.

**Runoff versus tank EC are distinguishable here**, which the open ``measurements``
object never allowed: ``measured_ec_before``/``measured_ec_after`` describe the
solution that went in, ``runoff_ec``/``runoff_ph`` what came back out of the pot.
A recipe reading a rising salt load must not confuse the two.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.common.enums import ApplicationMethod, McpPermission
from app.domain.models.feeding_event import FeedingEvent, FeedingEventFertilizer
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.context import ToolContext

#: A single call records one fertigation, not a season of them. The bound exists
#: so a malformed recipe cannot make one call fan out into an unbounded number of
#: catalogue lookups; a real mix rarely exceeds five products.
MAX_FERTILIZERS_PER_EVENT = 20


class FeedingFertilizerInput(BaseModel):
    """One product and the amount of it that went into this feeding."""

    fertilizer_key: str = Field(description="Key from list_fertilizers.")
    ml_applied: float = Field(gt=0, description="Millilitres of this product in the mixed solution.")


def _fertilizer_payload(event: FeedingEvent) -> list[dict[str, Any]]:
    return [{"fertilizer_key": f.fertilizer_key, "ml_applied": f.ml_applied} for f in event.fertilizers_used]


@mcp_tool(name="record_feeding_event", permission=McpPermission.WRITE)
class RecordFeedingEvent(WriteToolBase):
    """Record a fertigation for a plant: amount, EC/pH before and after, runoff, tank."""

    class Input(WriteToolInput):
        plant_key: str = Field(description="Key of the plant that was fed. Resolve it with list_plants.")
        volume_applied_liters: float = Field(
            gt=0,
            description="Litres of solution applied. This is the 'how much' the care log never carried.",
        )
        application_method: ApplicationMethod = Field(
            default=ApplicationMethod.FERTIGATION,
            description="How the solution reached the plant.",
        )
        is_supplemental: bool = Field(
            default=False,
            description="True when this is an extra feed on top of the plan's schedule.",
        )
        fertilizers_used: list[FeedingFertilizerInput] = Field(
            default_factory=list,
            max_length=MAX_FERTILIZERS_PER_EVENT,
            description="Products and millilitres that went into the mix. Keys come from list_fertilizers.",
        )
        measured_ec_before: float | None = Field(
            default=None,
            ge=0,
            description="EC of the solution going in, mS/cm. Tier-1 evidence for the supply side.",
        )
        measured_ec_after: float | None = Field(default=None, ge=0, description="EC measured after feeding, mS/cm.")
        measured_ph_before: float | None = Field(default=None, ge=0, le=14, description="pH of the solution going in.")
        measured_ph_after: float | None = Field(default=None, ge=0, le=14, description="pH measured after feeding.")
        runoff_ec: float | None = Field(
            default=None,
            ge=0,
            description="EC of the drain-to-waste runoff, mS/cm — the pot's answer, not the tank's.",
        )
        runoff_ph: float | None = Field(default=None, ge=0, le=14, description="pH of the runoff.")
        runoff_volume_liters: float | None = Field(default=None, ge=0, description="Litres of runoff collected.")
        tank_fill_event_key: str | None = Field(
            default=None,
            description="Tank fill event this solution came from, if it was mixed in a tank.",
        )
        notes: str | None = Field(default=None, max_length=2000, description="Free-form remark, max 2000 characters.")

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, fertilizers = self._resolve(ctx, args)
        return self._response(
            summary=(
                f"Would record {args.volume_applied_liters} L of "
                f"'{args.application_method}' for plant '{plant.key}'"
                + (f" using {len(fertilizers)} products." if fertilizers else " with no fertiliser products.")
            ),
            data={
                "plant_key": plant.key,
                "volume_applied_liters": args.volume_applied_liters,
                "application_method": str(args.application_method),
                "fertilizers_used": [
                    {"fertilizer_key": key, "ml_applied": ml, "product_name": name} for key, ml, name in fertilizers
                ],
                "measured_ec_before": args.measured_ec_before,
                "measured_ph_before": args.measured_ph_before,
                "runoff_ec": args.runoff_ec,
                "runoff_ph": args.runoff_ph,
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, _fertilizers = self._resolve(ctx, args)
        event = FeedingEvent(
            tenant_key=ctx.tenant_key,
            plant_key=plant.key,
            application_method=args.application_method,
            is_supplemental=args.is_supplemental,
            # Stored verbatim and deliberately *not* dereferenced. A TankFillEvent
            # carries no tenant of its own and the repository offers no
            # tenant-filtered lookup by key, so resolving it here would be a new
            # unfiltered cross-tenant read — the class of hole #927/#947 closed.
            # POST /t/{slug}/feeding-events stores the same field unvalidated, so
            # this tool is no thinner a guard than the REST path it mirrors.
            tank_fill_event_key=args.tank_fill_event_key,
            volume_applied_liters=args.volume_applied_liters,
            fertilizers_used=[
                FeedingEventFertilizer(fertilizer_key=f.fertilizer_key, ml_applied=f.ml_applied)
                for f in args.fertilizers_used
            ],
            measured_ec_before=args.measured_ec_before,
            measured_ec_after=args.measured_ec_after,
            measured_ph_before=args.measured_ph_before,
            measured_ph_after=args.measured_ph_after,
            runoff_ec=args.runoff_ec,
            runoff_ph=args.runoff_ph,
            runoff_volume_liters=args.runoff_volume_liters,
            notes=args.notes,
        )
        created = ctx.feeding_service.create_event(event)

        return self._response(
            summary=(
                f"Recorded {created.volume_applied_liters} L of '{created.application_method}' "
                f"for plant '{plant.key}'."
                + (f" EC in: {created.measured_ec_before} mS/cm." if created.measured_ec_before is not None else "")
                + (f" Runoff EC: {created.runoff_ec} mS/cm." if created.runoff_ec is not None else "")
            ),
            data={
                "feeding_event_key": created.key,
                "plant_key": created.plant_key,
                "timestamp": created.timestamp,
                "application_method": str(created.application_method),
                "is_supplemental": created.is_supplemental,
                "volume_applied_liters": created.volume_applied_liters,
                "fertilizers_used": _fertilizer_payload(created),
                "measured_ec_before": created.measured_ec_before,
                "measured_ec_after": created.measured_ec_after,
                "measured_ph_before": created.measured_ph_before,
                "measured_ph_after": created.measured_ph_after,
                "runoff_ec": created.runoff_ec,
                "runoff_ph": created.runoff_ph,
                "runoff_volume_liters": created.runoff_volume_liters,
                "tank_fill_event_key": created.tank_fill_event_key,
            },
            links=[
                ctx.api_link(f"/feeding-events/plant/{created.plant_key}"),
                ctx.ui_link(f"/plants/{created.plant_key}"),
            ],
        )

    @staticmethod
    def _resolve(ctx: ToolContext, args: Input) -> tuple[Any, list[tuple[str, float, str | None]]]:
        """Ownership-check the plant and every referenced fertiliser (SEC-001).

        Both gates run on the dry-run path as well, so a preview cannot approve a
        call the real one would reject. The plant read yields the project's
        cross-tenant 404 contract (never a 403), and the fertiliser read spans the
        hybrid catalogue — the tenant's own products plus the global seeds — so a
        foreign tenant's private product is ``not_found`` here rather than a
        dangling ``feeding_used`` edge on the tenant's own record.
        """

        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        resolved: list[tuple[str, float, str | None]] = []
        for entry in args.fertilizers_used:
            fertilizer = ctx.fertilizer_service.get_fertilizer(entry.fertilizer_key, tenant_key=ctx.tenant_key)
            resolved.append((entry.fertilizer_key, entry.ml_applied, getattr(fertilizer, "product_name", None)))
        return plant, resolved


__all__ = ["MAX_FERTILIZERS_PER_EVENT", "FeedingFertilizerInput", "RecordFeedingEvent"]
