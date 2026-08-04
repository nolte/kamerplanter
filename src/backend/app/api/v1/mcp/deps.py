"""REQ-033 MCP router dependencies (§4.3).

Resolves the calling principal from the transport (``X-API-Key`` header or
``Authorization: Bearer kp_...``) and provides the tool dispatcher. The key may
belong to a personal account or to a service account; either way the principal
carries only the tenants that account is an active member of. When the MCP
server is disabled (``MCP_SERVER_ENABLED=false``) every endpoint answers HTTP
404, so the interface appears not to exist (mirrors the AI operator flag).
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials

from app.common.auth import bearer_scheme
from app.common.dependencies import get_mcp_authenticator, get_mcp_dispatcher
from app.common.exceptions import NotFoundError, UnauthorizedError
from app.common.request_ip import resolve_client_ip
from app.config.settings import settings
from app.mcp_server.auth import McpAuthenticator
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.principal import McpPrincipal


def require_mcp_enabled() -> None:
    """Gate the whole MCP surface behind the operator flag (§6)."""

    if not settings.mcp_server_enabled:
        raise NotFoundError("MCP server", "disabled")


# Security scheme (not a raw Header parameter) so the OpenAPI document shows
# the X-API-Key alternative alongside the Bearer scheme on MCP operations.
api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    scheme_name="McpApiKey",
    description="`kp_`-prefixed API key (personal or service account) for MCP clients.",
)


def get_mcp_principal(
    request: Request,
    _enabled: None = Depends(require_mcp_enabled),
    x_api_key: str | None = Depends(api_key_scheme),
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    authenticator: McpAuthenticator = Depends(get_mcp_authenticator),
) -> McpPrincipal:
    """Authenticate the MCP caller via its API key (§4.3).

    Accepts a personal account's key as well as a service account's; the
    principal is scoped to that account's tenant memberships either way. The
    resolved client IP is threaded into the authenticator so it can enforce the
    key's ``ip_allowlist`` control (SEC-004).
    """

    raw_key = x_api_key
    if not raw_key and bearer is not None and bearer.scheme == "Bearer":
        raw_key = bearer.credentials
    if not raw_key:
        raise UnauthorizedError("Missing MCP API key (X-API-Key).")
    return authenticator.authenticate(raw_key, client_ip=resolve_client_ip(request))


def get_dispatcher(
    _enabled: None = Depends(require_mcp_enabled),
    dispatcher: ToolDispatcher = Depends(get_mcp_dispatcher),
) -> ToolDispatcher:
    return dispatcher
