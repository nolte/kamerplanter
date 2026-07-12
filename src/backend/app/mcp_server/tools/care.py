"""REQ-033 care tools (§2.1 read + §2.2 write). Delegates to ``CareReminderService``."""

from __future__ import annotations

from pydantic import Field

from app.common.enums import McpPermission, ReminderType
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import ToolBase, ToolInput, WriteToolBase, WriteToolInput, mcp_tool
from app.mcp_server.context import ToolContext

_ACTIONABLE_URGENCIES = {"overdue", "due_today"}


@mcp_tool(name="get_due_care_tasks", permission=McpPermission.READ)
class GetDueCareTasks(ToolBase):
    """List today's / overdue care reminders grouped by urgency."""

    class Input(ToolInput):
        urgency: str = Field(
            default="actionable",
            description="'actionable' (overdue + due today), 'all', or a single urgency value.",
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        entries = ctx.care_service.get_care_dashboard_for_tenant(ctx.tenant_key)
        if args.urgency == "all":
            selected = entries
        elif args.urgency == "actionable":
            selected = [e for e in entries if e.urgency in _ACTIONABLE_URGENCIES]
        else:
            selected = [e for e in entries if e.urgency == args.urgency]
        data = {
            "count": len(selected),
            "items": [
                {
                    "plant_key": e.plant_key,
                    "plant_name": e.plant_name,
                    "species_name": e.species_name,
                    "reminder_type": e.reminder_type,
                    "urgency": e.urgency,
                    "due_date": e.due_date,
                }
                for e in selected
            ],
        }
        return self._response(
            summary=f"{len(selected)} care reminders match '{args.urgency}'.",
            data=data,
            links=[ctx.api_link("/care/dashboard"), ctx.ui_link("/care")],
        )


@mcp_tool(name="confirm_care_task", permission=McpPermission.WRITE)
class ConfirmCareTask(WriteToolBase):
    """Confirm a care reminder for a plant ("I have watered it")."""

    class Input(WriteToolInput):
        plant_key: str
        reminder_type: ReminderType
        notes: str | None = None

    async def preview(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        return self._response(
            summary=f"Would confirm a '{args.reminder_type}' reminder for plant '{args.plant_key}'.",
            data={"plant_key": args.plant_key, "reminder_type": args.reminder_type},
        )

    async def execute(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        confirmation = ctx.care_service.confirm_reminder(
            plant_key=args.plant_key,
            reminder_type=args.reminder_type,
            notes=args.notes,
        )
        return self._response(
            summary=f"Confirmed '{args.reminder_type}' for plant '{args.plant_key}'.",
            data={
                "plant_key": args.plant_key,
                "reminder_type": args.reminder_type,
                "confirmation_key": getattr(confirmation, "key", None),
            },
            links=[ctx.ui_link("/care")],
        )
