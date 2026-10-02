from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


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
    #: Push endpoints the push service reported as gone (HTTP 404/410, #1827).
    #: Structured, so the sender can prune them — until #1827 they were encoded
    #: into ``error`` as ``expired:<endpoint>,…`` and nothing parsed them. Never
    #: serialised or printed: an endpoint's path is the device's push token.
    expired_endpoints: list[str] = Field(default_factory=list, exclude=True, repr=False)


# ── Notification Preferences sub-models ─────────────────────────────


#: Keys under which a preference once carried a mail recipient. The e-mail
#: channel mails the account's confirmed address only (#1885); none of these is
#: stored, read or sent to any more.
EMAIL_RECIPIENT_KEYS: tuple[str, ...] = ("email", "address")

#: The only keys ``channels.email.config`` may hold (#1885): a positive list, so
#: a spelling of the recipient this module has not thought of (``Email``, ``to``,
#: ``recipient``) is not stored either.
EMAIL_CONFIG_KEYS: frozenset[str] = frozenset({"digest"})


class ChannelPreference(BaseModel):
    """Per-channel delivery preference.

    ``config`` carries channel-specific settings by convention (no schema).
    For the ``email`` channel: ``config["digest"]`` (bool) opts the user into the
    daily email digest (REQ-030). The recipient is not configurable (#1885): the
    channel mails the account's confirmed address, and a ``config["email"]``
    sent by a client is dropped by :class:`NotificationPreferences`.
    For the ``pwa`` channel: ``config["subscriptions"]`` holds the Web Push
    subscriptions.
    """

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

    @model_validator(mode="after")
    def _drop_free_text_email_recipient(self) -> NotificationPreferences:
        """Never hold a typed-in mail recipient (#1885).

        Runs on every construction (the preferences route, a row loaded from the
        database), so a recipient neither gets stored nor survives a read.
        """
        email_pref = self.channels.get("email")
        if email_pref is not None:
            for key in [k for k in email_pref.config if k not in EMAIL_CONFIG_KEYS]:
                del email_pref.config[key]
        return self
