"""The bed list as a download (REQ-053 GP-FR-145, GP-FR-175, SR-016, SR-024; WP 8.25, #2668).

What the service hands the CSV engine: one :class:`BedListExportRow` per listed location, with the labels the
spreadsheet shows resolved already - the type's name instead of its key, the irrigation zone's name instead of its
key, and (only on request) the display names of the members the bed is assigned to. **No account key is part of a
row**: the assignment reaches the engine as display names, never as the user or membership keys behind them.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.domain.models.garden_plan import BedCounters
from app.domain.models.site import Location

#: More rows than this are refused as a whole (422 ``export.too_many_rows``), never cut. A site holds at most 500
#: plan objects (GP-NFR-017) - the bound sits well above it, so only a legacy site without the plan quota reaches it.
MAX_BED_LIST_EXPORT_ROWS = 2_000

#: The published code of a bed list that would be larger than :data:`MAX_BED_LIST_EXPORT_ROWS` (as the care log's).
ERROR_TOO_MANY_ROWS = "export.too_many_rows"


@dataclass(frozen=True)
class LocationTypeName:
    """The readable name of a location type in both languages (``name_en`` ``None`` when the type has none)."""

    name: str
    name_en: str | None = None

    def for_locale(self, locale: str) -> str:
        """The English name for ``en`` when there is one, else the (German) name."""
        return self.name_en if locale == "en" and self.name_en else self.name


@dataclass(frozen=True)
class BedAssignee:
    """One member a bed is assigned to (``location_assignments``), as the repository reads it.

    ``user_key`` stays inside the service: it decides whether the account was erased (then the name reads
    ``anonymisiert``) and is dropped before anything leaves the service.
    """

    location_key: str
    user_key: str | None
    display_name: str | None


class BedListExportRow(BaseModel):
    """One location of the download, with its counters and the readable labels of its references."""

    location: Location
    #: ``None`` when the listing carries no counters (it always does for the bed list).
    counters: BedCounters | None = None
    #: The location type's name in the requested language; ``None`` when the type does not resolve.
    type_name: str | None = None
    #: The irrigation zone's name; ``None`` when the bed has no zone or the zone is gone.
    zone_name: str | None = None
    #: Display names of the members the bed is assigned to, sorted; ``None`` when the assignment was not asked
    #: for (SR-024 opt-in) - an empty list means "asked for, nobody assigned".
    assignees: list[str] | None = Field(default=None)
