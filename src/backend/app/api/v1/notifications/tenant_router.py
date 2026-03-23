"""Tenant-scoped notification API endpoints (REQ-030).

All endpoints are mounted under /api/v1/t/{tenant_slug}/notifications/.
"""

from fastapi import APIRouter, Depends, Query

from app.api.v1.notifications.schemas import (
    ChannelStatusResponse,
    NotificationListResponse,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    NotificationResponse,
    TestNotificationRequest,
    TestNotificationResponse,
    UnreadCountResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_notification_service
from app.common.exceptions import NotFoundError
from app.domain.models.notification import NotificationPreferences
from app.domain.models.tenant_context import TenantContext
from app.domain.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _notification_response(n) -> NotificationResponse:
    """Convert domain Notification to API response."""
    return NotificationResponse(
        key=n.key or "",
        tenant_key=n.tenant_key,
        user_key=n.user_key,
        notification_type=n.notification_type,
        title=n.title,
        body=n.body,
        urgency=n.urgency,
        data=n.data,
        actions=[
            {"action_id": a.action_id, "title": a.title, "uri": a.uri}
            for a in n.actions
        ],
        image_url=n.image_url,
        group_key=n.group_key,
        channels_sent=n.channels_sent,
        channels_failed=n.channels_failed,
        status=n.status,
        read_at=n.read_at,
        acted_at=n.acted_at,
        escalation_level=n.escalation_level,
        parent_notification_key=n.parent_notification_key,
        created_at=n.created_at,
        updated_at=n.updated_at,
    )


# ── List notifications ───────────────────────────────────────────────


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """List notifications for the current user within this tenant."""
    items = service.list_notifications(
        user_key=ctx.user_key,
        tenant_key=ctx.tenant_key,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    unread_count = service.count_unread(
        user_key=ctx.user_key,
        tenant_key=ctx.tenant_key,
    )
    return NotificationListResponse(
        items=[_notification_response(n) for n in items],
        total=len(items),
        unread_count=unread_count,
    )


# ── Unread count ─────────────────────────────────────────────────────


@router.get("/count", response_model=UnreadCountResponse)
def count_unread(
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
    """Count unread notifications for the current user."""
    count = service.count_unread(
        user_key=ctx.user_key,
        tenant_key=ctx.tenant_key,
    )
    return UnreadCountResponse(unread_count=count)


# ── Mark as read ─────────────────────────────────────────────────────


@router.post(
    "/{notification_key}/read",
    response_model=NotificationResponse,
)
def mark_read(
    notification_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark a notification as read."""
    result = service.mark_read(notification_key, ctx.tenant_key, user_key=ctx.user_key)
    if result is None:
        raise NotFoundError(
            entity="Notification",
            key=notification_key,
        )
    return _notification_response(result)


# ── Mark as acted ────────────────────────────────────────────────────


@router.post(
    "/{notification_key}/act",
    response_model=NotificationResponse,
)
def mark_acted(
    notification_key: str,
    action_id: str = Query(..., min_length=1),
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    """Mark a notification action as performed (actionable button callback)."""
    result = service.mark_acted(notification_key, ctx.tenant_key, action_id, user_key=ctx.user_key)
    if result is None:
        raise NotFoundError(
            entity="Notification",
            key=notification_key,
        )
    return _notification_response(result)


# ── Preferences ──────────────────────────────────────────────────────


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_preferences(
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferencesResponse:
    """Get notification preferences for the current user."""
    prefs = service.get_preferences(ctx.user_key)
    return NotificationPreferencesResponse(
        key=prefs.key,
        user_key=prefs.user_key or ctx.user_key,
        channels=prefs.channels,
        quiet_hours=prefs.quiet_hours,
        batching=prefs.batching,
        escalation=prefs.escalation,
        type_overrides=prefs.type_overrides,
        daily_summary=prefs.daily_summary,
        created_at=prefs.created_at,
        updated_at=prefs.updated_at,
    )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_preferences(
    body: NotificationPreferencesRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferencesResponse:
    """Update notification preferences for the current user."""
    prefs = NotificationPreferences(
        user_key=ctx.user_key,
        channels=body.channels,
        quiet_hours=body.quiet_hours,
        batching=body.batching,
        escalation=body.escalation,
        type_overrides=body.type_overrides,
        daily_summary=body.daily_summary,
    )
    updated = service.update_preferences(ctx.user_key, prefs)
    return NotificationPreferencesResponse(
        key=updated.key,
        user_key=updated.user_key,
        channels=updated.channels,
        quiet_hours=updated.quiet_hours,
        batching=updated.batching,
        escalation=updated.escalation,
        type_overrides=updated.type_overrides,
        daily_summary=updated.daily_summary,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


# ── Channel status ──────────────────────────────────────────────────


@router.get(
    "/channels/status",
    response_model=list[ChannelStatusResponse],
)
async def channel_status(
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> list[ChannelStatusResponse]:
    """Health status of all registered notification channels."""
    statuses = await service.get_channel_status()
    return [
        ChannelStatusResponse(
            channel_key=s["channel_key"],
            healthy=s["healthy"],
            supports_actions=s["supports_actions"],
            supports_batching=s["supports_batching"],
        )
        for s in statuses
    ]


# ── Test notification ───────────────────────────────────────────────


@router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(
    body: TestNotificationRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: NotificationService = Depends(get_notification_service),
) -> TestNotificationResponse:
    """Send a test notification through a specific channel.

    Rate limited to 5 requests per hour per user.
    """
    result = await service.send_test(
        user_key=ctx.user_key,
        tenant_key=ctx.tenant_key,
        channel_key=body.channel_key,
    )
    return TestNotificationResponse(
        status=result.get("status", "error"),
        channel_key=body.channel_key,
        success=result.get("success", False),
        error=result.get("error"),
    )
