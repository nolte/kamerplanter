"""REQ-033 MCP tool execution context.

A :class:`ToolContext` carries the authenticated principal plus the **one**
membership this call acts in into a tool handler, and lazily exposes the
existing domain services the tool delegates to. The MCP layer never
re-implements business logic (§1 grundprinzipien) — it is a thin aggregation
layer that calls the same services the REST API uses, so tenant isolation,
validation and permission invariants are inherited unchanged.

A principal may hold several memberships (§4.3). The dispatcher resolves exactly
one of them per call and hands it in here, so a tool can only ever see a single
tenant and cannot widen its own scope: ``ctx.tenant_key`` is the resolved
membership's, never a caller-supplied value.

Services are resolved through the standard ``app.common.dependencies`` factories,
but can be overridden in the constructor for isolated unit tests.
"""

from __future__ import annotations

from typing import Any

from app.common.enums import TenantRole
from app.mcp_server.principal import McpPrincipal, McpTenantMembership


class ToolContext:
    """Per-call context handed to every MCP tool handler."""

    def __init__(
        self,
        principal: McpPrincipal,
        membership: McpTenantMembership | None = None,
        *,
        services: dict[str, Any] | None = None,
    ) -> None:
        self.principal = principal
        self.membership = membership
        self._services: dict[str, Any] = dict(services or {})

    # ── acting-tenant shortcuts ──────────────────────────────────────────
    def _require_membership(self) -> McpTenantMembership:
        if self.membership is None:
            # A tenant-agnostic tool (global catalogue data) asked for a tenant.
            # That is a wiring bug, not a caller error — fail loudly.
            raise RuntimeError("This tool is not tenant-scoped; no acting tenant was bound to the context.")
        return self.membership

    @property
    def tenant_key(self) -> str:
        return self._require_membership().tenant_key

    @property
    def tenant_slug(self) -> str:
        return self._require_membership().tenant_slug

    @property
    def role(self) -> TenantRole:
        return self._require_membership().role

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
    def nutrient_plan_service(self) -> Any:
        return self._service("nutrient_plan_service")

    @property
    def calendar_service(self) -> Any:
        return self._service("calendar_service")

    @property
    def ipm_service(self) -> Any:
        return self._service("ipm_service")

    @property
    def fertilizer_service(self) -> Any:
        return self._service("fertilizer_service")

    @property
    def substrate_service(self) -> Any:
        return self._service("substrate_service")

    @property
    def feeding_service(self) -> Any:
        """Fertigation records — amount, EC/pH before/after, runoff, tank reference.

        The same service ``/t/{slug}/feeding-events`` uses. Its plant-scoped read
        (:meth:`FeedingService.get_by_plant`) takes ``tenant_key`` keyword-only
        and without a default since #927, so a tool cannot read another tenant's
        fertigation record by forgetting an argument.
        """

        return self._service("feeding_service")

    @property
    def observation_service(self) -> Any:
        """Time-series sensor readings (TimescaleDB, REQ-005).

        Degrades to a null repository when no TimescaleDB is configured, so a
        reading tool must treat "no samples" and "no time-series backend" as
        different answers rather than assuming the first.
        """

        return self._service("observation_service")

    @property
    def sensor_service(self) -> Any:
        """Sensor master data — which sensors sit at a site, location or tank."""

        return self._service("sensor_service")

    @property
    def knowledge_service(self) -> Any:
        """Async RAG port to the Knowledge-Service microservice (REQ-031 §4.1).

        Deliberately the **async** ``IKnowledgeService`` adapter and not the
        synchronous ``KnowledgeServiceClient`` the REST proxy uses: a tool handler
        runs on the event loop, and the sync client would block it for the whole
        round-trip. The adapter also carries the per-call timeout, the retry and
        the circuit breaker the sync client lacks (NFR-007).
        """

        return self._service("knowledge_service_adapter")

    @property
    def overwintering_service(self) -> Any:
        return self._service("overwintering_profile_service")

    @property
    def starter_kit_service(self) -> Any:
        return self._service("starter_kit_service")

    @property
    def phase_sequence_service(self) -> Any:
        return self._service("phase_sequence_service")

    @property
    def hardiness_zone_service(self) -> Any:
        return self._service("hardiness_zone_service")

    @property
    def glossary_service(self) -> Any:
        return self._service("glossary_service")

    @property
    def plant_diary_service(self) -> Any:
        """Diary entries incl. the REQ-050 analysis state machine, lease and CAS."""

        return self._service("plant_diary_service")

    @property
    def attachment_service(self) -> Any:
        """Attachment records and their thumbnail renditions (NFR-013).

        REQ-050 §4.4 delivers renditions only, never originals — that constraint
        lives in the tool, not here; this is the same service the REST attachment
        endpoints use.
        """

        return self._service("attachment_service")

    @property
    def phase_service(self) -> Any:
        """Growth phases; resolves a plant's current phase across both key-spaces."""

        return self._service("phase_service")

    @property
    def mcp_audit_repo(self) -> Any:
        return self._service("mcp_audit_repo")

    # ── deep-link helpers (§2.6) ─────────────────────────────────────────
    def global_link(self, path: str) -> dict[str, str]:
        """A link to tenant-independent data (the species, IPM and glossary catalogues).

        Tenant-agnostic tools have no membership bound, so they cannot use
        :meth:`api_link` — it would raise. Reaching for the wrong helper is easy
        to do and the failure only appears on the real dispatch path, so
        ``test_no_global_tool_uses_a_tenant_bound_link`` guards the choice.
        """

        return {"type": "api", "url": f"/api/v1{path}"}

    def ui_link(self, path: str) -> dict[str, str]:
        return {"type": "ui", "url": f"/t/{self.tenant_slug}{path}"}

    def api_link(self, path: str) -> dict[str, str]:
        return {"type": "api", "url": f"/api/v1/t/{self.tenant_slug}{path}"}
