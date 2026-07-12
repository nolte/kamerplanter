"""REQ-033 MCP router dependencies (§4.3).

Resolves the service-account principal from the transport (``X-API-Key`` header
or ``Authorization: Bearer kp_...``) and provides the tool dispatcher. When the
MCP server is disabled (``MCP_SERVER_ENABLED=false``) every endpoint answers HTTP
404, so the interface appears not to exist (mirrors the AI operator flag).
"""

from __future__ import annotations

from fastapi import Depends, Header

from app.common.dependencies import get_mcp_authenticator, get_mcp_dispatcher
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.config.settings import settings
from app.mcp_server.auth import McpAuthenticator
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.principal import McpPrincipal


def require_mcp_enabled() -> None:
    """Gate the whole MCP surface behind the operator flag (§6)."""

    if not settings.mcp_server_enabled:
        raise NotFoundError("MCP server", "disabled")


def get_mcp_principal(
    _enabled: None = Depends(require_mcp_enabled),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
    authenticator: McpAuthenticator = Depends(get_mcp_authenticator),
) -> McpPrincipal:
    """Authenticate the MCP caller via its service-account API key (§4.3)."""

    raw_key = x_api_key
    if not raw_key and authorization and authorization.startswith("Bearer "):
        raw_key = authorization[7:]
    if not raw_key:
        raise UnauthorizedError("Missing MCP service-account API key (X-API-Key).")
    return authenticator.authenticate(raw_key)


def get_dispatcher(
    _enabled: None = Depends(require_mcp_enabled),
    dispatcher: ToolDispatcher = Depends(get_mcp_dispatcher),
) -> ToolDispatcher:
    return dispatcher
