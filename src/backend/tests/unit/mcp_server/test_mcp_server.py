"""REQ-033 MCP server scaffold tests."""

import pytest

from app.mcp_server.server import MCPServer


class TestMCPServerScaffold:
    def test_register_tool_appears_in_list(self):
        srv = MCPServer()
        srv.register_tool("plants.search", lambda q: [])
        assert "plants.search" in srv.list_tools()

    def test_list_tools_returns_sorted(self):
        srv = MCPServer()
        srv.register_tool("zeta", lambda: None)
        srv.register_tool("alpha", lambda: None)
        assert srv.list_tools() == ["alpha", "zeta"]

    @pytest.mark.asyncio
    async def test_serve_raises_until_follow_up(self):
        srv = MCPServer()
        with pytest.raises(NotImplementedError, match="pending follow-up"):
            await srv.serve()
