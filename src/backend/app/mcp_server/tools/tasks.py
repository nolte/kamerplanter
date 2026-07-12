"""REQ-033 task read tools (§2.1). Delegates to ``TaskService``."""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext


@mcp_tool(name="list_tasks", permission=McpPermission.READ)
class ListTasks(ToolBase):
    """List the tenant's tasks, optionally filtered by status."""

    class Input(ToolInput):
        status: str | None = Field(
            default=None,
            description="Optional task status filter (pending, in_progress, completed, ...).",
        )
        offset: int = Field(default=0, ge=0)
        limit: int = Field(default=25, ge=1, le=100)

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        filters = {"status": args.status} if args.status else None
        tasks, total = ctx.task_service.list_tasks(
            offset=args.offset,
            limit=args.limit,
            filters=filters,
            tenant_key=ctx.tenant_key,
        )
        data = {
            "total": total,
            "items": [
                {
                    "task_key": t.key,
                    "title": getattr(t, "title", None),
                    "status": getattr(t, "status", None),
                    "priority": getattr(t, "priority", None),
                    "due_date": getattr(t, "due_date", None),
                    "category": getattr(t, "category", None),
                }
                for t in tasks
            ],
        }
        status_note = f" with status '{args.status}'" if args.status else ""
        return self._response(
            summary=f"{total} tasks{status_note} ({len(tasks)} returned).",
            data=data,
            links=[ctx.api_link("/tasks"), ctx.ui_link("/tasks")],
        )
