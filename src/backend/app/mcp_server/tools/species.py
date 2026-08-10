"""REQ-033 species read tools (§2.1). Delegates to ``SpeciesService``.

The species catalogue is where most of the seeded knowledge lives: the 210
``plant_info*.yaml`` records carry growth periods, sowing and harvest windows,
frost sensitivity, toxicity, propagation and nutrient demand. ``get_species_info``
returns that whole picture rather than a name and a genus, so the seeded content
can actually be inspected through MCP instead of merely confirmed to exist.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext

#: Fields that survive :func:`_drop_empty` as an explicit ``null`` (issue #1005).
#:
#: These are the fields whose *omission* a consumer reads as a negative answer
#: rather than as "no data". Dropping ``toxicity`` from an unresearched record
#: makes the response indistinguishable from one that says "not toxic" — a
#: safety clearance nobody gave, and the dangerous direction to be wrong in.
#: The same holds for ``allows_harvest``: an agent reasoning about a harvest gate
#: must be able to tell "no harvest data" from "this species must not be
#: harvested" (see #1002 for the value side of that field).
#:
#: This is a deliberate *carve-out*, not a new default. Every other field keeps
#: the sparse-reads-as-sparse behaviour documented on ``_drop_empty`` — turning
#: the whole record into explicit nulls would destroy the property that a sparse
#: response is itself the answer to "is this record complete?" (#949).
SAFETY_CRITICAL_FIELDS = frozenset(
    {
        "toxicity",
        "toxicity_severity",
        "allergen_info",
        "allows_harvest",
    }
)


def _drop_empty(data: dict[str, Any], *, keep: frozenset[str] = frozenset()) -> dict[str, Any]:
    """Strip null/empty values so an unpopulated record reads as sparse, not noisy.

    Deliberately keeps ``False`` and ``0``: on this catalogue both are meaningful
    answers (``allows_harvest=False``, ``base_temp=0``), not missing data.

    ``keep`` names the fields that are emitted even when empty — see
    :data:`SAFETY_CRITICAL_FIELDS` for why that exception exists and why it is
    kept small.
    """

    return {k: v for k, v in data.items() if k in keep or (v is not None and v != [] and v != "")}


def _cultivar_summary(cultivar: Any) -> dict[str, Any]:
    return _drop_empty(
        {
            "cultivar_key": cultivar.key,
            "name": cultivar.name,
            "species_key": cultivar.species_key,
            "breeder": cultivar.breeder,
            "breeding_year": cultivar.breeding_year,
            "traits": list(cultivar.traits or []),
            "seed_type": getattr(cultivar, "seed_type", None),
            "days_to_maturity": getattr(cultivar, "days_to_maturity", None),
            "dtm_reference": getattr(cultivar, "dtm_reference", None),
        }
    )


@mcp_tool(name="list_species", permission=McpPermission.READ)
class ListSpecies(ToolBase):
    """List the plant species catalog (paginated)."""

    class Input(ToolInput):
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=25, ge=1, le=100)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-003 (#808): scope to the GLOBAL seed catalogue only (tenant_key="").
        # These species tools are registered as *tenant-agnostic* global tools
        # (their Input is ToolInput, not TenantToolInput), so the dispatcher binds
        # no membership and ``ctx.tenant_key`` would raise — there is no single
        # acting tenant to union against. The safe, honest scope is therefore the
        # shared catalogue every principal may see: ``tenant_key=""`` collapses the
        # hybrid union to global-only, so a foreign (and any tenant-owned) species
        # is excluded, closing the previous whole-catalogue leak (tenant_key=None).
        species, total = ctx.species_service.list_species(offset=args.offset, limit=args.limit, tenant_key="")
        data = {
            "total": total,
            "items": [
                {
                    "species_key": s.key,
                    "scientific_name": s.scientific_name,
                    "common_names": s.common_names,
                    "genus": s.genus,
                }
                for s in species
            ],
        }
        return self._response(
            summary=f"{total} species in the catalog ({len(species)} returned).",
            data=data,
            links=[{"type": "api", "url": "/api/v1/species"}],
        )


@mcp_tool(name="get_species_info", permission=McpPermission.READ)
class GetSpeciesInfo(ToolBase):
    """Full stammdaten for one species: timing, hardiness, toxicity, companions, cultivars."""

    class Input(ToolInput):
        species_key: str
        include_cultivars: bool = Field(
            default=True,
            description="Include the cultivars recorded for this species.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-003 (#808): global-only scope, for the same reason as list_species
        # above — this is a tenant-agnostic global tool with no membership bound,
        # so it resolves species against the shared catalogue (tenant_key="").
        # A foreign (or tenant-owned) key answers not_found rather than leaking.
        species = ctx.species_service.get_species(args.species_key, tenant_key="")
        try:
            companions = ctx.species_service.get_compatible_species(args.species_key)
        except Exception:  # noqa: BLE001 — companion graph is optional context
            companions = []

        get = lambda field: getattr(species, field, None)  # noqa: E731 - local shorthand
        data = _drop_empty(
            {
                "species_key": species.key,
                "scientific_name": species.scientific_name,
                "common_names": species.common_names,
                "synonyms": get("synonyms"),
                "genus": species.genus,
                "family_key": get("family_key"),
                "growth_habit": get("growth_habit"),
                "root_type": get("root_type"),
                "plant_category": get("plant_category"),
                "description": get("description"),
                "native_habitat": get("native_habitat"),
                # ── The phase-sequence resolver's own discriminators (issue #949).
                # Not cosmetic: ``plant_category``, ``photosynthesis_type`` and
                # ``growth_habit`` are what decide which sequence a species lands on,
                # so an agent assessing a resolution could otherwise see neither the
                # inputs of the decision nor whether the record is complete enough to
                # resolve at all. An empty ``photosynthesis_type`` alone is what put a
                # perennial tree on a 126-day annual harvest cycle. ``_drop_empty``
                # omits the nulls, so a sparse record reads as sparse — which is
                # itself the answer to "is this record complete?".
                "photosynthesis_type": get("photosynthesis_type"),
                "indoor_suitable": get("indoor_suitable"),
                "mature_height_cm": get("mature_height_cm"),
                # ── Timing: the part the sowing calendar and task engine build on
                "direct_sow_months": get("direct_sow_months"),
                "harvest_months": get("harvest_months"),
                "bloom_months": get("bloom_months"),
                "pruning_months": get("pruning_months"),
                "sowing_indoor_weeks_before_last_frost": get("sowing_indoor_weeks_before_last_frost"),
                "sowing_outdoor_after_last_frost_days": get("sowing_outdoor_after_last_frost_days"),
                "harvest_from_year": get("harvest_from_year"),
                "bloom_from_year": get("bloom_from_year"),
                # ── Climate and feeding
                "hardiness_zones": get("hardiness_zones"),
                "frost_sensitivity": get("frost_sensitivity"),
                "base_temp_gdd": get("base_temp"),
                "nutrient_demand_level": get("nutrient_demand_level"),
                "green_manure_suitable": get("green_manure_suitable"),
                # ── Safety: never omitted *at all*, an LLM must be able to warn.
                # These three and ``allows_harvest`` below are the
                # SAFETY_CRITICAL_FIELDS carve-out: they stay in the payload as
                # explicit nulls when unpopulated, so "we have no toxicity data"
                # cannot be mistaken for "this species is not toxic" (#1005).
                "toxicity": get("toxicity"),
                "toxicity_severity": get("toxicity_severity"),
                "allergen_info": get("allergen_info"),
                # ── Cultivation ("allows_harvest" is safety-critical, see above)
                "allows_harvest": get("allows_harvest"),
                "harvest_pattern": get("harvest_pattern"),
                "traits": get("traits"),
                "growing_periods": [
                    _drop_empty(gp.model_dump()) if hasattr(gp, "model_dump") else gp
                    for gp in (get("growing_periods") or [])
                ],
                "seed_profile": (
                    species.seed_profile.model_dump() if getattr(species, "seed_profile", None) is not None else None
                ),
                "compatible_companions": companions,
            },
            keep=SAFETY_CRITICAL_FIELDS,
        )

        if args.include_cultivars:
            try:
                # SEC-003 pendant (#1090): global-only, same reasoning as the species
                # read above — a tenant-owned cultivar of a global species must not
                # appear in this block. The species itself was already resolved with
                # ``tenant_key=""``, so the co-scoped parent check inside
                # ``list_cultivars`` can only agree; the ``except`` below therefore
                # still means "no cultivars", not "scope refused".
                cultivars = ctx.species_service.list_cultivars(args.species_key, tenant_key="")
            except Exception:  # noqa: BLE001 — a species without cultivars is normal
                cultivars = []
            if cultivars:
                data["cultivars"] = [_cultivar_summary(c) for c in cultivars]

        common = (species.common_names or [None])[0]
        label = f"{species.scientific_name}" + (f" ({common})" if common else "")
        # Count the values that actually carry something. ``len(data)`` used to be
        # the same number, but the safety carve-out puts unpopulated fields into
        # the payload — counting those would make the summary an LLM may read on
        # its own claim more than the record says.
        populated = sum(1 for value in data.values() if value is not None)
        return self._response(
            summary=f"Species {label}: {populated} populated fields, "
            f"{len(data.get('cultivars', []))} cultivars, {len(companions)} companions.",
            data=data,
            links=[{"type": "api", "url": f"/api/v1/species/{species.key}"}],
        )


@mcp_tool(name="list_cultivars", permission=McpPermission.READ)
class ListCultivars(ToolBase):
    """List the cultivars recorded for one species."""

    class Input(ToolInput):
        species_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-003 pendant (#1090): scope to the GLOBAL seed catalogue only
        # (tenant_key=""), for the same reason as list_species above — this is a
        # tenant-agnostic global tool, the dispatcher binds no membership and
        # ``ctx.tenant_key`` would raise, so there is no acting tenant to union
        # against. ``""`` collapses the hybrid union to global-only, excluding
        # every tenant-owned cultivar; the previous tenant-less call was the
        # unscoped system read and showed an LLM client the whole catalogue.
        #
        # The argument also co-scopes the *parent species* check (C-3, operator
        # decision Q3): asking for the cultivars of a tenant-owned species raises
        # NotFoundError, which the transport publishes as the contract's
        # ``not_found``. That is deliberately not caught here — swallowing it into
        # an empty list would confirm the species key exists and re-open the
        # cross-tenant existence oracle the scoping closes.
        cultivars = ctx.species_service.list_cultivars(args.species_key, tenant_key="")
        return self._response(
            summary=f"{len(cultivars)} cultivars for species '{args.species_key}'.",
            data={
                "species_key": args.species_key,
                "count": len(cultivars),
                "items": [_cultivar_summary(c) for c in cultivars],
            },
            links=[{"type": "api", "url": f"/api/v1/species/{args.species_key}/cultivars"}],
        )


@mcp_tool(name="get_cultivar", permission=McpPermission.READ)
class GetCultivar(ToolBase):
    """Return one cultivar: breeder, traits, seed type and days to maturity."""

    class Input(ToolInput):
        cultivar_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        # SEC-003 pendant (#1090): global-only, for the same reason as the tools
        # above — a tenant-agnostic global tool has no membership bound, so it
        # resolves against the shared catalogue (tenant_key=""). A tenant-owned
        # key answers not_found rather than leaking, and it answers it exactly
        # like an absent key does (C-3 checks ownership *after* the load), so this
        # tool cannot be walked to enumerate foreign cultivars.
        cultivar = ctx.species_service.get_cultivar(args.cultivar_key, tenant_key="")
        data = _cultivar_summary(cultivar)
        return self._response(
            summary=f"Cultivar '{cultivar.name}' of species '{cultivar.species_key}'.",
            data=data,
            # Cultivars are addressed *under their species* — ``/api/v1/cultivars/{key}``
            # never existed as a route, so this link used to hand an agent a 404
            # (K3, #1090). See ``api/v1/cultivars/router.py``'s prefix.
            links=[{"type": "api", "url": f"/api/v1/species/{cultivar.species_key}/cultivars/{cultivar.key}"}],
        )
