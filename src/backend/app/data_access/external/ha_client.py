import httpx
import structlog

logger = structlog.get_logger(__name__)


class HomeAssistantClient:
    """Synchronous HTTP client for Home Assistant REST API."""

    def __init__(self, base_url: str, token: str, timeout: int = 10) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._timeout = timeout

    # ── Async methods (for notification engine) ──────────────────────

    async def fire_event(self, event_type: str, event_data: dict) -> dict:
        """POST /api/events/{event_type} — fires a custom event in HA."""
        url = f"{self._base_url}/api/events/{event_type}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                url, json=event_data, headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def create_persistent_notification(
        self, title: str, message: str, notification_id: str,
    ) -> None:
        """POST /api/services/persistent_notification/create."""
        url = f"{self._base_url}/api/services/persistent_notification/create"
        payload = {
            "title": title,
            "message": message,
            "notification_id": notification_id,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers)
            resp.raise_for_status()

    async def dismiss_persistent_notification(self, notification_id: str) -> None:
        """POST /api/services/persistent_notification/dismiss."""
        url = f"{self._base_url}/api/services/persistent_notification/dismiss"
        payload = {"notification_id": notification_id}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers)
            resp.raise_for_status()

    async def call_service(
        self, domain: str, service: str, service_data: dict,
    ) -> dict:
        """POST /api/services/{domain}/{service} — generic service call."""
        url = f"{self._base_url}/api/services/{domain}/{service}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                url, json=service_data, headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

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
            except (ValueError, TypeError):
                value = None
        return {
            "value": value,
            "last_changed": data.get("last_changed"),
            "entity_id": entity_id,
            "unit": data.get("attributes", {}).get("unit_of_measurement"),
        }
