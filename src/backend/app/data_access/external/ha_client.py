import httpx
import structlog

from app.common.url_safety import validate_ha_url

logger = structlog.get_logger(__name__)


class HomeAssistantClient:
    """Synchronous HTTP client for Home Assistant REST API."""

    def __init__(self, base_url: str, token: str, timeout: int = 10, *, allow_private: bool = False) -> None:
        # SEC-B3: the base_url is tenant/admin-configurable and every method dials
        # it with the bearer token attached — validate it once at construction so
        # a URL pointing at cloud-metadata / internal addresses is rejected before
        # any request is made. ``allow_private`` gates LAN Home Assistant (opt-in).
        self._base_url = validate_ha_url(base_url, allow_private=allow_private).rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._timeout = timeout

    # ── Async methods (for notification engine) ──────────────────────

    async def fire_event(self, event_type: str, event_data: dict) -> dict:
        """POST /api/events/{event_type} — fires a custom event in HA."""
        url = f"{self._base_url}/api/events/{event_type}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                url,
                json=event_data,
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def create_persistent_notification(
        self,
        title: str,
        message: str,
        notification_id: str,
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
        self,
        domain: str,
        service: str,
        service_data: dict,
    ) -> dict:
        """POST /api/services/{domain}/{service} — generic service call."""
        url = f"{self._base_url}/api/services/{domain}/{service}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                url,
                json=service_data,
                headers=self._headers,
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

    def list_weather_entities(self) -> list[dict]:
        """GET /api/states -> all weather.* entities (REQ-046 §3.4, mode A).

        Companion to :meth:`list_sensor_entities`, which hard-filters ``sensor.``
        and is therefore not reusable for weather entities.
        """
        url = f"{self._base_url}/api/states"
        resp = httpx.get(url, headers=self._headers, timeout=self._timeout)
        resp.raise_for_status()
        results = []
        for entity in resp.json():
            eid: str = entity.get("entity_id", "")
            if not eid.startswith("weather."):
                continue
            attrs = entity.get("attributes", {})
            results.append(
                {
                    "entity_id": eid,
                    "friendly_name": attrs.get("friendly_name", eid),
                    "state": entity.get("state"),
                }
            )
        return results

    def get_state_attributes(self, entity_id: str) -> dict | None:
        """GET /api/states/{entity_id} -> the raw ``attributes`` block or None.

        Unlike :meth:`get_state`, this returns the full attribute dict (including
        ``forecast``) without collapsing non-numeric values, as required by the
        weather.* forecast reader (REQ-046 §3.4). Returns ``None`` on 404.
        """
        url = f"{self._base_url}/api/states/{entity_id}"
        resp = httpx.get(url, headers=self._headers, timeout=self._timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("attributes", {})

    def get_state(self, entity_id: str, *, timeout: float | None = None) -> dict | None:
        """GET /api/states/{entity_id} -> parsed state dict or None.

        Args:
            entity_id: The Home Assistant entity to read.
            timeout: Optional per-call ceiling in seconds, capped at the client's
                configured timeout — never used to *raise* it. A caller working
                against a wall-clock deadline (the diary environment capture,
                REQ-013 §2.3a) passes the time it has left, so one slow entity
                cannot spend the whole budget.

        Returns:
            ``value`` is ``None`` for a non-numeric state — Home Assistant
            reports ``unavailable`` / ``unknown`` as the state string.

            **Three timestamps, and they are not interchangeable.**
            ``last_changed`` moves only when the state *string* changes, so a
            perfectly healthy sensor reporting a constant 22.0 °C keeps a
            ``last_changed`` that is hours old; ``last_updated`` moves when state
            or attributes change and has almost the same problem;
            ``last_reported`` (HA ≥ 2024.6) moves on **every** report and is the
            only honest freshness signal. All three are returned so a consumer
            can pick the one its question needs — see
            ``EnvironmentSnapshotService`` for the staleness use.
        """
        url = f"{self._base_url}/api/states/{entity_id}"
        effective_timeout = self._timeout if timeout is None else min(self._timeout, timeout)
        resp = httpx.get(url, headers=self._headers, timeout=effective_timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        state_str = data.get("state", "")
        value: float | None = None
        if state_str not in ("unavailable", "unknown", ""):
            try:
                value = float(state_str)
            except (ValueError, TypeError):  # fmt: skip
                value = None
        return {
            "value": value,
            "last_changed": data.get("last_changed"),
            "last_updated": data.get("last_updated"),
            "last_reported": data.get("last_reported"),
            "entity_id": entity_id,
            "unit": data.get("attributes", {}).get("unit_of_measurement"),
        }
