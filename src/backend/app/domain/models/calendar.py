from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import CalendarEventCategory, CalendarEventSource


class CalendarEvent(BaseModel):
    id: str = ""
    title: str = ""
    description: str = ""
    category: CalendarEventCategory = CalendarEventCategory.CUSTOM
    source: CalendarEventSource = CalendarEventSource.TASK
    color: str = ""
    start: datetime | None = None
    end: datetime | None = None
    all_day: bool = False
    plant_key: str | None = None
    task_key: str | None = None
    site_key: str | None = None
    location_key: str | None = None
    metadata: dict = Field(default_factory=dict)
    # REQ-015 v1.6: iCal VEVENT extras (RFC 5545 + Spec §3.3 line 1938)
    priority: int | None = Field(default=None, ge=0, le=9)
    status: str | None = None  # CONFIRMED | TENTATIVE | CANCELLED (RFC 5545)
    alarm_minutes_before: int | None = Field(default=None, ge=0)


class CalendarEventsQuery(BaseModel):
    start_date: date
    end_date: date
    categories: list[CalendarEventCategory] = Field(default_factory=list)
    site_key: str | None = None
    tenant_key: str = ""


class CalendarFeedFilters(BaseModel):
    categories: list[CalendarEventCategory] = Field(default_factory=list)
    site_key: str | None = None


class CalendarFeed(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    token: str = ""
    user_key: str = ""
    filters: CalendarFeedFilters = Field(default_factory=CalendarFeedFilters)
    is_active: bool = True
    # REQ-015 CF-005 (Spec §3.3 line 94): optional expiry — feed becomes
    # invalid after this timestamp and the iCal endpoint returns HTTP 410.
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
