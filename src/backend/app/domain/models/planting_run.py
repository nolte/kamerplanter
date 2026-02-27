from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import EntryRole, PlantingRunStatus, PlantingRunType

ALLOWED_STATUS_TRANSITIONS: dict[PlantingRunStatus, list[PlantingRunStatus]] = {
    PlantingRunStatus.PLANNED: [PlantingRunStatus.ACTIVE, PlantingRunStatus.CANCELLED],
    PlantingRunStatus.ACTIVE: [PlantingRunStatus.HARVESTING, PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED],
    PlantingRunStatus.HARVESTING: [PlantingRunStatus.COMPLETED, PlantingRunStatus.CANCELLED],
    PlantingRunStatus.COMPLETED: [],
    PlantingRunStatus.CANCELLED: [],
}


class PlantingRunEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    run_key: str = ""
    species_key: str
    cultivar_key: str | None = None
    quantity: int = Field(ge=1)
    role: EntryRole = EntryRole.PRIMARY
    id_prefix: str = Field(pattern=r"^[A-Z]{2,5}$")
    spacing_cm: float | None = Field(default=None, ge=0)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PlantingRun(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    run_type: PlantingRunType
    status: PlantingRunStatus = PlantingRunStatus.PLANNED
    planned_quantity: int = Field(default=0, ge=0)
    actual_quantity: int = Field(default=0, ge=0)
    location_key: str | None = None
    substrate_batch_key: str | None = None
    planned_start_date: date | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    source_plant_key: str | None = None
    nutrient_plan_key: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_clone_has_source(self) -> PlantingRun:
        if self.run_type == PlantingRunType.CLONE and not self.source_plant_key:
            raise ValueError("Clone runs require a source_plant_key.")
        return self

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: PlantingRunStatus) -> PlantingRunStatus:
        if v not in PlantingRunStatus:
            raise ValueError(f"Invalid status: {v}")
        return v
