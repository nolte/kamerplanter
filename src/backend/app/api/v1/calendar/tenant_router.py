from datetime import date

from fastapi import APIRouter, Depends, Query, Request

from app.api.v1.calendar.router import _feed_response
from app.api.v1.calendar.schemas import (
    CalendarEventSchema,
    CalendarEventsResponse,
    CalendarFeedCreateRequest,
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
from app.domain.models.calendar import (
    CalendarEventsQuery,
    CalendarFeed,
    CalendarFeedFilters,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
def get_calendar_events(
    start: date = Query(...),
    end: date = Query(...),
    category: str | None = Query(default=None),
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarEventsResponse:
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
    site_id: str | None = Query(default=None),
    year: int = Query(default=None),
    ctx: TenantContext = Depends(get_current_tenant),
) -> SowingCalendarResponse:
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
    site_id: str | None = Query(default=None),
    year: int = Query(default=None),
    ctx: TenantContext = Depends(get_current_tenant),
) -> SeasonOverviewResponse:
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
    svc: CalendarService = get_calendar_service()
    feeds = svc.list_feeds(ctx.user_key, ctx.tenant_key)
    return [_feed_response(f, request) for f in feeds]


@router.get("/feeds/{key}")
def get_feed(
    key: str,
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    svc: CalendarService = get_calendar_service()
    feed = svc.get_feed(key, tenant_key=ctx.tenant_key)
    return _feed_response(feed, request)


@router.put("/feeds/{key}")
def update_feed(
    key: str,
    body: CalendarFeedUpdateRequest,
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
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
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
) -> None:
    svc: CalendarService = get_calendar_service()
    svc.get_feed(key, tenant_key=ctx.tenant_key)
    svc.delete_feed(key)


@router.post("/feeds/{key}/regenerate-token")
def regenerate_token(
    key: str,
    request: Request,
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    svc: CalendarService = get_calendar_service()
    svc.get_feed(key, tenant_key=ctx.tenant_key)
    feed = svc.regenerate_token(key)
    return _feed_response(feed, request)
