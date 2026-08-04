"""REQ-033 privacy tool (§4.6, DSGVO REQ-025 AC-S3).

Lets a service account inspect its own MCP audit trail (hash-only, no PII). The
human-facing ``GET /privacy/mcp-activity`` endpoint reuses the same repository.
"""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="get_mcp_activity", permission=McpPermission.READ)
class GetMcpActivity(ToolBase):
    """Return this service account's recent MCP tool-call audit trail."""

    class Input(ToolInput):
        limit: int = Field(default=50, ge=1, le=200)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entries = ctx.mcp_audit_repo.list_for_service_account(
            ctx.principal.account_key,
            limit=args.limit,
        )
        data = {
            "count": len(entries),
            "items": [
                {
                    "tool_name": e.tool_name,
                    "status": e.status,
                    "output_size_bytes": e.output_size_bytes,
                    "duration_ms": e.duration_ms,
                    "error_class": e.error_class,
                    "created_at": e.created_at,
                }
                for e in entries
            ],
        }
        return self._response(
            summary=f"{len(entries)} recent MCP tool calls for this service account.",
            data=data,
            links=[{"type": "api", "url": "/api/v1/privacy/mcp-activity"}],
        )
