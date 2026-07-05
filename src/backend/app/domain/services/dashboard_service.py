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

from app.domain.interfaces.dashboard_repositories import (
    CareReminderDashboardRepository,
    PlantDashboardRepository,
    TankDashboardRepository,
    TaskDashboardRepository,
)

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

    Each repository is injected against a typed ``Protocol``
    (:mod:`app.domain.interfaces.dashboard_repositories`) rather than probed with
    ``hasattr``. The required repositories (``plant_repo`` / ``task_repo``) are
    called directly (via ``_require_methods``), so a missing method surfaces as a
    loud ``AttributeError`` instead of silently collapsing a whole tile to ``0``
    (REQ-009 R7). The optional repositories (``tank_repo`` / ``care_repo``) are
    guarded by a plain presence check — the guard asks "is the repository
    wired?", never "does the method happen to exist?". ``activity_repo`` is wired
    but not yet consumed (see ``_recent_activities``).
    """

    def __init__(
        self,
        *,
        plant_repo: PlantDashboardRepository,
        task_repo: TaskDashboardRepository,
        tank_repo: TankDashboardRepository | None = None,
        care_repo: CareReminderDashboardRepository | None = None,
        activity_repo: object | None = None,  # reserved for a future activity event-log feed
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
    #
    # Each aggregator distinguishes two failure classes (REQ-009 R7/R8):
    #
    # * a **missing repository method** — a programming/wiring error. It is
    #   detected up-front by ``_require_methods`` (before the query call) and
    #   raised so the tile can never silently collapse to ``0`` (which would be
    #   indistinguishable from a legit empty tenant). This is the exact masking
    #   that caused the hard-zero dashboard.
    # * any other ``Exception`` raised **while the method runs** (DB down,
    #   malformed document, even an internal ``AttributeError`` on a ``None``
    #   field) — a genuine runtime error: logged and degraded to ``0``/``[]`` so
    #   one broken section never takes down the whole overview. The up-front
    #   existence check is kept separate from the ``try`` precisely so a runtime
    #   ``AttributeError`` is degraded rather than mistaken for a missing method.

    @staticmethod
    def _require_methods(repo: object, *names: str) -> None:
        """Raise if ``repo`` is missing any required dashboard method (REQ-009 R7)."""
        missing = [name for name in names if not hasattr(repo, name)]
        if missing:
            raise AttributeError(f"{type(repo).__name__} is missing required dashboard method(s): {', '.join(missing)}")

    def _plant_counts(self, tenant_key: str) -> tuple[int, int]:
        self._require_methods(self._plant_repo, "count_for_tenant", "count_active_for_tenant")
        try:
            total = int(self._plant_repo.count_for_tenant(tenant_key) or 0)
            active = int(self._plant_repo.count_active_for_tenant(tenant_key) or 0)
            return total, active
        except Exception:
            logger.exception("dashboard.plant_counts.failed", tenant_key=tenant_key)
            return 0, 0

    def _task_counts(self, tenant_key: str, today: date) -> tuple[int, int]:
        self._require_methods(self._task_repo, "count_open_due_on", "count_overdue")
        try:
            return (
                int(self._task_repo.count_open_due_on(tenant_key, today) or 0),
                int(self._task_repo.count_overdue(tenant_key, today) or 0),
            )
        except Exception:
            logger.exception("dashboard.task_counts.failed", tenant_key=tenant_key)
            return 0, 0

    def _tank_low_count(self, tenant_key: str) -> int:
        if self._tank_repo is None:
            return 0
        self._require_methods(self._tank_repo, "count_below_threshold")
        try:
            return int(self._tank_repo.count_below_threshold(tenant_key) or 0)
        except Exception:
            logger.exception("dashboard.tank_low_count.failed", tenant_key=tenant_key)
            return 0

    def _care_due_count(self, tenant_key: str, today: date) -> int:
        if self._care_repo is None:
            return 0
        self._require_methods(self._care_repo, "count_due_on")
        try:
            return int(self._care_repo.count_due_on(tenant_key, today) or 0)
        except Exception:
            logger.exception("dashboard.care_due_count.failed", tenant_key=tenant_key)
            return 0

    def _upcoming_tasks(self, tenant_key: str, today: date, limit: int = 5) -> list[dict[str, Any]]:
        self._require_methods(self._task_repo, "list_upcoming")
        try:
            window_end = today + timedelta(days=7)
            return list(self._task_repo.list_upcoming(tenant_key, today, window_end, limit) or [])
        except Exception:
            logger.exception("dashboard.upcoming_tasks.failed", tenant_key=tenant_key)
            return []

    def _recent_activities(self, tenant_key: str, now: datetime, limit: int = 5) -> list[dict[str, Any]]:
        # Deferred (REQ-009 roadmap): there is no per-tenant activity *event log*
        # to feed a "recent activities" list. The ``activities`` collection is a
        # global catalog of activity-type definitions (tenant_key == ""), not a
        # record of performed actions, so scanning it per tenant would return an
        # empty list dressed up as an implemented feature — exactly the masking
        # this change removes. Kept as an explicit empty section until an event
        # log exists; ``activity_repo`` stays wired for that future source.
        return []
