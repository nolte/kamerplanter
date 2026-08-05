"""REQ-033 MCP Streamable-HTTP transport (§1.2, §4).

Exposes the curated MCP tool palette. Surfaces:

* ``POST   /mcp``            — the MCP endpoint: JSON-RPC 2.0 over Streamable
                               HTTP (initialize / tools/list / tools/call / ping).
* ``GET    /mcp``            — 405: this server sends no server-initiated
                               messages, which the transport explicitly permits.
* ``DELETE /mcp``            — terminate the session named by ``Mcp-Session-Id``.
* ``POST   /mcp/rpc``        — retained alias of ``POST /mcp`` (deprecated).
* ``GET    /mcp/tools``      — REST-friendly discovery (role-filtered), not part
                               of the MCP protocol.
* ``POST   /mcp/tools/{name}`` — REST-friendly tool call, likewise non-protocol.

**Transport conformance.** Streamable HTTP (protocol revision 2025-03-26 and
later) folds the old two-endpoint HTTP+SSE transport into a single endpoint that
answers a POSTed JSON-RPC message with either ``application/json`` or an SSE
stream. This server always answers with ``application/json``, which the transport
allows, and therefore:

* returns ``202 Accepted`` with an empty body for a notification or response,
  which JSON-RPC requires must never be answered;
* negotiates ``protocolVersion`` against the client's request in ``initialize``;
* issues an ``Mcp-Session-Id`` on ``initialize`` and validates it afterwards,
  answering ``404`` for an unknown one so the client re-initialises;
* rejects ``GET`` with ``405``, the sanctioned answer for a server that opens no
  server-to-client stream. Progress notifications (§4.5) would need that stream.

Every tool call flows through :class:`ToolDispatcher`, which binds the caller's
role in the acting tenant to the tool's MCP permission, applies
dry-run/idempotency and audit-logs the outcome. Business logic stays in the
delegated domain services.
"""

from __future__ import annotations

from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Body, Depends, Header, Path, Response
from fastapi.responses import JSONResponse

from app.api.v1.mcp.deps import get_dispatcher, get_mcp_principal, get_session_store
from app.common.exceptions import KamerplanterError
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.core.permissions import has_mcp_permission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.registry import load_tools
from app.mcp_server.session import McpSessionStore

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"], responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE})

#: Protocol revisions this server implements, newest first. The negotiation in
#: ``initialize`` echoes the client's revision when it appears here and otherwise
#: answers with the newest one, letting the client decide whether to proceed.
_SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
_LATEST_PROTOCOL_VERSION = _SUPPORTED_PROTOCOL_VERSIONS[0]
#: What to assume when a client omits the MCP-Protocol-Version header on a
#: follow-up request — the transport prescribes this exact fallback.
_ASSUMED_PROTOCOL_VERSION = "2025-03-26"
_SERVER_INFO = {"name": "kamerplanter-mcp", "version": "1.0"}
_SESSION_HEADER = "Mcp-Session-Id"


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
    """Invoke a single MCP tool (REST-friendly).

    Returns the structured payload only. Image content blocks are an MCP
    protocol construct — their ``content_index`` addresses the ``content`` array
    of a ``tools/call`` result, which this surface does not build — so a tool
    delivering images (REQ-050 §4.4) must be called over ``POST /mcp``. Inventing
    a second image encoding here would give recipes two contracts to get wrong.
    """

    response = await dispatcher.dispatch(principal, tool_name, arguments)
    return response.to_payload()


# ── MCP JSON-RPC 2.0 over HTTP ────────────────────────────────────────────────
def _rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _rpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


#: Kamerplanter's internal, SCREAMING_CASE error codes → the lowercase dotted
#: codes the MCP contract publishes (REQ-050 §4.0, REQ-033 AC-2). The published
#: code is what a recipe branches on, so it must be stable and must never be
#: derived from the human-readable message.
_CONTRACT_ERROR_CODES: dict[str, str] = {
    "ENTITY_NOT_FOUND": "not_found",
    "FORBIDDEN": "permission.denied",
    "UNAUTHORIZED": "permission.denied",
    "VALIDATION_ERROR": "validation.error",
    "PAYLOAD_TOO_LARGE": "payload.too_large",
    "DUPLICATE_ENTRY": "conflict.duplicate",
    "RATE_LIMIT_EXCEEDED": "rate_limit.exceeded",
}


