"""REQ-009 Dashboard aggregation service.

Spec: ``spec/req/REQ-009_Dashboard.md`` v2.1.

The dashboard surfaces a consolidated view across REQ-001 (plants),
REQ-006 (tasks), REQ-007 (harvest), REQ-014 (tanks), REQ-022 (care
reminders) and REQ-005 (sensors). This service is the read-side
aggregator — it stitches together small, cheap counts and a handful
of recent items per category so the frontend can render a one-screen
overview without having to fan out to half a dozen REST endpoints.

Out of scope (kept on the REQ-009 roadmap):

- WebSocket fan-out for live updates (Spec §3, ConnectionManager).
- Configurable widget grid + persistence (Spec §2 Nodes).
- Per-tenant + per-user pinning of widgets.

The service intentionally accepts already-loaded dependencies so it
stays cheap to test: each repository is consulted at most once per
``get_summary`` call.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class DashboardCounts:
    """Cardinal counts surfaced by the dashboard tiles."""

    plants_total: int
    plants_active: int
    open_tasks_today: int
    overdue_tasks: int
    tanks_low: int  # number of tanks below their low-level threshold
    care_reminders_due: int


@dataclass(frozen=True)
class DashboardSummary:
    """Top-level read-model for the dashboard page (REQ-009)."""

    generated_at: datetime
    tenant_key: str
    counts: DashboardCounts
    upcoming_tasks: list[dict[str, Any]]
    recent_activities: list[dict[str, Any]]


class DashboardService:
    """REQ-009 dashboard aggregator.

    Each loader is injected as a ``Callable`` so the service stays
    repository-shape-agnostic and unit-testable without ArangoDB.
    """

    def __init__(
        self,
        *,
        plant_repo: Any,
        task_repo: Any,
        tank_repo: Any | None = None,
        care_repo: Any | None = None,
        activity_repo: Any | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._plant_repo = plant_repo
        self._task_repo = task_repo
        self._tank_repo = tank_repo
        self._care_repo = care_repo
        self._activity_repo = activity_repo
        self._clock = clock

    def get_summary(self, tenant_key: str) -> DashboardSummary:
        """Build a fresh DashboardSummary for the active tenant."""

        now = self._clock()
        today = now.date()

        plants_total, plants_active = self._plant_counts(tenant_key)
        open_today, overdue = self._task_counts(tenant_key, today)
        tanks_low = self._tank_low_count(tenant_key)
        care_due = self._care_due_count(tenant_key, today)

        counts = DashboardCounts(
            plants_total=plants_total,
            plants_active=plants_active,
            open_tasks_today=open_today,
            overdue_tasks=overdue,
            tanks_low=tanks_low,
            care_reminders_due=care_due,
        )

        return DashboardSummary(
            generated_at=now,
            tenant_key=tenant_key,
            counts=counts,
            upcoming_tasks=self._upcoming_tasks(tenant_key, today),
            recent_activities=self._recent_activities(tenant_key, now),
        )

    # ── Internal aggregators ─────────────────────────────────────────

    def _plant_counts(self, tenant_key: str) -> tuple[int, int]:
        if not hasattr(self._plant_repo, "count_for_tenant"):
            return 0, 0
        try:
            total = int(self._plant_repo.count_for_tenant(tenant_key) or 0)
            active = (
                int(self._plant_repo.count_active_for_tenant(tenant_key) or 0)
                if hasattr(self._plant_repo, "count_active_for_tenant")
                else total
            )
            return total, active
        except Exception:
            logger.exception("dashboard.plant_counts.failed", tenant_key=tenant_key)
            return 0, 0

    def _task_counts(self, tenant_key: str, today: date) -> tuple[int, int]:
        if not hasattr(self._task_repo, "count_open_due_on") or not hasattr(self._task_repo, "count_overdue"):
            return 0, 0
        try:
            return (
                int(self._task_repo.count_open_due_on(tenant_key, today) or 0),
                int(self._task_repo.count_overdue(tenant_key, today) or 0),
            )
        except Exception:
            logger.exception("dashboard.task_counts.failed", tenant_key=tenant_key)
            return 0, 0

    def _tank_low_count(self, tenant_key: str) -> int:
        if not self._tank_repo or not hasattr(self._tank_repo, "count_below_threshold"):
            return 0
        try:
            return int(self._tank_repo.count_below_threshold(tenant_key) or 0)
        except Exception:
            logger.exception("dashboard.tank_low_count.failed", tenant_key=tenant_key)
            return 0

    def _care_due_count(self, tenant_key: str, today: date) -> int:
        if not self._care_repo or not hasattr(self._care_repo, "count_due_on"):
            return 0
        try:
            return int(self._care_repo.count_due_on(tenant_key, today) or 0)
        except Exception:
            logger.exception("dashboard.care_due_count.failed", tenant_key=tenant_key)
            return 0

    def _upcoming_tasks(self, tenant_key: str, today: date, limit: int = 5) -> list[dict[str, Any]]:
        if not hasattr(self._task_repo, "list_upcoming"):
            return []
        try:
            window_end = today + timedelta(days=7)
            return list(self._task_repo.list_upcoming(tenant_key, today, window_end, limit) or [])
        except Exception:
            logger.exception("dashboard.upcoming_tasks.failed", tenant_key=tenant_key)
            return []

    def _recent_activities(self, tenant_key: str, now: datetime, limit: int = 5) -> list[dict[str, Any]]:
        if not self._activity_repo or not hasattr(self._activity_repo, "list_recent"):
            return []
        try:
            since = now - timedelta(days=7)
            return list(self._activity_repo.list_recent(tenant_key, since, limit) or [])
        except Exception:
            logger.exception("dashboard.recent_activities.failed", tenant_key=tenant_key)
            return []
