from datetime import date, datetime

from pydantic import BaseModel


class PlantCreate(BaseModel):
    instance_id: str
    species_key: str
    cultivar_key: str | None = None
    slot_key: str | None = None
    substrate_batch_key: str | None = None
    plant_name: str | None = None
    planted_on: date
    current_phase: str = "seedling"

class PlantResponse(BaseModel):
    key: str
    instance_id: str
    species_key: str
    cultivar_key: str | None
    slot_key: str | None
    substrate_batch_key: str | None
    plant_name: str | None
    planted_on: date
    removed_on: date | None
    current_phase: str
    current_phase_key: str | None
    current_phase_started_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class ValidatePlantingRequest(BaseModel):
    species_key: str

class ValidatePlantingResponse(BaseModel):
    valid: bool
    warnings: list[str]
    benefits: list[str]
