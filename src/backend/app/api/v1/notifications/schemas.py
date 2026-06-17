"""Pydantic v2 schemas for notification API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    quiet_hours: QuietHoursPreference = Field(default_factory=QuietHoursPreference)
    batching: BatchingPreference = Field(default_factory=BatchingPreference)
    escalation: EscalationPreference = Field(default_factory=EscalationPreference)
    type_overrides: dict[str, TypeOverride] = Field(default_factory=dict)
    daily_summary: DailySummaryPreference = Field(default_factory=DailySummaryPreference)


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response."""

    model_config = ConfigDict(from_attributes=True)

    key: str | None = None
    user_key: str
    channels: dict[str, ChannelPreference] = Field(default_factory=dict)
    quiet_hours: QuietHoursPreference = Field(default_factory=QuietHoursPreference)
    batching: BatchingPreference = Field(default_factory=BatchingPreference)
    escalation: EscalationPreference = Field(default_factory=EscalationPreference)
    type_overrides: dict[str, TypeOverride] = Field(default_factory=dict)
    daily_summary: DailySummaryPreference = Field(default_factory=DailySummaryPreference)
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


# ── Web Push (PWA) ───────────────────────────────────────────────────

# SEC-004 — input-validation bounds for Web Push subscription fields.
_MAX_ENDPOINT_LENGTH = 2048
_MAX_KEY_LENGTH = 256
# base64url alphabet with optional trailing padding.
_BASE64URL_PATTERN = r"^[A-Za-z0-9_-]+=*$"


def _require_https_url(value: str) -> str:
    """Reject any endpoint that is not a syntactically valid https URL.

    A defence-in-depth check at the schema boundary; the SSRF check
    (DNS resolution + IP-range rejection) runs additionally in the service.
    """
    if not value.startswith("https://"):
        raise ValueError("Push endpoint must be an https URL.")
    return value


class VapidPublicKeyResponse(BaseModel):
    """VAPID public key for client-side Web Push subscription."""

    vapid_public_key: str


class PwaSubscribeRequest(BaseModel):
    """Request body to register a Web Push subscription."""

    endpoint: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_ENDPOINT_LENGTH,
        description="Push service endpoint URL (https).",
    )
    p256dh: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_KEY_LENGTH,
        pattern=_BASE64URL_PATTERN,
        description="Client public key (base64url).",
    )
    auth: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_KEY_LENGTH,
        pattern=_BASE64URL_PATTERN,
        description="Client auth secret (base64url).",
    )
    user_agent: str | None = Field(
        default=None,
        max_length=512,
        description="Originating user agent, for display only.",
    )

    @field_validator("endpoint")
    @classmethod
    def _validate_endpoint(cls, value: str) -> str:
        return _require_https_url(value)


class PwaSubscribeResponse(BaseModel):
    """Result of registering a Web Push subscription."""

    endpoint: str


class PwaUnsubscribeRequest(BaseModel):
    """Request body to remove a Web Push subscription."""

    endpoint: str = Field(
        ...,
        min_length=1,
        max_length=_MAX_ENDPOINT_LENGTH,
        description="Push service endpoint URL (https).",
    )

    @field_validator("endpoint")
    @classmethod
    def _validate_endpoint(cls, value: str) -> str:
        return _require_https_url(value)


class PwaUnsubscribeResponse(BaseModel):
    """Result of removing a Web Push subscription."""

    removed: bool
