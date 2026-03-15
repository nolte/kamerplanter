import httpx
import structlog

logger = structlog.get_logger(__name__)


class HomeAssistantClient:
    """Synchronous HTTP client for Home Assistant REST API."""

    def __init__(self, base_url: str, token: str, timeout: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._timeout = timeout

    def list_sensor_entities(self) -> list[dict]:
        """GET /api/states -> all sensor.* entities with attributes."""
        url = f"{self._base_url}/api/states"
        resp = httpx.get(url, headers=self._headers, timeout=self._timeout)
        resp.raise_for_status()
        results = []
        for entity in resp.json():
            eid: str = entity.get("entity_id", "")
            if not eid.startswith("sensor."):
                continue
            attrs = entity.get("attributes", {})
            results.append(
                {
                    "entity_id": eid,
                    "friendly_name": attrs.get("friendly_name", eid),
                    "unit_of_measurement": attrs.get("unit_of_measurement"),
                    "device_class": attrs.get("device_class"),
                    "state": entity.get("state"),
                }
            )
        return results

    def get_state(self, entity_id: str) -> dict | None:
        """GET /api/states/{entity_id} -> parsed state dict or None."""
        url = f"{self._base_url}/api/states/{entity_id}"
        resp = httpx.get(url, headers=self._headers, timeout=self._timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        state_str = data.get("state", "")
        value: float | None = None
        if state_str not in ("unavailable", "unknown", ""):
            try:
                value = float(state_str)
            except ValueError, TypeError:
                value = None
        return {
            "value": value,
            "last_changed": data.get("last_changed"),
            "entity_id": entity_id,
            "unit": data.get("attributes", {}).get("unit_of_measurement"),
        }
