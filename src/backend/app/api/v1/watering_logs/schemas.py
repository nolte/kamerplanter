from __future__ import annotations

from datetime import datetime
from typing import NoReturn

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic_core import InitErrorDetails, PydanticCustomError

from app.common.enums import ApplicationMethod, WaterSource
from app.domain.models.watering_log import WateringLogRuleViolation, find_watering_log_violations


def _raise_as_field_errors(model: BaseModel, violations: list[WateringLogRuleViolation]) -> NoReturn:
    """Report domain rule violations as *request* validation errors, per field.

    A plain ``raise ValueError`` inside a request-schema validator also yields a
    422, but Pydantic files it under ``loc = ("body",)``: the client learns only
    that "the body" is wrong. Building the errors explicitly puts each violation
    on the fields it is about, so the NFR-006 envelope carries
    ``details[].field = "body.plant_keys"`` and the frontend's ``getFieldErrors``
    can mark the offending inputs instead of a phantom ``body`` field.

    Args:
        model: The validated request model the violations were found on.
        violations: The broken rules, as reported by the domain.

    Raises:
        ValidationError: Always — one error entry per (violation, field) pair.
    """
    raise ValidationError.from_exception_data(
        model.__class__.__name__,
        [
            InitErrorDetails(
                type=PydanticCustomError(violation.code, violation.message),
                loc=(field,),
                input=getattr(model, field, None),
            )
            for violation in violations
            for field in violation.fields
        ],
    )


class WateringLogFertilizerSchema(BaseModel):
    fertilizer_key: str
    ml_per_liter: float = Field(gt=0)


class WateringLogCreate(BaseModel):
    # Both enum fields mirror the domain contract (``WateringLog``) exactly. Typed
    # as ``str`` they let an unknown value through the API layer and blow up inside
    # the domain model as an unhandled ``ValidationError`` — HTTP 500 for what is a
    # caller error (#970, same shape as #966/#967).
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    is_supplemental: bool = False
    volume_liters: float = Field(gt=0)
    plant_keys: list[str] = Field(default_factory=list)
    slot_keys: list[str] = Field(default_factory=list)
    tank_fill_event_key: str | None = None
    nutrient_plan_key: str | None = None
    channel_id: str | None = None
    fertilizers_used: list[WateringLogFertilizerSchema] = Field(default_factory=list)
    ec_before: float | None = Field(default=None, ge=0)
    ec_after: float | None = Field(default=None, ge=0)
    ph_before: float | None = Field(default=None, ge=0, le=14)
    ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    water_source: WaterSource | None = None
    performed_by: str | None = None
    notes: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "application_method": "drench",
                    "is_supplemental": False,
                    "volume_liters": 2.5,
                    "plant_keys": ["plant_tomate_1"],
                    "water_source": "rainwater",
                    "ec_before": 1.4,
                    "ph_before": 6.2,
                    "fertilizers_used": [{"fertilizer_key": "fert_biobizz_grow", "ml_per_liter": 2.0}],
                    "performed_by": "Lisa",
                }
            ]
        }
    )

    @model_validator(mode="after")
    def check_domain_rules(self) -> WateringLogCreate:
        """Apply the domain's own cross-field rules here, at the boundary.

        The router builds a ``WateringLog`` from this body, and the domain model
        rejects the same combinations — but as a ``pydantic.ValidationError``,
        which is not FastAPI's ``RequestValidationError`` and therefore fell
        through to the 500 handler (#970). Rules are not restated here; they are
        read from the one place that owns them.
        """
        violations = find_watering_log_violations(
            is_supplemental=self.is_supplemental,
            application_method=self.application_method,
            slot_keys=self.slot_keys,
            plant_keys=self.plant_keys,
        )
        if violations:
            _raise_as_field_errors(self, violations)
        return self


