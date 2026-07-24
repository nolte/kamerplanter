from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.v1.calendar.schemas import (
    CalendarEventSchema,
    CalendarEventsResponse,
    CalendarFeedCreateRequest,
    CalendarFeedFiltersSchema,
    CalendarFeedResponse,
    CalendarFeedUpdateRequest,
    FrostConfigSchema,
    MonthSummarySchema,
    SeasonOverviewResponse,
    SowingBarSchema,
    SowingCalendarEntrySchema,
    SowingCalendarResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_calendar_service
from app.common.enums import CalendarEventCategory
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.calendar import (
    CalendarEventsQuery,
    CalendarFeed,
    CalendarFeedFilters,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"], responses=NOT_FOUND_RESPONSE)


def _feed_response(
    feed: CalendarFeed,
    request: Request,
) -> CalendarFeedResponse:
    base_url = str(request.base_url).rstrip("/")
    ical_url = f"{base_url}/api/v1/calendar/feeds/{feed.key}/feed.ics?token={feed.token}"
    return CalendarFeedResponse(
        key=feed.key or "",
        name=feed.name,
        token=feed.token,
        user_key=feed.user_key,
        filters=CalendarFeedFiltersSchema(
            categories=[c.value for c in feed.filters.categories],
            site_key=feed.filters.site_key,
        ),
        is_active=feed.is_active,
        ical_url=ical_url,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
    )


@router.get("/events")
def get_calendar_events(
    start: date = Query(..., description="Inclusive start date of the query window."),
    end: date = Query(..., description="Inclusive end date of the query window."),
    category: str | None = Query(default=None, description="Comma-separated list of event categories to include."),
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarEventsResponse:
    """Return calendar events for the tenant within a date window."""
    svc: CalendarService = get_calendar_service()
    categories: list[CalendarEventCategory] = []
    if category:
        for c in category.split(","):
            c = c.strip()
            if c:
                categories.append(CalendarEventCategory(c))
    query = CalendarEventsQuery(
        start_date=start,
        end_date=end,
        categories=categories,
        tenant_key=ctx.tenant_key,
    )
    events = svc.get_events(query)
    return CalendarEventsResponse(
        events=[
            CalendarEventSchema(
                id=e.id,
                title=e.title,
                description=e.description,
                category=e.category.value,
                source=e.source.value,
                color=e.color,
                start=e.start,
                end=e.end,
                all_day=e.all_day,
                plant_key=e.plant_key,
                task_key=e.task_key,
                site_key=e.site_key,
                location_key=e.location_key,
                metadata=e.metadata,
            )
            for e in events
        ],
        total=len(events),
    )


@router.get("/sowing")
def get_sowing_calendar(
    site_id: str | None = Query(default=None, description="Restrict the calendar to a single site."),
    year: int = Query(default=None, description="Calendar year; defaults to the current year."),
    ctx: TenantContext = Depends(get_current_tenant),
) -> SowingCalendarResponse:
    """Return the sowing calendar with per-species phase bars for a year."""
    from datetime import date as _date

    svc: CalendarService = get_calendar_service()
    effective_year = year if year else _date.today().year
    entries, frost_config = svc.get_sowing_calendar(site_id, effective_year)
    return SowingCalendarResponse(
        entries=[
            SowingCalendarEntrySchema(
                species_key=e.species_key,
                species_name=e.species_name,
                common_name=e.common_name,
                plant_category=e.plant_category,
                bars=[
                    SowingBarSchema(
                        phase=b.phase,
                        color=b.color,
                        start_date=b.start_date,
                        end_date=b.end_date,
                        label=b.label,
                    )
                    for b in e.bars
                ],
            )
            for e in entries
        ],
        frost_config=FrostConfigSchema(
            last_frost_date=frost_config.last_frost_date,
            first_frost_date=frost_config.first_frost_date,
            eisheilige_date=frost_config.eisheilige_date,
        ),
        year=effective_year,
        total=len(entries),
    )


@router.get("/season-overview")
def get_season_overview(
    site_id: str | None = Query(default=None, description="Restrict the overview to a single site."),
    year: int = Query(default=None, description="Calendar year; defaults to the current year."),
    ctx: TenantContext = Depends(get_current_tenant),
) -> SeasonOverviewResponse:
    """Return a month-by-month season overview with activity counts."""
    from datetime import date as _date

    svc: CalendarService = get_calendar_service()
    effective_year = year if year else _date.today().year
    overview = svc.get_season_overview(site_id, effective_year)
    return SeasonOverviewResponse(
        site_key=overview.site_key,
        site_name=overview.site_name,
        year=overview.year,
        months=[
            MonthSummarySchema(
                month=m.month,
                month_name=m.month_name,
                sowing_count=m.sowing_count,
                harvest_count=m.harvest_count,
                bloom_count=m.bloom_count,
                task_count=m.task_count,
                top_tasks=m.top_tasks,
                is_current=m.is_current,
            )
            for m in overview.months
        ],
    )


@router.post("/feeds", status_code=201)
def create_feed(
    body: CalendarFeedCreateRequest,
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    """Create a subscribable iCal feed for the tenant's calendar."""
    svc: CalendarService = get_calendar_service()
    cats = [CalendarEventCategory(c) for c in body.filters.categories]
    feed = CalendarFeed(
        name=body.name,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        filters=CalendarFeedFilters(categories=cats, site_key=body.filters.site_key),
    )
    created = svc.create_feed(feed)
    return _feed_response(created, request)


@router.get("/feeds")
def list_feeds(
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> list[CalendarFeedResponse]:
    """List the tenant's calendar feeds."""
    svc: CalendarService = get_calendar_service()
    feeds = svc.list_feeds(ctx.user_key, ctx.tenant_key)
    return [_feed_response(f, request) for f in feeds]


@router.get("/feeds/{key}")
def get_feed(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    """Return a single calendar feed by key."""
    svc: CalendarService = get_calendar_service()
    feed = svc.get_feed(key, tenant_key=ctx.tenant_key)
    return _feed_response(feed, request)


@router.put("/feeds/{key}")
def update_feed(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    body: CalendarFeedUpdateRequest,
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    """Update a calendar feed's name, filters or active state."""
    svc: CalendarService = get_calendar_service()
    svc.get_feed(key, tenant_key=ctx.tenant_key)
    cats = [CalendarEventCategory(c) for c in body.filters.categories]
    feed = CalendarFeed(
        name=body.name,
        is_active=body.is_active,
        filters=CalendarFeedFilters(categories=cats, site_key=body.filters.site_key),
    )
    updated = svc.update_feed(key, feed)
    return _feed_response(updated, request)


@router.delete("/feeds/{key}", status_code=204)
def delete_feed(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    ctx: TenantContext = Depends(get_current_tenant),
) -> None:
    """Delete a calendar feed."""
    svc: CalendarService = get_calendar_service()
    svc.get_feed(key, tenant_key=ctx.tenant_key)
    svc.delete_feed(key)


@router.post("/feeds/{key}/regenerate-token")
def regenerate_token(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    """Rotate a calendar feed's access token, invalidating the old iCal URL."""
    svc: CalendarService = get_calendar_service()
    svc.get_feed(key, tenant_key=ctx.tenant_key)
    feed = svc.regenerate_token(key)
    return _feed_response(feed, request)
