from datetime import date

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from app.common.dependencies import get_calendar_service
from app.common.enums import CalendarEventCategory
from app.domain.models.calendar import (
    CalendarEventsQuery,
    CalendarFeed,
    CalendarFeedFilters,
)
from app.domain.services.calendar_service import CalendarService

from .schemas import (
    CalendarEventSchema,
    CalendarEventsResponse,
    CalendarFeedCreateRequest,
    CalendarFeedFiltersSchema,
    CalendarFeedResponse,
    CalendarFeedUpdateRequest,
)

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _feed_response(
    feed: CalendarFeed, request: Request,
) -> CalendarFeedResponse:
    base_url = str(request.base_url).rstrip("/")
    ical_url = (
        f"{base_url}/api/v1/calendar/feeds/{feed.key}/feed.ics"
        f"?token={feed.token}"
    )
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
    start: date = Query(...),
    end: date = Query(...),
    category: str | None = Query(default=None),
    tenant_key: str = Query(default=""),
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
        tenant_key=tenant_key,
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


@router.post("/feeds", status_code=201)
def create_feed(
    body: CalendarFeedCreateRequest, request: Request,
) -> CalendarFeedResponse:
    svc: CalendarService = get_calendar_service()
    cats = [CalendarEventCategory(c) for c in body.filters.categories]
    feed = CalendarFeed(
        name=body.name,
        tenant_key="",
        user_key="",
        filters=CalendarFeedFilters(
            categories=cats,
            site_key=body.filters.site_key,
        ),
    )
    created = svc.create_feed(feed)
    return _feed_response(created, request)


@router.get("/feeds")
def list_feeds(
    request: Request,
    user_key: str = Query(default=""),
    tenant_key: str = Query(default=""),
) -> list[CalendarFeedResponse]:
    svc: CalendarService = get_calendar_service()
    feeds = svc.list_feeds(user_key, tenant_key)
    return [_feed_response(f, request) for f in feeds]


@router.get("/feeds/{key}")
def get_feed(key: str, request: Request) -> CalendarFeedResponse:
    svc: CalendarService = get_calendar_service()
    feed = svc.get_feed(key)
    return _feed_response(feed, request)


@router.put("/feeds/{key}")
def update_feed(
    key: str, body: CalendarFeedUpdateRequest, request: Request,
) -> CalendarFeedResponse:
    svc: CalendarService = get_calendar_service()
    cats = [CalendarEventCategory(c) for c in body.filters.categories]
    feed = CalendarFeed(
        name=body.name,
        is_active=body.is_active,
        filters=CalendarFeedFilters(
            categories=cats,
            site_key=body.filters.site_key,
        ),
    )
    updated = svc.update_feed(key, feed)
    return _feed_response(updated, request)


@router.delete("/feeds/{key}", status_code=204)
def delete_feed(key: str) -> None:
    svc: CalendarService = get_calendar_service()
    svc.delete_feed(key)


@router.post("/feeds/{key}/regenerate-token")
def regenerate_token(key: str, request: Request) -> CalendarFeedResponse:
    svc: CalendarService = get_calendar_service()
    feed = svc.regenerate_token(key)
    return _feed_response(feed, request)


@router.get("/feeds/{key}/feed.ics")
def get_ical_feed(key: str, token: str = Query(...)) -> Response:
    svc: CalendarService = get_calendar_service()
    ical_content = svc.generate_ical_for_feed(key, token)
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=feed-{key}.ics"},
    )
