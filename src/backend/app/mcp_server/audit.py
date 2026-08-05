"""REQ-033 MCP audit logging (§4.6, DSGVO REQ-025).

One :class:`app.domain.models.mcp.McpAuditLog` entry per tool call. The logger
hashes the tool arguments (``input_hash``) so free-text payloads (diary entries,
symptom descriptions) never reach the log (AC-S5); API keys are never passed in
(AC-S2).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import structlog

from app.common.enums import McpToolStatus
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository
from app.domain.models.mcp import McpAuditLog
from app.mcp_server.principal import McpPrincipal, McpTenantMembership

logger = structlog.get_logger(__name__)


def hash_arguments(raw_args: dict[str, Any]) -> str:
    """Return a stable sha256 over the tool arguments (no plaintext, §4.6)."""

    canonical = json.dumps(raw_args, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


class MCPAuditLogger:
    """Persists an audit entry per tool call; never raises into the caller path."""

    def __init__(self, repo: ArangoMcpAuditRepository) -> None:
        self._repo = repo

    def record(
        self,
        principal: McpPrincipal,
        *,
        tool_name: str,
        input_hash: str,
        status: McpToolStatus,
        output_size_bytes: int = 0,
        image_bytes: int = 0,
        duration_ms: int = 0,
        error_class: str | None = None,
        membership: McpTenantMembership | None = None,
    ) -> None:
        """Record one tool call.

        ``membership`` is the tenant the call acted in, as resolved by the
        dispatcher. It is absent for a tenant-agnostic tool and for a call that
        failed *before* the tenant was bound (unknown tenant, invalid input) —
        such entries carry an empty ``tenant_key`` rather than guessing one.

        ``image_bytes`` is the Base-64 size of the response's image content
        blocks, kept apart from ``output_size_bytes`` so a photo call cannot
        drown the size statistic of every other tool (REQ-033 §4.3b, AC-S9).
        """

        entry = McpAuditLog(
            service_account_key=principal.account_key,
            tenant_key=membership.tenant_key if membership else "",
            tool_name=tool_name,
            input_hash=input_hash,
            output_size_bytes=output_size_bytes,
            image_bytes=image_bytes,
            duration_ms=duration_ms,
            status=status,
            error_class=error_class,
            created_at=datetime.now(UTC),
        )
        try:
            self._repo.record(entry)
        except Exception as exc:  # noqa: BLE001 — audit must never break the request
            logger.warning("mcp_audit_write_failed", tool=tool_name, error=str(exc))
