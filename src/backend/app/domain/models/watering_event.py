from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import ApplicationMethod, WaterSource


class FertilizerSnapshot(BaseModel):
    product_key: str | None = None
    product_name: str
    ml_per_liter: float = Field(gt=0)


class WateringEvent(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    watered_at: datetime | None = None
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    is_supplemental: bool = False
    volume_liters: float = Field(gt=0)
    slot_keys: list[str] = Field(min_length=1)
    tank_fill_event_key: str | None = None
    nutrient_plan_key: str | None = None
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)
    target_ec: float | None = Field(default=None, ge=0)
    target_ph: float | None = Field(default=None, ge=0, le=14)
    measured_ec: float | None = Field(default=None, ge=0)
    measured_ph: float | None = Field(default=None, ge=0, le=14)
    runoff_ec: float | None = Field(default=None, ge=0)
    runoff_ph: float | None = Field(default=None, ge=0, le=14)
    water_source: WaterSource | None = None
    performed_by: str | None = None
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_supplemental_not_fertigation(self) -> "WateringEvent":
        if self.is_supplemental and self.application_method == ApplicationMethod.FERTIGATION:
            raise ValueError(
                "Supplemental watering cannot use fertigation application method"
            )
        return self
