"""E2E core-lifecycle journeys for REQ-022 — care reminders (self-provisioning).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-022.md, Abschnitt 27):
  TC-REQ-022-J087  ->  TC-022-087  Core-Journey — new plant yields a watering reminder, one-tap confirm
  TC-REQ-022-J088  ->  TC-022-088  Core-Journey — after confirmation the reminder is no longer due (reload)

Each journey provisions its own plant instance through the real create dialog and
triggers care-reminder generation, so the core path always runs — no runtime
``pytest.skip`` for missing seed data (NFR-008a §2 self-provisioning; UI-NFR-022).

Adaptation to the real implemented flow (issue #589 R3): the ``/pflege`` route
redirects to ``/aufgaben/queue`` (REQ-022 care dashboard merged into the task
queue; the standalone ``PflegeDashboardPage.tsx`` component is not wired into
``AppRoutes.tsx``). The journeys therefore act on the care-reminder cards in the
merged task queue — the surface a browser user actually reaches. See the
referenced PR follow-up issue.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import provision_plant_with_live_watering_card
from .pages.pflege_dashboard_page import PflegeDashboardPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_queue_page import TaskQueuePage


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def plant_creator(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    return TaskQueuePage(browser, base_url)


@pytest.fixture
def pflege(browser: WebDriver, base_url: str) -> PflegeDashboardPage:
    return PflegeDashboardPage(browser, base_url)


# ── Shared arrange step ──────────────────────────────────────────────────────


# ── TC-022-087 ───────────────────────────────────────────────────────────────


class TestCoreJourneyConfirmWateringReminder:
    """A freshly provisioned plant yields a watering reminder that is confirmed."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_confirm_watering_reminder(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-087: New plant → watering reminder → one-tap confirm.

        Spec: TC-022-087 -- Core-Journey Gieß-Erinnerung bestätigen.
        """
        key, instance_id = provision_plant_with_live_watering_card(
            plant_creator, pflege, id_prefix="JOURNEY-022"
        )
        screenshot(
            "TC-REQ-022-J087_reminder-card",
            f"Care dashboard with watering reminder for {instance_id}",
        )

        pflege.click_confirm_on_card(key, "watering")
        # The one-tap confirm may open a CareConfirmDialog for measurements — submit it.
        time.sleep(0.5)
        if pflege.is_confirm_dialog_open():
            pflege.submit_confirm_dialog()
        time.sleep(1.0)
        screenshot(
            "TC-REQ-022-J087_after-confirm", "Care dashboard after confirming the watering reminder"
        )

        pflege.open()
        assert not pflege.has_care_card(key, "watering"), (
            f"TC-REQ-022-J087 FAIL: Watering reminder for '{instance_id}' should be gone "
            f"after confirmation"
        )


# ── TC-022-088 ───────────────────────────────────────────────────────────────


class TestCoreJourneyReminderPersistsConfirmed:
    """After confirmation the reminder stays gone across a reload."""

    @pytest.mark.core_crud
    def test_reminder_not_due_after_reload(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        pflege: PflegeDashboardPage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-022-088: After confirmation the reminder is no longer due (reload).

        Spec: TC-022-088 -- Core-Journey Reload-Persistenz der Bestätigung.
        """
        key, instance_id = provision_plant_with_live_watering_card(
            plant_creator, pflege, id_prefix="JOURNEY-022P"
        )
        pflege.click_confirm_on_card(key, "watering")
        time.sleep(0.5)
        if pflege.is_confirm_dialog_open():
            pflege.submit_confirm_dialog()
        time.sleep(1.0)

        # Reload the dashboard — the confirmation must persist server-side.
        pflege.open()
        screenshot(
            "TC-REQ-022-J088_after-reload",
            f"Care dashboard after reload — reminder for {instance_id} not due",
        )
        assert not pflege.has_care_card(key, "watering"), (
            f"TC-REQ-022-J088 FAIL: After reload the watering reminder for '{instance_id}' "
            f"should remain confirmed (not due)"
        )
