from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class Sensor(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    metric_type: str  # "ec_ms", "ph", "water_temp_celsius", etc.
    ha_entity_id: str | None = None  # e.g. "sensor.tank_ec"
    unit_of_measurement: str | None = None  # e.g. "mS/cm", "pH", "°C"
    mqtt_topic: str | None = None  # Future: direct MQTT
    tank_key: str | None = None  # Denormalized for fast lookups
    site_key: str | None = None
    location_key: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _at_most_one_parent(self) -> Sensor:
        parents = [k for k in (self.tank_key, self.site_key, self.location_key) if k]
        if len(parents) > 1:
            msg = "Sensor may be attached to at most one of tank_key, site_key, or location_key"
            raise ValueError(msg)
        return self
