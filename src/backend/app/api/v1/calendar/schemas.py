"""Request/response schemas for /calendar (REQ-015).

Category-valued fields carry ``CalendarEventCategory``, not ``str`` (#1520). The
router used to convert them itself — ``[CalendarEventCategory(c) for c in
body.filters.categories]`` — and a misspelt member raised a bare ``ValueError``
that reached the ``Exception`` handler, so ``{"categories": ["Harvest"]}``
answered 500 for input the application itself rejects. Declared here, Pydantic
answers 422 with ``details[].field`` (NFR-006) and OpenAPI lists the members.
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from app.common.enums import CalendarEventCategory


def _split_category_filter(value: object) -> object:
    """Accept the comma-separated ``?category=a,b`` form the endpoint has always taken.

    FastAPI hands a repeated query parameter over as a list of raw strings, so the
    documented single-parameter comma form arrives as ``["a,b"]``. Splitting here —
    *before* field validation — keeps the wire format of the endpoint unchanged
    while letting Pydantic, not the handler, decide whether each member exists.
    Blank segments are dropped, exactly as the hand-rolled loop did.
    """
    if not isinstance(value, list):
        return value
    members: list[object] = []
    for item in value:
        if isinstance(item, str):
            members.extend(part.strip() for part in item.split(",") if part.strip())
        else:
            members.append(item)
    return members


#: The ``?category=`` filter: zero or more categories, comma-separated or repeated.
CategoryFilter = Annotated[list[CalendarEventCategory], BeforeValidator(_split_category_filter)]


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
    categories: list[CalendarEventCategory] = Field(default_factory=list)
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
    """Query parameters of ``GET /calendar/events``.

    A *model*, not three loose parameters, because FastAPI validates a sequence
    query parameter item by item and a list-level ``BeforeValidator`` never runs
    on it — the endpoint's documented comma-separated form would have become a
    422. Inside a query model Pydantic validates the field as a whole, so
    ``?category=harvest,feeding`` and ``?category=harvest&category=feeding`` both
    work and ``?category=Harvest`` is a 422 naming ``query.category.0``.
    """

    start: date = Field(description="Inclusive start date of the query window.")
    end: date = Field(description="Inclusive end date of the query window.")
    category: CategoryFilter = Field(
        default_factory=list,
        description="Event categories to include — comma-separated, or the parameter repeated.",
    )


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
    plant_category: str | None = None
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
