from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ApplicationMethod


class FeedingEventFertilizer(BaseModel):
    fertilizer_key: str
    ml_applied: float = Field(gt=0)


class FeedingEvent(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    plant_key: str
    timestamp: datetime | None = None
    application_method: ApplicationMethod = ApplicationMethod.FERTIGATION
    is_supplemental: bool = False
    tank_fill_event_key: str | None = None
    #: ``None`` for a dry dose (``g`` / ``kg`` / ``g_per_m2``) logged by a task completion (REQ-053 WP 4.3); the
    #: API still requires it on a create, so a fertigation row always carries it.
    volume_applied_liters: float | None = Field(default=None, gt=0)
    fertilizers_used: list[FeedingEventFertilizer] = Field(default_factory=list)
    measured_ec_before: float | None = Field(default=None, ge=0)
    measured_ec_after: float | None = Field(default=None, ge=0)
    measured_ph_before: float | None = Field(default=None, ge=0, le=14)
    measured_ph_after: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_volume_liters: float | None = Field(default=None, ge=0)
    watering_event_key: str | None = None
    channel_id: str | None = None
    notes: str | None = None
    # ── REQ-053 WP 4.3: a feeding logged by a bed task completion (GP-FR-083, GP-ACC-024) — additive ──
    #: The bed the task was bound to; ``plant_key`` holds the first plant (empty for the whole bed).
    location_key: str | None = None
    #: Every plant of the dose; empty for the whole bed.
    plant_keys: list[str] = Field(default_factory=list)
    task_key: str | None = None
    #: The product and the dose as typed (``quantity`` in ``unit``) and, for an area dose, the total for the bed.
    product_key: str | None = None
    material: str | None = None
    dose_quantity: float | None = Field(default=None, ge=0)
    dose_unit: str | None = None
    quantity_total: float | None = Field(default=None, ge=0)
    quantity_total_unit: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