def _contract_error_code(exc: KamerplanterError) -> str:
    """The published error code for a failed tool call.

    An error that already carries its contract code (``conflict.already_claimed``
    …) — :class:`~app.mcp_server.base.McpToolError` and the domain's
    :class:`~app.common.exceptions.ContractError` alike — passes through
    untouched; the generic application errors are translated through the table
    above, which is why they exist as two vocabularies at all. Anything
    else — a domain error from one of the non-diary tools — is lower-cased, which
    keeps it stable and machine-readable without pretending it is part of the
    documented §4.0 set.
    """

    return _CONTRACT_ERROR_CODES.get(exc.error_code, exc.error_code.lower())


def _tool_result(response: McpToolResponse) -> dict[str, Any]:
    """Wire form of a successful tool call (REQ-050 §4.0, REQ-033 §4.3b).

    ``summary`` stays the leading content block and image blocks are *appended*,
    so a tool that sets no blocks produces byte-identical output to before this
    became possible. ``structuredContent`` never carries the image data: it comes
    from ``to_payload()``, which excludes the blocks — otherwise every photo
    would go over the wire twice.
    """

    content: list[dict[str, Any]] = [{"type": "text", "text": response.summary}]
    content.extend(block.model_dump(by_alias=True) for block in response.content_blocks)
    return {"isError": False, "content": content, "structuredContent": response.to_payload()}


def _tool_error_result(exc: KamerplanterError) -> dict[str, Any]:
    """Wire form of a failed tool call — a *result*, not a JSON-RPC error (§4.0).

    A JSON-RPC ``error`` means protocol or authentication failure and is not
    actionable for a recipe; a tool failure must arrive as ``isError: true`` with
    a machine-readable ``structuredContent``. The text block keeps the code as a
    prefix because it is the only thing a language model sees without reading the
    structured part.

    ``details`` is selected by **attribute, not by class**. Two sibling classes
    carry the free-form MCP ``details`` object today —
    :class:`~app.mcp_server.base.McpToolError` and
    :class:`~app.common.exceptions.ContractError`, the latter being what the
    diary tools raise — and neither derives from the other. An ``isinstance``
    gate on one of them let a ``DiaryAnalysisAlreadyClaimedError`` reach the
    recipe with the right ``error_code`` but without ``claimed_by`` /
    ``lease_expires_at``: the two facts REQ-050 §4.2 gives an agent to decide
    whether to come back later. Keying off the attribute makes the contract
    depend on what an error *carries* rather than on where it happens to sit in
    the hierarchy, which is also what stops the next contract-error class from
    silently losing its details.

    The envelope crosses a trust boundary, so exactly three keys leave here:
    ``error_code``, ``message`` and the §4-documented ``details``. The type guard
    is not decoration — ``details`` is copied verbatim into a client-facing
    payload, so anything that is not a plain mapping (an ORM object, an
    exception, a string) is dropped rather than serialised, and the copy keeps a
    later mutation of the exception out of the response.
    """

    code = _contract_error_code(exc)
    structured: dict[str, Any] = {"error_code": code, "message": exc.message}
    error_details = getattr(exc, "error_details", None)
    if isinstance(error_details, dict) and error_details:
        structured["details"] = dict(error_details)
    return {
        "isError": True,
        "content": [{"type": "text", "text": f"{code}: {exc.message}"}],
        "structuredContent": structured,
    }


def _negotiate_protocol_version(requested: Any) -> str:
    """Answer the client's requested revision when supported, else the newest."""

    if isinstance(requested, str) and requested in _SUPPORTED_PROTOCOL_VERSIONS:
        return requested
    return _LATEST_PROTOCOL_VERSION


