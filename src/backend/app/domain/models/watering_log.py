from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import ApplicationMethod, WaterSource


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
        if self.is_supplemental and self.application_method == ApplicationMethod.FERTIGATION:
            raise ValueError(
                "Supplemental watering cannot use fertigation application method",
            )
        if not self.slot_keys and not self.plant_keys:
            raise ValueError(
                "At least one of slot_keys or plant_keys must be provided",
            )
        return self
