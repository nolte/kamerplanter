from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import SuccessionPlanStatus


class SuccessionPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    species_key: str
    cultivar_key: str | None = None
    interval_days: int = Field(ge=1)
    start_date: date
    end_date: date
    plants_per_batch: int = Field(ge=1)
    reminder_days_before: int = Field(default=3, ge=0)
    location_key: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> SuccessionPlanCreate:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class SuccessionPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    cultivar_key: str | None = None
    interval_days: int | None = Field(default=None, ge=1)
    start_date: date | None = None
    end_date: date | None = None
    plants_per_batch: int | None = Field(default=None, ge=1)
    reminder_days_before: int | None = Field(default=None, ge=0)
    location_key: str | None = None
    notes: str | None = None
    status: SuccessionPlanStatus | None = None


class SuccessionPlanResponse(BaseModel):
    key: str
    name: str
    species_key: str
    cultivar_key: str | None
    interval_days: int
    start_date: date
    end_date: date
    plants_per_batch: int
    total_batches: int
    completed_batches: int
    status: SuccessionPlanStatus
    reminder_days_before: int
    location_key: str | None
    notes: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GenerateRunSummary(BaseModel):
    run_key: str
    name: str
    succession_sequence: int | None = None
    succession_total: int | None = None
    planned_start_date: date | None = None


class GenerateRunsResponse(BaseModel):
    plan: SuccessionPlanResponse
    generated_count: int
    runs: list[GenerateRunSummary]


class GenerateNextRunResponse(BaseModel):
    plan: SuccessionPlanResponse
    generated: bool
    run: GenerateRunSummary | None = None
