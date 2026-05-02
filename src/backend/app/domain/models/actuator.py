"""REQ-018 Environment-control actuator model (scaffold)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ActuatorProtocol = Literal["home_assistant", "mqtt", "manual"]
ActuatorState = Literal["off", "on", "manual_override", "fault"]


class Actuator(BaseModel):
    """REQ-018 v1.0 scaffold — physical or HA-mediated actuator."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str
    protocol: ActuatorProtocol = "home_assistant"
    ha_entity_id: str | None = None
    state: ActuatorState = "off"
    last_changed_at: datetime | None = None

    model_config = {"populate_by_name": True}
