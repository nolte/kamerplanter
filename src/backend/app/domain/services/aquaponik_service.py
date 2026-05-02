"""REQ-026 Aquaponik service scaffold.

Manages the fish-tank-coupled nutrient loop. Concrete pH/ammonia/
nitrate balance logic lands with the REQ-026 implementation PR.
"""

from __future__ import annotations

from typing import Any


class AquaponikService:
    """Scaffold service — pins the public surface for REQ-026."""

    def __init__(self, repo: Any | None = None) -> None:
        self._repo = repo

    def get_loop_status(self, tenant_key: str) -> dict[str, Any]:
        raise NotImplementedError("REQ-026 AquaponikService.get_loop_status — pending follow-up.")

    def record_water_test(self, tenant_key: str, ph: float, ammonia: float, nitrate: float) -> dict[str, Any]:
        raise NotImplementedError("REQ-026 AquaponikService.record_water_test — pending follow-up.")
