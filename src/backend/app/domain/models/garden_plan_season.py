"""The report of "new season from the previous year" (REQ-053 GP-FR-171, WP 7.16, GP-API ``plan/new-season``).

One report serves the ``dry_run`` and the applied run, like the import's. It carries keys and counts only: a bed is
named by its key, never by its name or a note, so nothing a user typed travels through the audit row or a log line.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

#: The year of the new season is bounded: the earliest the product could hold data for, and next year at the latest.
MIN_SEASON_YEAR = 2001
#: ``year`` may be at most this many years after the current one (planning the coming season in autumn).
MAX_SEASON_YEARS_AHEAD = 1
#: Archived slots read per run, as a ceiling on memory: a bed is capped at 2 000 live slots (V-22).
MAX_ARCHIVED_READ = 20_000

type SeasonBedStatus = Literal[
    "copied", "skipped_active_plants", "skipped_retired", "skipped_slot_quota", "nothing_to_copy"
]


class SeasonBedOutcome(BaseModel):
    """What happens to one bed: how many slots are (to be) re-created, or why none."""

    location_key: str
    status: SeasonBedStatus
    slots: int = 0
    #: Slots of the previous year left out because their geometry no longer lies inside the bed's shape (V-04).
    slots_outside_bed: int = 0


class PlanSeasonReport(BaseModel):
    year: int
    #: The calendar year whose archived slots are the source (``year - 1``).
    source_year: int
    dry_run: bool
    applied: bool = False
    plan_revision: int | None = None
    beds_copied: int = 0
    beds_skipped: int = 0
    slots_to_create: int = 0
    beds: list[SeasonBedOutcome] = Field(default_factory=list)
