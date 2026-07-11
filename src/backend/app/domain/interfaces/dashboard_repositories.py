"""Typed repository contracts consumed by the REQ-009 dashboard aggregator.

The :class:`~app.domain.services.dashboard_service.DashboardService` stitches
together a handful of cheap tenant-scoped counts and short lists. Historically it
probed each repository with ``hasattr(...)`` and silently fell back to ``0`` /
``[]`` — which masked the fact that *none* of the expected methods was
implemented, so every dashboard tile rendered a hard ``0`` regardless of tenant.

These ``Protocol`` classes make the required repository shape explicit and typed
(NFR-001 5-layer boundary: the service depends on an interface, not a concrete
ArangoDB repository). The service references them instead of ``Any`` and calls
the methods directly, so a future missing method surfaces as a loud
``AttributeError`` rather than collapsing into a legit-looking empty state
(REQ-009 R7).

Structural typing (``Protocol``) is intentional: the concrete Arango repositories
already inherit their own ``I…Repository`` ABCs, and the dashboard only needs a
narrow read-side view onto each. No repository has to inherit these Protocols to
satisfy them.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PlantDashboardRepository(Protocol):
    """Plant-instance counts + list for the "active plants" / "plant grid" tiles."""

    def count_for_tenant(self, tenant_key: str) -> int:
        """Total plant instances owned by ``tenant_key``."""
        ...

    def count_active_for_tenant(self, tenant_key: str) -> int:
        """Alive plant instances (``removed_on == null``) owned by ``tenant_key``."""
        ...

    def list_active_for_tenant(self, tenant_key: str, limit: int) -> list[dict[str, Any]]:
        """Newest alive plant instances (``_key`` + label fields) for the plant grid."""
        ...


@runtime_checkable
class TaskDashboardRepository(Protocol):
    """Task counts + upcoming list for the "tasks today" tile."""

    def count_open_due_on(self, tenant_key: str, today: date) -> int:
        """Open tasks (``status IN {pending, in_progress}``) due on ``today``."""
        ...

    def count_overdue(self, tenant_key: str, today: date) -> int:
        """Open tasks whose due date is strictly before ``today``."""
        ...

    def list_upcoming(
        self,
        tenant_key: str,
        today: date,
        window_end: date,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Open tasks due within ``[today, window_end]``, soonest first."""
        ...


@runtime_checkable
class TankDashboardRepository(Protocol):
    """Tank count for the "tanks low" tile."""

    def count_below_threshold(self, tenant_key: str) -> int:
        """Tanks whose latest fill level is below their low-fill threshold."""
        ...


@runtime_checkable
class CareReminderDashboardRepository(Protocol):
    """Care-reminder count for the "care reminders" tile."""

    def count_due_on(self, tenant_key: str, today: date) -> int:
        """Care reminders actionable on ``today`` (due today plus overdue)."""
        ...
