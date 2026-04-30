"""REQ-016 InvenTree integration adapter (scaffold).

Optional integration with the InvenTree inventory management system —
syncs Fertilizer / Substrate stock and reservation data. Concrete
HTTP calls land with the REQ-016 follow-up PR; the adapter shape
itself is pinned here so the service layer can wire up.
"""

from __future__ import annotations

from typing import Any


class InvenTreeAdapter:
    """Scaffold adapter — pins the public surface for REQ-016."""

    def __init__(self, base_url: str, api_token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token

    async def list_stock_for_part(self, part_id: int) -> list[dict[str, Any]]:
        """Return stock entries for an InvenTree part. Pending follow-up."""
        raise NotImplementedError("InvenTreeAdapter.list_stock_for_part — pending REQ-016 follow-up.")

    async def reserve_part(self, part_id: int, quantity: float) -> dict[str, Any]:
        """Reserve a quantity of a part for an upcoming order. Pending follow-up."""
        raise NotImplementedError("InvenTreeAdapter.reserve_part — pending REQ-016 follow-up.")

    async def health_check(self) -> dict[str, Any]:
        """Ping the configured InvenTree instance."""
        return {
            "backend": "inventree",
            "base_url": self._base_url,
            "ready": False,
            "reason": "scaffolding — REQ-016 follow-up wires the HTTP client",
        }
