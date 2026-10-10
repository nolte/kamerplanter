from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.v1.calendar.schemas import (
    CalendarEventSchema,
    CalendarEventsResponse,
    CalendarFeedCreateRequest,
    CalendarFeedFiltersSchema,
    CalendarFeedIssuedResponse,
    CalendarFeedResponse,
    CalendarFeedUpdateRequest,
    CalendarQueryParams,
    FrostConfigSchema,
    MonthSummarySchema,
    SeasonOverviewResponse,
    SowingBarSchema,
    SowingCalendarEntrySchema,
    SowingCalendarResponse,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.datetimes import today_utc
from app.common.dependencies import get_calendar_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.core.permissions import Action, ResourceType
from app.domain.models.calendar import (
    CalendarEventsQuery,
    CalendarFeed,
    CalendarFeedFilters,
    CalendarFeedIssued,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"], responses=NOT_FOUND_RESPONSE)


def _default_calendar_year() -> int:
    """The calendar year assumed when the caller names none.

    UTC (§12a), which keeps this default on the same clock as everything it is
    handed to: ``SeasonOverviewEngine`` marks the current month by comparing
    ``today_utc().year`` against exactly this value, and the sowing bars are
    built from frost dates derived from UTC-stamped records. Reading the two
    from different clocks would, for the hours around New Year, request a year
    the engine then declares "not current" — blanking ``is_current`` for the
    whole overview.

    **Open product question (#858).** This is the one converted site whose
    "right" answer is not purely technical: a year the *user* sees arguably
    belongs to the user's or the tenant's timezone, not to UTC. It is not
    implementable today — no ``Tenant`` carries a timezone (only ``Site`` does,
    defaulting to ``"UTC"``), and ``site_id`` is optional on both endpoints, so
    there is no timezone to resolve for the unscoped call. Deciding between
    "tenant timezone", "site timezone when scoped" and "keep UTC" is a product
    call; until it is made, UTC is the consistent choice rather than the
    accidental one the server's ``TZ`` provided. The practical exposure is
    small: the local and UTC *year* differ only in the hours around 1 January.
    """
    return today_utc().year


def _feed_response(feed: CalendarFeed) -> CalendarFeedResponse:
    """A feed for a read: names nothing secret, since the token is not kept (#2171)."""
    return CalendarFeedResponse(
        key=feed.key or "",
        name=feed.name,
        user_key=feed.user_key,
        filters=CalendarFeedFiltersSchema(
            categories=[c.value for c in feed.filters.categories],
            site_key=feed.filters.site_key,
        ),
        is_active=feed.is_active,
        created_at=feed.created_at,
        updated_at=feed.updated_at,
    )


def _issued_feed_response(issued: CalendarFeedIssued, request: Request) -> CalendarFeedIssuedResponse:
    """The create / rotate response: the one place the raw token and its URL appear (#2171)."""
    feed = issued.feed
    base_url = str(request.base_url).rstrip("/")
    ical_url = f"{base_url}/api/v1/calendar/feeds/{feed.key}/feed.ics?token={issued.token}"
    return CalendarFeedIssuedResponse(
        **_feed_response(feed).model_dump(),
        token=issued.token,
        ical_url=ical_url,
    )


@router.get("/events")
def get_calendar_events(
    params: Annotated[CalendarQueryParams, Query()],
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarEventsResponse:
    """Return calendar events for the tenant within a date window."""
    svc: CalendarService = get_calendar_service()
    query = CalendarEventsQuery(
        start_date=params.start,
        end_date=params.end,
        categories=params.category,
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
    svc: CalendarService = get_calendar_service()
    effective_year = year if year else _default_calendar_year()
    entries, frost_config = svc.get_sowing_calendar(site_id, effective_year, tenant_key=ctx.tenant_key)
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
    svc: CalendarService = get_calendar_service()
    effective_year = year if year else _default_calendar_year()
    overview = svc.get_season_overview(site_id, effective_year, tenant_key=ctx.tenant_key)
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
    ctx: TenantContext = Depends(require_permission(ResourceType.CALENDAR_FEED, Action.CREATE)),
) -> CalendarFeedIssuedResponse:
    """Create a subscribable iCal feed; the response carries its token and URL, once."""
    svc: CalendarService = get_calendar_service()
    feed = CalendarFeed(
        name=body.name,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        filters=CalendarFeedFilters(categories=body.filters.categories, site_key=body.filters.site_key),
    )
    return _issued_feed_response(svc.create_feed(feed), request)


@router.get("/feeds")
def list_feeds(
    ctx: TenantContext = Depends(get_current_tenant),
) -> list[CalendarFeedResponse]:
    """List the tenant's calendar feeds."""
    svc: CalendarService = get_calendar_service()
    feeds = svc.list_feeds(ctx.user_key, ctx.tenant_key)
    return [_feed_response(f) for f in feeds]


@router.get("/feeds/{key}")
def get_feed(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    ctx: TenantContext = Depends(get_current_tenant),
) -> CalendarFeedResponse:
    """Return a single calendar feed by key (without its token, which is not kept)."""
    svc: CalendarService = get_calendar_service()
    feed = svc.get_feed(key, tenant_key=ctx.tenant_key)
    return _feed_response(feed)


@router.put("/feeds/{key}")
def update_feed(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    body: CalendarFeedUpdateRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.CALENDAR_FEED, Action.UPDATE)),
) -> CalendarFeedResponse:
    """Update a calendar feed's name, filters or active state."""
    svc: CalendarService = get_calendar_service()
    feed = CalendarFeed(
        name=body.name,
        is_active=body.is_active,
        filters=CalendarFeedFilters(categories=body.filters.categories, site_key=body.filters.site_key),
    )
    updated = svc.update_feed(key, feed, tenant_key=ctx.tenant_key)
    return _feed_response(updated)


@router.delete("/feeds/{key}", status_code=204)
def delete_feed(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.CALENDAR_FEED, Action.DELETE)),
) -> None:
    """Delete a calendar feed."""
    svc: CalendarService = get_calendar_service()
    svc.delete_feed(key, tenant_key=ctx.tenant_key)


@router.post("/feeds/{key}/regenerate-token")
def regenerate_token(
    key: Annotated[str, Path(description="Document key of the calendar feed.")],
    request: Request,
    ctx: TenantContext = Depends(require_permission(ResourceType.CALENDAR_FEED, Action.UPDATE)),
) -> CalendarFeedIssuedResponse:
    """Rotate a feed's token: the old iCal URL stops working, the new one is shown once."""
    svc: CalendarService = get_calendar_service()
    return _issued_feed_response(svc.regenerate_token(key, tenant_key=ctx.tenant_key), request)
