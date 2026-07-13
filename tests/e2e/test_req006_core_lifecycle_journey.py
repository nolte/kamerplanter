"""E2E core-lifecycle journeys for REQ-006 — care task queue (self-provisioning).

Spec-TC Mapping (test TC -> spec/e2e-testcases/TC-REQ-006.md, Gruppe 17):
  TC-REQ-006-J076  ->  TC-006-076  Core-Journey — create a care task and complete it in the queue
  TC-REQ-006-J077  ->  TC-006-077  Core-Journey — completed care task is documented

Each journey provisions its own plant instance through the real create dialog, so
the core path always runs — no runtime ``pytest.skip`` for missing seed data
(NFR-008a §2 self-provisioning; UI-NFR-022 data-testid addressing).

Adaptations to the real implemented flow (issue #589 R3):
- The TaskCreateDialog category enum has no dedicated "watering/Gießen" value; the
  journey uses the ``care_reminder`` (Pflege) category, which is the care-task
  category in the merged task queue.
- The TaskQueuePage has no "show completed tasks" toggle. TC-006-077 therefore
  verifies the completed task on the plant instance's Tasks tab, which reliably
  lists open *and* completed tasks (#578/#599) — the real surface where a
  completed care task stays documented. See the referenced follow-up issue.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from ._journey_helpers import provision_plant, unique_suffix
from .pages.phase_transition_page import PlantInstanceDetailExt
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.task_queue_page import TaskQueuePage


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def plant_creator(browser: WebDriver, base_url: str) -> PlantInstanceListPage:
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: WebDriver, base_url: str) -> PlantInstanceDetailExt:
    return PlantInstanceDetailExt(browser, base_url)


@pytest.fixture
def task_queue(browser: WebDriver, base_url: str) -> TaskQueuePage:
    return TaskQueuePage(browser, base_url)


# ── Shared arrange step ──────────────────────────────────────────────────────


def _create_care_task(
    task_queue: TaskQueuePage, instance_id: str, task_name: str
) -> None:
    """Create a care task for the plant *instance_id* via the queue dialog."""
    task_queue.open()
    task_queue.click_create_task()
    task_queue.fill_task_name(task_name)
    task_queue.select_task_category("care_reminder")
    task_queue.set_due_date_today()
    task_queue.select_task_priority("high")
    task_queue.select_task_plant_by_text(instance_id)
    task_queue.submit_task_form()
    task_queue.wait_for_loading_complete()


# ── TC-006-076 ───────────────────────────────────────────────────────────────


class TestCoreJourneyCreateAndCompleteTask:
    """Self-provision a plant, create a care task and complete it in the queue."""

    @pytest.mark.smoke
    @pytest.mark.core_crud
    def test_create_and_complete_care_task(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-J076: Create a care task and complete it from the queue.

        Spec: TC-006-076 -- Core-Journey Pflege-Task anlegen + abschließen.
        """
        _key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-006")
        task_name = f"Journey gießen {unique_suffix()}"

        _create_care_task(task_queue, instance_id, task_name)
        screenshot("TC-REQ-006-J076_task-created",
                   f"Task queue after creating '{task_name}'")

        task_key = task_queue.find_task_key_by_name(task_name)
        assert task_key is not None, (
            f"TC-REQ-006-J076 FAIL: Newly created task '{task_name}' should appear in the queue"
        )

        task_queue.complete_task(task_key)
        time.sleep(1.0)
        screenshot("TC-REQ-006-J076_task-completed",
                   "Task queue after completing the care task")

        # The completed task leaves the active groups (overdue/today/week).
        task_queue.open()
        assert not task_queue.has_task_with_name(task_name), (
            f"TC-REQ-006-J076 FAIL: Completed task '{task_name}' should disappear "
            f"from the active task queue"
        )


# ── TC-006-077 ───────────────────────────────────────────────────────────────


class TestCoreJourneyCompletedTaskDocumented:
    """A completed care task stays documented on the plant's Tasks tab."""

    @pytest.mark.core_crud
    def test_completed_task_visible_on_plant_tab(
        self,
        plant_creator: PlantInstanceListPage,
        task_queue: TaskQueuePage,
        plant_detail: PlantInstanceDetailExt,
        screenshot: Callable[..., Path],
    ) -> None:
        """TC-REQ-006-J077: Completed care task remains documented for the plant.

        Spec: TC-006-077 -- Core-Journey abgeschlossener Care-Task nachvollziehbar.
        Verified on the plant instance Tasks tab (real flow; the queue has no
        "show completed" toggle — see PR follow-up issue).
        """
        key, instance_id = provision_plant(plant_creator, id_prefix="JOURNEY-006V")
        task_name = f"Journey gießen {unique_suffix()}"

        _create_care_task(task_queue, instance_id, task_name)
        task_key = task_queue.find_task_key_by_name(task_name)
        assert task_key is not None, (
            f"TC-REQ-006-J077 FAIL: Task '{task_name}' should appear before completion"
        )
        task_queue.complete_task(task_key)
        time.sleep(1.0)

        # The plant's Tasks tab lists open AND completed tasks (#578/#599).
        plant_detail.open(key)
        plant_detail.open_tasks_tab()
        screenshot("TC-REQ-006-J077_plant-tasks-tab",
                   f"Plant {instance_id} Tasks tab showing the completed task")
        assert task_name in plant_detail.get_body_text(), (
            f"TC-REQ-006-J077 FAIL: Completed task '{task_name}' should stay documented "
            f"on the plant instance Tasks tab"
        )
