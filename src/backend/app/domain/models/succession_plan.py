from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import SuccessionPlanStatus


class SuccessionPlan(BaseModel):
    """REQ-013 §2 — staggered-sowing plan that generates a series of PlantingRuns.

    A succession plan (Staffelanbau) describes a species that is re-sown at a
    fixed interval across a growing window ("all 3 weeks re-sow lettuce"). The
    plan auto-generates one PlantingRun per batch; ``total_batches`` is derived
    from the schedule and ``completed_batches`` tracks how many batches have
    already been generated.
    """

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    species_key: str
    cultivar_key: str | None = None
    interval_days: int = Field(ge=1)
    start_date: date
    end_date: date
    plants_per_batch: int = Field(ge=1)
    total_batches: int = Field(default=0, ge=0)
    completed_batches: int = Field(default=0, ge=0)
    status: SuccessionPlanStatus = SuccessionPlanStatus.PLANNED
    reminder_days_before: int = Field(default=3, ge=0)
    location_key: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_date_range(self) -> SuccessionPlan:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self
