"""REQ-033 tools for integrated pest management (§2.1 read, §2.2 write, REQ-010).

Pests, diseases and treatments are **global** catalogue data — the same rows
every tenant sees, exactly like the species catalogue — so those tools carry no
``tenant`` argument. The exceptions are the inspection history and
``create_inspection``, which belong to a specific plant and are therefore
tenant-scoped.

The treatment data carries the safety interval (Karenz) that gates harvesting
after a chemical application; it is surfaced prominently because an LLM
recommending a treatment without it would be giving unsafe advice.

**Why the write tool had to exist.** The image-analysis process *reads*
``get_plant_inspections`` to set its prior — a pest already recorded on a plant
raises the likelihood of the same pest recurring — but before
:class:`CreateInspection` an agent had no way to *write* one. On a plant tended
entirely through agents the IPM history therefore stayed empty forever and the
prior never accumulated, no matter how often the same pest was found.
``create_inspection`` is what turns a sequence of one-off analyses into a
history; ``get_plant_inspections`` is the read tool that finds the result again
(REQ-033 §4.1 addressability rule).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.common.enums import McpPermission, PestPressureLevel, PlantPart
from app.domain.models.ipm import Inspection, InspectionFinding
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import (
    TenantToolInput,
    ToolBase,
    ToolInput,
    WriteToolBase,
    WriteToolInput,
    mcp_tool,
)
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


def _specificity_rank(beneficial: Any) -> tuple[int, str]:
    """Sort key that puts the specialist ahead of the generalist (#1007).

    Every beneficial returned for a pest does prey on it, so the list carries no
    wrong entry — only a misleading order. Ladybirds and lacewings are primarily
    aphid predators that take mites opportunistically; the predatory mites are
    what a grower actually releases against spider mites. A consumer reading
    top-down, or truncating to the first entry, recommended the ladybird.

    The proxy for specificity is the length of ``preys_on`` **ascending**: the
    fewer prey a beneficial has, the more of a specialist it is. It sorts on data
    the catalogue already carries, rather than on a specialist/generalist flag
    that would be a schema change.

    Ties break on ``scientific_name`` so that two equally specific enemies keep a
    deterministic order between reads instead of inheriting the storage order.
    """

    prey = getattr(beneficial, "preys_on", None) or []
    return len(prey), str(getattr(beneficial, "scientific_name", "") or "")


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
    """One pest in full: biology, counter-measures by IPM tier, natural enemies (specialists first)."""

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
                # Sorted by specificity against *this* pest, specialists first —
                # see _specificity_rank for the proxy and the tie-break.
                "beneficials": [
                    {
                        "common_name": b.common_name,
                        "scientific_name": b.scientific_name,
                        "preys_on": b.preys_on,
                        "description": b.description,
                    }
                    for b in sorted(detail.get("beneficials", []), key=_specificity_rank)
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
                "inspection_key": i.key,
                "inspected_at": i.inspected_at,
                "pressure_level": i.pressure_level,
                "detected_pest_keys": i.detected_pest_keys,
                "detected_disease_keys": i.detected_disease_keys,
                "symptoms_observed": i.symptoms_observed,
                # The structured half of what create_inspection wrote. Without it
                # the confidence and the plant part an agent recorded would be
                # write-only — the palette's addressability rule read the other
                # way round (§4.1): a write whose result no read tool surfaces.
                "findings": [_finding_payload(f) for f in getattr(i, "findings", [])],
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


# ── §2.2 create_inspection ────────────────────────────────────────────────────
#: Bound on one call's findings. An inspection is one visit to one plant; beyond
#: this the payload stops being an observation and starts being a data dump, and
#: each finding costs up to two catalogue lookups for its pest/disease reference.
MAX_FINDINGS_PER_INSPECTION = 25


class InspectionFindingInput(BaseModel):
    """The finding shape an analysis agent actually produces.

    Named to match ``DiaryFinding`` (REQ-050 §5) where the concepts coincide, so
    a result reached through ``submit_diary_analysis`` can become an inspection
    without renaming anything. Bounds are declared on the domain model
    :class:`~app.domain.models.ipm.InspectionFinding`; they are repeated in the
    field descriptions here only so a recipe reading the published ``inputSchema``
    learns them without being rejected first.
    """

    symptom: str = Field(min_length=1, max_length=500, description="What was observed, in plain words.")
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How sure the observer is, 0.0-1.0. Omit rather than guessing.",
    )
    affected_plant_part: PlantPart | None = Field(
        default=None,
        description="Which part of the plant shows it: leaf, stem, root, flower or fruit.",
    )
    pest_key: str | None = Field(default=None, description="Attributed pest, from list_pests. Omit when unsure.")
    disease_key: str | None = Field(
        default=None,
        description="Attributed disease, from list_diseases. Omit when unsure.",
    )
    rationale: str | None = Field(default=None, max_length=2000, description="Why this reading, max 2000 characters.")


def _finding_payload(finding: Any) -> dict[str, Any]:
    return {
        "symptom": finding.symptom,
        "confidence": finding.confidence,
        "affected_plant_part": str(finding.affected_plant_part) if finding.affected_plant_part else None,
        "pest_key": finding.pest_key,
        "disease_key": finding.disease_key,
        "rationale": finding.rationale,
    }


@mcp_tool(name="create_inspection", permission=McpPermission.WRITE)
class CreateInspection(WriteToolBase):
    """Record an IPM inspection for a plant: pressure level, symptoms and structured findings."""

    class Input(WriteToolInput):
        plant_key: str = Field(description="Key of the inspected plant. Resolve it with list_plants.")
        pressure_level: PestPressureLevel = Field(
            default=PestPressureLevel.NONE,
            description="Observed pest pressure: none, low, medium, high or critical.",
        )
        findings: list[InspectionFindingInput] = Field(
            default_factory=list,
            max_length=MAX_FINDINGS_PER_INSPECTION,
            description=(
                "Structured observations — symptom, confidence, affected plant part. "
                "Their symptom strings are mirrored into symptoms_observed automatically."
            ),
        )
        symptoms_observed: list[str] = Field(
            default_factory=list,
            description="Plain symptom strings, for observations that carry no confidence or plant part.",
        )
        detected_pest_keys: list[str] = Field(
            default_factory=list,
            description="Pests identified, from list_pests. Merged with the pest_keys named in findings.",
        )
        detected_disease_keys: list[str] = Field(
            default_factory=list,
            description="Diseases identified, from list_diseases. Merged with the disease_keys named in findings.",
        )
        inspector: str = Field(
            default="",
            max_length=200,
            description="Who inspected. Defaults to the calling account when left empty.",
        )
        inspected_at: datetime | None = Field(
            default=None,
            description="When the inspection happened (ISO-8601 UTC). Defaults to now.",
        )
        environmental_conditions: dict | None = Field(
            default=None,
            description="Conditions at inspection time, e.g. {'temperature_c': 24.5, 'humidity_percent': 62}.",
        )
        notes: str | None = Field(default=None, max_length=2000, description="Free-form remark, max 2000 characters.")

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, pest_keys, disease_keys, symptoms = self._resolve(ctx, args)
        return self._response(
            summary=(
                f"Would record a '{args.pressure_level}' inspection for plant '{plant.key}' "
                f"with {len(symptoms)} symptoms, {len(pest_keys)} pests and {len(disease_keys)} diseases."
            ),
            data={
                "plant_key": plant.key,
                "pressure_level": str(args.pressure_level),
                "symptoms_observed": symptoms,
                "detected_pest_keys": pest_keys,
                "detected_disease_keys": disease_keys,
                "findings": [_finding_payload(f) for f in args.findings],
            },
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        plant, pest_keys, disease_keys, symptoms = self._resolve(ctx, args)
        inspection = Inspection(
            tenant_key=ctx.tenant_key,
            plant_key=plant.key,
            # Attribution defaults to the calling account rather than staying
            # empty: an inspection with no inspector is indistinguishable from a
            # legacy row, and REQ-050's disclosure rule is that a machine-written
            # record says so.
            inspector=args.inspector.strip() or f"mcp:{ctx.principal.account_key}",
            inspected_at=args.inspected_at,
            pressure_level=args.pressure_level,
            detected_pest_keys=pest_keys,
            detected_disease_keys=disease_keys,
            symptoms_observed=symptoms,
            findings=[InspectionFinding(**finding.model_dump()) for finding in args.findings],
            environmental_conditions=args.environmental_conditions,
            notes=args.notes,
        )
        # create_inspection re-verifies the plant against inspection.tenant_key in
        # the repository (#517) before wiring any edge, so the ownership gate holds
        # even if this call site were ever refactored past the fetch above.
        created = ctx.ipm_service.create_inspection(plant.key, inspection)

        name = plant.plant_name or plant.instance_id
        return self._response(
            summary=(
                f"Recorded a '{created.pressure_level}' inspection for '{name}' "
                f"({len(created.symptoms_observed)} symptoms, {len(created.detected_pest_keys)} pests)."
            ),
            data={
                "inspection_key": created.key,
                "plant_key": created.plant_key,
                "inspected_at": created.inspected_at,
                "inspector": created.inspector,
                "pressure_level": str(created.pressure_level),
                "detected_pest_keys": list(created.detected_pest_keys),
                "detected_disease_keys": list(created.detected_disease_keys),
                "symptoms_observed": list(created.symptoms_observed),
                "findings": [_finding_payload(f) for f in created.findings],
                "notes": created.notes,
            },
            links=[
                ctx.api_link(f"/ipm/plants/{created.plant_key}/inspections"),
                ctx.ui_link(f"/plants/{created.plant_key}#ipm"),
            ],
        )

    @staticmethod
    def _resolve(ctx: ToolContext, args: Input) -> tuple[Any, list[str], list[str], list[str]]:
        """Ownership-check the plant, validate every catalogue key, merge the lists.

        Both the preview and the real call run this, so a dry run cannot approve
        an inspection the write would reject.

        Pest and disease keys are validated because the repository wires a
        ``detected_pest`` edge to ``pests/{key}`` without looking: an unchecked
        key becomes a dangling edge that every later graph traversal has to step
        over. They are *global* catalogue reads, so no tenant is involved and
        validating them leaks nothing.

        Symptoms and catalogue keys are merged from the two channels — the flat
        lists and the structured findings — and deduplicated with insertion order
        preserved, so an agent that fills only ``findings`` still produces a row
        that the existing ``symptoms_observed`` readers (the UI among them) can
        read.
        """

        plant = ctx.plant_service.get_plant(args.plant_key, tenant_key=ctx.tenant_key)

        symptoms = list(args.symptoms_observed) + [f.symptom for f in args.findings]
        pest_keys = list(args.detected_pest_keys) + [f.pest_key for f in args.findings if f.pest_key]
        disease_keys = list(args.detected_disease_keys) + [f.disease_key for f in args.findings if f.disease_key]

        pest_keys = list(dict.fromkeys(pest_keys))
        disease_keys = list(dict.fromkeys(disease_keys))
        for pest_key in pest_keys:
            ctx.ipm_service.get_pest(pest_key)
        for disease_key in disease_keys:
            ctx.ipm_service.get_disease(disease_key)

        return plant, pest_keys, disease_keys, list(dict.fromkeys(symptoms))


__all__ = [
    "MAX_FINDINGS_PER_INSPECTION",
    "CreateInspection",
    "GetDisease",
    "GetPest",
    "GetPlantInspections",
    "GetTreatment",
    "InspectionFindingInput",
    "ListDiseases",
    "ListPests",
]
