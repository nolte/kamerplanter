from datetime import datetime
from types import UnionType
from typing import Union, get_args, get_origin

from pydantic import BaseModel, Field, model_validator

from app.common.enums import CareStyleType, ConfirmAction, ReminderType, WateringMethod
from app.domain.models.care_reminder import CareProfile


def _nullable_on_the_profile() -> frozenset[str]:
    """Every field :class:`CareProfile` admits ``None`` for, read off its annotations."""
    nullable = set()
    for name, field in CareProfile.model_fields.items():
        annotation = field.annotation
        if get_origin(annotation) in (Union, UnionType) and type(None) in get_args(annotation):
            nullable.add(name)
    return frozenset(nullable)


class CareProfileResponse(BaseModel):
    key: str
    care_style: CareStyleType
    watering_interval_days: int
    winter_watering_multiplier: float
    watering_method: WateringMethod
    water_quality_hint: str | None = None
    fertilizing_interval_days: int
    fertilizing_active_months: list[int]
    repotting_interval_months: int
    pest_check_interval_days: int
    location_check_enabled: bool
    location_check_months: list[int]
    humidity_check_enabled: bool
    humidity_check_interval_days: int
    adaptive_learning_enabled: bool
    auto_create_watering_task: bool
    auto_create_fertilizing_task: bool
    auto_create_repotting_task: bool
    auto_create_pest_check_task: bool
    watering_interval_learned: int | None = None
    fertilizing_interval_learned: int | None = None
    notes: str | None = None
    auto_generated: bool
    plant_key: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CareProfileUpdate(BaseModel):
    care_style: CareStyleType | None = None
    watering_interval_days: int | None = Field(default=None, ge=1, le=90)
    winter_watering_multiplier: float | None = Field(default=None, ge=1.0, le=5.0)
    watering_method: WateringMethod | None = None
    water_quality_hint: str | None = None
    fertilizing_interval_days: int | None = Field(default=None, ge=7, le=90)
    fertilizing_active_months: list[int] | None = None
    repotting_interval_months: int | None = Field(default=None, ge=6, le=60)
    pest_check_interval_days: int | None = Field(default=None, ge=3, le=90)
    location_check_enabled: bool | None = None
    location_check_months: list[int] | None = None
    humidity_check_enabled: bool | None = None
    humidity_check_interval_days: int | None = Field(default=None, ge=3, le=90)
    adaptive_learning_enabled: bool | None = None
    auto_create_watering_task: bool | None = None
    auto_create_fertilizing_task: bool | None = None
    auto_create_repotting_task: bool | None = None
    auto_create_pest_check_task: bool | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _reject_null_where_null_is_not_a_value(self) -> CareProfileUpdate:
        """A ``null`` is only accepted for a field the profile can actually hold as one.

        ``None`` carries two meanings in this schema and the router now tells them
        apart by ``model_fields_set`` (#1506): a field the body omitted is left alone,
        a field the body sent as ``null`` is written. For ``notes`` and
        ``water_quality_hint`` that write is a clear — the frontend's care form sends
        exactly that the moment the user empties the box. For every other field the
        domain model has no ``None`` to write, so the request is refused here at the
        boundary (422) rather than reaching ``CareProfile(**data)`` as a 500 or being
        silently dropped, which is the behaviour this issue is about.
        """
        offenders = sorted(
            name
            for name in self.model_fields_set
            if getattr(self, name, None) is None and name not in CLEARABLE_PROFILE_FIELDS
        )
        if offenders:
            raise ValueError(
                f"null is not a value for {', '.join(offenders)}; omit the field to leave it "
                f"unchanged. Only {', '.join(sorted(CLEARABLE_PROFILE_FIELDS))} may be cleared."
            )
        return self


#: The fields a ``PATCH`` body may send as ``null`` to clear — today ``notes`` and
#: ``water_quality_hint`` (#1506).
#:
#: **The intersection, not either side alone** (#1506 review, SCR-006). A field is
#: clearable only if *both* are true: :class:`CareProfile` admits ``None`` for it
#: (otherwise there is no ``null`` to store), **and** :class:`CareProfileUpdate`
#: exposes it (otherwise no request can name it anyway). Taking the model's nullable
#: set alone answered with eight names — ``key``, ``created_at``, ``updated_at``, the
#: two ``*_learned`` intervals and ``dormancy_watering`` among them — none of which a
#: client can send, which made the constant read as a far wider promise than the
#: schema keeps.
#:
#: Derived rather than listed, so making a further exposed field nullable on
#: ``CareProfile`` widens both sides at once instead of leaving its ``null`` rejected
#: with nothing failing. Defined after the class because it reads its fields; the
#: validator above resolves it at call time.
CLEARABLE_PROFILE_FIELDS: frozenset[str] = _nullable_on_the_profile() & frozenset(CareProfileUpdate.model_fields)


class FeedingDetailSchema(BaseModel):
    fertilizer_key: str
    ml_applied: float = Field(gt=0)


class ConfirmRequest(BaseModel):
    reminder_type: ReminderType
    notes: str | None = None
    volume_liters: float | None = Field(default=None, gt=0)
    fertilizers_used: list[FeedingDetailSchema] | None = None
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)


class SnoozeRequest(BaseModel):
    reminder_type: ReminderType
    snooze_days: int = Field(default=1, ge=1, le=7)


class CareConfirmationResponse(BaseModel):
    key: str
    plant_key: str
    care_profile_key: str
    reminder_type: ReminderType
    action: ConfirmAction
    confirmed_at: datetime
    snooze_days: int | None = None
    watering_log_key: str | None = None
    notes: str | None = None
    interval_at_time: int | None = None


class CareDashboardEntryResponse(BaseModel):
    plant_key: str
    plant_name: str
    species_name: str | None = None
    reminder_type: ReminderType
    urgency: str
    due_date: str | None = None
    care_profile_key: str
    task_key: str | None = None
