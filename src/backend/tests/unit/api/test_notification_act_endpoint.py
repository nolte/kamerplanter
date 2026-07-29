"""Unit tests for the REQ-030 §4.2 actionable ``/act`` callback (#742).

The router function is exercised directly with mocked services so the one-tap
"Done" orchestration (confirm the source care reminder + stamp acted/read) is
asserted without spinning up the full ASGI/auth stack.
"""

from __future__ import annotations

import pytest

from app.api.v1.notifications.tenant_router import mark_acted
from app.common.enums import ReminderType, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.notification import Notification, NotificationStatus
from app.domain.models.tenant_context import TenantContext


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key="t1",
        tenant_slug="personal",
        user_key="user-a",
        role=TenantRole.LEAD,
    )


class _ServiceStub:
    def __init__(self, notif: Notification | None) -> None:
        self._notif = notif
        self.mark_read_calls: list[tuple] = []
        self.mark_acted_calls: list[tuple] = []

    def get_notification(self, key, tenant_key, user_key=None):
        return self._notif

    def mark_read(self, key, tenant_key, user_key=None):
        self.mark_read_calls.append((key, tenant_key, user_key))
        return self._notif

    def mark_acted(self, key, tenant_key, action_id, user_key=None):
        self.mark_acted_calls.append((key, tenant_key, action_id, user_key))
        if self._notif is not None:
            self._notif.acted_at = self._notif.acted_at
        return self._notif


class _CareStub:
    def __init__(self) -> None:
        self.confirm_calls: list[dict] = []

    def confirm_reminder(self, plant_key, reminder_type, *, tenant_key="", user_key=""):
        self.confirm_calls.append(
            {
                "plant_key": plant_key,
                "reminder_type": reminder_type,
                "tenant_key": tenant_key,
                "user_key": user_key,
            }
        )


def _care_notification() -> Notification:
    return Notification(
        _key="n1",
        tenant_key="t1",
        user_key="user-a",
        notification_type="care.watering",
        title="Monstera",
        body="watering due",
        data={"plant_key": "plant1", "reminder_type": "watering"},
        group_key="care.watering:plant1",
        status=NotificationStatus.DELIVERED,
    )


def test_act_on_care_notification_confirms_source():
    notif = _care_notification()
    service = _ServiceStub(notif)
    care = _CareStub()

    mark_acted("n1", action_id="confirm", ctx=_ctx(), service=service, care_service=care)

    # §4.2 — the source reminder is confirmed for the plant + type in the data.
    assert len(care.confirm_calls) == 1
    call = care.confirm_calls[0]
    assert call["plant_key"] == "plant1"
    assert call["reminder_type"] == ReminderType.WATERING
    assert call["tenant_key"] == "t1"
    assert call["user_key"] == "user-a"
    # ... and the notification is stamped read + acted.
    assert service.mark_read_calls
    assert service.mark_acted_calls


def test_act_on_non_care_notification_does_not_confirm():
    notif = _care_notification()
    notif.notification_type = "task.due"
    notif.data = {"task_key": "task1"}
    service = _ServiceStub(notif)
    care = _CareStub()

    mark_acted("n1", action_id="confirm", ctx=_ctx(), service=service, care_service=care)

    assert care.confirm_calls == []  # no care source to confirm
    assert service.mark_acted_calls  # but still acted


def test_act_ignores_non_confirm_action():
    notif = _care_notification()
    service = _ServiceStub(notif)
    care = _CareStub()

    mark_acted("n1", action_id="snooze", ctx=_ctx(), service=service, care_service=care)

    assert care.confirm_calls == []
    assert service.mark_acted_calls


def test_act_missing_notification_raises_not_found():
    service = _ServiceStub(None)
    care = _CareStub()

    with pytest.raises(NotFoundError):
        mark_acted("missing", action_id="confirm", ctx=_ctx(), service=service, care_service=care)
    assert care.confirm_calls == []
