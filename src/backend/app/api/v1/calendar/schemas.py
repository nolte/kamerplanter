
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class CalendarEventSchema(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    category: str = ""
    source: str = ""
    color: str = ""
    start: datetime | None = None
    end: datetime | None = None
    all_day: bool = False
    plant_key: str | None = None
    task_key: str | None = None
    site_key: str | None = None
    location_key: str | None = None
    metadata: dict = Field(default_factory=dict)


class CalendarEventsResponse(BaseModel):
    events: list[CalendarEventSchema] = Field(default_factory=list)
    total: int = 0


class CalendarFeedFiltersSchema(BaseModel):
    categories: list[str] = Field(default_factory=list)
    site_key: str | None = None


class CalendarFeedCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    filters: CalendarFeedFiltersSchema = Field(
        default_factory=CalendarFeedFiltersSchema,
    )


class CalendarFeedUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    filters: CalendarFeedFiltersSchema = Field(
        default_factory=CalendarFeedFiltersSchema,
    )
    is_active: bool = True


class CalendarFeedResponse(BaseModel):
    key: str = ""
    name: str = ""
    token: str = ""
    user_key: str = ""
    filters: CalendarFeedFiltersSchema = Field(
        default_factory=CalendarFeedFiltersSchema,
    )
    is_active: bool = True
    ical_url: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CalendarQueryParams(BaseModel):
    start: date
    end: date
    category: str | None = None


# ── Sowing Calendar (REQ-015 §3.8) ──────────────────────────────────


class FrostConfigSchema(BaseModel):
    last_frost_date: date
    first_frost_date: date | None = None
    eisheilige_date: date


class SowingBarSchema(BaseModel):
    phase: str
    color: str
    start_date: date
    end_date: date
    label: str = ""


class SowingCalendarEntrySchema(BaseModel):
    species_key: str
    species_name: str
    common_name: str = ""
    link_species_key: str = ""
    bars: list[SowingBarSchema] = Field(default_factory=list)


class SowingCalendarResponse(BaseModel):
    entries: list[SowingCalendarEntrySchema] = Field(default_factory=list)
    frost_config: FrostConfigSchema
    year: int
    total: int = 0


# ── Season Overview (REQ-015 §3.9) ──────────────────────────────────


class MonthSummarySchema(BaseModel):
    month: int
    month_name: str = ""
    sowing_count: int = 0
    harvest_count: int = 0
    bloom_count: int = 0
    task_count: int = 0
    top_tasks: list[str] = Field(default_factory=list)
    is_current: bool = False


class SeasonOverviewResponse(BaseModel):
    site_key: str = ""
    site_name: str = ""
    year: int
    months: list[MonthSummarySchema] = Field(default_factory=list)
