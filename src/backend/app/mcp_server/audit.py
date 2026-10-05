"""REQ-033 MCP audit logging (§4.6, DSGVO REQ-025).

One :class:`app.domain.models.mcp.McpAuditLog` entry per tool call. The logger
hashes the tool arguments (``input_hash``) so free-text payloads (diary entries,
symptom descriptions) never reach the log (AC-S5); API keys are never passed in
(AC-S2).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import BaseModel

from app.common.enums import McpToolStatus
from app.common.log_privacy import loggable_error
from app.common.request_context import current_request
from app.data_access.arango.mcp_repository import ArangoMcpAuditRepository
from app.domain.models.mcp import McpAuditLog
from app.mcp_server.principal import McpPrincipal, McpTenantMembership

logger = structlog.get_logger(__name__)


def hash_arguments(raw_args: dict[str, Any]) -> str:
    """Return a stable sha256 over the tool arguments (no plaintext, §4.6)."""

    canonical = json.dumps(raw_args, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


#: A value recorded as an entity key: the shape of an ArangoDB document key as
#: this system mints them. Anything else — free text in a key-named field, a
#: sentence, an address — is not a key and is not recorded (AC-S5).
_ENTITY_KEY = re.compile(r"[A-Za-z0-9_-]{1,64}")
#: Key-named input fields that do not name a stored entity.
_NOT_ENTITY_FIELDS = frozenset({"idempotency_key"})
_MAX_ENTITY_FIELDS = 10
_MAX_KEYS_PER_FIELD = 20


def entity_keys_of(args: BaseModel) -> dict[str, list[str]]:
    """The record keys a typed tool input names, by field (#2130, MT-034).

    Only fields named ``*_key``/``*_keys`` qualify, only values of document-key
    shape are kept, and both counts are bounded, so the audit row answers "which
    plant did this call touch?" without ever holding the free text the argument
    hash exists to keep out (AC-S5).
    """
    found: dict[str, list[str]] = {}
    for name in type(args).model_fields:
        if name in _NOT_ENTITY_FIELDS or not (name.endswith("_key") or name.endswith("_keys")):
            continue
        value = getattr(args, name, None)
        values = value if isinstance(value, list | tuple) else [value]
        keys = [v for v in values if isinstance(v, str) and _ENTITY_KEY.fullmatch(v)][:_MAX_KEYS_PER_FIELD]
        if keys:
            found[name] = keys
        if len(found) >= _MAX_ENTITY_FIELDS:
            break
    return found


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
        entity_keys: dict[str, list[str]] | None = None,
    ) -> None:
        """Record one tool call.

        ``membership`` is the tenant the call acted in, as resolved by the
        dispatcher. It is absent for a tenant-agnostic tool and for a call that
        failed *before* the tenant was bound (unknown tenant, invalid input) —
        such entries carry an empty ``tenant_key`` rather than guessing one.

        ``image_bytes`` is the Base-64 size of the response's image content
        blocks, kept apart from ``output_size_bytes`` so a photo call cannot
        drown the size statistic of every other tool (REQ-033 §4.3b, AC-S9).

        ``entity_keys`` are the record keys the typed input named
        (:func:`entity_keys_of`); absent for a call that failed validation. The
        key and network references come from the principal, the request id from
        the request the call arrived on (#2130).
        """

        telemetry = current_request()
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
            api_key_ref=principal.api_key_ref,
            client_ip_ref=principal.client_ip_ref,
            request_id=telemetry.request_id if telemetry is not None else None,
            entity_keys=entity_keys or None,
        )
        try:
            self._repo.record(entry)
        except Exception as exc:  # noqa: BLE001 — audit must never break the request
            logger.warning("mcp_audit_write_failed", tool=tool_name, error=loggable_error(exc))
