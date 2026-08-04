"""REQ-033 read tool for the sowing calendar (§2.1, REQ-015).

The sowing calendar answers "when do I sow, plant out and harvest this?" per
species, with the windows shifted against the site's frost dates.

Two things shape this tool. First, ownership: passing a ``site_key`` pulls in
that site's frost configuration *and* its planting runs, so the site is verified
against the acting tenant before the calendar is built — otherwise the tool would
read another tenant's runs. Second, size: the underlying engine walks the entire
species catalogue (thousands of entries), which would bury an LLM. The species
filter is therefore effectively mandatory in practice, and the page is capped.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.common.datetimes import today_utc
from app.common.enums import McpPermission
from app.common.exceptions import ValidationError
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import TenantToolInput, ToolBase, mcp_tool
from app.mcp_server.context import ToolContext

#: Species per answer. The calendar is a wide structure — several bars per
#: species — so a generous page would cost far more context than it is worth.
_MAX_SPECIES = 25


def _bar(bar: Any) -> dict[str, Any]:
    return {
        "phase": bar.phase,
        "start_date": bar.start_date,
        "end_date": bar.end_date,
        "label": bar.label,
    }


@mcp_tool(name="get_sowing_calendar", permission=McpPermission.READ)
class GetSowingCalendar(ToolBase):
    """Sowing, planting-out and harvest windows per species for one year."""

    class Input(TenantToolInput):
        query: str | None = Field(
            default=None,
            description=(
                "Case-insensitive substring filter over scientific and common species names. "
                "Strongly recommended: without it the answer spans the whole catalogue and is truncated."
            ),
        )
        year: int | None = Field(
            default=None,
            ge=2000,
            le=2100,
            description="Calendar year. Defaults to the current year.",
        )
        site_key: str | None = Field(
            default=None,
            description=(
                "Shift the windows against this site's frost dates and include its planting runs. "
                "Without it, generic frost defaults apply."
            ),
        )
        limit: int = Field(default=_MAX_SPECIES, ge=1, le=_MAX_SPECIES)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        year = args.year or today_utc().year

        if args.site_key:
            # Verify the site belongs to the acting tenant before its runs and
            # frost data are read — a foreign key must not reach the engine.
            ctx.site_service.get_site(args.site_key, tenant_key=ctx.tenant_key)

        entries, frost = ctx.calendar_service.get_sowing_calendar(args.site_key, year)

        selected = list(entries)
        if args.query:
            needle = args.query.strip().lower()
            selected = [e for e in selected if needle in f"{e.species_name} {e.common_name}".lower()]
        elif len(selected) > args.limit:
            # Refuse to silently hand back an arbitrary slice of the catalogue:
            # a truncated calendar reads like a complete one and would be wrong.
            raise ValidationError(
                f"The calendar covers {len(selected)} species. Pass 'query' to narrow it down "
                f"(or raise 'limit' up to {_MAX_SPECIES})."
            )

        truncated = len(selected) > args.limit
        page = selected[: args.limit]
        items = [
            {
                "species_key": e.species_key,
                "species_name": e.species_name,
                "common_name": e.common_name,
                "bars": [_bar(b) for b in e.bars],
            }
            for e in page
        ]

        summary = f"Sowing calendar {year}: {len(page)} species"
        if truncated:
            summary += f" (of {len(selected)} matching — narrow the query to see the rest)"
        summary += "."
        return self._response(
            summary=summary,
            data={
                "year": year,
                "count": len(page),
                "matched": len(selected),
                "truncated": truncated,
                "frost": {
                    "last_frost_date": frost.last_frost_date,
                    "first_frost_date": frost.first_frost_date,
                    "eisheilige_date": frost.eisheilige_date,
                },
                "items": items,
            },
            links=[ctx.api_link("/calendar/sowing"), ctx.ui_link("/calendar")],
        )
