"""Per-tenant allowlist of Home Assistant entities (MT-015, #2112).

Kamerplanter talks to **one** Home Assistant instance — the operator's — with one
token, for every tenant (REQ-005 §1.3, REQ-018 §1.3: "single-household
instance"). Which of that instance's entities a tenant may *use* — bind to a
sensor, an actuator, a weather source or a notification destination, and have
read or switched on its behalf — is decided by the platform admin, one row per
``(tenant_key, entity_id)``.

A Home Assistant ``notify`` *service* is not an entity, but it is addressed the
same way (``notify.<slug>``) and is granted the same way, so one allowlist covers
every destination a tenant can steer.

Source code is English only (NFR-003).
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

#: ``<domain>.<object_id>`` — the shape Home Assistant itself enforces. ASCII only,
#: ``fullmatch``: no newline slack, no Unicode letters. The id is later interpolated
#: into ``/api/states/{entity_id}``, so the shape is also the path-injection bound.
HA_ENTITY_ID_PATTERN = re.compile(r"[a-z0-9_]{1,64}\.[a-z0-9_]{1,191}", re.ASCII)
HA_ENTITY_ID_MAX_LENGTH = 256


def is_ha_entity_id(value: object) -> bool:
    """Whether ``value`` has the shape of a Home Assistant entity id."""
    return isinstance(value, str) and HA_ENTITY_ID_PATTERN.fullmatch(value) is not None


class HaEntityGrantSource(StrEnum):
    """How a grant came into existence."""

    #: Granted by a platform admin in the admin panel.
    ADMIN = "admin"
    #: Seeded by migration v0084 from a reference that existed before the allowlist.
    MIGRATION = "migration"
    #: Recorded when an entity was bound in light mode, where the only user is the operator.
    LIGHT_MODE = "light_mode"


class HaEntityGrant(BaseModel):
    """One Home Assistant entity released for one tenant."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = Field(min_length=1)
    entity_id: str = Field(min_length=3, max_length=HA_ENTITY_ID_MAX_LENGTH)
    source: HaEntityGrantSource = HaEntityGrantSource.ADMIN
    created_at: datetime | None = None

    model_config = {"populate_by_name": True, "use_enum_values": True}

    @field_validator("entity_id")
    @classmethod
    def _entity_id_shape(cls, value: str) -> str:
        if not is_ha_entity_id(value):
            raise ValueError("entity_id must be a Home Assistant entity id such as sensor.tent_temperature")
        return value
