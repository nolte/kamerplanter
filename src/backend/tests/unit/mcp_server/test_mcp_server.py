"""REQ-033 MCP server facade tests.

The scaffold ``NotImplementedError`` is gone: ``serve()`` now materialises the
curated tool palette. The facade still supports ad-hoc ``register_tool`` and
merges it with the shared registry.
"""

import pytest

from app.mcp_server.server import MCPServer


class TestMCPServer:
    def test_register_tool_appears_in_list(self):
        srv = MCPServer()
        srv.register_tool("plants.search", lambda q: [])
        assert "plants.search" in srv.list_tools()

    def test_list_tools_returns_sorted(self):
        srv = MCPServer()
        srv.register_tool("zeta", lambda: None)
        srv.register_tool("alpha", lambda: None)
        assert srv.list_tools() == sorted(srv.list_tools())

    def test_curated_palette_registered(self):
        srv = MCPServer()
        names = srv.list_tools()
        for expected in ("get_harvest_readiness", "archive_plant", "create_site", "get_mcp_activity"):
            assert expected in names

    def test_tool_specs_carry_permission(self):
        srv = MCPServer()
        specs = {s.name: s for s in srv.tool_specs()}
        assert specs["get_harvest_readiness"].permission == "mcp.read"
        assert specs["archive_plant"].permission == "mcp.write"
        assert specs["create_site"].permission == "mcp.setup"

    @pytest.mark.asyncio
    async def test_serve_returns_served_tools(self):
        srv = MCPServer()
        served = await srv.serve()
        assert "get_harvest_readiness" in served
