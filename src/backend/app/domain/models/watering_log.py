from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import ApplicationMethod, WaterSource


@dataclass(frozen=True)
class WateringLogRuleViolation:
    """One broken cross-field rule of a watering log, plus the fields it is about.

    ``fields`` lets the API boundary report the violation *per field*
    (``details[].field`` of the NFR-006 error envelope) instead of as one opaque
    body-level message, and ``code`` is the stable machine-readable marker a
    client may branch on — ``message`` is free to change.
    """

    code: str
    message: str
    fields: tuple[str, ...]


def find_watering_log_violations(
    *,
    is_supplemental: bool,
    application_method: ApplicationMethod,
    slot_keys: Sequence[str],
    plant_keys: Sequence[str],
) -> list[WateringLogRuleViolation]:
    """Return the watering-log cross-field rules that the given values break.

    This function is the **single statement** of those rules. Three places need
    them and each needs a different error shape, which is why it reports the
    violations instead of raising (#970):

    * :meth:`WateringLog.check_valid` — the last line of defence for every
      non-HTTP caller (Celery tasks, MCP tools, migrations). It still raises, and
      must: a caller that assembles a model wrongly has a bug, not a bad request.
    * ``WateringLogCreate`` in the API layer, which turns the same violations
      into a 422 **before** the domain model is built. A domain-model validation
      error escaping a request handler is a plain ``pydantic.ValidationError``,
      not FastAPI's ``RequestValidationError``; it matches neither validation
      handler and lands on the 500 handler, so the caller was told "we broke"
      for input we ourselves consider invalid.
    * ``WateringLogService.update_log``, which must judge a partial patch against
      the *merged* state, something no request schema can see.

    Args:
        is_supplemental: Whether the watering is a supplemental (top-up) pass.
        application_method: How the solution is applied.
        slot_keys: Slots the log is attached to.
        plant_keys: Plant instances the log is attached to.

    Returns:
        The violated rules, in the order they are checked. Empty = valid.
    """
    violations: list[WateringLogRuleViolation] = []
    if is_supplemental and application_method == ApplicationMethod.FERTIGATION:
        violations.append(
            WateringLogRuleViolation(
                code="supplemental_cannot_fertigate",
                message="Supplemental watering cannot use fertigation application method",
                fields=("is_supplemental", "application_method"),
            )
        )
    if not slot_keys and not plant_keys:
        violations.append(
            WateringLogRuleViolation(
                code="watering_target_required",
                message="At least one of slot_keys or plant_keys must be provided",
                fields=("slot_keys", "plant_keys"),
            )
        )
    return violations


class WateringLogFertilizer(BaseModel):
    """Fertilizer usage record within a watering log entry."""

    fertilizer_key: str
    ml_per_liter: float = Field(gt=0)


class WateringLog(BaseModel):
    """Unified watering/feeding log entry (Gießprotokoll).

    Replaces both WateringEvent and FeedingEvent.
    One document per watering action — references plants and/or slots.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""

    # ── When ──────────────────────────────────────────────────────────
    logged_at: datetime | None = None

    # ── What was applied ──────────────────────────────────────────────
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    is_supplemental: bool = False
    volume_liters: float = Field(gt=0)
    fertilizers_used: list[WateringLogFertilizer] = Field(default_factory=list)

    # ── Where / to whom ───────────────────────────────────────────────
    plant_keys: list[str] = Field(default_factory=list)
    slot_keys: list[str] = Field(default_factory=list)

    # ── References ────────────────────────────────────────────────────
    tank_fill_event_key: str | None = None
    nutrient_plan_key: str | None = None
    task_key: str | None = None
    channel_id: str | None = None

    # ── Water source & operator ───────────────────────────────────────
    water_source: WaterSource | None = None
    performed_by: str | None = None

    # ── EC/pH measurements (before = input solution, after = measured) ──
    ec_before: float | None = Field(default=None, ge=0)
    ec_after: float | None = Field(default=None, ge=0)
    ph_before: float | None = Field(default=None, ge=0, le=14)
    ph_after: float | None = Field(default=None, ge=0, le=14)

    # ── Runoff measurements ───────────────────────────────────────────
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)

    # ── Notes & timestamps ────────────────────────────────────────────
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_valid(self) -> WateringLog:
        """Reject a log that breaks a cross-field rule (the rules live in one place).

        Deliberately kept raising even though the API boundary now rejects the same
        input with a 422 first (#970): this is the last line of defence for callers
        that never touch HTTP — Celery tasks, MCP tools, migrations, services
        assembling a log themselves.
        """
        violations = find_watering_log_violations(
            is_supplemental=self.is_supplemental,
            application_method=self.application_method,
            slot_keys=self.slot_keys,
            plant_keys=self.plant_keys,
        )
        if violations:
            raise ValueError(violations[0].message)
        return self