@router.post("", summary="MCP endpoint (Streamable HTTP)")
@router.post("/rpc", deprecated=True, summary="Deprecated alias of POST /mcp")
async def mcp_endpoint(
    response: Response,
    payload: dict[str, Any] = Body(..., description="MCP JSON-RPC 2.0 message."),
    principal: McpPrincipal = Depends(get_mcp_principal),
    dispatcher: ToolDispatcher = Depends(get_dispatcher),
    sessions: McpSessionStore = Depends(get_session_store),
    mcp_session_id: Annotated[str | None, Header(alias="Mcp-Session-Id")] = None,
    mcp_protocol_version: Annotated[str | None, Header(alias="MCP-Protocol-Version")] = None,
) -> Any:
    """Handle one MCP message (initialize / tools/list / tools/call / ping).

    Answers with ``application/json``; the transport permits this in place of an
    SSE stream. Session and protocol-version headers are validated on every
    message except ``initialize``, which is what establishes them.
    """

    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}
    is_initialize = method == "initialize"

    # An unknown or foreign session id gets 404 — the transport's signal for
    # "start over with initialize". Absent header means the stateless mode,
    # which stays valid. Authorisation never depends on this: the API key was
    # already verified by the time we get here.
    if (
        mcp_session_id
        and not is_initialize
        and not sessions.is_valid(mcp_session_id, account_key=principal.account_key)
    ):
        return JSONResponse(
            status_code=404,
            content=_rpc_error(request_id, -32001, "Unknown or expired session — re-run initialize."),
        )

    # A client that omits the version header on a follow-up is treated as
    # speaking the revision the transport prescribes as the fallback.
    if mcp_protocol_version and mcp_protocol_version not in _SUPPORTED_PROTOCOL_VERSIONS:
        return JSONResponse(
            status_code=400,
            content=_rpc_error(
                request_id,
                -32000,
                f"Unsupported MCP-Protocol-Version '{mcp_protocol_version}'; "
                f"this server speaks {', '.join(_SUPPORTED_PROTOCOL_VERSIONS)}.",
            ),
        )
    effective_version = mcp_protocol_version or _ASSUMED_PROTOCOL_VERSION

    # A JSON-RPC *notification* (or a client→server response) carries no "id" and
    # MUST NOT be answered — not even with an error. Every MCP client sends
    # `notifications/initialized` right after `initialize`, so replying "method
    # not found" there breaks the handshake for a spec-strict client.
    if "id" not in payload:
        return Response(status_code=202)

    if is_initialize:
        negotiated = _negotiate_protocol_version(params.get("protocolVersion"))
        session_id = sessions.create(account_key=principal.account_key)
        if session_id:
            response.headers[_SESSION_HEADER] = session_id
        response.headers["MCP-Protocol-Version"] = negotiated
        return _rpc_result(
            request_id,
            {
                "protocolVersion": negotiated,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": _SERVER_INFO,
            },
        )

    response.headers["MCP-Protocol-Version"] = effective_version

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
            tool_response = await dispatcher.dispatch(principal, tool_name, arguments)
        except KamerplanterError as exc:
            # Surface a structured tool error to the LLM client (isError) instead
            # of a transport-level failure, so the model can react (§2.6, §4.0).
            return _rpc_result(request_id, _tool_error_result(exc))
        return _rpc_result(request_id, _tool_result(tool_response))

    return _rpc_error(request_id, -32601, f"Method not found: {method}")


@router.get("", summary="Server-to-client stream (not offered)")
async def mcp_stream(_principal: McpPrincipal = Depends(get_mcp_principal)) -> Response:
    """Refuse the optional server-to-client SSE stream with ``405``.

    Streamable HTTP lets a client open a stream here to receive server-initiated
    messages, and lets a server that has none decline with ``405`` — which is the
    honest answer for this server: every response is returned directly on the
    POST. Implementing the stream is the prerequisite for the progress
    notifications in §4.5, and is tracked there.
    """

    return Response(status_code=405, headers={"Allow": "POST, DELETE"})


@router.delete("", status_code=204, summary="Terminate the MCP session")
async def mcp_terminate_session(
    principal: McpPrincipal = Depends(get_mcp_principal),
    sessions: McpSessionStore = Depends(get_session_store),
    mcp_session_id: Annotated[str | None, Header(alias="Mcp-Session-Id")] = None,
) -> Response:
    """End the session named by ``Mcp-Session-Id`` (idempotent)."""

    # Only the owning account may end its own session; a foreign or unknown id is
    # silently a no-op, which keeps the endpoint from confirming id existence.
    if mcp_session_id and sessions.is_valid(mcp_session_id, account_key=principal.account_key):
        sessions.terminate(mcp_session_id)
    return Response(status_code=204)
