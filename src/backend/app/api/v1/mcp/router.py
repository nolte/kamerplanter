"""REQ-033 MCP HTTP transport (§1.2, §4).

Exposes the curated MCP tool palette over HTTP (+ SSE handshake). Surfaces:

* ``GET  /mcp/tools``        — REST-friendly discovery (role-filtered).
* ``POST /mcp/tools/{name}`` — REST-friendly tool call.
* ``POST /mcp/rpc``          — MCP JSON-RPC 2.0 (initialize / tools/list /
                               tools/call / ping) for protocol clients.
* ``GET  /mcp/sse``          — SSE endpoint handshake for the HTTP+SSE transport.

Every tool call flows through :class:`ToolDispatcher`, which binds the caller's
service-account role to the tool's MCP permission, applies dry-run/idempotency
and audit-logs the outcome. Business logic stays in the delegated domain
services.
"""

from __future__ import annotations

from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import StreamingResponse

from app.api.v1.mcp.deps import get_dispatcher, get_mcp_principal
from app.common.exceptions import KamerplanterError
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.core.permissions import has_mcp_permission
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.registry import load_tools

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"], responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})

_PROTOCOL_VERSION = "2024-11-05"
_SERVER_INFO = {"name": "kamerplanter-mcp", "version": "1.0"}


def _visible_specs(principal: McpPrincipal) -> list[dict[str, Any]]:
    """Every tool the principal may invoke in *at least one* of its tenants.

    A user can be admin in their own garden and viewer in a community garden, so
    discovery is the union over their roles — hiding a tool they may use
    somewhere would be wrong. The per-call check is the binding one: the
    dispatcher re-evaluates the permission against the role held in the tenant
    the call actually names, so a tool listed here can still be refused for a
    tenant where the caller is only a viewer.
    """

    registry = load_tools()
    roles = principal.roles()
    return [
        spec.model_dump()
        for spec in registry.specs()
        if any(has_mcp_permission(role, spec.permission) for role in roles)
    ]


@router.get("/tools")
def list_mcp_tools(principal: McpPrincipal = Depends(get_mcp_principal)) -> dict[str, Any]:
    """List the tools this API key may invoke (role-filtered discovery)."""

    return {
        "tenants": [
            {"slug": m.tenant_slug, "name": m.tenant_name, "role": m.role.value} for m in principal.memberships
        ],
        "tools": _visible_specs(principal),
    }


@router.post("/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: Annotated[str, Path(description="Name of the MCP tool to invoke.")],
    arguments: dict[str, Any] = Body(default_factory=dict, description="Arguments passed to the tool."),
    principal: McpPrincipal = Depends(get_mcp_principal),
    dispatcher: ToolDispatcher = Depends(get_dispatcher),
) -> dict[str, Any]:
    """Invoke a single MCP tool (REST-friendly)."""

    response = await dispatcher.dispatch(principal, tool_name, arguments)
    return response.to_payload()


# ── MCP JSON-RPC 2.0 over HTTP ────────────────────────────────────────────────
def _rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _rpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


@router.post("/rpc")
async def mcp_rpc(
    payload: dict[str, Any] = Body(..., description="MCP JSON-RPC 2.0 request envelope."),
    principal: McpPrincipal = Depends(get_mcp_principal),
    dispatcher: ToolDispatcher = Depends(get_dispatcher),
) -> dict[str, Any]:
    """Handle an MCP JSON-RPC request (initialize / tools/list / tools/call / ping)."""

    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}

    if method == "initialize":
        return _rpc_result(
            request_id,
            {
                "protocolVersion": _PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": _SERVER_INFO,
            },
        )
    if method == "ping":
        return _rpc_result(request_id, {})
    if method == "tools/list":
        tools = [
            {
                "name": spec["name"],
                "description": spec["description"],
                "inputSchema": spec["input_schema"],
                "annotations": {"destructive": spec["destructive"], "readOnlyHint": not spec["write"]},
            }
            for spec in _visible_specs(principal)
        ]
        return _rpc_result(request_id, {"tools": tools})
    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments") or {}
        try:
            response = await dispatcher.dispatch(principal, tool_name, arguments)
        except KamerplanterError as exc:
            # Surface a structured tool error to the LLM client (isError) instead
            # of a transport-level failure, so the model can react (§2.6).
            return _rpc_result(
                request_id,
                {
                    "isError": True,
                    "content": [{"type": "text", "text": f"{exc.error_code}: {exc.message}"}],
                },
            )
        return _rpc_result(
            request_id,
            {
                "isError": False,
                "content": [{"type": "text", "text": response.summary}],
                "structuredContent": response.to_payload(),
            },
        )

    return _rpc_error(request_id, -32601, f"Method not found: {method}")


@router.get("/sse")
async def mcp_sse(principal: McpPrincipal = Depends(get_mcp_principal)) -> StreamingResponse:
    """SSE endpoint handshake for the HTTP+SSE transport (§1.2).

    Emits the ``endpoint`` event pointing protocol clients at ``/mcp/rpc`` for
    JSON-RPC message posting, then completes. Long-running progress
    notifications (§4.5) are a documented follow-up.
    """

    async def _event_stream():
        yield "event: endpoint\ndata: /api/v1/mcp/rpc\n\n"
        yield "event: ready\ndata: {}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
