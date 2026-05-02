from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import ApplicationMethod, WaterSource


class FertilizerSnapshot(BaseModel):
    product_key: str | None = None
    product_name: str
    ml_per_liter: float = Field(gt=0)


class WateringEvent(BaseModel):
    """Watering event tied to one or more slots/plants.

    REQ-014 v1.6 (W-021) aligned the field names with TankFillEvent:
    ``slot_keys`` is the canonical field, the deprecated ``plant_keys`` alias
    is kept for backwards compatibility with REQ-013 v1.x callers and the
    current frontend. EC values carry the ``_ms`` suffix (mS/cm) to mirror
    the unit-explicit naming used everywhere else in the schema.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    watered_at: datetime | None = None
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    is_supplemental: bool = False
    volume_liters: float = Field(gt=0)
    slot_keys: list[str] = Field(default_factory=list)
    # Deprecated alias for ``slot_keys`` — accepted on input, mirrored on
    # output for legacy REQ-013/frontend consumers. Will be removed once the
    # frontend follows the rename.
    plant_keys: list[str] = Field(default_factory=list)
    tank_fill_event_key: str | None = None
    nutrient_plan_key: str | None = None
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)
    target_ec_ms: float | None = Field(default=None, ge=0)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    measured_ec_ms: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_ec_ms: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    # Deprecated unit-less EC aliases, see W-021. Mirror to ``*_ms`` on input
    # and output until the frontend follows. ``ec`` here is implicitly mS/cm.
    target_ec: float | None = Field(default=None, ge=0)
    measured_ec: float | None = Field(default=None, ge=0)
    runoff_ec: float | None = Field(default=None, ge=0)
    water_source: WaterSource | None = None
    performed_by: str | None = None
    task_key: str | None = None
    channel_id: str | None = None
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_valid(self) -> WateringEvent:
        if self.is_supplemental and self.application_method == ApplicationMethod.FERTIGATION:
            raise ValueError("Supplemental watering cannot use fertigation application method")
        # Dual-write the legacy aliases so readers see the same value
        # whichever name they pick (W-021 v1.6 transition window).
        if self.slot_keys and not self.plant_keys:
            self.plant_keys = list(self.slot_keys)
        elif self.plant_keys and not self.slot_keys:
            self.slot_keys = list(self.plant_keys)
        for canonical, legacy in (
            ("target_ec_ms", "target_ec"),
            ("measured_ec_ms", "measured_ec"),
            ("runoff_ec_ms", "runoff_ec"),
        ):
            canonical_value = getattr(self, canonical)
            legacy_value = getattr(self, legacy)
            if canonical_value is None and legacy_value is not None:
                setattr(self, canonical, legacy_value)
            elif legacy_value is None and canonical_value is not None:
                setattr(self, legacy, canonical_value)
        return self
