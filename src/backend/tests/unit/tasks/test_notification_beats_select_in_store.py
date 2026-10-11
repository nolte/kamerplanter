"""MT-032 (#2128): the care notification beats select the due reminders in the store, one tenant at a time.

``notifications.dispatch_due_care`` and ``notifications.send_daily_summary`` read the WHOLE
``tasks`` collection of every tenant (``get_all_pages(task_repo, all_tenants=True)``) into
the worker and picked out the open care reminders of the day in Python. Worker memory grew
with the installation's total task count, and one daily run held every tenant's tasks at
once. They now ask ``list_open_care_reminders_due`` once per active tenant, with the day's
window, and finish a tenant before the next one is read.

``CareReminderStore.get_all`` raises, so the old read is a failure here rather than a
double that would have answered it. The query's own semantics are measured against the
server in ``tests/integration/test_care_reminders_due_query.py``.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantStatus, TenantType
from app.domain.models.tenant import Tenant
from tests.support.care_reminder_store import CareReminderStore

NOW = datetime.now(UTC)
DAY_START = datetime(NOW.year, NOW.month, NOW.day, tzinfo=UTC)
DAY_END = datetime(NOW.year, NOW.month, NOW.day, 23, 59, 59, tzinfo=UTC)


def _tenant(key: str, status: TenantStatus = TenantStatus.ACTIVE) -> Tenant:
    return Tenant(
        _key=key, name=key, slug=key, tenant_type=TenantType.ORGANIZATION, owner_user_key="owner", status=status
    )


def _reminder(key: str, tenant: str, due: datetime) -> dict:
    return {
        "_key": key,
        "category": "care_reminder",
        "status": "pending",
        "due_date": due.isoformat(),
        "priority": "medium",
        "name": f"Plant {key} — watering",
        "plant_key": f"p-{key}",
        "assigned_to": "member",
        "tenant_key": tenant,
    }


class _Tenants:
    def __init__(self, *tenants: Tenant) -> None:
        self.stored = {t.key: t for t in tenants}

    def get_by_key(self, key: str) -> Tenant | None:
        return self.stored.get(key)

    def get_all(self, offset: int = 0, limit: int = 1000, **_kwargs):  # noqa: ANN201 - the paging contract
        rows = list(self.stored.values())
        return rows[offset : offset + limit], len(rows)


class _Journal:
    """Records the order of store reads and sends, to show one tenant is finished before the next is read."""

    def __init__(self, store: CareReminderStore) -> None:
        self.events: list[tuple[str, str]] = []
        self._store = store

    def list_open_care_reminders_due(self, **kwargs):  # noqa: ANN003, ANN201
        self.events.append(("read", kwargs["tenant_key"]))
        return self._store.list_open_care_reminders_due(**kwargs)

    def get_all(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        return self._store.get_all(*args, **kwargs)

    async def send_care_notifications(self, tenant_key: str, tasks: list[dict]) -> dict:
        self.events.append(("send", tenant_key))
        return {"users_notified": 1, "total_sent": len(tasks)}

    def get_preferences(self, _user_key: str):  # noqa: ANN201
        prefs = MagicMock()
        prefs.daily_summary.enabled = True
        return prefs

    async def send_notification(self, **kwargs) -> None:  # noqa: ANN003
        self.events.append(("send", kwargs["tenant_key"]))


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN201
    store = CareReminderStore(
        [
            _reminder("a-today", "t-a", DAY_START + timedelta(hours=6)),
            _reminder("a-overdue", "t-a", DAY_START - timedelta(days=2)),
            _reminder("b-today", "t-b", DAY_START + timedelta(hours=9)),
            _reminder("closed-today", "t-closed", DAY_START + timedelta(hours=6)),
        ]
    )
    journal = _Journal(store)
    deps = ModuleType("app.common.dependencies")
    deps.get_task_repo = MagicMock(return_value=journal)  # type: ignore[attr-defined]
    deps.get_notification_service = MagicMock(return_value=journal)  # type: ignore[attr-defined]
    deps.get_membership_repo = MagicMock(  # type: ignore[attr-defined]
        return_value=MagicMock(get_by_user_and_tenant=lambda *_a: MagicMock(is_active=True))
    )
    deps.get_tenant_repo = MagicMock(  # type: ignore[attr-defined]
        return_value=_Tenants(_tenant("t-a"), _tenant("t-b"), _tenant("t-closed", TenantStatus.SUSPENDED))
    )
    monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)
    return store, journal


def test_the_dispatch_asks_the_store_for_each_active_tenants_reminders_of_today(world) -> None:
    store, _journal = world
    from app.tasks.notification_tasks import dispatch_due_care_notifications

    result = dispatch_due_care_notifications()

    assert store.asked == [("t-a", DAY_START, DAY_END), ("t-b", DAY_START, DAY_END)]
    assert result["tasks_found"] == 2


def test_the_daily_summary_asks_without_a_lower_bound_so_overdue_reminders_count(world) -> None:
    store, _journal = world
    from app.tasks.notification_tasks import send_daily_summary

    result = send_daily_summary()

    assert store.asked == [("t-a", None, DAY_END), ("t-b", None, DAY_END)]
    assert result["summaries_sent"] == 2


@pytest.mark.parametrize("beat", ["dispatch_due_care_notifications", "send_daily_summary"])
def test_a_tenant_is_sent_before_the_next_tenant_is_read(world, beat: str) -> None:
    """The worker holds one tenant's due reminders at a time, not the installation's."""
    _store, journal = world
    import app.tasks.notification_tasks as module

    getattr(module, beat)()

    assert journal.events == [("read", "t-a"), ("send", "t-a"), ("read", "t-b"), ("send", "t-b")]
