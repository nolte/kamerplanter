"""REQ-033 MCP server entry point (scaffold)."""

from __future__ import annotations

from typing import Any


class MCPServer:
    """Scaffold MCP server — pins the public surface for REQ-033."""

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register_tool(self, name: str, handler: Any) -> None:
        """Register a callable tool that LLM clients can invoke."""
        self._tools[name] = handler

    def list_tools(self) -> list[str]:
        """Return the names of every registered tool."""
        return sorted(self._tools)

    async def serve(self, host: str = "0.0.0.0", port: int = 7000) -> None:
        raise NotImplementedError("REQ-033 MCPServer.serve — pending follow-up.")
