"""ADR-008 F-8 — the escalation beat, end to end over the real engine and propagation owner.

``escalate_overdue_notifications`` walks every tenant and asks the engine to
escalate that tenant's overdue watering reminders. Before F-8 the overdue query
read **every** tenant's rows and the engine stamped whatever it found, so the
first tenant of the walk escalated all of them — including the rows of a tenant
the walk itself skips because it is not ``active`` (#2166).

Here nothing between the Celery task function and the stored rows is a mock: the
task, :class:`NotificationEngine`, :class:`NotificationPropagationService` and
the stateful
:class:`~tests.unit.domain.services.notification_fakes.EscalationNotificationRepo`
(tenant-scoped overdue query, conditional claim — the real AQL's semantics). Only
the outside world is doubled: preferences, Redis (dedup switched off), channels.

Traces to issue #1061, feature F-8 (no TC-ID: a beat-level unit test).
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantStatus, TenantType
from app.domain.engines.notification_engine import NotificationEngine
from app.domain.models.notification import NotificationPreferences
from app.domain.models.tenant import Tenant
from app.domain.services.notification_propagation_service import NotificationPropagationService
from tests.unit.domain.services.notification_fakes import EscalationNotificationRepo

USER = "member"


def _tenant(key: str, status: TenantStatus = TenantStatus.ACTIVE) -> Tenant:
    return Tenant(
        _key=key, name=key, slug=key, tenant_type=TenantType.ORGANIZATION, owner_user_key="owner", status=status
    )


class _Tenants:
    """The paged ``get_all`` the beat walks, in insertion order (tenant A first)."""

    def __init__(self, *tenants: Tenant) -> None:
        self._rows = list(tenants)

    def get_all(self, offset: int = 0, limit: int = 1000, **_kwargs):  # noqa: ANN201 - the paging contract
        return self._rows[offset : offset + limit], len(self._rows)


class _RunAwareRepo(EscalationNotificationRepo):
    """Records in which tenant's run each claim happened."""

    def __init__(self) -> None:
        super().__init__()
        self.current_run = ""
        self.claimed_in: list[tuple[str, str]] = []

    def claim_escalation_level(self, key: str, *, tenant_key: str, escalation_level: int):  # noqa: ANN201
        claimed = super().claim_escalation_level(key, tenant_key=tenant_key, escalation_level=escalation_level)
        if claimed is not None:
            self.claimed_in.append((key, self.current_run))
        return claimed


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    repo = _RunAwareRepo()
    preference_repo = MagicMock()
    preference_repo.get_by_user.return_value = NotificationPreferences(user_key=USER)
    redis = MagicMock()
    redis.get.return_value = None  # no Redis dedup: only the claim can keep a row from escalating twice
    engine = NotificationEngine(
        notification_repo=repo,
        preference_repo=preference_repo,
        channel_registry=MagicMock(),
        redis_client=redis,
        user_repo=MagicMock(),
        propagation=NotificationPropagationService(repo),
    )
    engine._is_quiet_hours = MagicMock(return_value=False)  # type: ignore[method-assign]
    engine._resolve_channels = MagicMock(return_value=[])  # type: ignore[method-assign]

    real_escalate = engine.escalate_overdue
    runs: list[str] = []

    async def escalate(tenant_key: str) -> dict:
        runs.append(tenant_key)
        repo.current_run = tenant_key
        return await real_escalate(tenant_key)

    engine.escalate_overdue = escalate  # type: ignore[method-assign]

    deps = ModuleType("app.common.dependencies")
    deps.get_notification_service = MagicMock(return_value=SimpleNamespace(_engine=engine))  # type: ignore[attr-defined]
    deps.get_tenant_repo = MagicMock(  # type: ignore[attr-defined]
        return_value=_Tenants(
            _tenant("tenant-a"),
            _tenant("tenant-b"),
            _tenant("tenant-c", TenantStatus.SUSPENDED),
        )
    )
    monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)

    rows = {
        tenant: repo.seed_overdue_care_row(tenant_key=tenant, user_key=USER, group_key=f"care.watering:p-{tenant}")
        for tenant in ("tenant-b", "tenant-c")
    }
    return SimpleNamespace(repo=repo, runs=runs, rows=rows)


def _beat() -> dict:
    from app.tasks.notification_tasks import escalate_overdue_notifications

    return escalate_overdue_notifications()


def test_a_row_of_tenant_b_is_escalated_once_in_b_s_own_run(world: SimpleNamespace) -> None:
    result = _beat()

    assert world.runs == ["tenant-a", "tenant-b"], "the suspended tenant is not walked at all"
    assert world.repo.claimed_in == [(world.rows["tenant-b"], "tenant-b")]
    escalations = world.repo.escalations()
    assert [(row.tenant_key, row.parent_notification_key) for row in escalations] == [
        ("tenant-b", world.rows["tenant-b"])
    ]
    assert result["total_escalated"] == 1


def test_a_suspended_tenants_row_is_not_escalated(world: SimpleNamespace) -> None:
    _beat()

    suspended_row = world.repo.get(world.rows["tenant-c"])
    assert suspended_row.escalation_level == 0
    assert all(row.tenant_key != "tenant-c" for row in world.repo.escalations())


def test_a_second_beat_escalates_nothing_more(world: SimpleNamespace) -> None:
    _beat()
    second = _beat()

    assert second["total_escalated"] == 0
    assert len(world.repo.escalations()) == 1
    assert world.repo.claimed_in == [(world.rows["tenant-b"], "tenant-b")]
