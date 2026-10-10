"""#2166 — the care-reminder beats leave a tenant alone that is not ``active``.

Measured on develop before this change: a tenant in ``pending_deletion`` (#2123) keeps
every membership active on purpose (so a cancellation restores them unchanged), and a
``suspended`` or ``orphaned`` tenant (#2134) keeps them too. The beats asked for the
membership only (#2114) or for nothing at all:

* ``generate_due_care_reminders`` wrote new care tasks into such a tenant every morning;
* ``dispatch_due_care`` and ``send_daily_summary`` notified its members of plants and due
  dates in a tenant they cannot open (it resolves for nobody, #2105);
* ``escalate_overdue`` escalated its notifications.

The stored tenant decides (``Tenant.is_active`` — ``status == active`` and nothing else),
asked once per tenant and run. A plant without a tenant keeps the pre-#1204 behaviour of
the installation-wide sweep.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantStatus, TenantType
from app.domain.models.tenant import Tenant

TODAY = datetime.now(UTC).isoformat()
CLOSED_STATES = [TenantStatus.PENDING_DELETION, TenantStatus.SUSPENDED, TenantStatus.ORPHANED, TenantStatus.DELETED]


def _tenant(key: str, status: TenantStatus = TenantStatus.ACTIVE) -> Tenant:
    return Tenant(
        _key=key, name=key, slug=key, tenant_type=TenantType.ORGANIZATION, owner_user_key="owner", status=status
    )


class _Tenants:
    """``ITenantRepository.get_by_key`` (and the paged listing ``escalate_overdue`` walks) over stored tenants."""

    def __init__(self, *tenants: Tenant) -> None:
        self.stored = {t.key: t for t in tenants}
        self.asked: list[str] = []

    def get_by_key(self, key: str) -> Tenant | None:
        self.asked.append(key)
        return self.stored.get(key)

    def get_all(self, offset: int = 0, limit: int = 1000, **_kwargs):  # noqa: ANN201 - the paging contract
        rows = list(self.stored.values())
        return rows[offset : offset + limit], len(rows)


# ── generate_due_care_reminders ─────────────────────────────────────────────


@pytest.fixture
def care_deps(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    deps = ModuleType("app.common.dependencies")
    for getter in (
        "get_care_reminder_service",
        "get_lifecycle_repo",
        "get_nutrient_plan_repo",
        "get_phase_sequence_repo",
        "get_plant_repo",
        "get_planting_run_repo",
        "get_season_state_repo",
        "get_task_repo",
        "get_tenant_repo",
    ):
        setattr(deps, getter, MagicMock())
    monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)
    return deps


def _wire_care(deps: ModuleType, tenants: _Tenants, plants: dict[str, str | None]) -> MagicMock:
    """One care profile per plant in *plants* (plant key -> tenant key); a watering task is always due."""
    care_service = MagicMock()
    care_service._repo.get_all_profiles.return_value = [SimpleNamespace(plant_key=key) for key in plants]
    care_service._repo.count_plants_without_profile.return_value = 0
    care_service._engine.should_generate_reminder.return_value = False
    care_service.ensure_next_watering_task.return_value = SimpleNamespace(due_date="2026-10-10")
    deps.get_care_reminder_service.return_value = care_service
    deps.get_planting_run_repo.return_value.get_plant_keys_with_active_schedule.return_value = set()
    deps.get_plant_repo.return_value.get_by_key.side_effect = lambda key: SimpleNamespace(
        current_phase_key=None,
        plant_name=key,
        instance_id=key,
        tenant_key=plants[key],
        removed_on=None,
        species_key="species-1",
        cultivar_key=None,
        site_key=None,
    )
    deps.get_nutrient_plan_repo.return_value.get_plant_plan.return_value = None
    deps.get_phase_sequence_repo.return_value = None
    deps.get_tenant_repo.return_value = tenants
    return care_service


def _watered(care_service: MagicMock) -> list[str]:
    return [call.args[0].plant_key for call in care_service.ensure_next_watering_task.call_args_list]


@pytest.mark.parametrize("status", CLOSED_STATES)
def test_no_care_task_is_generated_in_a_tenant_that_is_not_active(care_deps: ModuleType, status: TenantStatus) -> None:
    tenants = _Tenants(_tenant("t-open"), _tenant("t-closed", status))
    care_service = _wire_care(care_deps, tenants, {"p-open": "t-open", "p-closed": "t-closed"})

    from app.tasks.care_tasks import generate_due_care_reminders

    result = generate_due_care_reminders()

    assert _watered(care_service) == ["p-open"]
    assert result["created"] == 1


def test_a_plant_whose_tenant_is_gone_gets_no_care_task(care_deps: ModuleType) -> None:
    care_service = _wire_care(care_deps, _Tenants(), {"p-1": "t-erased"})

    from app.tasks.care_tasks import generate_due_care_reminders

    generate_due_care_reminders()

    assert _watered(care_service) == []


def test_a_plant_without_a_tenant_keeps_the_installation_sweep(care_deps: ModuleType) -> None:
    tenants = _Tenants()
    care_service = _wire_care(care_deps, tenants, {"p-legacy": None})

    from app.tasks.care_tasks import generate_due_care_reminders

    generate_due_care_reminders()

    assert _watered(care_service) == ["p-legacy"]
    assert tenants.asked == []


def test_each_tenant_is_read_once_per_run(care_deps: ModuleType) -> None:
    tenants = _Tenants(_tenant("t-1"))
    _wire_care(care_deps, tenants, {f"p-{i}": "t-1" for i in range(4)})

    from app.tasks.care_tasks import generate_due_care_reminders

    generate_due_care_reminders()

    assert tenants.asked == ["t-1"]


# ── the notification beats ──────────────────────────────────────────────────


class _Memberships:
    def get_by_user_and_tenant(self, _user_key: str, _tenant_key: str):  # noqa: ANN201
        return MagicMock(is_active=True)  # everybody is an active member: only the tenant decides


class _Notifier:
    def __init__(self) -> None:
        self.care: list[str] = []
        self.summaries: list[str] = []
        self.escalated: list[str] = []
        self.prefs = MagicMock()
        self.prefs.daily_summary.enabled = True
        self._engine = SimpleNamespace(escalate_overdue=self._escalate)

    async def send_care_notifications(self, tenant_key: str, tasks: list[dict]) -> dict:
        self.care.append(tenant_key)
        return {"users_notified": 1, "total_sent": len(tasks)}

    def get_preferences(self, _user_key: str):  # noqa: ANN201
        return self.prefs

    async def send_notification(self, **kwargs) -> None:  # noqa: ANN003
        self.summaries.append(kwargs["tenant_key"])

    async def _escalate(self, tenant_key: str) -> dict:
        self.escalated.append(tenant_key)
        return {"escalated": 1}


def _task(tenant: str) -> dict:
    return {
        "category": "care_reminder",
        "status": "pending",
        "due_date": TODAY,
        "priority": "medium",
        "name": f"Plant-{tenant} — watering",
        "plant_key": f"p-{tenant}",
        "assigned_to": "member",
        "tenant_key": tenant,
    }


@pytest.fixture
def notify(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN201
    def _build(status: TenantStatus) -> _Notifier:
        deps = ModuleType("app.common.dependencies")
        notifier = _Notifier()
        tasks = MagicMock()
        tasks.get_all.return_value = ([_task("t-open"), _task("t-closed")], 2)
        deps.get_task_repo = MagicMock(return_value=tasks)  # type: ignore[attr-defined]
        deps.get_notification_service = MagicMock(return_value=notifier)  # type: ignore[attr-defined]
        deps.get_membership_repo = MagicMock(return_value=_Memberships())  # type: ignore[attr-defined]
        deps.get_tenant_repo = MagicMock(  # type: ignore[attr-defined]
            return_value=_Tenants(_tenant("t-open"), _tenant("t-closed", status))
        )
        monkeypatch.setitem(sys.modules, "app.common.dependencies", deps)
        return notifier

    return _build


@pytest.mark.parametrize("status", CLOSED_STATES)
def test_the_due_care_dispatch_leaves_out_a_tenant_that_is_not_active(notify, status: TenantStatus) -> None:  # noqa: ANN001
    notifier = notify(status)
    from app.tasks.notification_tasks import dispatch_due_care_notifications

    result = dispatch_due_care_notifications()

    assert notifier.care == ["t-open"]
    assert result["tasks_found"] == 1


@pytest.mark.parametrize("status", CLOSED_STATES)
def test_the_daily_summary_leaves_out_a_tenant_that_is_not_active(notify, status: TenantStatus) -> None:  # noqa: ANN001
    notifier = notify(status)
    from app.tasks.notification_tasks import send_daily_summary

    send_daily_summary()

    assert notifier.summaries == ["t-open"]


@pytest.mark.parametrize("status", CLOSED_STATES)
def test_the_escalation_leaves_out_a_tenant_that_is_not_active(notify, status: TenantStatus) -> None:  # noqa: ANN001
    notifier = notify(status)
    from app.tasks.notification_tasks import escalate_overdue_notifications

    result = escalate_overdue_notifications()

    assert notifier.escalated == ["t-open"]
    assert result["tenants_processed"] == 1
