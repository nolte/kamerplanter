from datetime import date, datetime

from pydantic import BaseModel, Field


class PlantInstance(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    instance_id: str
    species_key: str
    cultivar_key: str | None = None
    slot_key: str | None = None
    substrate_batch_key: str | None = None
    plant_name: str | None = None
    planted_on: date
    removed_on: date | None = None
    current_phase: str = "seedling"
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
