"""REQ-033 read tools for integrated pest management (§2.1, REQ-010).

Pests, diseases and treatments are **global** catalogue data — the same rows
every tenant sees, exactly like the species catalogue — so these tools carry no
``tenant`` argument. The one exception is the inspection history, which belongs
to a specific plant and is therefore tenant-scoped.

The treatment data carries the safety interval (Karenz) that gates harvesting
after a chemical application; it is surfaced prominently because an LLM
recommending a treatment without it would be giving unsafe advice.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext

_MAX_LIMIT = 100
#: The catalogue is small enough to scan in one go for a substring filter, but
#: large enough that returning all of it would swamp the answer.
_SCAN_LIMIT = 500


def _matches(*fields: Any, needle: str) -> bool:
    return needle in " ".join(str(f) for f in fields if f).lower()


def _pest_summary(pest: Any) -> dict[str, Any]:
    return {
        "pest_key": pest.key,
        "scientific_name": pest.scientific_name,
        "common_name": pest.common_name,
        "common_name_de": pest.common_name_de,
        "pest_type": pest.pest_type,
        "damage_symptoms": pest.damage_symptoms_de or pest.damage_symptoms,
    }


def _disease_summary(disease: Any) -> dict[str, Any]:
    return {
        "disease_key": disease.key,
        "scientific_name": disease.scientific_name,
        "common_name": disease.common_name,
        "pathogen_type": disease.pathogen_type,
        "incubation_period_days": disease.incubation_period_days,
        "environmental_triggers": disease.environmental_triggers,
        "affected_plant_parts": disease.affected_plant_parts,
    }


def _treatment_summary(t: Any) -> dict[str, Any]:
    return {
        "treatment_key": t.key,
        "name": t.name_de or t.name,
        "treatment_type": t.treatment_type,
        "active_ingredient": t.active_ingredient,
        "application_method": t.application_method,
        # The Karenz: days that must pass between applying this and harvesting.
        "safety_interval_days": t.safety_interval_days,
        "dosage_per_liter": t.dosage_per_liter,
        "protective_equipment": t.protective_equipment,
    }


@mcp_tool(name="list_pests", permission=McpPermission.READ)
class ListPests(ToolBase):
    """List the pest catalogue, optionally filtered by name or damage symptom."""

    class Input(ToolInput):
        query: str | None = Field(
            default=None,
            description="Case-insensitive filter over scientific, common and German names plus damage symptoms.",
        )
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        pests, total = ctx.ipm_service.list_pests(offset=0, limit=_SCAN_LIMIT)
        selected = list(pests)
        if args.query:
            needle = args.query.strip().lower()
            selected = [
                p
                for p in selected
                if _matches(
                    p.scientific_name,
                    p.common_name,
                    p.common_name_de,
                    p.damage_symptoms,
                    p.damage_symptoms_de,
                    needle=needle,
                )
            ]
        page = selected[: args.limit]
        return self._response(
            summary=f"{len(page)} pests"
            + (f" match '{args.query}'" if args.query else f" of {total} in the catalogue")
            + ".",
            data={"count": len(page), "matched": len(selected), "items": [_pest_summary(p) for p in page]},
            links=[ctx.global_link("/ipm/pests")],
        )


@mcp_tool(name="get_pest", permission=McpPermission.READ)
class GetPest(ToolBase):
    """One pest in full: biology, counter-measures by IPM tier, and its natural enemies."""

    class Input(ToolInput):
        pest_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # get_pest_detail already assembles the IPM picture: treatments sorted by
        # the prevention→monitoring→intervention hierarchy, matching beneficials
        # and the detection symptom hint.
        detail = ctx.ipm_service.get_pest_detail(args.pest_key)
        pest = detail["pest"]

        data = _pest_summary(pest)
        data.update(
            {
                "lifecycle_days": pest.lifecycle_days,
                "optimal_temp_min": pest.optimal_temp_min,
                "optimal_temp_max": pest.optimal_temp_max,
                "description": pest.description_de or pest.description,
                "detection_symptom_hint": detail.get("detection_symptom_hint"),
                # Sorted by IPM tier, so the first entries are the gentlest measures.
                "treatments": [_treatment_summary(t) for t in detail.get("treatments", [])],
                "beneficials": [
                    {
                        "common_name": b.common_name,
                        "scientific_name": b.scientific_name,
                        "preys_on": b.preys_on,
                        "description": b.description,
                    }
                    for b in detail.get("beneficials", [])
                ],
            }
        )
        name = pest.common_name_de or pest.common_name
        n_ben = len(data["beneficials"])
        return self._response(
            summary=f"{name} ({pest.scientific_name}): {len(data['treatments'])} counter-measures, "
            f"{n_ben} natural enemies.",
            data=data,
            links=[ctx.global_link(f"/ipm/pests/{pest.key}")],
        )


@mcp_tool(name="list_diseases", permission=McpPermission.READ)
class ListDiseases(ToolBase):
    """List the plant-disease catalogue, optionally filtered by name or pathogen."""

    class Input(ToolInput):
        query: str | None = Field(default=None, description="Case-insensitive filter over names and pathogen type.")
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        diseases, total = ctx.ipm_service.list_diseases(offset=0, limit=_SCAN_LIMIT)
        selected = list(diseases)
        if args.query:
            needle = args.query.strip().lower()
            selected = [
                d for d in selected if _matches(d.scientific_name, d.common_name, d.pathogen_type, needle=needle)
            ]
        page = selected[: args.limit]
        return self._response(
            summary=f"{len(page)} diseases"
            + (f" match '{args.query}'" if args.query else f" of {total} in the catalogue")
            + ".",
            data={"count": len(page), "matched": len(selected), "items": [_disease_summary(d) for d in page]},
            links=[ctx.global_link("/ipm/diseases")],
        )


@mcp_tool(name="get_disease", permission=McpPermission.READ)
class GetDisease(ToolBase):
    """One disease in full: pathogen, incubation, triggers and affected plant parts."""

    class Input(ToolInput):
        disease_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        disease = ctx.ipm_service.get_disease(args.disease_key)
        data = _disease_summary(disease)
        data["description"] = getattr(disease, "description_de", None) or getattr(disease, "description", None)
        return self._response(
            summary=f"{disease.common_name} ({disease.scientific_name}), pathogen: {disease.pathogen_type}.",
            data=data,
            links=[ctx.global_link(f"/ipm/diseases/{disease.key}")],
        )


@mcp_tool(name="get_treatment", permission=McpPermission.READ)
class GetTreatment(ToolBase):
    """One treatment in full — including the safety interval before harvest (Karenz)."""

    class Input(ToolInput):
        treatment_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        treatment = ctx.ipm_service.get_treatment(args.treatment_key)
        data = _treatment_summary(treatment)
        data.update(
            {
                "description": treatment.description_de or treatment.description,
                "how_to_apply": treatment.how_to_apply_de or treatment.how_to_apply,
                "mode_of_action": treatment.mode_of_action_de or treatment.mode_of_action,
                "precautions": treatment.precautions_de or treatment.precautions,
            }
        )
        karenz = treatment.safety_interval_days
        note = (
            f" Karenz: {karenz} days must pass before harvesting." if karenz else " No safety interval before harvest."
        )
        return self._response(
            summary=f"{data['name']} ({treatment.treatment_type})." + note,
            data=data,
            links=[ctx.global_link(f"/ipm/treatments/{treatment.key}")],
        )


@mcp_tool(name="get_plant_inspections", permission=McpPermission.READ)
class GetPlantInspections(ToolBase):
    """Return a plant's IPM inspection history: pressure level, findings, symptoms."""

    class Input(TenantToolInput):
        plant_key: str
        limit: int = Field(default=20, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # get_inspections takes no tenant, so ownership is established on the
        # plant first — the same fetch-then-use guard the care log applies.
        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)
        inspections, total = ctx.ipm_service.get_inspections(plant.key, offset=0, limit=args.limit)

        items = [
            {
                "inspected_at": i.inspected_at,
                "pressure_level": i.pressure_level,
                "detected_pest_keys": i.detected_pest_keys,
                "detected_disease_keys": i.detected_disease_keys,
                "symptoms_observed": i.symptoms_observed,
                "notes": i.notes,
            }
            for i in inspections
        ]
        name = plant.plant_name or plant.instance_id
        return self._response(
            summary=f"{len(items)} inspections recorded for '{name}' (of {total})."
            if items
            else f"No inspections recorded for '{name}' yet.",
            data={"plant_key": plant.key, "count": len(items), "total": total, "items": items},
            links=[ctx.ui_link(f"/plants/{plant.key}#ipm")],
        )
