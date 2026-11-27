import re
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


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
    #: The recipient. Required on every write (the repository refuses ``""``): every
    #: reader is per user, so an empty one was a row nobody's inbox shows (MT-045.8).
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

    @field_validator("escalation_level", mode="before")
    @classmethod
    def _missing_level_is_zero(cls, value: object) -> object:
        """A stored ``null`` level reads as 0, like a missing one (#3135).

        The overdue query and the claim read ``NOT_NULL(doc.escalation_level, 0)``;
        without this a selected null row would fail validation and abort the
        tenant's whole run.
        """
        return 0 if value is None else value


#: The one notification type the overdue escalation reads (REQ-030 §1.2: watering only).
#: Matched exactly: a prefix would also take :data:`WATERING_ESCALATION_TYPE` (#3135).
WATERING_REMINDER_TYPE = "care.watering"

#: The ``group_key`` prefix of the plant's single watering reminder row, the one the
#: propagation owner keeps in step with the plant's watering task
#: (``care.watering:<plant_key>``). Only this row is escalated: the due-care dispatch
#: also writes ``care.watering`` rows (group ``care:<user>:watering``), one per due
#: day, which no confirmation closes — escalating them too gave a second chain per
#: occurrence that kept running after the plant was watered (#3135).
WATERING_REMINDER_GROUP_PREFIX = "care.watering:"

#: The type of the notification the escalation sends. It shares the reminder's
#: ``group_key`` (closing the reminder closes its escalations) but is an event row,
#: never an escalation candidate and never the row a reminder update keeps (#3135).
WATERING_ESCALATION_TYPE = "care.watering.escalation"

#: The ISO spellings an announced due date may have — the intersection of what
#: Python's ``datetime.fromisoformat`` and ArangoDB's ``DATE_TIMESTAMP`` both read
#: the same way (measured on ArangoDB 3.12.13, #3135): a calendar date, optionally
#: ``T`` + ``HH:MM`` with optional seconds and fraction, optionally ``Z`` or
#: ``±HH:MM``. Outside it the two disagree in both directions — ArangoDB reads
#: ``" 2026-11-20"``, ``"+2026-11-20"`` and a space separator, Python reads
#: ``"2026-11-20T12"``, ``"20261120"``, ``"2026-W47-5"``, ``"+0200"`` and hour 24, and
#: ArangoDB reads year 0000 — so the overdue query and :func:`announced_due_date` both
#: require this shape first (hours 00–23, minutes and seconds 00–59, years 1000–9999).
#: Plain ``[0-9]`` (no ``\d``) so the same text is a valid ArangoDB ``REGEX_TEST``. It ends
#: in ``\z`` (end of input), not ``$``: in both engines ``$`` also matches before a
#: trailing line break — in ArangoDB even before ``\r\n`` (measured) — so a value
#: with a trailing newline passed.
DUE_DATE_SHAPE = (
    "^[1-9][0-9]{3}-[0-9]{2}-[0-9]{2}"
    "(T([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9]([.][0-9]+)?)?(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])?)?\\z"
)
_DUE_DATE_SHAPE = re.compile(DUE_DATE_SHAPE)


def announced_due_date(notification: Notification) -> datetime | None:
    """The due date of the occurrence a care reminder row announces, as an aware instant.

    The propagation owner writes it into ``data["due_date"]`` as an ISO string on
    every create, new occurrence and retiming
    (``NotificationPropagationService.sync_care_notification``, in the same call
    that moves the task). The overdue escalation measures "overdue" from it
    (REQ-030 §1.2, "Tag 0 = fällig"), never from ``created_at``: the row is reused
    across occurrences and keeps its creation time (#3135).

    The reading is the overdue query's, clause by clause: the value must be a
    string of :data:`DUE_DATE_SHAPE`, its calendar date must exist (ArangoDB rolls
    ``2026-02-30`` over into March, the query refuses it like Python does), and a
    value without an offset is UTC. Anything else is ``None`` — a row without a
    readable due date is not proven overdue.
    """
    raw = notification.data.get("due_date") if isinstance(notification.data, dict) else None
    if not isinstance(raw, str) or not _DUE_DATE_SHAPE.fullmatch(raw):
        return None
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def is_watering_escalation(notification: Notification) -> bool:
    """Whether *notification* is an overdue escalation sent for another row of its group (#3135).

    An escalation carries the reminder's ``group_key`` — closing the reminder closes
    its escalations too — but it is an event row: it follows no source, is never an
    escalation candidate, and a reminder update must neither keep it in place of the
    reminder nor prune the reminder as its duplicate. A row that names the row it
    was sent for (``parent_notification_key``) is one, whatever its type says.
    """
    if notification.notification_type == WATERING_ESCALATION_TYPE:
        return True
    return notification.parent_notification_key is not None


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
