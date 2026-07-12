"""REQ-033 MCP server facade.

Thin facade over the process-wide :class:`ToolRegistry`. The real transport is
mounted on the FastAPI backend (``app.api.v1.mcp.router``) as HTTP + SSE
(§1.2) — this class is the in-process entry point that loads the curated tool
palette and exposes it for discovery and dispatch.

The dedicated standalone ``src/mcp-server/`` process with a stdio transport
described in REQ-033 §4.1 is a documented future follow-up; for this iteration
the MCP surface is served in-process by the backend (see the design note in the
PR/report).
"""

from __future__ import annotations

from typing import Any

from app.domain.models.mcp import McpToolSpec
from app.mcp_server.registry import load_tools, registry


class MCPServer:
    """In-process MCP tool host backed by the global registry."""

    def __init__(self) -> None:
        # Legacy free-function tools (kept for the scaffold registration API);
        # curated class-based tools live in the shared registry.
        self._tools: dict[str, Any] = {}
        load_tools()

    def register_tool(self, name: str, handler: Any) -> None:
        """Register a callable tool that LLM clients can invoke."""
        self._tools[name] = handler

    def list_tools(self) -> list[str]:
        """Return the names of every registered tool (registry + local)."""
        return sorted(set(self._tools) | set(registry.names()))

    def tool_specs(self) -> list[McpToolSpec]:
        """Return the discovery descriptors for every curated tool (tools/list)."""
        return registry.specs()

    async def serve(self) -> list[str]:
        """Load the tool palette and report the served tools.

        The HTTP + SSE transport is provided by the FastAPI backend; this method
        materialises the registry (idempotent) and returns the served tool names
        so an operator/health probe can confirm the palette is wired.
        """
        load_tools()
        return self.list_tools()
