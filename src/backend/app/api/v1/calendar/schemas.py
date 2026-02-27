from datetime import date, datetime

from pydantic import BaseModel, Field


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
