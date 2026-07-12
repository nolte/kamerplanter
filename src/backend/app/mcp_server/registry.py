"""REQ-033 MCP tool registry (§1.2, §4.2).

A process-wide registry of the curated MCP tool palette. Tools register
themselves at import time via the :func:`app.mcp_server.base.mcp_tool` decorator;
the discovery endpoint and the dispatcher read from this single registry.
"""

from __future__ import annotations

from app.domain.models.mcp import McpToolSpec


class ToolRegistry:
    """Name → tool-instance registry with sorted discovery output."""

    def __init__(self) -> None:
        self._tools: dict[str, object] = {}

    def register(self, tool: object) -> None:
        name = getattr(tool, "tool_name", "")
        if not name:
            raise ValueError("MCP tool must declare a non-empty tool_name.")
        self._tools[name] = tool

    def get(self, name: str) -> object | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[McpToolSpec]:
        return [self._tools[name].spec() for name in self.names()]  # type: ignore[attr-defined]

    def clear(self) -> None:
        """Test-only: reset the registry."""

        self._tools.clear()


#: Process-wide singleton.
registry = ToolRegistry()


def load_tools() -> ToolRegistry:
    """Import the tool modules so their ``@mcp_tool`` decorators register them.

    Idempotent: re-importing is cheap and re-registration overwrites in place.
    """

    from app.mcp_server import tools  # noqa: F401  (side-effect import)

    return registry
