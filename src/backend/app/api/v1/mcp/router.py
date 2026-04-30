"""REQ-033 MCP HTTP discovery router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["mcp"])
