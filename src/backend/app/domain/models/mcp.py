"""REQ-033 MCP server — persistence + response models.

The MCP server keeps no own domain data (§3); these models only back the two
adapter-layer collections (``mcp_audit_log``, ``mcp_idempotency_record``) and
the LLM-facing tool-response envelope (§2.6).

Source code is English only (NFR-003).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.common.enums import McpPermission, McpToolStatus


class McpAuditLog(BaseModel):
    """One audit entry per MCP tool call (§3, §4.6).

    Records *no* PII: tool arguments are hashed (``input_hash``) so free-text
    diary/symptom payloads never reach the log (AC-S5). API keys never appear
    here (AC-S2).
    """

    key: str | None = Field(default=None, alias="_key")
    service_account_key: str  # FK -> users (the service account)
    tenant_key: str  # FK -> tenants
    tool_name: str
    input_hash: str  # sha256 over the tool arguments
    output_size_bytes: int = 0
    duration_ms: int = 0
    status: McpToolStatus
    error_class: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True, "use_enum_values": True}


class McpAuditLogEntry(BaseModel):
    """Read-projection of an audit entry for the privacy self-service view (§4.6)."""

    tool_name: str
    tenant_key: str
    status: McpToolStatus
    output_size_bytes: int
    duration_ms: int
    error_class: str | None
    created_at: datetime | None

    model_config = {"use_enum_values": True}


class McpIdempotencyRecord(BaseModel):
    """Idempotency replay record for a write tool (§2.6, §3).

    Keyed by ``(service_account_key, tenant_key, tool_name, idempotency_key)``; a
    repeated call within the TTL replays ``result_payload`` instead of writing
    twice (AC-19). ``tenant_key`` is part of the scope (SEC-005): a multi-tenant
    service account holding two tenant-scoped keys must never replay tenant-A's
    stored result for a tenant-B call.
    """

    key: str | None = Field(default=None, alias="_key")
    service_account_key: str
    tenant_key: str
    tool_name: str
    idempotency_key: str
    input_hash: str
    result_payload: dict[str, Any]
    created_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = {"populate_by_name": True}


class McpToolLink(BaseModel):
    """A UI/API deep link the end user can follow for details (§2.6)."""

    type: str  # "ui" | "api"
    url: str


class McpToolResponse(BaseModel):
    """LLM-friendly tool response envelope (§2.6).

    ``summary`` is a one-sentence recap for the LLM, ``data`` the structured
    result, ``links`` point the human user at the UI/API. Write tools also set
    ``dry_run``/``idempotency_key``/``idempotent_replay``.
    """

    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    links: list[McpToolLink] = Field(default_factory=list)
    dry_run: bool | None = None
    idempotency_key: str | None = None
    idempotent_replay: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        """Serialise to a compact dict, dropping the write-only fields when unset."""

        return self.model_dump(exclude_none=True)


class McpToolSpec(BaseModel):
    """Public MCP tool descriptor returned by discovery (tools/list, §1.2)."""

    name: str
    description: str
    permission: McpPermission
    write: bool = False
    destructive: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": True}
