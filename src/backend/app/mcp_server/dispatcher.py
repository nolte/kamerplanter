"""REQ-033 MCP tool dispatcher (§4.2 – §4.6).

The single choke point every tool call passes through. In order:

1. resolve the tool from the registry (unknown → ``not_found``);
2. enforce the tool's MCP permission against the caller's role (§4.4) —
   a refusal is audited with ``status="denied"`` and raised as ``permission.denied``;
3. validate the typed input;
4. run the handler, applying dry-run + idempotency orchestration for write tools;
5. audit the outcome (hash-only, no PII, §4.6).

Business logic stays in the delegated domain services — the dispatcher only owns
security binding, idempotency and audit.
"""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from app.common.enums import McpToolStatus
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError, ValidationError
from app.core.permissions import assert_mcp_permission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.audit import MCPAuditLogger, hash_arguments
from app.mcp_server.base import ToolBase, WriteToolBase
from app.mcp_server.context import ToolContext
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.registry import ToolRegistry


class ToolDispatcher:
    """Executes a named tool for an authenticated principal."""

    def __init__(
        self,
        registry: ToolRegistry,
        audit_logger: MCPAuditLogger,
        idempotency: IdempotencyStore,
        *,
        services: dict[str, Any] | None = None,
    ) -> None:
        self._registry = registry
        self._audit = audit_logger
        self._idempotency = idempotency
        self._services = services

    async def dispatch(
        self,
        principal: McpPrincipal,
        tool_name: str,
        raw_args: dict[str, Any] | None,
    ) -> McpToolResponse:
        raw_args = raw_args or {}
        input_hash = hash_arguments(raw_args)

        tool = self._registry.get(tool_name)
        if tool is None:
            raise NotFoundError("MCP tool", tool_name)
        assert isinstance(tool, ToolBase)

        # 1. Permission binding (§4.4). A refusal is audited then surfaced as 403.
        try:
            assert_mcp_permission(principal.role, tool.permission)
        except ForbiddenError:
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.DENIED,
                error_class="permission.denied",
            )
            raise

        # 2. Typed input validation.
        try:
            args = tool.Input(**raw_args)
        except PydanticValidationError as exc:
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.ERROR,
                error_class="validation.input",
            )
            raise ValidationError(f"Invalid arguments for tool '{tool_name}': {exc.errors()}") from exc

        ctx = ToolContext(principal, services=self._services)
        started = perf_counter()
        try:
            response, status = await self._run(tool, ctx, args, principal, tool_name, input_hash)
        except KamerplanterError as exc:
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.ERROR,
                duration_ms=int((perf_counter() - started) * 1000),
                error_class=exc.error_code,
            )
            raise
        except Exception as exc:  # noqa: BLE001 — audit unexpected failures too
            self._audit.record(
                principal,
                tool_name=tool_name,
                input_hash=input_hash,
                status=McpToolStatus.ERROR,
                duration_ms=int((perf_counter() - started) * 1000),
                error_class=type(exc).__name__,
            )
            raise

        duration_ms = int((perf_counter() - started) * 1000)
        output_size = len(json.dumps(response.to_payload(), default=str).encode())
        self._audit.record(
            principal,
            tool_name=tool_name,
            input_hash=input_hash,
            status=status,
            output_size_bytes=output_size,
            duration_ms=duration_ms,
        )
        return response

    async def _run(
        self,
        tool: ToolBase,
        ctx: ToolContext,
        args: Any,
        principal: McpPrincipal,
        tool_name: str,
        input_hash: str,
    ) -> tuple[McpToolResponse, McpToolStatus]:
        if not isinstance(tool, WriteToolBase):
            return await tool.run(ctx, args), McpToolStatus.OK

        # ── Write tool: dry-run + idempotency (§2.6) ─────────────────────
        if getattr(args, "dry_run", False):
            response = await tool.preview(ctx, args)
            response.dry_run = True
            response.idempotency_key = getattr(args, "idempotency_key", None)
            response.idempotent_replay = False
            return response, McpToolStatus.DRY_RUN

        idem_key = getattr(args, "idempotency_key", None)
        if idem_key:
            replay = self._idempotency.lookup(principal, tool_name, idem_key)
            if replay is not None:
                return replay, McpToolStatus.OK
            response = await tool.execute(ctx, args)
            response.dry_run = False
            response.idempotency_key = idem_key
            response.idempotent_replay = False
            self._idempotency.store(principal, tool_name, idem_key, input_hash, response)
            return response, McpToolStatus.OK

        response = await tool.execute(ctx, args)
        response.dry_run = False
        return response, McpToolStatus.OK
