"""REQ-018 Actuator service scaffold."""

from __future__ import annotations

from typing import Any

from app.domain.models.actuator import Actuator


class ActuatorService:
    """Scaffold service — pins the public surface for REQ-018."""

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def list_for_tenant(self, tenant_key: str) -> list[Actuator]:
        raise NotImplementedError("REQ-018 ActuatorService.list_for_tenant — pending follow-up.")

    def set_state(self, key: str, state: str, source: str = "manual") -> Actuator:
        raise NotImplementedError("REQ-018 ActuatorService.set_state — pending follow-up.")
