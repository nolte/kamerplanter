"""REQ-015 §4.2 — the public iCal subscription route (``feed.ics``, #2226).

A calendar client (Thunderbird, Apple Kalender, Google Calendar, the Home
Assistant calendar coordinator) subscribes to the URL the feed-management routes
hand out once, at create and at rotation
(:func:`app.api.v1.calendar.tenant_router.feed_subscription_url`). That client
has no session, so the route carries no JWT and no tenant slug: the feed token
in the query string *is* the authorisation (CF-007, both deployment modes), and
the feed it resolves to decides the tenant whose events are rendered (CF-002).

What the route holds, and where:

* **One answer for every refusal.** No token, an unknown token, the token of
  another feed and a deactivated feed all answer the same ``404``
  (:meth:`CalendarService.generate_ical_for_feed`), so neither a feed key nor a
  token can be probed. A feed past ``expires_at`` answers ``410`` (CF-005) — to
  the holder of its token only.
* **Two rate limits** (CF-004): per client IP ``settings.rate_limit_calendar_feed``,
  and per presented token ``settings.rate_limit_calendar_feed_per_token``
  (#2226 review SEC-005) - a leaked URL polled from many addresses is still one
  bounded bucket. The token bucket is keyed by a digest of the token, so a
  caller without the token cannot spend a subscriber's budget.
* **No token in a log line.** The backend access log and the request logging
  write the path through ``loggable_path`` (feed key → ``{}``, query →
  ``?<redacted>``), the frontend nginx logs ``/api/...`` only, and the error
  tracker drops the query. This module logs nothing of the request itself.
* **Not cached.** ``Cache-Control: no-store`` — a shared cache must not keep a
  tenant's calendar under a URL whose token was just rotated away.

The issue that restored this route found it deleted in March 2026 while the
feed-management routes kept issuing URLs to it: the URL form is therefore built
in one place and pinned against this route's template by a test.
"""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import Response

from app.api.v1.auth.router import limiter
from app.common.dependencies import get_calendar_service
from app.common.openapi_responses import ErrorResponse
from app.config.settings import settings
from app.domain.services.calendar_service import CalendarService

#: The route's path below the ``/api/v1`` mount; the issued subscription URL is
#: built from it (``tenant_router.feed_subscription_url``), so the two cannot drift.
FEED_ICS_PATH = "/calendar/feeds/{key}/feed.ics"

#: Upper bounds of the two caller-written values. A token is
#: ``secrets.token_urlsafe(32)`` (43 characters); the bound leaves room for any
#: token issued before #2171 and refuses a request body in the query string.
_MAX_KEY_LENGTH = 254
_MAX_TOKEN_LENGTH = 256

router = APIRouter(tags=["calendar"])


def feed_token_rate_limit_key(request: Request) -> str:
    """The rate-limit bucket of the token a ``feed.ics`` request presents (#2226 review SEC-005).

    A truncated SHA-256 of the token with its own prefix: the raw token never
    becomes a storage key, and it is a different digest from the one the feed
    row stores, so a storage dump does not name a feed. Requests without a
    token share one bucket; they are refused with 404 anyway.
    """
    token = request.query_params.get("token", "")[:_MAX_TOKEN_LENGTH]
    return "feed-token:" + hashlib.sha256(b"kamerplanter-feed-rate-limit:" + token.encode()).hexdigest()[:32]


@router.get(
    FEED_ICS_PATH,
    response_class=Response,
    responses={
        200: {
            "description": "The feed's events as an iCalendar document (RFC 5545).",
            "content": {"text/calendar": {"schema": {"type": "string"}}},
        },
        404: {
            "model": ErrorResponse,
            "description": "No active feed with this key opens with this token (also: no token, inactive feed).",
        },
        410: {"model": ErrorResponse, "description": "The feed is past its expiry date (CF-005)."},
        429: {
            "model": ErrorResponse,
            "description": "Too many feed requests from this address, or for this token (CF-004).",
        },
    },
)
@limiter.limit(settings.rate_limit_calendar_feed)
@limiter.limit(settings.rate_limit_calendar_feed_per_token, key_func=feed_token_rate_limit_key)
def get_ical_feed(
    request: Request,
    key: Annotated[str, Path(max_length=_MAX_KEY_LENGTH, description="Key of the calendar feed.")],
    token: Annotated[
        str,
        Query(
            max_length=_MAX_TOKEN_LENGTH,
            description="The feed token from the subscription URL. Missing or wrong answers 404.",
        ),
    ] = "",
    service: CalendarService = Depends(get_calendar_service),
) -> Response:
    """Render one calendar feed as iCal for a subscribing client — no login, the token authorises."""
    ical = service.generate_ical_for_feed(key, token)
    return Response(
        content=ical,
        media_type="text/calendar",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'inline; filename="kamerplanter.ics"',
        },
    )
