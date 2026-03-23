from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NotificationUrgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class NotificationAction(BaseModel):
    action_id: str
    title: str
    uri: str | None = None


class Notification(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    user_key: str = ""
    notification_type: str
    title: str
    body: str
    urgency: NotificationUrgency = NotificationUrgency.NORMAL
    data: dict = Field(default_factory=dict)
    actions: list[NotificationAction] = Field(default_factory=list)
    image_url: str | None = None
    group_key: str | None = None
    ha_event_type: str | None = None
    channels_sent: list[str] = Field(default_factory=list)
    channels_failed: list[str] = Field(default_factory=list)
    status: NotificationStatus = NotificationStatus.PENDING
    read_at: datetime | None = None
    acted_at: datetime | None = None
    escalation_level: int = Field(default=0, ge=0)
    parent_notification_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ChannelResult(BaseModel):
    channel_key: str
    success: bool
    error: str | None = None
    external_id: str | None = None


# ── Notification Preferences sub-models ─────────────────────────────


class ChannelPreference(BaseModel):
    enabled: bool = False
    priority: int = Field(default=0, ge=0)
    config: dict = Field(default_factory=dict)


class QuietHoursPreference(BaseModel):
    enabled: bool = True
    start: str = "22:00"
    end: str = "07:00"
    timezone: str = "Europe/Berlin"


class BatchingPreference(BaseModel):
    enabled: bool = True
    window_minutes: int = Field(default=30, ge=1, le=120)
    max_batch_size: int = Field(default=10, ge=1, le=50)


class EscalationPreference(BaseModel):
    watering_enabled: bool = True
    escalation_days: list[int] = Field(default_factory=lambda: [2, 4, 7])


class TypeOverride(BaseModel):
    channels: list[str] = Field(default_factory=list)
    ignore_quiet_hours: bool = False


class DailySummaryPreference(BaseModel):
    enabled: bool = False
    time: str = "07:00"
    channel: str = "home_assistant"


class NotificationPreferences(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str = ""
    channels: dict[str, ChannelPreference] = Field(default_factory=dict)
    quiet_hours: QuietHoursPreference = Field(default_factory=QuietHoursPreference)
    batching: BatchingPreference = Field(default_factory=BatchingPreference)
    escalation: EscalationPreference = Field(default_factory=EscalationPreference)
    type_overrides: dict[str, TypeOverride] = Field(default_factory=dict)
    daily_summary: DailySummaryPreference = Field(default_factory=DailySummaryPreference)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
