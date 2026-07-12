"""REQ-033 species read tools (§2.1). Delegates to ``SpeciesService``."""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="list_species", permission=McpPermission.READ)
class ListSpecies(ToolBase):
    """List the plant species catalog (paginated)."""

    class Input(ToolInput):
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=25, ge=1, le=100)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        species, total = ctx.species_service.list_species(offset=args.offset, limit=args.limit)
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
    """Return stammdaten for one species incl. companion-planting hints."""

    class Input(ToolInput):
        species_key: str

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        species = ctx.species_service.get_species(args.species_key)
        try:
            companions = ctx.species_service.get_compatible_species(args.species_key)
        except Exception:  # noqa: BLE001 — companion graph is optional context
            companions = []
        data = {
            "species_key": species.key,
            "scientific_name": species.scientific_name,
            "common_names": species.common_names,
            "genus": species.genus,
            "growth_habit": getattr(species, "growth_habit", None),
            "compatible_companions": companions,
        }
        return self._response(
            summary=f"Species '{species.scientific_name}'.",
            data=data,
            links=[{"type": "api", "url": f"/api/v1/species/{species.key}"}],
        )
