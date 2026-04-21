"""mDNS/Zeroconf service announcement for Kamerplanter backend.

Registers a ``_kamerplanter._tcp.local.`` service so that Home Assistant
can auto-discover the backend via Zeroconf.
"""

from __future__ import annotations

import uuid

import structlog
from zeroconf import ServiceInfo, Zeroconf

logger = structlog.get_logger()

MDNS_SERVICE_TYPE = "_kamerplanter._tcp.local."


def generate_instance_id() -> str:
    """Generate a stable instance ID (``kp-<short-uuid>``)."""
    return f"kp-{uuid.uuid4().hex[:8]}"


def create_service_info(
    *,
    port: int,
    version: str,
    mode: str,
    api_path: str = "/api",
    instance_id: str,
    tenant: str | None = None,
) -> ServiceInfo:
    """Create mDNS ServiceInfo for Kamerplanter backend."""
    properties: dict[str, str] = {
        "version": version,
        "mode": mode,
        "api_path": api_path,
        "instance_id": instance_id,
    }
    if tenant:
        properties["tenant"] = tenant

    return ServiceInfo(
        type_=MDNS_SERVICE_TYPE,
        name=f"Kamerplanter ({instance_id}).{MDNS_SERVICE_TYPE}",
        port=port,
        properties=properties,
        server=f"{instance_id}.local.",
    )


class MdnsAnnouncer:
    """Manages mDNS service announcement lifecycle."""

    def __init__(self, service_info: ServiceInfo) -> None:
        self._info = service_info
        self._zeroconf: Zeroconf | None = None

    def start(self) -> None:
        """Register mDNS service."""
        self._zeroconf = Zeroconf()
        self._zeroconf.register_service(self._info)
        logger.info(
            "mdns_registered",
            service_type=MDNS_SERVICE_TYPE,
            instance_id=self._info.properties.get(b"instance_id", b"").decode(),
            port=self._info.port,
        )

    def stop(self) -> None:
        """Unregister mDNS service."""
        if self._zeroconf:
            self._zeroconf.unregister_service(self._info)
            self._zeroconf.close()
            self._zeroconf = None
            logger.info("mdns_unregistered")
