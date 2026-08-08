"""REQ-033 read tools for the remaining seeded catalogues (§2.1).

Roughly forty collections are populated from ``app/migrations/seed_data/*.yaml``.
The species, IPM, nutrient-plan and fertiliser catalogues have their own modules;
this one covers the rest that carry standing reference data an LLM needs to give
grounded answers: substrates, overwintering templates, starter kits, phase
definitions, hardiness zones and the glossary.

Two of these are tenant-scoped and the others are not, and the split is not
arbitrary: substrates, phase definitions, hardiness zones and glossary terms are
global reference data, whereas overwintering profiles and starter kits are
resolved per tenant (a tenant sees the shared templates *plus* its own).

**What these tools do and do not prove.** They report what is in the database.
Comparing that against the YAML source is a separate step and stays with the
`seed-data-validator`; a green read here means "this arrived", not "this matches
the seed file".
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext

_MAX_LIMIT = 200


def _drop_empty(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}


def substrate_display_name(substrate: Any) -> str | None:
    """The catalogue name of a substrate — German first, English as the fallback.

    ``Substrate`` carries ``name_de`` and ``name_en`` and **no** ``name`` field.
    Reading ``substrate.name`` therefore always yields nothing, which is what made
    ``get_plant`` report ``substrate_name: null`` next to a key that had resolved
    perfectly well, and what made this module's ``list_substrates`` filter match
    no record at all (#1006).

    DE-first mirrors the rest of the palette (``name_de or name``,
    ``common_name_de or common_name``). ``None`` is returned only when the
    catalogue record genuinely carries no name in either language — a gap in the
    data rather than in the join, and one the caller should be able to see.
    """

    for field in ("name_de", "name_en"):
        value = getattr(substrate, field, None)
        if value:
            return str(value)
    return None


def _dump(obj: Any) -> dict[str, Any]:
    """Model-dump an entity, keeping the ``_key`` alias readable as ``key``."""

    if hasattr(obj, "model_dump"):
        data = obj.model_dump()
        if "key" not in data and getattr(obj, "key", None):
            data["key"] = obj.key
        return _drop_empty(data)
    return {"value": str(obj)}


@mcp_tool(name="list_substrates", permission=McpPermission.READ)
class ListSubstrates(ToolBase):
    """List the substrate catalogue (REQ-019): media, their type and properties."""

    class Input(ToolInput):
        query: str | None = Field(
            default=None,
            description="Case-insensitive filter over the substrate name, German and English.",
        )
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        substrates, total = ctx.substrate_service.list_substrates(offset=0, limit=_MAX_LIMIT)
        selected = list(substrates)
        if args.query:
            needle = args.query.strip().lower()
            # Both names are the haystack. Filtering on a non-existent ``name``
            # attribute matched nothing at all, so every query answered "no such
            # substrate" — a wrong answer, not an empty one (#1006).
            selected = [
                s
                for s in selected
                if needle in f"{getattr(s, 'name_de', '') or ''} {getattr(s, 'name_en', '') or ''}".lower()
            ]
        page = selected[: args.limit]
        return self._response(
            summary=f"{len(page)} substrates (of {total} in the catalogue).",
            data={"count": len(page), "total": total, "items": [_dump(s) for s in page]},
            links=[{"type": "api", "url": "/api/v1/substrates"}],
        )


@mcp_tool(name="list_overwintering_profiles", permission=McpPermission.READ)
class ListOverwinteringProfiles(ToolBase):
    """List overwintering profiles: protection method, storage conditions, timing."""

    class Input(TenantToolInput):
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        profiles, total = ctx.overwintering_service.list_profiles(
            ctx.tenant_key,
            offset=args.offset,
            limit=args.limit,
        )
        return self._response(
            summary=f"{len(profiles)} overwintering profiles (of {total}).",
            data={"count": len(profiles), "total": total, "items": [_dump(p) for p in profiles]},
            links=[ctx.api_link("/overwintering-profiles")],
        )


@mcp_tool(name="list_starter_kits", permission=McpPermission.READ)
class ListStarterKits(ToolBase):
    """List the onboarding starter kits (REQ-020) available to this tenant."""

    class Input(TenantToolInput):
        difficulty: str | None = Field(default=None, description="Restrict to one difficulty level, e.g. 'beginner'.")

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        kits = ctx.starter_kit_service.list_kits_for_tenant(ctx.tenant_key, difficulty=args.difficulty)
        return self._response(
            summary=f"{len(kits)} starter kits available"
            + (f" at difficulty '{args.difficulty}'" if args.difficulty else "")
            + ".",
            data={"count": len(kits), "items": [_dump(k) for k in kits]},
            links=[ctx.api_link("/onboarding/starter-kits")],
        )


@mcp_tool(name="list_phase_definitions", permission=McpPermission.READ)
class ListPhaseDefinitions(ToolBase):
    """List the growth-phase definitions that drive the lifecycle engine (REQ-003)."""

    class Input(ToolInput):
        name_filter: str | None = Field(default=None, description="Filter by definition name.")
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        definitions, total = ctx.phase_sequence_service.list_definitions(
            offset=args.offset,
            limit=args.limit,
            name_filter=args.name_filter,
        )
        return self._response(
            summary=f"{len(definitions)} phase definitions (of {total}).",
            data={"count": len(definitions), "total": total, "items": [_dump(d) for d in definitions]},
            links=[{"type": "api", "url": "/api/v1/phase-sequences/definitions"}],
        )


@mcp_tool(name="list_hardiness_zones", permission=McpPermission.READ)
class ListHardinessZones(ToolBase):
    """List the USDA hardiness zones with their temperature ranges."""

    class Input(ToolInput):
        pass

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        zones = ctx.hardiness_zone_service.list_zones()
        return self._response(
            summary=f"{len(zones)} hardiness zones.",
            data={"count": len(zones), "items": [_dump(z) for z in zones]},
            links=[{"type": "api", "url": "/api/v1/hardiness-zones"}],
        )


@mcp_tool(name="search_glossary", permission=McpPermission.READ)
class SearchGlossary(ToolBase):
    """Search the domain glossary — the project's own definitions of VPD, EC, Karenz and friends."""

    class Input(ToolInput):
        query: str | None = Field(default=None, description="Case-insensitive filter over slug and label.")
        category: str | None = Field(default=None, description="Restrict to one glossary category.")
        language: str = Field(default="de", description="Label language, 'de' or 'en'.")
        limit: int = Field(default=50, ge=1, le=_MAX_LIMIT)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        terms = ctx.glossary_service.list_terms(category=args.category, language=args.language)
        selected = list(terms)
        if args.query:
            needle = args.query.strip().lower()
            selected = [t for t in selected if needle in f"{t.slug} {t.label}".lower()]
        page = selected[: args.limit]
        return self._response(
            summary=f"{len(page)} glossary terms" + (f" match '{args.query}'" if args.query else "") + ".",
            data={
                "count": len(page),
                "matched": len(selected),
                "language": args.language,
                "items": [{"slug": t.slug, "label": t.label, "category": t.category} for t in page],
            },
            links=[{"type": "api", "url": "/api/v1/glossary/terms"}],
        )
