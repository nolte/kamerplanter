from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime

    from app.common.enums import SubstrateType


class PlantInstance(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    instance_id: str
    species_key: str
    cultivar_key: str | None = None
    location_key: str | None = None
    slot_key: str | None = None
    substrate_batch_key: str | None = None
    substrate_key: str | None = Field(
        default=None,
        description="Reference to a Substrate record — substrate_type_override is auto-derived",
    )
    plant_name: str | None = None
    planted_on: date
    removed_on: date | None = None
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    container_volume_liters: float | None = Field(
        default=None,
        ge=0.1,
        le=500,
        description="Actual container/pot volume in liters for this plant instance",
    )
    substrate_type_override: SubstrateType | None = Field(
        default=None,
        description="Direct substrate type — overrides substrate_batch_key lookup",
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
