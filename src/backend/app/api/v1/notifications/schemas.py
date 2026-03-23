"""Pydantic v2 schemas for notification API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.notification import (
    BatchingPreference,
    ChannelPreference,
    DailySummaryPreference,
    EscalationPreference,
    NotificationStatus,
    NotificationUrgency,
    QuietHoursPreference,
    TypeOverride,
)

# ── Response schemas ─────────────────────────────────────────────────


class NotificationActionResponse(BaseModel):
    """Actionable button in a notification."""

    action_id: str
    title: str
    uri: str | None = None


class NotificationResponse(BaseModel):
    """Single notification response."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    tenant_key: str
    user_key: str
    notification_type: str
    title: str
    body: str
    urgency: NotificationUrgency
    data: dict = Field(default_factory=dict)
    actions: list[NotificationActionResponse] = Field(default_factory=list)
    image_url: str | None = None
    group_key: str | None = None
    channels_sent: list[str] = Field(default_factory=list)
    channels_failed: list[str] = Field(default_factory=list)
    status: NotificationStatus
    read_at: datetime | None = None
    acted_at: datetime | None = None
    escalation_level: int = 0
    parent_notification_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    items: list[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""

    unread_count: int


# ── Preferences schemas ─────────────────────────────────────────────


class NotificationPreferencesRequest(BaseModel):
    """Request body for updating notification preferences."""

    channels: dict[str, ChannelPreference] = Field(default_factory=dict)
    quiet_hours: QuietHoursPreference = Field(
        default_factory=QuietHoursPreference
    )
    batching: BatchingPreference = Field(default_factory=BatchingPreference)
    escalation: EscalationPreference = Field(
        default_factory=EscalationPreference
    )
    type_overrides: dict[str, TypeOverride] = Field(default_factory=dict)
    daily_summary: DailySummaryPreference = Field(
        default_factory=DailySummaryPreference
    )


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response."""

    model_config = ConfigDict(from_attributes=True)

    key: str | None = None
    user_key: str
    channels: dict[str, ChannelPreference] = Field(default_factory=dict)
    quiet_hours: QuietHoursPreference = Field(
        default_factory=QuietHoursPreference
    )
    batching: BatchingPreference = Field(default_factory=BatchingPreference)
    escalation: EscalationPreference = Field(
        default_factory=EscalationPreference
    )
    type_overrides: dict[str, TypeOverride] = Field(default_factory=dict)
    daily_summary: DailySummaryPreference = Field(
        default_factory=DailySummaryPreference
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Channel status ──────────────────────────────────────────────────


class ChannelStatusResponse(BaseModel):
    """Health status of a notification channel."""

    channel_key: str
    healthy: bool
    supports_actions: bool
    supports_batching: bool


# ── Test notification ───────────────────────────────────────────────


class TestNotificationRequest(BaseModel):
    """Request body for sending a test notification."""

    channel_key: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Channel key to test (e.g. 'home_assistant', 'email').",
    )


class TestNotificationResponse(BaseModel):
    """Result of a test notification."""

    status: str
    channel_key: str
    success: bool
    error: str | None = None
