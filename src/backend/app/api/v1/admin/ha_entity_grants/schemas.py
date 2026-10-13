"""Schemas of the platform-admin Home Assistant entity allowlist (MT-015, #2112)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.ha_entity_grant import HA_ENTITY_ID_MAX_LENGTH
from app.domain.services.ha_entity_grant_service import MAX_GRANTS_PER_REQUEST


class HaEntityGrantResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"entity_id": "sensor.tent_temperature", "source": "admin", "created_at": "2026-10-05T08:00:00+00:00"}
            ]
        }
    )

    entity_id: str
    source: str
    created_at: datetime | None = None


class HaEntityGrantsRequest(BaseModel):
    """Entities to release for the tenant. Already granted ones are left as they are."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"entity_ids": ["sensor.tent_temperature", "notify.mobile_app_phone"]}]}
    )

    entity_ids: list[str] = Field(
        min_length=1,
        max_length=MAX_GRANTS_PER_REQUEST,
        description="Home Assistant entity ids (``<domain>.<object_id>``); a notify service as ``notify.<service>``.",
    )


class HaEntityGrantsResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "created": 1,
                    "grants": [
                        {
                            "entity_id": "sensor.tent_temperature",
                            "source": "admin",
                            "created_at": "2026-10-05T08:00:00+00:00",
                        }
                    ],
                }
            ]
        }
    )

    created: int = Field(description="How many of the requested entities were not granted before.")
    grants: list[HaEntityGrantResponse]


class HaEntityInventoryItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "entity_id": "sensor.tent_temperature",
                    "domain": "sensor",
                    "friendly_name": "Tent temperature",
                    "unit_of_measurement": "°C",
                    "device_class": "temperature",
                    "granted": True,
                    "present": True,
                }
            ]
        }
    )

    entity_id: str = Field(max_length=HA_ENTITY_ID_MAX_LENGTH)
    domain: str
    friendly_name: str | None = None
    unit_of_measurement: str | None = None
    device_class: str | None = None
    granted: bool
    present: bool = Field(description="False for a granted entity Home Assistant no longer reports.")


class HaEntityInventoryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ha_configured": True,
                    "entities": [
                        {
                            "entity_id": "sensor.tent_temperature",
                            "domain": "sensor",
                            "friendly_name": "Tent temperature",
                            "unit_of_measurement": "°C",
                            "device_class": "temperature",
                            "granted": True,
                            "present": True,
                        }
                    ],
                }
            ]
        }
    )

    ha_configured: bool
    entities: list[HaEntityInventoryItem]
