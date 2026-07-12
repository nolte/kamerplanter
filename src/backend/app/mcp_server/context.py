"""REQ-033 MCP tool execution context.

A :class:`ToolContext` carries the authenticated principal (tenant + role) into a
tool handler and lazily exposes the existing domain services the tool delegates
to. The MCP layer never re-implements business logic (§1 grundprinzipien) — it
is a thin aggregation layer that calls the same services the REST API uses, so
tenant isolation, validation and permission invariants are inherited unchanged.

Services are resolved through the standard ``app.common.dependencies`` factories,
but can be overridden in the constructor for isolated unit tests.
"""

from __future__ import annotations

from typing import Any

from app.common.enums import TenantRole
from app.mcp_server.principal import McpPrincipal


class ToolContext:
    """Per-call context handed to every MCP tool handler."""

    def __init__(
        self,
        principal: McpPrincipal,
        *,
        services: dict[str, Any] | None = None,
    ) -> None:
        self.principal = principal
        self._services: dict[str, Any] = dict(services or {})

    # ── principal shortcuts ──────────────────────────────────────────────
    @property
    def tenant_key(self) -> str:
        return self.principal.tenant_key

    @property
    def tenant_slug(self) -> str:
        return self.principal.tenant_slug

    @property
    def role(self) -> TenantRole:
        return self.principal.role

    # ── service resolution ───────────────────────────────────────────────
    def _service(self, name: str) -> Any:
        if name not in self._services:
            from app.common import dependencies as deps

            factory = getattr(deps, f"get_{name}")
            self._services[name] = factory()
        return self._services[name]

    @property
    def species_service(self) -> Any:
        return self._service("species_service")

    @property
    def plant_service(self) -> Any:
        return self._service("plant_instance_service")

    @property
    def site_service(self) -> Any:
        return self._service("site_service")

    @property
    def harvest_service(self) -> Any:
        return self._service("harvest_service")

    @property
    def task_service(self) -> Any:
        return self._service("task_service")

    @property
    def planting_run_service(self) -> Any:
        return self._service("planting_run_service")

    @property
    def care_service(self) -> Any:
        return self._service("care_reminder_service")

    @property
    def mcp_audit_repo(self) -> Any:
        return self._service("mcp_audit_repo")

    # ── deep-link helpers (§2.6) ─────────────────────────────────────────
    def ui_link(self, path: str) -> dict[str, str]:
        return {"type": "ui", "url": f"/t/{self.tenant_slug}{path}"}

    def api_link(self, path: str) -> dict[str, str]:
        return {"type": "api", "url": f"/api/v1/t/{self.tenant_slug}{path}"}
