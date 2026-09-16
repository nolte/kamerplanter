"""Who may confirm a care reminder through the notification callback (#1441).

`POST /t/{slug}/notifications/{key}/act` carried no rank check at all: every
route in `notifications/tenant_router.py` resolved its caller through bare
`get_current_tenant`, which establishes membership and not rank. For a `care.*`
notification with a confirm action the handler reaches
`CareReminderService.confirm_reminder`, which persists a `CareConfirmation` and
a `WateringLog` — exactly the writes `require_permission('watering-log',
CREATE)` refuses a viewer on the direct route
(`watering_logs/tenant_router.py:57`). A viewer therefore had a one-tap bypass
of the rank gate.

The allowlist entry in `tests/unit/api/test_write_route_gates.py` claimed that
branch was "gated inline on the domain role". Nothing checked that claim and it
was never true; this module is what checks it now.

## What the tests hold the route to

Three statements, because a gate that refuses everyone would satisfy the first
alone and break the feature:

1. a viewer tapping a confirm action on a `care.*` notification is refused, and
   **no** `CareConfirmation` and **no** `WateringLog` reaches a repository;
2. a grower still confirms, and both writes happen;
3. a viewer still gets a **non**-care notification stamped read + acted — the
   per-user state of `mark_acted` stays open to every member, which is what the
   allowlist entry is legitimately about.

## Real vs doubled

**Real**: the notifications tenant router, the error handler that shapes the
403, `MembershipEngine`'s rank predicate as the handler consumes it, and the
real `CareReminderService` — so "no confirmation was written" is provable as an
absent repository call rather than as an absent call on a service double that
could have been shaped to agree. **Doubled**: the care-reminder, plant and
watering-log repositories (recorders), and the notification service, whose
per-user stamping is the third statement's subject and not the write under test.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.notifications.tenant_router import router as notifications_router
from app.common import auth as auth_mod
from app.common.dependencies import get_care_reminder_service, get_notification_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.notification import Notification, NotificationAction, NotificationStatus
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.care_reminder_service import CareReminderService

_TENANT_KEY = "t1"
_PLANT_KEY = "plant1"


class _RecordingCareRepo:
    """Care-reminder repository recorder: a refusal is an absent `create_confirmation`."""

    def __init__(self) -> None:
        self.confirmations: list[Any] = []
        self.edges: list[tuple[str, str, str]] = []
        self.updated_profiles: list[tuple[str, Any]] = []

    # ── reads ──
    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile:
        return CareProfile(_key="profile1", plant_key=plant_key, adaptive_learning_enabled=False)

    def get_confirmations_by_plant(self, plant_key: str, reminder_type: Any, limit: int = 10) -> list[Any]:
        return []

    # ── writes ──
    def create_confirmation(self, confirmation: Any) -> Any:
        self.confirmations.append(confirmation)
        confirmation.key = f"confirmation{len(self.confirmations)}"
        return confirmation

    def create_confirmation_edges(self, confirmation_key: str, profile_key: str, plant_key: str) -> None:
        self.edges.append((confirmation_key, profile_key, plant_key))

    def update_profile(self, key: str, profile: Any) -> Any:
        self.updated_profiles.append((key, profile))
        return profile


class _RecordingWateringLogRepo:
    """Watering-log repository recorder."""

    def __init__(self) -> None:
        self.created: list[Any] = []

    def create(self, log: Any) -> Any:
        self.created.append(log)
        log.key = f"log{len(self.created)}"
        return log


class _PlantRepo:
    """Resolves the one plant the care notification points at."""

    def __init__(self) -> None:
        self._plant = PlantInstance(
            _key=_PLANT_KEY,
            tenant_key=_TENANT_KEY,
            instance_id="P-1",
            species_key="species1",
            slot_key="slot1",
            planted_on=date(2026, 1, 1),
        )

    def get_by_key(self, key: str) -> PlantInstance | None:
        return self._plant if key == _PLANT_KEY else None

    def get_or_raise(self, key: str) -> PlantInstance:
        plant = self.get_by_key(key)
        if plant is None:  # pragma: no cover - the tests only address the known plant
            raise AssertionError(f"unexpected plant key {key}")
        return plant


class _NotificationServiceStub:
    """Serves the addressed notification and records the per-user stamping."""

    def __init__(self, notification: Notification) -> None:
        self._notification = notification
        self.read_calls: list[tuple] = []
        self.acted_calls: list[tuple] = []

    def get_notification(self, key: str, tenant_key: str, user_key: str | None = None) -> Notification | None:
        return self._notification if key == self._notification.key else None

    def mark_read(self, key: str, tenant_key: str, user_key: str | None = None) -> Notification | None:
        self.read_calls.append((key, tenant_key, user_key))
        return self._notification

    def mark_acted(self, key: str, tenant_key: str, action_id: str, user_key: str | None = None) -> Notification | None:
        self.acted_calls.append((key, tenant_key, action_id, user_key))
        return self._notification


def _notification(*, notification_type: str, data: dict[str, Any]) -> Notification:
    return Notification(
        _key="n1",
        tenant_key=_TENANT_KEY,
        user_key="user-a",
        notification_type=notification_type,
        title="Monstera",
        body="watering due",
        data=data,
        actions=[NotificationAction(action_id="confirm", title="Erledigt")],
        group_key="care.watering:plant1",
        status=NotificationStatus.DELIVERED,
    )


def _care_notification() -> Notification:
    return _notification(
        notification_type="care.watering",
        data={"plant_key": _PLANT_KEY, "reminder_type": "watering"},
    )


class _Harness:
    """The mounted route plus the recorders behind it."""

    def __init__(self, *, role: TenantRole, notification: Notification) -> None:
        self.care_repo = _RecordingCareRepo()
        self.watering_log_repo = _RecordingWateringLogRepo()
        self.notification_service = _NotificationServiceStub(notification)
        care_service = CareReminderService(
            self.care_repo,  # type: ignore[arg-type]
            CareReminderEngine(),
            watering_log_repo=self.watering_log_repo,  # type: ignore[arg-type]
            plant_repo=_PlantRepo(),  # type: ignore[arg-type]
        )

        app = FastAPI()
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.include_router(notifications_router, prefix="/api/v1/t/{tenant_slug}")
        app.dependency_overrides[auth_mod.get_current_tenant] = lambda: TenantContext(
            tenant_key=_TENANT_KEY,
            tenant_slug="personal",
            user_key="user-a",
            role=role,
        )
        app.dependency_overrides[get_notification_service] = lambda: self.notification_service
        app.dependency_overrides[get_care_reminder_service] = lambda: care_service
        self.client = TestClient(app)

    def act(self, action_id: str = "confirm"):
        return self.client.post(
            f"/api/v1/t/personal/notifications/n1/act?action_id={action_id}",
        )

    @property
    def care_writes(self) -> int:
        return len(self.care_repo.confirmations) + len(self.watering_log_repo.created)


class TestAViewerMayNotConfirmThroughTheNotification:
    """The gap: the one-tap callback wrote what the direct route refuses a viewer."""

    def test_confirm_action_is_refused(self) -> None:
        harness = _Harness(role=TenantRole.VIEWER, notification=_care_notification())

        response = harness.act()

        assert response.status_code == 403, response.text

    def test_no_care_confirmation_and_no_watering_log_is_written(self) -> None:
        harness = _Harness(role=TenantRole.VIEWER, notification=_care_notification())

        harness.act()

        assert harness.care_repo.confirmations == [], "a CareConfirmation reached the repository"
        assert harness.watering_log_repo.created == [], "a WateringLog reached the repository"
        assert harness.care_writes == 0

    def test_the_refusal_names_the_rank_the_caller_lacks(self) -> None:
        """A generic 403 leaves the caller guessing between "not this tenant" and "not this role"."""
        harness = _Harness(role=TenantRole.VIEWER, notification=_care_notification())

        response = harness.act()

        assert "viewer" in response.text.lower()

    def test_the_notification_is_not_stamped_either(self) -> None:
        """The refusal happens before the per-user stamping, so the badge does not lie.

        Dropping the reminder out of the unread list while refusing to record the
        care it announced would leave the plant silently unwatered.
        """
        harness = _Harness(role=TenantRole.VIEWER, notification=_care_notification())

        harness.act()

        assert harness.notification_service.acted_calls == []


class TestAGrowerStillConfirms:
    """The half that keeps the gate from being a blanket refusal."""

    def test_the_confirmation_and_the_watering_log_are_written(self) -> None:
        harness = _Harness(role=TenantRole.GROWER, notification=_care_notification())

        response = harness.act()

        assert response.status_code == 200, response.text
        assert len(harness.care_repo.confirmations) == 1
        assert len(harness.watering_log_repo.created) == 1
        assert harness.watering_log_repo.created[0].tenant_key == _TENANT_KEY
        assert harness.notification_service.acted_calls, "the notification is still stamped acted"

    def test_a_lead_confirms_too(self) -> None:
        harness = _Harness(role=TenantRole.LEAD, notification=_care_notification())

        response = harness.act()

        assert response.status_code == 200, response.text
        assert len(harness.care_repo.confirmations) == 1


class TestPerUserStateStaysOpenToEveryMember:
    """No collateral damage: `mark_acted` is per-user state for everything else."""

    def test_a_viewer_still_acts_on_a_non_care_notification(self) -> None:
        harness = _Harness(
            role=TenantRole.VIEWER,
            notification=_notification(notification_type="task.due", data={"task_key": "task1"}),
        )

        response = harness.act()

        assert response.status_code == 200, response.text
        assert harness.notification_service.read_calls, "read was stamped"
        assert harness.notification_service.acted_calls, "acted was stamped"
        assert harness.care_writes == 0

    def test_a_viewer_still_acts_on_a_care_notification_with_a_non_confirm_action(self) -> None:
        """Only the confirming branch writes; snoozing a care reminder does not."""
        harness = _Harness(role=TenantRole.VIEWER, notification=_care_notification())

        response = harness.act(action_id="snooze")

        assert response.status_code == 200, response.text
        assert harness.notification_service.acted_calls
        assert harness.care_writes == 0


@pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD])
def test_the_rank_the_route_demands_is_the_one_the_direct_route_demands(role: TenantRole) -> None:
    """Pins the two surfaces to the *same* predicate, not to two role lists that agree today.

    `require_permission('watering-log', CREATE)` resolves through
    `MembershipEngine.can_edit_resource`; so does the branch gate. Were either
    side to literalise a role list, this case turns red for the role they stop
    agreeing on.
    """
    from app.domain.engines.membership_engine import MembershipEngine

    harness = _Harness(role=role, notification=_care_notification())

    response = harness.act()

    expected = 200 if MembershipEngine.can_edit_resource(role) else 403
    assert response.status_code == expected, response.text