class WateringLogUpdate(BaseModel):
    # Enum-typed for the same reason as on create — with a twist: this path wrote
    # the document *before* the domain model was rebuilt from it, so an unknown
    # value was persisted and every later read of that log then raised (#970).
    application_method: ApplicationMethod | None = None
    is_supplemental: bool | None = None
    volume_liters: float | None = Field(default=None, gt=0)
    ec_before: float | None = Field(default=None, ge=0)
    ec_after: float | None = Field(default=None, ge=0)
    ph_before: float | None = Field(default=None, ge=0, le=14)
    ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    notes: str | None = None

    # No cross-field validator here on purpose: a patch may carry
    # ``is_supplemental`` without ``application_method`` (or the other way round),
    # so only the *merged* state decides — which the service checks before writing
    # (``WateringLogService.update_log``). Restating half the rule here would give
    # the same condition two homes and one of them a blind spot.

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "volume_liters": 3.0,
                    "application_method": "foliar",
                    "runoff_ec": 1.8,
                    "notes": "Nachgegossen, Substrat war noch trocken.",
                }
            ]
        }
    )


class ResolvedPlant(BaseModel):
    key: str
    name: str


class ResolvedFertilizer(BaseModel):
    key: str
    name: str
    ml_per_liter: float


class WateringLogResponse(BaseModel):
    key: str
    logged_at: datetime | None
    application_method: str
    is_supplemental: bool
    volume_liters: float
    plant_keys: list[str]
    slot_keys: list[str]
    tank_fill_event_key: str | None
    nutrient_plan_key: str | None
    task_key: str | None
    channel_id: str | None
    fertilizers_used: list[WateringLogFertilizerSchema]
    ec_before: float | None
    ec_after: float | None
    ph_before: float | None
    ph_after: float | None
    runoff_ec: float | None
    runoff_ph: float | None
    runoff_volume_liters: float | None
    water_source: str | None
    performed_by: str | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_plants: list[ResolvedPlant] = Field(default_factory=list)
    resolved_fertilizers: list[ResolvedFertilizer] = Field(default_factory=list)


class WateringLogWithWarnings(BaseModel):
    log: WateringLogResponse
    warnings: list[dict]


class MethodStats(BaseModel):
    method: str
    count: int
    total_volume: float


class WateringStatsResponse(BaseModel):
    total_events: int
    total_volume: float
    by_method: list[MethodStats]


class WateringConfirmOverrides(BaseModel):
    """What a confirmation may override on the log the plan would have produced.

    Was a free-form ``dict``, which left the fertilizer lines unvalidated at the
    boundary: the service builds ``WateringLogFertilizer`` from them, so a missing
    ``fertilizer_key`` raised ``KeyError`` and a dose of ``0`` raised
    ``ValidationError`` — both unhandled, both HTTP 500 for caller input (#970).
    """

    fertilizers: list[WateringLogFertilizerSchema] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"fertilizers": [{"fertilizer_key": "fert_biobizz_grow", "ml_per_liter": 2.0}]}]
        }
    )


class WateringConfirmRequest(BaseModel):
    run_key: str
    task_key: str
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    volume_liters: float | None = Field(default=None, gt=0)
    overrides: WateringConfirmOverrides | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_key": "run_tomaten_2026",
                    "task_key": "task_giessen_kw24",
                    "measured_ec": 1.6,
                    "measured_ph": 6.1,
                    "volume_liters": 4.0,
                }
            ]
        }
    )


class WateringQuickConfirmRequest(BaseModel):
    run_key: str
    task_key: str


class WateringConfirmResponse(BaseModel):
    watering_log_key: str
    task_completed: bool
    warnings: list[dict] = Field(default_factory=list)


class RunoffAnalysisResponse(BaseModel):
    """Drain-to-waste runoff analysis, or an ``error`` when runoff data is incomplete.

    All fields are optional so the successful analysis and the ``error`` fallback
    share one model; the endpoint uses ``response_model_exclude_unset`` so only the
    keys actually produced are serialized (the JSON stays identical to the raw dict).
    """

    error: str | None = None
    ec_delta: float | None = None
    ec_status: str | None = None
    ec_message: str | None = None
    ph_delta: float | None = None
    ph_status: str | None = None
    ph_message: str | None = None
    runoff_percent: float | None = None
    volume_status: str | None = None
    volume_message: str | None = None
    overall_health: str | None = None
